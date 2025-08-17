import yaml
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))

from agents.services.decision_engine import DecisionEngine
from agents.utils.config import os as _os


@pytest.mark.integration
def test_scenarios_source_choices():
    fixture = Path(__file__).parent.parent / "fixtures" / "scenarios.yaml"
    # Minimal env for Settings
    _os.environ.setdefault("ENVIRONMENT", "test")
    _os.environ.setdefault("BACKEND_URL", "http://localhost:9000")
    _os.environ.setdefault("DB_HOST", "localhost")
    _os.environ.setdefault("DB_PORT", "5432")
    _os.environ.setdefault("POSTGRES_USER", "test")
    _os.environ.setdefault("POSTGRES_PASSWORD", "test")
    _os.environ.setdefault("POSTGRES_DB", "test")
    _os.environ.setdefault("REDIS_HOST", "localhost")
    _os.environ.setdefault("REDIS_PORT", "6379")
    _os.environ.setdefault("JWT_SECRET", "secret")
    _os.environ.setdefault("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    _os.environ.setdefault("PROMETHEUS_ENDPOINT", "http://localhost:9090")
    _os.environ.setdefault("OPENAI_API_KEY", "sk-test")
    data = yaml.safe_load(fixture.read_text())
    de = DecisionEngine()

    for sc in data.get("scenarios", []):
        plan = de.plan(sc["query"])
        assert any(s in plan.sources for s in sc["expect_sources_any"]), f"Scenario {sc['name']} failed: sources={plan.sources}"

