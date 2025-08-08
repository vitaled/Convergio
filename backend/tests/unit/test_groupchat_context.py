#!/usr/bin/env python3
"""
Unit tests for groupchat/context.py
"""

import os
import sys


_BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _BACKEND_PATH not in sys.path:
    sys.path.insert(0, _BACKEND_PATH)


def test_enhance_message_with_context_basic():
    from src.agents.services.groupchat.context import enhance_message_with_context

    class _S:
        environment = "test"
        expected_agents_count = 40

    msg = enhance_message_with_context(settings=_S, message="Hello", context=None)
    assert "System Context:" in msg
    assert "Hello" in msg


def test_enhance_message_with_context_with_agent_routing():
    from src.agents.services.groupchat.context import enhance_message_with_context

    class _S:
        environment = "test"
        expected_agents_count = 40

    ctx = {"agent_name": "ali_chief_of_staff", "agent_role": "Orchestrator"}
    msg = enhance_message_with_context(settings=_S, message="Plan launch", context=ctx)
    assert "DIRECT REQUEST to ali_chief_of_staff (Orchestrator)" in msg
    assert "Plan launch" in msg


