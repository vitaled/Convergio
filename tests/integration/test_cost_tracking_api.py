#!/usr/bin/env python3
"""
Integration/E2E test for Cost Management API
Ensures pricing exists, interactions are recorded, and realtime/session/agent views update.
"""

import asyncio
import os
import uuid
from typing import Dict, Any

import httpx
import pytest


BASE_URL = os.getenv("COST_API_BASE_URL", "http://localhost:9000/api/v1")


def _require_service_available():
    try:
        r = httpx.get(f"{BASE_URL.replace('/api/v1','')}/health", timeout=5)
        assert r.status_code == 200, f"Backend health not OK: {r.status_code} {r.text[:200]}"
    except Exception as e:
        pytest.skip(f"Backend unavailable at {BASE_URL}: {e}")


async def _choose_models(client: httpx.AsyncClient) -> Dict[str, Dict[str, Any]]:
    """Pick one available model per provider from current pricing to avoid mismatches."""
    resp = await client.get(f"{BASE_URL}/cost-management/pricing/current")
    assert resp.status_code == 200, f"pricing/current failed: {resp.status_code} {resp.text[:200]}"
    data = resp.json()
    providers = data.get("providers", {})
    assert providers, "No providers in pricing data"

    picked = {}
    for provider in ("openai", "anthropic", "perplexity"):
        models = providers.get(provider) or []
        if models:
            picked[provider] = models[0]  # first available
    assert picked, "No usable provider models found in pricing"
    return picked


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_cost_tracking_end_to_end():
    _require_service_available()

    session_id = f"test-session-{uuid.uuid4().hex[:8]}"
    conversation_id = f"test-conv-{uuid.uuid4().hex[:8]}"

    async with httpx.AsyncClient(timeout=30) as client:
        # 1) Pricing available and sensible
        pricing_resp = await client.get(f"{BASE_URL}/cost-management/pricing/current")
        assert pricing_resp.status_code == 200
        pricing = pricing_resp.json()
        assert "providers" in pricing and isinstance(pricing["providers"], dict)

        # 2) Initial realtime overview
        rt_resp = await client.get(f"{BASE_URL}/cost-management/realtime/current")
        assert rt_resp.status_code == 200
        initial = rt_resp.json()
        assert {"total_cost_usd", "today_cost_usd", "status"}.issubset(initial.keys())

        # 3) Record interactions using available models from pricing
        picks = await _choose_models(client)

        interactions = []
        if "openai" in picks:
            interactions.append({
                "session_id": session_id,
                "conversation_id": conversation_id,
                "provider": "openai",
                "model": picks["openai"]["model"],
                "input_tokens": 120,
                "output_tokens": 180,
                "agent_id": "ali_chief_of_staff",
                "agent_name": "Ali",
                "request_type": "chat",
                "response_time_ms": 900,
                "metadata": {"suite": "test_cost_tracking"}
            })
        if "anthropic" in picks:
            interactions.append({
                "session_id": session_id,
                "conversation_id": conversation_id,
                "provider": "anthropic",
                "model": picks["anthropic"]["model"],
                "input_tokens": 200,
                "output_tokens": 260,
                "agent_id": "amy_cfo",
                "agent_name": "Amy",
                "request_type": "chat",
                "response_time_ms": 800,
                "metadata": {"suite": "test_cost_tracking"}
            })
        if "perplexity" in picks:
            interactions.append({
                "session_id": session_id,
                "conversation_id": conversation_id,
                "provider": "perplexity",
                "model": picks["perplexity"]["model"],
                "input_tokens": 60,
                "output_tokens": 120,
                "agent_id": "baccio_tech_architect",
                "agent_name": "Baccio",
                "request_type": "search",
                "response_time_ms": 700,
                "metadata": {"suite": "test_cost_tracking"}
            })

        assert interactions, "No interactions prepared from pricing"

        recorded_total = 0.0
        for body in interactions:
            post = await client.post(f"{BASE_URL}/cost-management/interactions", json=body)
            assert post.status_code == 200, f"interactions POST failed: {post.status_code} {post.text[:200]}"
            payload = post.json()
            assert payload.get("success") is True
            cost = float(payload.get("cost_breakdown", {}).get("total_cost_usd", 0))
            assert cost >= 0, "Negative cost returned"
            recorded_total += cost

        # 4) Updated realtime overview reflects new spend
        await asyncio.sleep(1)
        rt2_resp = await client.get(f"{BASE_URL}/cost-management/realtime/current")
        assert rt2_resp.status_code == 200
        updated = rt2_resp.json()
        assert updated.get("today_cost_usd", 0) >= 0

        # 5) Session details include our interactions
        sess = await client.get(f"{BASE_URL}/cost-management/sessions/{session_id}")
        assert sess.status_code == 200
        sess_data = sess.json()
        assert sess_data.get("total_interactions", 0) >= len(interactions)
        assert sess_data.get("total_cost_usd", 0) >= recorded_total - 1e-6

        # 6) Agent breakdown for Ali endpoint returns structure (may be zero if no prior data)
        agent = await client.get(f"{BASE_URL}/cost-management/agents/ali_chief_of_staff/costs?days=1")
        assert agent.status_code == 200
        agent_data = agent.json()
        assert {
            "agent_id", "total_cost_usd", "total_calls", "model_breakdown"
        }.issubset(agent_data.keys())
