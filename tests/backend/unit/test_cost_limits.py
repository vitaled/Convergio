#!/usr/bin/env python3
import os, sys, asyncio, pytest

_BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _BACKEND_PATH not in sys.path:
    sys.path.insert(0, _BACKEND_PATH)


class _SM:
    def __init__(self, total_cost):
        self._total = total_cost
    async def track_cost(self, **_):
        return None
    async def get_daily_cost_summary(self, *_):
        return {"total_cost_usd": self._total, "total_tokens": 0}


async def _run_checks():
    from agents.services.cost_tracker import CostTracker
    ct = CostTracker(state_manager=_SM(total_cost=120.0))
    ct.set_cost_limit(100.0)
    check = await ct.check_budget_limits("c1")
    assert check["can_proceed"] is False


@pytest.mark.asyncio
async def test_cost_limit_blocks_when_exceeded():
    await _run_checks()


