"""
Selection Metrics
Lightweight in-memory collection of speaker selection rationale for audits/metrics.
"""

import threading
from collections import Counter
from typing import Dict

_lock = threading.Lock()
_reason_counter: Counter = Counter()
_picked_counter: Counter = Counter()


def record_selection_metrics(rationale: Dict[str, str]) -> None:
    """Record a selection rationale occurrence.
    Expected keys: 'reason', 'picked'
    """
    reason = rationale.get("reason", "unknown")
    picked = rationale.get("picked", "unknown")
    with _lock:
        _reason_counter[reason] += 1
        _picked_counter[picked] += 1


def get_selection_metrics() -> Dict[str, Dict[str, int]]:
    """Return current counters for reasons and picked agents."""
    with _lock:
        return {
            "reasons": dict(_reason_counter),
            "picked": dict(_picked_counter),
        }


def reset_selection_metrics() -> None:
    """Reset metrics (useful in tests)."""
    with _lock:
        _reason_counter.clear()
        _picked_counter.clear()


def get_selection_history(conversation_id: str = None, limit: int = 100) -> list:
    """Get selection history for a conversation or recent selections.
    
    Args:
        conversation_id: Optional conversation ID to filter by
        limit: Maximum number of entries to return
        
    Returns:
        List of selection history entries
    """
    # For now, return a simple list based on current metrics
    # In production, this would query from a proper storage system
    with _lock:
        history = []
        # Counter.most_common exists; type: ignore for mypy if needed
        for reason, count in _reason_counter.most_common(limit):  # type: ignore[attr-defined]
            history.append({
                "reason": reason,
                "count": count,
                "conversation_id": conversation_id
            })
        return history

