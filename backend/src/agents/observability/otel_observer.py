"""
OpenTelemetry-backed AutoGen observer.

Uses the shared start_span helper to gracefully no-op if OTEL isn't configured.
Also emits lightweight structlog info for quick grepping.
"""

from __future__ import annotations

from typing import Any, Dict
import structlog

from ..utils.tracing import start_span
from .autogen_observer import AutoGenObserver


logger = structlog.get_logger()


class OtelAutoGenObserver(AutoGenObserver):
    async def on_conversation_start(self, metadata: Dict[str, Any]) -> None:
        logger.info("observer.conversation_start", **metadata)
        # Start a root span for the conversation; child spans will nest under current context
        with start_span(
            "autogen.conversation",
            {
                "conversation.id": metadata.get("conversation_id"),
                "user.id": metadata.get("user_id"),
                "mode": metadata.get("mode"),
                "agent.name": metadata.get("agent_name"),
            },
        ):
            pass

    async def on_model_stream_event(self, event: Any, metadata: Dict[str, Any]) -> None:
        # Don't log full content to avoid noise; capture sizes and sources
        attrs = {
            "conversation.id": metadata.get("conversation_id"),
            "source": getattr(event, "source", "unknown"),
            "has_content": bool(getattr(event, "content", None)),
        }
        content = getattr(event, "content", None)
        if isinstance(content, str):
            attrs["content.len"] = len(content)
        with start_span("autogen.stream.event", attrs):
            # No-op body; span serves as a breadcrumb
            pass

    async def on_conversation_end(self, summary: Dict[str, Any], metadata: Dict[str, Any]) -> None:
        end_attrs = {
            "conversation.id": metadata.get("conversation_id"),
            "user.id": metadata.get("user_id"),
            "total_messages": summary.get("total_messages"),
            "turn_count": summary.get("turn_count", summary.get("total_messages")),
            "duration.seconds": summary.get("duration_seconds"),
            "cost.total": (summary.get("cost_breakdown", {}) or {}).get("total_cost"),
        }
        logger.info("observer.conversation_end", **{**metadata, **summary})
        with start_span("autogen.conversation.end", end_attrs):
            pass
