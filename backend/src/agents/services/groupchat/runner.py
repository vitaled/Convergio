"""
GroupChat Runner
Utilities to run GroupChat streaming and collect messages and response.

Observer-aware: allows passing observers and run metadata so external systems
can subscribe to stream events without coupling to AutoGen internals.
"""

from typing import List, Tuple, Any, Dict, Iterable, Optional

from ...observability.autogen_observer import AutoGenObserver


async def run_groupchat_stream(
    group_chat,
    task: str,
    *,
    observers: Optional[Iterable[AutoGenObserver]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Any], str]:
    messages: List[Any] = []
    full_response = ""
    run_meta = metadata or {}
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
        if observers:
            for obs in observers:
                try:
                    await obs.on_model_stream_event(response, run_meta)
                except Exception:
                    pass
    return messages, full_response


