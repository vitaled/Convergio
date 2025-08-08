"""
GroupChat shared types.
"""

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class GroupChatResult:
    response: str
    agents_used: List[str]
    turn_count: int
    duration_seconds: float
    cost_breakdown: Dict[str, Any]
    timestamp: str
    conversation_summary: str
    routing_decisions: List[Dict[str, Any]] | None = None


