#!/usr/bin/env python3
import os, sys, pytest
from types import SimpleNamespace

_BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _BACKEND_PATH not in sys.path:
    sys.path.insert(0, _BACKEND_PATH)


@pytest.mark.asyncio
async def test_hitl_gates_conversation_when_required(monkeypatch):
    import agents.utils.config as cfg
    cfg.get_settings.cache_clear()
    cfg.load_env_from_root = lambda: None  # type: ignore
    base_envs = {
        "BACKEND_URL": "http://localhost:8000",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "POSTGRES_USER": "u",
        "POSTGRES_PASSWORD": "p",
        "POSTGRES_DB": "d",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "JWT_SECRET": "secret",
        "OPENAI_API_KEY": "key",
        "OTEL_EXPORTER_OTLP_ENDPOINT": "http://localhost:4318",
        "PROMETHEUS_ENDPOINT": "http://localhost:9090/metrics",
        "HITL": "true",
        "COST_SAFETY": "false",
        "RAG_IN_LOOP": "false",
    }
    for k, v in base_envs.items():
        monkeypatch.setenv(k, v)

    import agents.services.autogen_groupchat_orchestrator as orch_mod
    from agents.services.autogen_groupchat_orchestrator import ModernGroupChatOrchestrator
    from agents.services.redis_state_manager import RedisStateManager
    from agents.services.cost_tracker import CostTracker

    # Stub groupchat creation to avoid real AutoGen team
    orch_mod.create_groupchat = lambda participants, model_client, max_turns: SimpleNamespace(agents=participants)  # type: ignore
    async def fake_run_groupchat_stream(group_chat, task):
        return [SimpleNamespace(content="ok", source="a")], "ok"
    orch_mod.run_groupchat_stream = fake_run_groupchat_stream  # type: ignore

    class FakeState(RedisStateManager):
        async def initialize(self):
            return None

    orch = ModernGroupChatOrchestrator(state_manager=FakeState("redis://"), cost_tracker=CostTracker(FakeState("redis://")))
    orch._initialized = True
    orch.agents = {"a": SimpleNamespace(name="a")}
    orch.model_client = SimpleNamespace(model="gpt-4o-mini")
    await orch._setup_group_chat()
    # Force HITL enabled and approval store present for deterministic behavior
    orch.settings.hitl_enabled = True
    from agents.services.hitl.approval_store import ApprovalStore
    orch.approval_store = ApprovalStore()

    with pytest.raises(RuntimeError) as exc:
        await orch.orchestrate_conversation("sensitive op", user_id="u1", context={"requires_approval": True})
    assert "Approval required" in str(exc.value)


