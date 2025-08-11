import os
from src.agents.tools.web_search_tool import WebSearchTool


def test_web_search_provider_health_mock(monkeypatch):
    # Ensure no provider keys are set
    for key in ["BING_API_KEY", "SERPER_API_KEY", "GOOGLE_API_KEY", "GOOGLE_CSE_ID"]:
        monkeypatch.delenv(key, raising=False)

    tool = WebSearchTool()
    health = tool.provider_health()

    assert health["provider"] == "mock"
    assert health["configured"] is False
    assert "note" in health
