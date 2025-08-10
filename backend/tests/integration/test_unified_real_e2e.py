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
async def test_unified_real_e2e_end_to_end(caplog, transcript_logger):
    """
    Unified real E2E covering:
    - Storing user OpenAI key (session)
    - DB read (talents list; optional create)
    - Vector: index a document, search it
    - Orchestrate real agents (AutoGen GroupChat) with real OpenAI
    """

    _require_real_flag()

    transcript_logger.section("Bootstrap: backend reachability check")
    async with httpx.AsyncClient() as client:
        if not await _is_alive(client):
            pytest.skip(f"Backend not reachable at {BASE_URL}. Start the server first.")

    # 0) Optionally store OpenAI key into session
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        async with httpx.AsyncClient() as client:
            payload = {"openai": openai_key}
            t0 = asyncio.get_event_loop().time()
            resp = await client.post(
                f"{BASE_URL}/api/v1/user-keys",
                json=payload,
                timeout=10.0,
            )
            dt = asyncio.get_event_loop().time() - t0
            transcript_logger.http(
                name="store_user_key",
                method="POST",
                url=f"{BASE_URL}/api/v1/user-keys",
                request_json=payload,
                status=resp.status_code,
                response_json=resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text,
                duration_s=dt,
            )
            assert resp.status_code in (200, 201), resp.text

    # 1) DB read: talents list (and ensure call works)
    async with httpx.AsyncClient() as client:
        t0 = asyncio.get_event_loop().time()
        r = await client.get(f"{BASE_URL}/api/v1/talents?limit=5", timeout=15.0)
        dt = asyncio.get_event_loop().time() - t0
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        talents_count = len(data)
        transcript_logger.http(
            name="talents_list",
            method="GET",
            url=f"{BASE_URL}/api/v1/talents?limit=5",
            request_json=None,
            status=r.status_code,
            response_json={"count": talents_count},
            duration_s=dt,
        )

    # 2) Vector: index a small document
    doc_title = "E2E Test Doc"
    doc_content = (
        "Convergio enables agentic orchestration. This document is used for an E2E test "
        "covering vector indexing and semantic search."
    )
    async with httpx.AsyncClient() as client:
        payload = {
            "title": doc_title,
            "content": doc_content,
            "metadata": {"source": "unified_e2e"},
            "chunk_size": 256,
            "chunk_overlap": 32,
        }
        t0 = asyncio.get_event_loop().time()
        r = await client.post(
            f"{BASE_URL}/api/v1/vector/documents/index",
            json=payload,
            timeout=60.0,
        )
        dt = asyncio.get_event_loop().time() - t0
        assert r.status_code == 200, r.text
        doc_info = r.json()
        assert doc_info.get("document_id") is not None
        transcript_logger.http(
            name="vector_index",
            method="POST",
            url=f"{BASE_URL}/api/v1/vector/documents/index",
            request_json=payload,
            status=r.status_code,
            response_json={"document_id": doc_info.get("document_id"), "embeddings_generated": doc_info.get("embeddings_generated")},
            duration_s=dt,
        )

    # 3) Vector: search the newly indexed content
    async with httpx.AsyncClient() as client:
        search_payload = {
            "query": "agentic orchestration test",
            "top_k": 3,
            "similarity_threshold": 0.3,
        }
        t0 = asyncio.get_event_loop().time()
        r = await client.post(
            f"{BASE_URL}/api/v1/vector/search",
            json=search_payload,
            timeout=30.0,
        )
        dt = asyncio.get_event_loop().time() - t0
        assert r.status_code == 200, r.text
        search = r.json()
        assert search.get("total_results", 0) >= 1
        transcript_logger.http(
            name="vector_search",
            method="POST",
            url=f"{BASE_URL}/api/v1/vector/search",
            request_json=search_payload,
            status=r.status_code,
            response_json={"total_results": search.get("total_results"), "processing_time_ms": search.get("processing_time_ms")},
            duration_s=dt,
        )

    # 4) Real agent orchestration via AutoGen GroupChat
    # Avoid specifying agent_name to exercise groupchat routing.
    async with httpx.AsyncClient(timeout=120.0) as client:
        convo_payload = {
            "message": "Synthesis: use vector context and backend data to provide a CEO-ready update.",
            "user_id": "e2e_user",
            "context": {"requires_approval": False},
        }
        t0 = asyncio.get_event_loop().time()
        r = await client.post(
            f"{BASE_URL}/api/v1/agents/conversation",
            json=convo_payload,
        )
        dt = asyncio.get_event_loop().time() - t0
        assert r.status_code == 200, r.text
        convo = r.json()
        assert isinstance(convo.get("response"), str) and len(convo["response"]) > 0
        assert isinstance(convo.get("agents_used", []), list)
        assert isinstance(convo.get("turn_count", 0), int)

        transcript_logger.http(
            name="agents_conversation",
            method="POST",
            url=f"{BASE_URL}/api/v1/agents/conversation",
            request_json=convo_payload,
            status=r.status_code,
            response_json={
                "agents_used": convo.get("agents_used"),
                "turn_count": convo.get("turn_count"),
                "duration_seconds": convo.get("duration_seconds"),
            },
            duration_s=dt,
        )

    # Basic smoke summary for logs
    print({
        "talents_count": talents_count,
        "doc_id": doc_info.get("document_id"),
        "vector_total_results": search.get("total_results"),
        "agents_used": convo.get("agents_used"),
        "turns": convo.get("turn_count"),
    })
