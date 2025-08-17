import pytest
import sys
from pathlib import Path

# Ensure backend/src is importable as 'src.*'
project_root = Path(__file__).parent.parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from agents.services.groupchat.runner import run_groupchat_stream


@pytest.mark.integration
@pytest.mark.asyncio
async def test_runner_accepts_plan_metadata(monkeypatch):
    class DummyGroupChat:
        async def run_stream(self, task: str):
            class Msg:
                def __init__(self, content, source="agent"):
                    self.content = content
                    self.source = source
            # one text message and end
            yield Msg("Hello from agent")

    messages, full_response = await run_groupchat_stream(
        DummyGroupChat(),
        task="hello",
        observers=None,
        metadata={"plan": {"sources": ["web"], "tools": ["web_search"]}},
        hard_timeout_seconds=5,
        termination_markers=None,
        max_events=5,
    )
    assert full_response.strip().startswith("Hello")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_runner_handles_no_plan_gracefully():
    class DummyGroupChat:
        async def run_stream(self, task: str):
            class Msg:
                def __init__(self, content, source="agent"):
                    self.content = content
                    self.source = source
            yield Msg("No plan here, but still responds")

    messages, full_response = await run_groupchat_stream(
        DummyGroupChat(),
        task="hello",
        observers=None,
        metadata={},
        hard_timeout_seconds=5,
        termination_markers=None,
        max_events=5,
    )
    assert "responds" in full_response


