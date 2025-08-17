import pytest
from agents.services.decision_engine import DecisionEngine


@pytest.mark.integration
def test_decision_engine_basic_plan():
    de = DecisionEngine()
    plan = de.plan("How many talents do we have? Show latest numbers.")
    assert "backend" in plan.sources or "vector" in plan.sources
    assert plan.model
    assert plan.max_turns >= 1
    assert plan.budget_usd > 0


@pytest.mark.integration
def test_decision_engine_web_search_needed():
    de = DecisionEngine()
    plan = de.plan("What is Microsoft's Q4 FY2025 revenue? Latest numbers please")
    assert "web" in plan.sources
    assert "web_search" in plan.tools


