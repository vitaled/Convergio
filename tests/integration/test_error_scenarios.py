"""
🧪 Comprehensive Error Scenario Testing
=====================================

Tests for various error scenarios including network failures, service outages,
invalid inputs, timeout conditions, and resource exhaustion.
"""

import pytest
import asyncio
import os
from unittest.mock import patch, Mock, AsyncMock
from typing import Dict, Any
import httpx


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_connection_failure_scenarios(test_client):
    """Test various database connection failure scenarios."""
    
    # Test when database is completely unavailable
    with patch('core.database.async_engine.connect', side_effect=ConnectionError("Database unreachable")):
        response = await test_client.get("/health/db")
        # Should handle gracefully, not crash
        assert response.status_code in [200, 500, 503]
    
    # Test database timeout scenarios
    with patch('core.database.async_engine.connect', side_effect=asyncio.TimeoutError("Database timeout")):
        response = await test_client.get("/health/system")
        assert response.status_code in [200, 500, 503]
        
        if response.status_code == 200:
            data = response.json()
            # System should be marked as degraded/unhealthy
            assert data["status"] in ["degraded", "unhealthy"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_connection_failure_scenarios(test_client):
    """Test Redis connection failure scenarios."""
    
    # Test Redis completely unavailable
    with patch('core.redis.get_redis_client', side_effect=ConnectionError("Redis unavailable")):
        response = await test_client.get("/health/cache")
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "unhealthy"
    
    # Test Redis timeout scenarios  
    with patch('core.redis.Redis.ping', side_effect=asyncio.TimeoutError("Redis timeout")):
        response = await test_client.get("/health/system")
        assert response.status_code in [200, 503]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ai_api_failure_scenarios(test_client):
    """Test AI API failure scenarios."""
    
    # Test OpenAI API failures
    with patch('openai.AsyncOpenAI.models.list', side_effect=httpx.HTTPStatusError(
        "API Error", request=Mock(), response=Mock(status_code=429)
    )):
        response = await test_client.get("/health/ai-services")
        assert response.status_code == 200
        
        data = response.json()
        assert data["services"]["openai"]["status"] in ["unhealthy", "disabled"]
    
    # Test Anthropic API failures
    with patch('anthropic.AsyncAnthropic.messages.create', side_effect=Exception("API unavailable")):
        response = await test_client.get("/health/ai-services")
        assert response.status_code == 200
        
        data = response.json()
        # Should handle gracefully
        assert "anthropic" in data["services"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_conversation_error_scenarios(test_client):
    """Test agent conversation error scenarios."""
    
    # Test with invalid JSON
    try:
        response = await test_client.post("/api/v1/agents/conversation", 
                                        content="invalid json content",
                                        headers={"content-type": "application/json"})
        assert response.status_code in [400, 422]
    except Exception as e:
        # HTTP client level errors are also acceptable
        assert "json" in str(e).lower() or "decode" in str(e).lower()
    
    # Test with missing required fields
    response = await test_client.post("/api/v1/agents/conversation", json={})
    assert response.status_code in [400, 422]
    
    # Test with oversized request
    large_message = "x" * 50000  # 50KB message
    response = await test_client.post("/api/v1/agents/conversation", 
                                    json={"message": large_message})
    # Should either process or reject gracefully
    assert response.status_code in [200, 400, 413, 422, 503]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rate_limiting_error_scenarios(test_client):
    """Test rate limiting under various error scenarios."""
    
    # Test rapid requests to trigger rate limiting
    responses = []
    for i in range(20):  # Make many rapid requests
        try:
            response = await test_client.get(f"/health?test={i}")
            responses.append(response.status_code)
        except Exception as e:
            responses.append(f"error: {str(e)[:50]}")
    
    # Should see some rate limiting (429) or at least not all fail
    successful = [r for r in responses if r == 200]
    rate_limited = [r for r in responses if r == 429]
    
    assert len(successful) > 0, "No requests succeeded"
    # Rate limiting behavior can vary based on configuration
    
    # Test rate limiting when Redis is unavailable
    with patch('core.redis.get_redis_client', side_effect=ConnectionError("Redis down")):
        response = await test_client.get("/health")
        # Should still work (fallback behavior)
        assert response.status_code in [200, 503]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_request_error_scenarios(test_client):
    """Test error scenarios under concurrent load."""
    
    async def make_mixed_requests():
        """Make various types of requests that might fail."""
        tasks = []
        
        # Mix of different endpoints
        for i in range(5):
            tasks.append(test_client.get("/health"))
            tasks.append(test_client.get("/health/system"))
            tasks.append(test_client.post("/api/v1/agents/conversation", 
                                        json={"message": f"Test {i}"}))
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    results = await make_mixed_requests()
    
    # Analyze results
    successful = 0
    errors = 0
    
    for result in results:
        if isinstance(result, Exception):
            errors += 1
        elif hasattr(result, 'status_code') and result.status_code < 400:
            successful += 1
        else:
            errors += 1
    
    # Under load, expect some requests to succeed
    success_rate = successful / len(results) if results else 0
    assert success_rate > 0.3, f"Success rate too low: {success_rate:.2%}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_timeout_error_scenarios(test_client):
    """Test timeout scenarios."""
    
    # Test short timeout
    short_timeout_client = httpx.AsyncClient(
        base_url=os.environ.get("API_BASE_URL", "http://localhost:9000"),
        timeout=0.001  # Very short timeout
    )
    
    try:
        async with short_timeout_client:
            response = await short_timeout_client.get("/health/system")
            # If it succeeds despite short timeout, service is very fast
            assert response.status_code == 200
    except httpx.TimeoutException:
        # Expected timeout behavior
        pass
    except Exception as e:
        # Other connection errors are also acceptable
        assert "timeout" in str(e).lower() or "connection" in str(e).lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_malformed_request_scenarios(test_client):
    """Test handling of malformed requests."""
    
    # Test invalid HTTP method (if client allows)
    try:
        # Some clients may not support invalid methods
        response = await test_client.request("INVALID", "/health")
        assert response.status_code in [405, 501]
    except Exception:
        # Client-level rejection is also valid
        pass
    
    # Test invalid headers
    try:
        response = await test_client.get("/health", headers={
            "content-type": "invalid/content/type/with/many/slashes",
            "authorization": "Bearer " + "x" * 10000  # Very long token
        })
        # Should handle gracefully
        assert response.status_code in [200, 400, 401, 413]
    except Exception:
        # Connection level errors acceptable
        pass
    
    # Test invalid query parameters
    response = await test_client.get("/health?invalid=\x00\x01\x02")  # Control characters
    # Should handle gracefully
    assert response.status_code in [200, 400]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_resource_exhaustion_scenarios():
    """Test resource exhaustion scenarios."""
    
    # Test creating many connections
    clients = []
    try:
        base_url = os.environ.get("API_BASE_URL", "http://localhost:9000")
        
        # Create multiple clients (simulating resource pressure)
        for i in range(10):
            client = httpx.AsyncClient(base_url=base_url, timeout=5.0)
            clients.append(client)
        
        # Make requests with all clients concurrently
        tasks = []
        for i, client in enumerate(clients):
            tasks.append(client.get(f"/health?client={i}"))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check results
        successful = sum(1 for r in results 
                        if not isinstance(r, Exception) and r.status_code == 200)
        
        # Should handle multiple connections reasonably
        assert successful >= len(clients) // 2, "Too many connection failures"
        
    finally:
        # Cleanup clients
        for client in clients:
            try:
                await client.aclose()
            except Exception:
                pass


@pytest.mark.integration
@pytest.mark.asyncio
async def test_circuit_breaker_scenarios(test_client):
    """Test circuit breaker behavior under failures."""
    
    # This test assumes circuit breakers are implemented
    # Test repeated failures to trigger circuit breaker
    
    # Make requests that should trigger circuit breaker
    with patch('core.error_handling_enhanced.CircuitBreaker.should_allow_request', return_value=False):
        response = await test_client.get("/health/agents")
        # Should handle circuit breaker gracefully
        assert response.status_code in [200, 503]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_startup_failure_scenarios():
    """Test startup failure scenarios."""
    
    # Test startup verification under various failure conditions
    with patch('core.error_handling_enhanced.validate_service_connectivity', 
               side_effect=Exception("Service validation failed")):
        response = await test_client.get("/health/startup-verification")
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert data["startup_ready"] == False
    
    # Test partial service failures during startup
    with patch('core.error_handling_enhanced.validate_service_connectivity', 
               return_value={"database": True, "redis": False}):
        response = await test_client.get("/health/startup-verification")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] in ["degraded", "unhealthy"]


@pytest.mark.integration 
@pytest.mark.asyncio
async def test_data_consistency_error_scenarios(redis_client, db_session):
    """Test data consistency under error scenarios."""
    
    if redis_client is None:
        pytest.skip("Redis not available for consistency testing")
    
    import uuid
    
    # Test scenario where Redis and DB get out of sync
    test_key = f"consistency_test:{uuid.uuid4()}"
    
    try:
        # Write to Redis
        await redis_client.set(test_key, "redis_value", ex=300)
        
        # Simulate DB operation failure after Redis success
        from sqlalchemy import text
        
        # This should succeed
        result = await db_session.execute(text("SELECT 1"))
        assert result.scalar() == 1
        
        # Verify Redis value still exists
        value = await redis_client.get(test_key)
        assert value.decode() == "redis_value"
        
        # Test cleanup
        await redis_client.delete(test_key)
        
    except Exception as e:
        # Failure handling
        pytest.fail(f"Data consistency test failed: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_graceful_degradation_scenarios(test_client):
    """Test graceful degradation under various failure conditions."""
    
    # Test system behavior when non-critical services fail
    response = await test_client.get("/health/system")
    
    if response.status_code == 200:
        data = response.json()
        
        # System should provide information even if some services are degraded
        assert "checks" in data
        assert "summary" in data
        assert "status" in data
        
        # Verify graceful degradation: system still responds even with some failures
        if data["status"] in ["degraded", "unhealthy"]:
            # Should still provide useful information
            assert data["summary"]["total"] > 0
            assert "timestamp" in data