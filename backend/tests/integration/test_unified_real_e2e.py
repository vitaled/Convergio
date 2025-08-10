import os
import asyncio
from typing import Optional

import pytest
import httpx


BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:9000")


def _require_real_flag() -> None:
    if os.getenv("RUN_REAL_OPENAI_TESTS") != "1":
        pytest.skip("Set RUN_REAL_OPENAI_TESTS=1 to run real OpenAI + live backend E2E tests", allow_module_level=True)


async def _is_alive(client: httpx.AsyncClient) -> bool:
    try:
        # Try a cheap endpoint that should exist
        r = await client.get(f"{BASE_URL}/api/v1/agents/ecosystem", timeout=5.0)
        return r.status_code in (200, 503, 500)  # 5xx still means server is reachable
    except Exception:
        return False


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_unified_real_e2e_end_to_end(caplog):
    """
    Unified real E2E covering:
    - Storing user OpenAI key (session)
    - DB read (talents list; optional create)
    - Vector: index a document, search it
    - Orchestrate real agents (AutoGen GroupChat) with real OpenAI
    """

    _require_real_flag()

    async with httpx.AsyncClient() as client:
        if not await _is_alive(client):
            pytest.skip(f"Backend not reachable at {BASE_URL}. Start the server first.")

    # 0) Optionally store OpenAI key into session
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{BASE_URL}/api/v1/user-keys",
                json={"openai": openai_key},
                timeout=10.0,
            )
            assert resp.status_code in (200, 201), resp.text

    # 1) DB read: talents list (and ensure call works)
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/api/v1/talents?limit=5", timeout=15.0)
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        talents_count = len(data)

    # 2) Vector: index a small document
    doc_title = "E2E Test Doc"
    doc_content = (
        "Convergio enables agentic orchestration. This document is used for an E2E test "
        "covering vector indexing and semantic search."
    )
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{BASE_URL}/api/v1/vector/documents/index",
            json={
                "title": doc_title,
                "content": doc_content,
                "metadata": {"source": "unified_e2e"},
                "chunk_size": 256,
                "chunk_overlap": 32,
            },
            timeout=60.0,
        )
        assert r.status_code == 200, r.text
        doc_info = r.json()
        assert doc_info.get("document_id") is not None

    # 3) Vector: search the newly indexed content
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{BASE_URL}/api/v1/vector/search",
            json={
                "query": "agentic orchestration test",
                "top_k": 3,
                "similarity_threshold": 0.3,
            },
            timeout=30.0,
        )
        assert r.status_code == 200, r.text
        search = r.json()
        assert search.get("total_results", 0) >= 1

    # 4) Real agent orchestration via AutoGen GroupChat
    # Avoid specifying agent_name to exercise groupchat routing.
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(
            f"{BASE_URL}/api/v1/agents/conversation",
            json={
                "message": "Synthesis: use vector context and backend data to provide a CEO-ready update.",
                "user_id": "e2e_user",
                "context": {"requires_approval": False},
            },
        )
        assert r.status_code == 200, r.text
        convo = r.json()
        assert isinstance(convo.get("response"), str) and len(convo["response"]) > 0
        assert isinstance(convo.get("agents_used", []), list)
        assert isinstance(convo.get("turn_count", 0), int)

    # Basic smoke summary for logs
    print({
        "talents_count": talents_count,
        "doc_id": doc_info.get("document_id"),
        "vector_total_results": search.get("total_results"),
        "agents_used": convo.get("agents_used"),
        "turns": convo.get("turn_count"),
    })
