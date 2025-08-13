#!/usr/bin/env python3
"""
Agent definitions and registry verification aligned with WhatIsConvergio vision.
"""

import os
from pathlib import Path
import pytest

# Ensure backend on path via tests/conftest.py
from src.agents.services.agent_loader import DynamicAgentLoader

NEW_AGENTS = ['angela-da', 'ethan-da', 'ethan-ic6da', 'marcus-pm', 'michael-vc', 'oliver-pm', 'sophia-govaffairs']


@pytest.mark.unit
def test_agent_definitions_present():
    base = Path(__file__).resolve().parents[2] / "backend" / "src" / "agents" / "definitions"
    loader = DynamicAgentLoader(str(base))
    agents = loader.scan_and_load_agents()

    missing = [a for a in NEW_AGENTS if a.replace('-', '_') not in agents]
    assert not missing, f"Missing agent definitions: {missing}"


@pytest.mark.integration
def test_agents_in_ali_knowledge_base():
    base = Path(__file__).resolve().parents[2] / "backend" / "src" / "agents" / "definitions"
    loader = DynamicAgentLoader(str(base))
    kb = loader.generate_ali_knowledge_base()

    missing = [a for a in NEW_AGENTS if a not in kb]
    assert not missing, f"Missing in Ali's knowledge base: {missing}"
