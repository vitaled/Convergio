#!/usr/bin/env python3
"""
End-to-end real test hitting:
- /api/v1/user-keys to store OpenAI key (optional if settings has key)
- /api/v1/vector/documents/index to index a doc with real OpenAI embeddings
- /api/v1/vector/search to retrieve it via similarity with real OpenAI embeddings
- /api/v1/ali/intelligence to produce a strategic response that also calls vector API

Requires: RUN_REAL_OPENAI_TESTS=1 and an OpenAI key (either env OPENAI_API_KEY or configured in settings).
Skips by default to avoid accidental costs.
"""

import os
import sys
import time
import json
import pytest
import pytest_asyncio
from httpx import AsyncClient

# Ensure backend root is on sys.path for importing src.*
_BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _BACKEND_PATH not in sys.path:
    sys.path.insert(0, _BACKEND_PATH)

from src.core.config import get_settings

RUN_REAL = os.environ.get("RUN_REAL_OPENAI_TESTS") == "1"
pytestmark = pytest.mark.skipif(not RUN_REAL, reason="Set RUN_REAL_OPENAI_TESTS=1 to run real E2E test")


@pytest_asyncio.fixture
async def client():
    # Real HTTP client against running backend
    async with AsyncClient(base_url="http://localhost:9000") as c:
        yield c


@pytest.mark.asyncio
async def test_real_e2e_vector_and_ali(client):
    # 0) Store OpenAI key for session if provided
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        print("🔑 Storing user OpenAI API key for session...")
        r = await client.post("/api/v1/user-keys", json={
            "openai_api_key": openai_key,
            "default_model": get_settings().OPENAI_MODEL,
        })
        assert r.status_code in (200, 201), f"Key store failed: {r.status_code} {r.text}"
        print("✅ Key stored =>", r.json())
    else:
        print("⚠️ No OPENAI_API_KEY env var set; relying on settings.OPENAI_API_KEY.")

    # 1) Index a document
    doc_payload = {
        "title": "Strategic AI Growth Plan",
        "content": (
            "Convergio's AI-native platform enables multi-agent orchestration for business workflows. "
            "Key growth opportunities include vector search enhancements, market expansion, and cost optimization."
        ),
        "metadata": {"domain": "strategy", "quarter": "Q3"},
        "chunk_size": 200,
        "chunk_overlap": 50,
    }

    print("\n📥 Indexing document...\n", json.dumps(doc_payload, ensure_ascii=False, indent=2))
    t0 = time.time()
    idx = await client.post("/api/v1/vector/documents/index", json=doc_payload)
    t_idx = time.time() - t0
    assert idx.status_code == 200, f"Index failed: {idx.status_code} {idx.text}"
    idx_data = idx.json()
    print("✅ Indexed:", idx_data)
    print(f"⏱️ Index latency: {t_idx:.2f}s")

    # 2) Similarity search
    search_payload = {"query": "AI orchestration and vector search", "top_k": 3, "similarity_threshold": 0.2}
    print("\n🔍 Similarity search...\n", json.dumps(search_payload, ensure_ascii=False, indent=2))
    t0 = time.time()
    sr = await client.post("/api/v1/vector/search", json=search_payload)
    t_search = time.time() - t0
    assert sr.status_code == 200, f"Search failed: {sr.status_code} {sr.text}"
    srj = sr.json()
    print("✅ Search results count:", srj.get("total_results"), "time:", srj.get("processing_time_ms"), "ms")
    for i, r in enumerate(srj.get("results", []), 1):
        print(f"  {i}. score={r['similarity_score']:.3f} title={r['title']}")
    print(f"⏱️ Search latency: {t_search:.2f}s")

    assert srj.get("total_results", 0) >= 1

    # 3) Ali intelligence (will internally call vector search again and OpenAI chat completions)
    ali_payload = {
        "message": "Quali sono le 3 azioni strategiche immediate per massimizzare la crescita AI nel prossimo trimestre?",
        "use_vector_search": True,
        "use_database_insights": False,
        "include_strategic_analysis": True,
    }

    print("\n🧠 Calling Ali intelligence...\n", json.dumps(ali_payload, ensure_ascii=False, indent=2))
    t0 = time.time()
    ali = await client.post("/api/v1/ali/intelligence", json=ali_payload)
    t_ali = time.time() - t0
    assert ali.status_code == 200, f"Ali failed: {ali.status_code} {ali.text}"

    ali_data = ali.json()
    print("\n📊 Ali response keys:", list(ali_data.keys()))
    print("confidence:", ali_data.get("confidence_score"), "sources:", ali_data.get("data_sources_used"))
    print("response preview:\n", ali_data.get("response", "")[:800])
    print("reasoning chain:")
    for i, step in enumerate(ali_data.get("reasoning_chain", []), 1):
        print(f"  {i}. {step}")
    print("suggested actions:")
    for i, a in enumerate(ali_data.get("suggested_actions", []), 1):
        print(f"  {i}. {a}")
    print(f"⏱️ Ali latency: {t_ali:.2f}s")

    assert isinstance(ali_data.get("response"), str) and len(ali_data["response"]) > 0
    assert "Vector Database" in ali_data.get("data_sources_used", [])
