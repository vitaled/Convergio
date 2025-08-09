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
_selection_history: list = []


def record_selection_metrics(rationale: Dict[str, str]) -> None:
    """Record a selection rationale occurrence.
    Expected keys: 'reason', 'picked'
    """
    reason = rationale.get("reason", "unknown")
    picked = rationale.get("picked", "unknown")
    with _lock:
        _reason_counter[reason] += 1
        _picked_counter[picked] += 1
        # Also append to selection history for audits
        _selection_history.append({"reason": reason, "picked": picked, **{k: v for k, v in rationale.items() if k not in {"reason", "picked"}}})


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
        _selection_history.clear()


def get_selection_history() -> list:
    """Return a shallow copy of the selection history."""
    with _lock:
        return list(_selection_history)

