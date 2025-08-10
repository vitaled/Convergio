#!/usr/bin/env python3
"""
E2E test: Ali Intelligence endpoint using real OpenAI API and real orchestrations

- Makes a live call to /api/v1/ali/intelligence
- Uses real OpenAI API via httpx to OpenAI
- Produces detailed logging of the full request/response lifecycle

Safety: The test is skipped unless RUN_REAL_OPENAI_TESTS=1 is set.
It also requires an OpenAI key available either as env OPENAI_API_KEY or via /api/v1/user-keys setup.
"""

import os
import sys
import asyncio
import json
import time
import pytest
import httpx
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Ensure backend root is on sys.path for importing src.*
_BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _BACKEND_PATH not in sys.path:
    sys.path.insert(0, _BACKEND_PATH)

from src.core.config import get_settings


RUN_REAL = os.environ.get("RUN_REAL_OPENAI_TESTS") == "1"

pytestmark = pytest.mark.skipif(not RUN_REAL, reason="Set RUN_REAL_OPENAI_TESTS=1 to run real OpenAI E2E test")


@pytest_asyncio.fixture
async def client():
    """Create httpx AsyncClient against ASGI app with minimal overrides."""
    # Use real HTTP against running backend so internal vector calls succeed
    async with AsyncClient(base_url="http://localhost:9000") as client:
        yield client


@pytest.mark.asyncio
async def test_ali_intelligence_real_openai(client):
    # Arrange: optionally store user key if available via env
    openai_key = os.environ.get("OPENAI_API_KEY")

    # Use a separate synchronous client because store_user_api_keys expects HTTP request context
    async with httpx.AsyncClient(base_url="http://localhost:9000") as setup_client:
        if openai_key:
            print("🔑 Storing user OpenAI API key for session...")
            resp = await setup_client.post("/api/v1/user-keys", json={"openai_api_key": openai_key, "default_model": get_settings().OPENAI_MODEL})
            assert resp.status_code in (200, 201), f"Failed to store key: {resp.status_code} {resp.text}"
            print(f"✅ Key stored: {resp.json()}")
        else:
            print("⚠️ No OPENAI_API_KEY env var set; relying on backend settings.OPENAI_API_KEY if configured.")

    # Act: call Ali endpoint
    payload = {
        "message": "Fai un'analisi strategica delle opportunità di crescita nei prossimi 6 mesi e proponi 3 azioni prioritarie.",
        "use_vector_search": True,
        "use_database_insights": True,
        "include_strategic_analysis": True
    }

    print("🚀 Calling /api/v1/ali/intelligence with payload:\n", json.dumps(payload, ensure_ascii=False, indent=2))
    t0 = time.time()
    response = await client.post("/api/v1/ali/intelligence", json=payload)
    dt = time.time() - t0

    # Assert baseline
    assert response.status_code == 200, f"Unexpected status: {response.status_code} {response.text}"

    data = response.json()

    # Detailed logs
    print("\n📥 Response JSON (truncated fields for readability):")
    print("- keys:", list(data.keys()))
    print("- confidence_score:", data.get("confidence_score"))
    print("- data_sources_used:", data.get("data_sources_used"))

    resp_text = data.get("response", "")
    print("\n📝 Ali Strategic Response (first 800 chars):\n", resp_text[:800])

    chain = data.get("reasoning_chain", [])
    print("\n🧭 Reasoning chain:")
    for i, step in enumerate(chain, 1):
        print(f"  {i}. {step}")

    actions = data.get("suggested_actions", [])
    print("\n✅ Suggested actions:")
    for i, a in enumerate(actions, 1):
        print(f"  {i}. {a}")

    related = data.get("related_insights", [])
    print("\n🔎 Related insights (count:", len(related), ")")
    for i, r in enumerate(related[:5], 1):
        print(f"  {i}. {r.get('title')}: {r.get('description')}")

    print(f"\n⏱️ Total latency: {dt:.2f}s")

    # Minimal validations that indicate real orchestration happened
    assert isinstance(data.get("response"), str) and len(data["response"]) > 0
    assert isinstance(chain, list) and len(chain) >= 3
    assert isinstance(actions, list) and len(actions) >= 1
