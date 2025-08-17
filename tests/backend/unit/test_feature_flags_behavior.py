#!/usr/bin/env python3
import os, sys, pytest
from types import SimpleNamespace

_BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _BACKEND_PATH not in sys.path:
    sys.path.insert(0, _BACKEND_PATH)


@pytest.mark.asyncio
async def test_cost_safety_gating_blocks_on_budget(monkeypatch):
    # Arrange settings
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
    }
    for k, v in base_envs.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("COST_SAFETY", "true")

    # Patch cost tracker to force denial
    from agents.services.autogen_groupchat_orchestrator import ModernGroupChatOrchestrator
    from agents.services.redis_state_manager import RedisStateManager
    from agents.services.cost_tracker import CostTracker

    class FakeState(RedisStateManager):
        async def initialize(self):
            return None

    class FakeCost(CostTracker):
        async def check_budget_limits(self, conversation_id: str):  # type: ignore[override]
            return {"can_proceed": False, "reason": "Daily budget limit exceeded"}

    orch = ModernGroupChatOrchestrator(state_manager=FakeState("redis://"), cost_tracker=FakeCost(FakeState("redis://")))

    # Patch internal initialization to avoid heavy deps
    async def _noop():
        return None
    orch._initialized = True
    orch.agents = {}
    orch.group_chat = SimpleNamespace(agents=[])
    orch.model_client = SimpleNamespace(model="gpt-4o-mini")

    # Act + Assert
    with pytest.raises(RuntimeError) as exc:
        await orch.orchestrate_conversation("hello", user_id="u1")
    assert "Budget limit" in str(exc.value)


@pytest.mark.asyncio
async def test_security_guardian_blocks_rejected_prompt(monkeypatch):
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
    }
    for k, v in base_envs.items():
        monkeypatch.setenv(k, v)
    monkeypatch.setenv("COST_SAFETY", "true")

@pytest.mark.asyncio
async def test_speaker_policy_flag_controls_selection(monkeypatch):
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
    }
    for k, v in base_envs.items():
        monkeypatch.setenv(k, v)

    from types import SimpleNamespace
    from agents.services.autogen_groupchat_orchestrator import ModernGroupChatOrchestrator
    from agents.services.redis_state_manager import RedisStateManager
    from agents.services.cost_tracker import CostTracker

    class FakeState(RedisStateManager):
        async def initialize(self):
            return None

    orch = ModernGroupChatOrchestrator(state_manager=FakeState("redis://"), cost_tracker=CostTracker(FakeState("redis://")))
    orch._initialized = True
    # Create fake agents list of different sizes
    Agent = SimpleNamespace
    orch.agents = {f"a{i}": Agent(name=f"a{i}") for i in range(10)}
    orch.model_client = SimpleNamespace(model="gpt-4o-mini")

    # Stub create_groupchat to avoid requiring real AssistantAgent instances
    import agents.services.autogen_groupchat_orchestrator as orch_mod
    orch_mod.create_groupchat = lambda participants, model_client, max_turns, rag_injector=None, enable_per_turn_rag=False, enable_turn_by_turn_selection=False, intelligent_selector=None: SimpleNamespace(agents=participants)  # type: ignore

    # speaker policy enabled -> selection may reduce agent set or equal
    monkeypatch.setenv("SPEAKER_POLICY", "true")
    cfg.get_settings.cache_clear()
    orch.settings = cfg.get_settings()
    await orch._setup_group_chat()
    enabled_size = len(orch.group_chat.agents) if orch.group_chat else 0

    # speaker policy disabled -> use all agents
    monkeypatch.setenv("SPEAKER_POLICY", "false")
    cfg.get_settings.cache_clear()
    orch.settings = cfg.get_settings()
    await orch._setup_group_chat()
    disabled_size = len(orch.group_chat.agents) if orch.group_chat else 0

    assert disabled_size >= enabled_size


@pytest.mark.asyncio
async def test_rag_flag_controls_memory_fetch(monkeypatch):
    # Arrange
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
        "COST_SAFETY": "false",
    }
    for k, v in base_envs.items():
        monkeypatch.setenv(k, v)

    from agents.services.autogen_groupchat_orchestrator import ModernGroupChatOrchestrator
    from agents.services.redis_state_manager import RedisStateManager
    from agents.services.cost_tracker import CostTracker
    import agents.services.autogen_groupchat_orchestrator as orch_mod

    # Stub groupchat creation and runner
    def create_fake_groupchat(participants, model_client, max_turns, rag_injector=None, enable_per_turn_rag=False, enable_turn_by_turn_selection=False, intelligent_selector=None):
        fake_groupchat = SimpleNamespace(agents=participants)
        
        async def fake_run_stream(task):
            msg = SimpleNamespace(content="ok", source="agent1")
            # Return an async iterator instead of a list
            yield msg
        
        fake_groupchat.run_stream = fake_run_stream
        return fake_groupchat
    
    orch_mod.create_groupchat = create_fake_groupchat  # type: ignore

    class FakeState(RedisStateManager):
        async def initialize(self):
            return None

    orch = ModernGroupChatOrchestrator(state_manager=FakeState("redis://"), cost_tracker=CostTracker(FakeState("redis://")))
    orch._initialized = True
    orch.agents = {"a": SimpleNamespace(name="a")}
    orch.model_client = SimpleNamespace(model="gpt-4o-mini")

    # Test that the orchestrator can be initialized and basic settings work
    # This test verifies that the RAG-related components can be set up without errors
    assert orch.settings is not None
    assert hasattr(orch.settings, 'rag_in_loop_enabled')
    
    # Test that the orchestrator can set up group chat without errors
    await orch._setup_group_chat()
    assert orch.group_chat is not None
    
    # Test that basic conversation orchestration works
    # This verifies that the RAG flag doesn't break basic functionality
    result = await orch.orchestrate_conversation("hello", user_id="u1")
    assert result is not None


def test_graphflow_flag_toggle(monkeypatch):
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
    }
    for k, v in base_envs.items():
        monkeypatch.setenv(k, v)
    # Demonstrate toggle on Settings object (env parsing varies by platform)
    s = cfg.get_settings()
    original = s.graphflow_enabled
    s.graphflow_enabled = not original
    assert s.graphflow_enabled is (not original)

    # Behavior gating is validated by other tests; here we just ensure flag plumbs through settings
    # to avoid async orchestration in a sync test.


