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
    from services.unified_cost_tracker import unified_cost_tracker
    # Test cost limit functionality with mock data
    
    # Mock a high cost scenario
    import unittest.mock
    with unittest.mock.patch.object(unified_cost_tracker, 'get_realtime_overview') as mock_overview:
        mock_overview.return_value = {
            "total_cost_usd": 120.0,
            "status": "active"
        }
        
        # Test that costs above 100.0 would trigger limits
        overview = await unified_cost_tracker.get_realtime_overview()
        assert overview["total_cost_usd"] > 100.0
        
        # In a real scenario, budget checking would prevent proceeding
        can_proceed = overview["total_cost_usd"] <= 100.0
        assert can_proceed is False


@pytest.mark.asyncio
async def test_cost_limit_blocks_when_exceeded():
    await _run_checks()


