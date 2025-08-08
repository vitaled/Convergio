"""
Optional tracing utilities.
Uses OpenTelemetry if available; otherwise provides no-op context managers.
"""

from contextlib import contextmanager
from typing import Optional, Dict, Any
import structlog

logger = structlog.get_logger()


@contextmanager
def start_span(name: str, attributes: Optional[Dict[str, Any]] = None):
    """Start a tracing span if OTEL is available; otherwise no-op.

    Example:
        with start_span("conversation", {"conversation_id": cid}):
            ...
    """
    try:
        from opentelemetry import trace  # type: ignore
        tracer = trace.get_tracer("convergio.agents")
        with tracer.start_as_current_span(name) as span:
            if attributes:
                for k, v in attributes.items():
                    try:
                        span.set_attribute(k, v)
                    except Exception:
                        pass
            yield span
        return
    except Exception:
        # No OTEL or failed; fallback to no-op while logging for observability
        logger.debug("tracing_noop", span=name, attrs=attributes or {})
        yield None


