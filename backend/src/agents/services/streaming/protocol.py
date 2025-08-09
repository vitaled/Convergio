"""
Streaming protocol shim for tests.
Defines event types and a tiny parser compatible with tests and server frames.
"""

from enum import Enum
from typing import Any, Dict, Tuple


class StreamingEventType(str, Enum):
    delta = "delta"
    agent_status = "agent_status"
    final = "final"
    error = "error"
    status = "status"
    tool_call = "tool_call"
    tool_result = "tool_result"
    handoff = "handoff"
    heartbeat = "heartbeat"


class StreamingProtocol:
    """Minimal protocol utilities used by tests."""

    def parse_frame(self, frame: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Return (event, data) from a server frame {type,event,data}.
        Falls back to top-level if already flat.
        """
        if "event" in frame and "data" in frame:
            return frame.get("event", "status"), frame.get("data", {})
        # Fallback for flat frames
        event = frame.get("chunk_type") or frame.get("event") or "status"
        return event, frame

