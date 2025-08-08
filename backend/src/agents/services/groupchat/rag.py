"""
RAG Helpers
Retrieve relevant context from memory and format as system message.
"""

from typing import Optional, List, Dict
from autogen_agentchat.messages import TextMessage


async def build_memory_context(memory_system, user_id: str, agent_id: Optional[str], query: str, limit: int = 5) -> Optional[TextMessage]:
    if not memory_system:
        return None
    memories = await memory_system.retrieve_relevant_context(
        query=query, user_id=user_id, agent_id=agent_id, limit=limit
    )
    if not memories:
        return None
    # Simple heuristics: de-duplicate and cap length
    seen: set[str] = set()
    distilled: List[str] = []
    for m in memories:
        content = (m.content or "").strip()
        if not content or content.lower() in seen:
            continue
        seen.add(content.lower())
        distilled.append(content[:400])
        if len(distilled) >= limit:
            break
    facts = "\n".join(f"- {c}" for c in distilled)
    return TextMessage(content=f"Relevant context:\n{facts}", source="system")


