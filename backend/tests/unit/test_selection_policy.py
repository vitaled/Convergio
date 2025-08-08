#!/usr/bin/env python3
"""
Unit tests for groupchat/selection_policy.py
"""

import os
import sys

_BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _BACKEND_PATH not in sys.path:
    sys.path.insert(0, _BACKEND_PATH)


class _A:
    def __init__(self, name):
        self.name = name


def test_select_key_agents_prioritizes_core():
    from src.agents.services.groupchat.selection_policy import select_key_agents
    agents = [_A("ali_chief_of_staff"), _A("amy_cfo"), _A("diana_performance_dashboard"), _A("x")]
    keys = select_key_agents(agents)
    names = [a.name for a in keys]
    assert "ali_chief_of_staff" in names
    assert "diana_performance_dashboard" in names


def test_pick_next_speaker_simple_rules():
    from src.agents.services.groupchat.selection_policy import pick_next_speaker
    participants = [_A("ali_chief_of_staff"), _A("amy_cfo"), _A("luca_security_expert")]
    assert pick_next_speaker("We need a cost plan", participants).name in ["amy_cfo", "ali_chief_of_staff"]
    assert pick_next_speaker("Security risk detected", participants).name in ["luca_security_expert", "ali_chief_of_staff"]
    assert pick_next_speaker("Strategic decision", participants).name == "ali_chief_of_staff"


def test_selection_rationale():
    from src.agents.services.groupchat.selection_policy import selection_rationale
    participants = [_A("ali_chief_of_staff"), _A("amy_cfo"), _A("luca_security_expert")]
    r = selection_rationale("please estimate budget and cost", participants)
    assert r["picked"] in ["amy_cfo", "ali_chief_of_staff"]
    assert r["reason"] in ["finance_keywords", "default_first"]


