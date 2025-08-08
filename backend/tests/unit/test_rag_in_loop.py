#!/usr/bin/env python3
"""
Unit tests for RAG in-the-loop helper
"""

import os
import sys
import pytest
import asyncio

# Ensure backend root on sys.path for src imports
_BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _BACKEND_PATH not in sys.path:
    sys.path.insert(0, _BACKEND_PATH)


class _FakeMemoryEntry:
    def __init__(self, content: str):
        self.content = content


class _FakeMemorySystem:
    def __init__(self, entries):
        self._entries = entries

    async def retrieve_relevant_context(self, query: str, user_id: str, agent_id=None, limit: int = 5):
        return self._entries[:limit]


@pytest.mark.asyncio
async def test_build_memory_context_with_results():
    from src.agents.services.groupchat.rag import build_memory_context

    mem = _FakeMemorySystem([
        _FakeMemoryEntry("Policy: Always double-check calculations"),
        _FakeMemoryEntry("User prefers concise answers")
    ])

    msg = await build_memory_context(mem, user_id="u1", agent_id=None, query="budget plan", limit=5)
    assert msg is not None
    assert msg.source == "system"
    assert "Relevant context:" in msg.content
    assert "User prefers concise answers" in msg.content


@pytest.mark.asyncio
async def test_build_memory_context_no_results():
    from src.agents.services.groupchat.rag import build_memory_context

    mem = _FakeMemorySystem([])

    msg = await build_memory_context(mem, user_id="u1", agent_id=None, query="anything", limit=5)
    assert msg is None


