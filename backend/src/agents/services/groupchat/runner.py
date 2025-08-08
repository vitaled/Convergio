"""
GroupChat Runner
Utilities to run GroupChat streaming and collect messages and response.
"""

from typing import List, Tuple, Any


async def run_groupchat_stream(group_chat, task: str) -> Tuple[List[Any], str]:
    messages: List[Any] = []
    full_response = ""
    async for response in group_chat.run_stream(task=task):
        messages.append(response)
        if hasattr(response, "content") and response.content:
            full_response += response.content
    return messages, full_response


