"""
RAG Helpers
Retrieve relevant context from memory and format as system message.
"""

from typing import Optional, List, Dict, Any
from autogen_agentchat.messages import TextMessage


async def build_memory_context(memory_system, user_id: str, agent_id: Optional[str], query: str, limit: int = 5, *, similarity_threshold: float = 0.0) -> Optional[TextMessage]:
    if not memory_system:
        return None
    memories: List[Any] = await memory_system.retrieve_relevant_context(
        query=query, user_id=user_id, agent_id=agent_id, limit=limit * 2
    )
    if not memories:
        return None
    # Simple heuristics: filter by similarity, de-duplicate and cap length
    seen: set[str] = set()
    distilled: List[str] = []
    for m in memories:
        content = (getattr(m, 'content', None) or "").strip()
        score = getattr(m, 'score', None)
        if score is None:
            # try metadata
            score = getattr(m, 'metadata', {}).get('score', None) if hasattr(m, 'metadata') else None
        if similarity_threshold and isinstance(score, (int, float)):
            if score < similarity_threshold:
                continue
        if not content or content.lower() in seen:
            continue
        seen.add(content.lower())
        distilled.append(content[:400])
        if len(distilled) >= limit:
            break
    facts = "\n".join(f"- {c}" for c in distilled)
    return TextMessage(content=f"Relevant context:\n{facts}", source="system")

