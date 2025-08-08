#!/usr/bin/env python3
"""
Unit tests for workflows API (`src/api/workflows.py`) covering list/execute/status.
"""

import os
import sys
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


# Ensure backend root on sys.path for src imports
_BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _BACKEND_PATH not in sys.path:
    sys.path.insert(0, _BACKEND_PATH)


def _make_app():
    from src.api.workflows import router as workflows_router
    app = FastAPI()
    app.include_router(workflows_router, prefix="/api/v1/workflows")
    return TestClient(app)


@pytest.mark.parametrize("total", [2])
def test_list_workflows_returns_expected_shape(total):
    client = _make_app()

    dummy_workflows = [
        {
            "workflow_id": "wf-1",
            "name": "WF 1",
            "description": "desc",
            "category": "strategic",
            "complexity": "medium",
            "estimated_duration": 120,
            "steps_count": 3,
        },
        {
            "workflow_id": "wf-2",
            "name": "WF 2",
            "description": "desc2",
            "category": "ops",
            "complexity": "low",
            "estimated_duration": 60,
            "steps_count": 2,
        },
    ][:total]

    class _DummyOrch:
        async def initialize(self):
            return None
        async def list_available_workflows(self):
            return dummy_workflows

    with patch("src.api.workflows.get_graphflow_orchestrator", return_value=_DummyOrch()):
        r = client.get("/api/v1/workflows/")
        assert r.status_code == 200
        data = r.json()
        assert "workflows" in data and isinstance(data["workflows"], list)
        assert data["total_count"] == len(dummy_workflows)


def test_execute_and_status_flow():
    client = _make_app()

    dummy_workflows = [
        {"workflow_id": "wf-1", "name": "WF 1", "description": "d", "category": "c", "complexity": "m", "estimated_duration": 10, "steps_count": 1}
    ]

    class _Exec:
        def __init__(self):
            self.execution_id = "exec-1"
            self.workflow_id = "wf-1"
            self.status = "running"
            self.current_step = None
            self.started_at = datetime.utcnow()
            self.completed_at = None
            self.results = None
            self.error_message = None

    class _DummyOrch:
        def __init__(self):
            self.executions = {"exec-1": _Exec()}
        async def list_available_workflows(self):
            return dummy_workflows
        async def execute_workflow(self, workflow_id: str, user_request: str, user_id: str, context: dict):
            return "exec-1"
        async def get_workflow_status(self, execution_id: str):
            return self.executions.get(execution_id)

    with patch("src.api.workflows.get_graphflow_orchestrator", return_value=_DummyOrch()):
        # Execute
        r = client.post("/api/v1/workflows/execute", json={
            "workflow_id": "wf-1",
            "user_request": "Do it",
            "user_id": "u1",
            "context": {}
        })
        assert r.status_code == 200
        exec_data = r.json()
        assert exec_data["execution_id"] == "exec-1"
        assert exec_data["status"] in ["started", "running"]

        # Status
        r2 = client.get("/api/v1/workflows/execution/exec-1")
        assert r2.status_code == 200
        st = r2.json()
        assert st["execution_id"] == "exec-1"
        assert st["workflow_id"] == "wf-1"
        assert st["status"] in ["running", "completed", "failed"]


