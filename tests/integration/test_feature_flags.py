import json
from fastapi import FastAPI
from fastapi.testclient import TestClient


def make_app_with_router(router, prefix: str = "/api"):
    app = FastAPI()
    app.include_router(router, prefix=prefix)
    return app


def test_workflows_health_disabled(monkeypatch):
    # Import module and flip feature flag
    from src.api import workflows as wf
    monkeypatch.setattr(wf, "settings", type("S", (), {"graphflow_enabled": False})())

    app = make_app_with_router(wf.router, "/api/workflows")
    client = TestClient(app)

    resp = client.get("/api/workflows/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "disabled"


def test_streaming_ws_disabled(monkeypatch):
    # Import module and flip feature flag
    from src.api import agents as ag
    # minimal settings stub
    monkeypatch.setattr(
        ag,
        "settings",
        type(
            "S",
            (),
            {
                "true_streaming_enabled": False,
                # needed for feature-flags endpoint
                "rag_in_loop_enabled": True,
                "speaker_policy_enabled": True,
                "graphflow_enabled": False,
                "hitl_enabled": False,
                "cost_safety_enabled": True,
            },
        )(),
    )

    app = make_app_with_router(ag.router, "/api/agents")
    client = TestClient(app)

    with client.websocket_connect("/api/agents/ws/streaming/u1/ali_chief_of_staff") as ws:
        # Expect a disabled status then close
        msg = ws.receive_json()
        assert msg["event"] == "disabled" or msg.get("type") == "status"
        # Server should close; trying to receive again should raise
        closed = False
        try:
            ws.receive_json()
        except Exception:
            closed = True
        assert closed

