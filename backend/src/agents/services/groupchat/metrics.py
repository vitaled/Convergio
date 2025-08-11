"""
GroupChat Metrics
Helpers to extract response, agents used, turns, and estimate cost.
"""

from typing import List, Dict, Any
from datetime import datetime


def extract_final_response(messages: List[Any]) -> str:
    if not messages:
        raise ValueError("messages list is empty")
    last = messages[-1]
    if not hasattr(last, "content") or not last.content:
        raise ValueError("last message has no content")
    
    # NO FALLBACK! If tool calls are not executed, we fail properly
    if isinstance(last.content, list):
        # Tool calls detected but not executed - this is an ERROR
        raise ValueError(f"Tool calls were not executed properly: {last.content}")
    
    return last.content


def extract_agents_used(messages: List[Any]) -> List[str]:
    agents = []
    for msg in messages:
        source = getattr(msg, "source", None)
        if source:
            agents.append(source)
    return list(set(agents))


def estimate_cost(messages: List[Any]) -> Dict[str, Any]:
    estimated_tokens = 1000
    cost_per_1k_tokens = 0.01
    total_cost = (estimated_tokens / 1000) * cost_per_1k_tokens
    return {
        "total_cost": total_cost,
        "estimated_tokens": estimated_tokens,
        "cost_per_1k_tokens": cost_per_1k_tokens,
        "currency": "USD",
    }


def serialize_chat_history(messages: List[Any]) -> List[Dict[str, Any]]:
    result = []
    for msg in messages:
        result.append({
            "source": getattr(msg, "source", "unknown"),
            "content": getattr(msg, "content", ""),
            "timestamp": getattr(msg, "created_at", datetime.now()).isoformat(),
        })
    return result


