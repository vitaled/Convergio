"""
AutoGen Observer Interface
Lightweight hooks to observe GroupChat runs and direct agent conversations.

These hooks are intentionally minimal to avoid tight coupling with
AutoGen internals. Implementations can forward events to OpenTelemetry,
logs, metrics, or external sinks.
"""

from __future__ import annotations

from typing import Any, Dict


class AutoGenObserver:
    """Observer contract for AutoGen conversations."""

    async def on_conversation_start(self, metadata: Dict[str, Any]) -> None:  # noqa: D401
        """Called when a conversation run starts.

        metadata typically contains:
        - conversation_id: str
        - user_id: str
        - task: str (enhanced message)
        - context: Optional[dict]
        - mode: "groupchat" | "direct-agent"
        - agent_name: Optional[str]
        """

    async def on_model_stream_event(self, event: Any, metadata: Dict[str, Any]) -> None:  # noqa: D401
        """Called for each streamed event/message from the model or agent."""

    async def on_conversation_end(self, summary: Dict[str, Any], metadata: Dict[str, Any]) -> None:  # noqa: D401
        """Called when a conversation run completes.

        summary typically contains:
        - total_messages: int
        - agents_used: list[str]
        - response_preview: str
        - duration_seconds: float (if available)
        - cost_breakdown: dict (if available)
        """
