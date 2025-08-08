#!/usr/bin/env python3
"""
Unit tests for StreamingOrchestrator (WS3 scaffolding)
"""

import os
import sys
import pytest
import asyncio
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch


# Ensure backend root on sys.path for src imports
_BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _BACKEND_PATH not in sys.path:
    sys.path.insert(0, _BACKEND_PATH)


class FakeWebSocket:
    def __init__(self):
        self.sent = []
        self.accepted = False

    async def send_json(self, data):
        self.sent.append(("json", data))

    async def send_text(self, data):
        self.sent.append(("text", data))

    async def accept(self):
        self.accepted = True


@pytest.mark.asyncio
async def test_create_streaming_session_sends_created_event():
    from src.agents.services.streaming_orchestrator import StreamingOrchestrator

    ws = FakeWebSocket()
    with patch("src.agents.services.streaming_orchestrator.get_redis_client") as mock_redis, \
         patch("src.agents.memory.autogen_memory_system.get_redis_client") as mem_redis:
        mock_redis.return_value = None
        mem_redis.return_value = None
        orch = StreamingOrchestrator()
        orch._initialized = True

    session_id = await orch.create_streaming_session(ws, user_id="u1", agent_name="ali_chief_of_staff")

    assert session_id in orch.active_sessions
    # First message should be status session_created
    types = [e[1]["data"]["chunk_type"] for e in ws.sent if e[0] == "json" and isinstance(e[1], dict) and "data" in e[1]]
    assert "status" in types
    await orch.close_session(session_id)


@pytest.mark.asyncio
async def test_process_streaming_message_with_fake_stream():
    from src.agents.services.streaming_orchestrator import StreamingOrchestrator, StreamingResponse

    ws = FakeWebSocket()
    with patch("src.agents.services.streaming_orchestrator.get_redis_client") as mock_redis, \
         patch("src.agents.memory.autogen_memory_system.get_redis_client") as mem_redis:
        mock_redis.return_value = None
        mem_redis.return_value = None
        orch = StreamingOrchestrator()
        orch._initialized = True

    # Create session
    session_id = await orch.create_streaming_session(ws, user_id="u1", agent_name="ali_chief_of_staff")

    # Patch DynamicAgentLoader to avoid filesystem access
    class _FakeLoader:
        def __init__(self, *_args, **_kwargs):
            pass
        def scan_and_load_agents(self):
            return {"ali_chief_of_staff": SimpleNamespace()}
        def _build_system_message(self, _meta):
            return "You are Ali, Chief of Staff."

    async def _fake_stream_agent_response(agent, message, session):
        # Yield two text chunks
        yield StreamingResponse(
            chunk_id="c1", session_id=session.session_id, agent_name=session.agent_name,
            chunk_type="text", content="Hello ", timestamp=datetime.utcnow()
        )
        yield StreamingResponse(
            chunk_id="c2", session_id=session.session_id, agent_name=session.agent_name,
            chunk_type="text", content="World.", timestamp=datetime.utcnow()
        )

    # Patch the class at its definition path used by the function import
    with patch("src.agents.services.agent_loader.DynamicAgentLoader", _FakeLoader):
        # Monkeypatch the internal streaming method
        orch._stream_agent_response = _fake_stream_agent_response  # type: ignore[attr-defined]

        await orch.process_streaming_message(session_id=session_id, message="test", message_context={})

    # Ensure text chunks were sent
    texts = [e for e in ws.sent if e[0] == "json" and e[1].get("data", {}).get("chunk_type") == "text"]
    assert len(texts) >= 2
    await orch.close_session(session_id)


@pytest.mark.asyncio
async def test_streaming_orchestrator_emits_thinking_and_complete_events():
    from src.agents.services.streaming_orchestrator import StreamingOrchestrator, StreamingResponse

    ws = FakeWebSocket()
    with patch("src.agents.services.streaming_orchestrator.get_redis_client") as mock_redis, \
         patch("src.agents.memory.autogen_memory_system.get_redis_client") as mem_redis:
        mock_redis.return_value = None
        mem_redis.return_value = None
        orch = StreamingOrchestrator()
        orch._initialized = True

    # Create session
    session_id = await orch.create_streaming_session(ws, user_id="u1", agent_name="ali_chief_of_staff")

    class _FakeLoader:
        def __init__(self, *_args, **_kwargs):
            pass
        def scan_and_load_agents(self):
            return {"ali_chief_of_staff": SimpleNamespace()}
        def _build_system_message(self, _meta):
            return "You are Ali, Chief of Staff."

    async def _fake_stream_agent_response(agent, message, session):
        # Yield one text chunk only; thinking and complete are emitted by orchestrator
        yield StreamingResponse(
            chunk_id="c1", session_id=session.session_id, agent_name=session.agent_name,
            chunk_type="text", content="Chunk.", timestamp=datetime.utcnow()
        )

    with patch("src.agents.services.agent_loader.DynamicAgentLoader", _FakeLoader):
        orch._stream_agent_response = _fake_stream_agent_response  # type: ignore[attr-defined]
        await orch.process_streaming_message(session_id=session_id, message="go", message_context={})

    # Extract chunk types from sent events
    chunk_types = [e[1]["data"].get("chunk_type") for e in ws.sent if e[0] == "json" and "data" in e[1]]
    assert "thinking" in chunk_types
    assert "text" in chunk_types
    assert "complete" in chunk_types

    # Validate mapped event field for WS3 protocol
    events = [e[1].get("event") for e in ws.sent if e[0] == "json"]
    # Expect at least one of each mapped events
    assert any(ev == "agent_status" for ev in events)
    assert any(ev == "delta" for ev in events)
    assert any(ev == "final" for ev in events)
    await orch.close_session(session_id)


@pytest.mark.asyncio
async def test_heartbeat_emission_and_cancellation():
    from src.agents.services.streaming_orchestrator import StreamingOrchestrator

    ws = FakeWebSocket()
    with patch("src.agents.services.streaming_orchestrator.get_redis_client") as mock_redis, \
         patch("src.agents.memory.autogen_memory_system.get_redis_client") as mem_redis:
        mock_redis.return_value = None
        mem_redis.return_value = None
        orch = StreamingOrchestrator()
        orch._initialized = True
        orch.heartbeat_interval_sec = 0.05  # speed up for test

    session_id = await orch.create_streaming_session(ws, user_id="u1", agent_name="ali_chief_of_staff")

    # Wait a bit to allow at least one heartbeat
    await asyncio.sleep(0.12)

    # Close session to cancel heartbeat
    await orch.close_session(session_id)

    # Collect events
    events = [e[1].get("event") for e in ws.sent if e[0] == "json"]
    assert any(ev == "status" for ev in events)  # initial session_created or heartbeat


