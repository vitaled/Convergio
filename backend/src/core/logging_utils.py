"""
Utilities for configuring non-blocking logging suitable for asyncio applications.
"""
import asyncio
import logging
import logging.handlers
from queue import Queue
from typing import List

class LocalQueueHandler(logging.handlers.QueueHandler):
    """A custom QueueHandler that avoids unnecessary processing for in-process queues."""
    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a record.

        Writes the LogRecord to the queue, handling task cancellation gracefully.
        This version removes the expensive `prepare()` call, as it's not needed
        for local, in-process queues.
        """
        try:
            self.enqueue(record)
        except asyncio.CancelledError:
            raise
        except Exception:
            self.handleError(record)

def setup_async_logging() -> None:
    """
    Set up non-blocking logging by moving all existing root handlers
    to a QueueListener running in a separate thread.

    This prevents logging I/O (e.g., writing to files or the console)
    from blocking the asyncio event loop.
    """
    queue = Queue()
    root_logger = logging.getLogger()

    # It's crucial to not have any handlers on the root logger when using structlog
    if not root_logger.hasHandlers():
        # If no handlers are configured, add a default one to capture logs.
        # This is a fallback and assumes basic console logging is desired.
        # In a real app, this should be configured properly before calling this function.
        logging.basicConfig()

    handlers: List[logging.Handler] = []

    # Create a queue handler to replace the existing handlers
    queue_handler = LocalQueueHandler(queue)

    # Remove existing handlers and store them for the listener
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handlers.append(handler)

    # Add the single queue handler to the root logger
    root_logger.addHandler(queue_handler)

    # Create and start the listener with the original handlers
    listener = logging.handlers.QueueListener(
        queue, *handlers, respect_handler_level=True
    )
    listener.start()
    logging.getLogger(__name__).info("Non-blocking asyncio logging configured.")
