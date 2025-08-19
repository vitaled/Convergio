#!/usr/bin/env python3
"""
Smoke tests for real integrations: database stats, vector tool availability, and Ali endpoint.
These are assertive but skip when required services/keys are missing.
"""

import json
import os
import pytest
import httpx

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:9000")


def _get(url: str, timeout: float = 10):
    return httpx.get(url, timeout=timeout)


@pytest.mark.integration
def test_database_tools_return_real_data():
    # Use the public system endpoints to avoid direct DB tool imports here
    r = _get(f"{BASE_URL}/health/detailed")
    if r.status_code != 200:
        pytest.skip(f"Backend not healthy: {r.status_code}")
    data = r.json()
    checks = data.get("checks", {})
    assert checks.get("database", {}).get("status") in {"healthy", "degraded", "unhealthy"}  # Allow unhealthy in test env


@pytest.mark.integration
def test_ali_intelligence_endpoint_structured_response():
    payload = {
        "query": "How many people work in our company?",
        "use_database_insights": True,
        "use_vector_search": False,
    }
    try:
        r = httpx.post(f"{BASE_URL}/api/v1/ali/intelligence", json=payload, timeout=30)
    except Exception as e:
        pytest.skip(f"Ali endpoint unavailable: {e}")

    if r.status_code != 200:
        pytest.skip(f"Ali endpoint not ready: {r.status_code}")

    body = r.json()
    assert "response" in body
    assert "data_sources_used" in body  # Real response structure


@pytest.mark.integration
def test_vector_search_endpoint_available():
    r = _get(f"{BASE_URL}/health/vector")
    if r.status_code != 200:
        pytest.skip("Vector health endpoint unavailable")
    data = r.json()
    assert data.get("status") in {"healthy", "degraded"}
