#!/usr/bin/env python3
import os, sys

_BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _BACKEND_PATH not in sys.path:
    sys.path.insert(0, _BACKEND_PATH)


def test_get_settings_basic_fields_present(monkeypatch):
    from agents.utils.config import get_settings
    # Avoid reading root .env for test
    import agents.utils.config as cfg
    cfg.get_settings.cache_clear()
    cfg.load_env_from_root = lambda: None  # type: ignore

    # Minimal required envs for model validation to avoid ValueError
    monkeypatch.setenv("BACKEND_URL", "http://localhost:8000")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("POSTGRES_USER", "u")
    monkeypatch.setenv("POSTGRES_PASSWORD", "p")
    monkeypatch.setenv("POSTGRES_DB", "d")
    monkeypatch.setenv("REDIS_HOST", "localhost")
    monkeypatch.setenv("REDIS_PORT", "6379")
    monkeypatch.setenv("JWT_SECRET", "secret")
    monkeypatch.setenv("OPENAI_API_KEY", "key")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    monkeypatch.setenv("PROMETHEUS_ENDPOINT", "http://localhost:9090/metrics")

    s = get_settings()
    assert isinstance(s.default_ai_model, str)
    assert isinstance(s.autogen_max_turns, int)
    assert isinstance(s.true_streaming_enabled, bool)


