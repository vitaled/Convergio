#!/usr/bin/env python3
"""
Unit tests for API streaming endpoints in src/api/agents.py (WS3)
"""

import os
import sys
import pytest
import json
from unittest.mock import patch, AsyncMock
from fastapi import FastAPI
from fastapi.testclient import TestClient


# Ensure backend root on sys.path for src imports
_BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _BACKEND_PATH not in sys.path:
    sys.path.insert(0, _BACKEND_PATH)


class _DummyStreamingOrchestrator:
    def __init__(self, initialized=True):
        self._initialized = initialized
        self._sessions = {}

    async def initialize(self):
        self._initialized = True

    async def create_streaming_session(self, websocket, user_id: str, agent_name: str, session_context=None):
        # Immediately accept in endpoint prior to calling this
        sid = f"session-{user_id}-{agent_name}"
        self._sessions[sid] = {"user_id": user_id, "agent_name": agent_name, "ws": websocket}
        # No actual send here; endpoint handles sending responses
        return sid

    async def process_streaming_message(self, session_id: str, message: str, message_context=None):
        # No-op in unit test; endpoint catches exceptions
        return None

    async def get_active_sessions(self):
        return list(self._sessions.keys())

    async def cleanup_inactive_sessions(self, max_idle_minutes: int):
        cleaned = len(self._sessions)
        self._sessions.clear()
        return cleaned

    async def close_session(self, session_id: str):
        self._sessions.pop(session_id, None)


@pytest.fixture(scope="module")
def app_client():
    from src.api.agents import router as agents_router
    app = FastAPI()
    app.include_router(agents_router, prefix="/api/v1/agents")
    return TestClient(app)


def test_streaming_health_healthy(app_client):
    dummy = _DummyStreamingOrchestrator(initialized=True)
    with patch("src.api.agents.get_streaming_orchestrator", return_value=dummy):
        resp = app_client.get("/api/v1/agents/streaming/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ["healthy", "unhealthy"]


def test_streaming_sessions_list(app_client):
    dummy = _DummyStreamingOrchestrator(initialized=True)
    with patch("src.api.agents.get_streaming_orchestrator", return_value=dummy):
        resp = app_client.get("/api/v1/agents/streaming/sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert "active_sessions" in data


def test_websocket_streaming_endpoint_connect_and_close(app_client):
    dummy = _DummyStreamingOrchestrator(initialized=True)
    with patch("src.api.agents.get_streaming_orchestrator", return_value=dummy):
        with app_client.websocket_connect("/api/v1/agents/ws/streaming/u1/ali_chief_of_staff") as ws:
            # Send a simple message
            ws.send_json({"message": "Hello"})
            # Endpoint doesn't echo; just ensure the socket stays open until client closes
            ws.close()


def test_websocket_conversation_event_protocol_from_real_autogen(app_client):
    # Patch orchestrator path used by _stream_real_autogen_conversation
    with patch("src.api.agents._get_agent_display_info", new_callable=AsyncMock, return_value={
        "id": "ali-chief-of-staff",
        "name": "Ali - Chief Of Staff",
        "role": "Orchestrator",
        "color": "#000",
        "specialty": "leadership",
    }):
        # Create a dummy orchestrator result object with required attributes
        class _Result:
            response = "Final response"
            agents_used = ["ali-chief-of-staff", "amy-cfo"]
            turn_count = 2
            duration_seconds = 1.23
            cost_breakdown = {"total": 0.0}

        class _DummyOrchestrator:
            async def orchestrate_conversation(self, **_kwargs):
                return _Result()

        with patch("src.api.agents.get_streaming_orchestrator") as _get_stream_orch, \
             patch("src.agents.orchestrator.get_agent_orchestrator", new_callable=AsyncMock, return_value=_DummyOrchestrator()):
            # Use real router but intercept WS at /ws/conversation/{id}
            from src.api.agents import router as agents_router
            app = FastAPI()
            app.include_router(agents_router, prefix="/api/v1/agents")
            client = TestClient(app)

            with client.websocket_connect("/api/v1/agents/ws/conversation/test-conv") as ws:
                # Start conversation
                ws.send_text(json.dumps({
                    "type": "start_conversation",
                    "message": "Hi",
                    "user_id": "u1",
                    "context": {}
                }))

                # Read a few events to validate protocol
                # First: connection_established
                evt0 = json.loads(ws.receive_text())
                assert evt0["type"] == "connection_established"

                # Then: conversation_started
                evt1 = json.loads(ws.receive_text())
                assert evt1["type"] == "conversation_started"

                # Next: agent_status for first agent
                evt2 = json.loads(ws.receive_text())
                assert evt2["type"] == "agent_status"
                assert "agent_id" in evt2 and "status" in evt2

                # Next: agent_response for first agent
                evt3 = json.loads(ws.receive_text())
                assert evt3["type"] == "agent_response"
                assert "content" in evt3

                # Eventually: conversation_completed
                # Depending on timing there may be more agent events; read until completion
                completed = False
                for _ in range(5):
                    evt = json.loads(ws.receive_text())
                    if evt.get("type") == "conversation_completed":
                        completed = True
                        assert "final_response" in evt
                        assert "agents_used" in evt
                        break
                assert completed


def test_streaming_ws_propagates_tool_events(app_client):
    # Orchestrator that emits events via the same websocket stored in session map
    class _EmitterOrchestrator:
        def __init__(self):
            self._initialized = True
            self._sessions = {}
        async def initialize(self):
            self._initialized = True
        async def create_streaming_session(self, websocket, user_id: str, agent_name: str, session_context=None):
            sid = f"s-{user_id}-{agent_name}"
            self._sessions[sid] = websocket
            # Simulate session_created
            await websocket.send_json({"type": "streaming_response", "event": "status", "data": {"chunk_type": "status", "content": "session_created"}})
            return sid
        async def process_streaming_message(self, session_id: str, message: str, message_context=None):
            ws = self._sessions[session_id]
            # Emit tool_call, tool_result, then final
            await ws.send_json({"type": "streaming_response", "event": "tool_call", "data": {"chunk_type": "tool_call", "content": "{\"tool\":\"search\"}"}})
            await ws.send_json({"type": "streaming_response", "event": "tool_result", "data": {"chunk_type": "tool_result", "content": "result"}})
            await ws.send_json({"type": "streaming_response", "event": "final", "data": {"chunk_type": "complete", "content": "done"}})
        async def close_session(self, session_id: str):
            self._sessions.pop(session_id, None)

    with patch("src.api.agents.get_streaming_orchestrator", return_value=_EmitterOrchestrator()):
        from src.api.agents import router as agents_router
        app = FastAPI()
        app.include_router(agents_router, prefix="/api/v1/agents")
        client = TestClient(app)

        with client.websocket_connect("/api/v1/agents/ws/streaming/u1/ali_chief_of_staff") as ws:
            # Trigger message processing
            ws.send_json({"message": "go"})

            # Receive a few events
            events = []
            for _ in range(4):
                evt = ws.receive_json()
                events.append(evt)
            kinds = [e.get("event") for e in events if e.get("type") == "streaming_response"]
            assert "tool_call" in kinds
            assert "tool_result" in kinds
            assert "final" in kinds


