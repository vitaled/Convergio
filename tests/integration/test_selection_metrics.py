from src.agents.services.groupchat.selection_policy import (
    pick_next_speaker,
)
from src.agents.services.groupchat.selection_metrics import (
    get_selection_metrics,
    reset_selection_metrics,
)


class StubAgent:
    def __init__(self, name: str):
        self.name = name


def test_selection_metrics_finance_keyword():
    reset_selection_metrics()
    participants = [StubAgent("amy_cfo"), StubAgent("ali_chief_of_staff")]  # order shouldn't matter
    _ = pick_next_speaker("Please review the budget and costs", participants)
    metrics = get_selection_metrics()
    assert metrics["reasons"].get("finance_keywords", 0) >= 1
    # chosen agent should be counted as picked
    assert metrics["picked"].get("amy_cfo", 0) >= 1

