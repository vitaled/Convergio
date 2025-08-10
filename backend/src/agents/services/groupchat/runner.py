"""
GroupChat Runner
Utilities to run GroupChat streaming and collect messages and response.

Observer-aware: allows passing observers and run metadata so external systems
can subscribe to stream events without coupling to AutoGen internals.
"""

from typing import List, Tuple, Any, Dict, Iterable, Optional
import time

from ...observability.autogen_observer import AutoGenObserver


async def run_groupchat_stream(
    group_chat,
    task: str,
    *,
    observers: Optional[Iterable[AutoGenObserver]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    hard_timeout_seconds: Optional[int] = None,
    termination_markers: Optional[List[str]] = None,
    max_events: Optional[int] = None,
) -> Tuple[List[Any], str]:
    messages: List[Any] = []
    full_response = ""
    run_meta = metadata or {}
    start_ts = time.monotonic()
    term_markers = [m.lower() for m in (termination_markers or [
        "final answer", "final response", "conclusion", "end_of_conversation", "terminate"
    ])]
    # Notify observers of conversation start (idempotent for direct use)
    if observers:
        for obs in observers:
            try:
                await obs.on_conversation_start({**run_meta, "task": task, "mode": run_meta.get("mode", "groupchat")})
            except Exception:
                pass

    async for response in group_chat.run_stream(task=task):
        messages.append(response)
        if hasattr(response, "content") and response.content:
            full_response += response.content
            # Early termination: content markers
            try:
                content_l = response.content.lower()
                if any(marker in content_l for marker in term_markers):
                    break
            except Exception:
                pass
        # Max events guard
        if max_events is not None and len(messages) >= max_events:
            break
        # Hard timeout guard
        if hard_timeout_seconds is not None and (time.monotonic() - start_ts) >= hard_timeout_seconds:
            # Append a gentle termination notice
            try:
                from autogen_agentchat.messages import TextMessage
                messages.append(TextMessage(content="[conversation truncated due to timeout]", source="system"))
            except Exception:
                pass
            break
        if observers:
            for obs in observers:
                try:
                    await obs.on_model_stream_event(response, run_meta)
                except Exception:
                    pass
    return messages, full_response


