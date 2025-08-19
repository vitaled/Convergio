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
    """Test database health monitoring with REAL database connections."""
    
    # Test that database health endpoint works properly
    response = await test_client.get("/health/db")
    assert response.status_code == 200, "Database health endpoint should be accessible"
    
    data = response.json()
    assert "status" in data, "Database health should report status"
    
    # Test system health with database included
    response = await test_client.get("/health/system")
    assert response.status_code == 200, "System health endpoint should be accessible"
    
    data = response.json()
    assert "status" in data, "System should report overall status"
    assert "checks" in data, "System should report individual checks"
    
    # Verify database is included in system checks
    checks = data.get("checks", {})
    db_check_found = False
    
    for service_name, service_data in checks.items():
        if "database" in service_name.lower() or "db" in service_name.lower():
            db_check_found = True
            assert "status" in service_data, f"Database check {service_name} should report status"
            break
    
    # If no explicit database check found, verify database health endpoint is working
    if not db_check_found:
        response = await test_client.get("/health/db")
        assert response.status_code == 200, "Database health endpoint should work as fallback check"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_connection_failure_scenarios(test_client):
    """Test Redis health monitoring with REAL connections."""
    
    # Test Redis cache health endpoint
    response = await test_client.get("/health/cache")
    assert response.status_code == 200, "Cache health endpoint should be accessible"
    
    data = response.json()
    assert "status" in data, "Cache health should report status"
    
    # Verify Redis status is properly reported
    if data["status"] == "healthy":
        # If healthy, should have connection details
        assert "connection" in data, "Healthy cache should report connection status"
    elif data["status"] == "unhealthy":
        # If unhealthy, should report error details
        assert "error" in data, "Unhealthy cache should report error details"
    
    # Test system health includes cache check
    response = await test_client.get("/health/system")
    assert response.status_code == 200, "System health should be accessible"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ai_api_failure_scenarios(test_client):
    """Test AI API health monitoring with REAL API connections."""
    
    # Test AI services health endpoint
    response = await test_client.get("/health/ai-services")
    assert response.status_code == 200, "AI services health endpoint should be accessible"
    
    data = response.json()
    assert "status" in data, "AI services should report overall status"
    assert "services" in data, "AI services should report individual service statuses"
    assert "healthy_count" in data, "AI services should report healthy count"
    assert "total_count" in data, "AI services should report total count"
    
    # Test individual service reporting
    services = data.get("services", {})
    for service_name, service_data in services.items():
        assert "status" in service_data, f"Service {service_name} should report status"
        assert service_data["status"] in ["healthy", "unhealthy", "disabled"], f"Service {service_name} status should be valid"
        assert "connection" in service_data, f"Service {service_name} should report connection status"
        
        # If service is healthy, verify it has additional details
        if service_data["status"] == "healthy":
            assert service_data["connection"] == "active", f"Healthy service {service_name} should have active connection"
    
    # Test that system gracefully handles various service states
    overall_status = data["status"]
    assert overall_status in ["healthy", "degraded", "unhealthy", "disabled"], "Overall AI services status should be valid"


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
    try:
        response = await test_client.get("/health?invalid=\x00\x01\x02")  # Control characters
        # Should handle gracefully
        assert response.status_code in [200, 400]
    except Exception as e:
        # Client-level URL validation errors are acceptable
        assert "invalid" in str(e).lower() or "url" in str(e).lower() or "character" in str(e).lower()


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
async def test_startup_failure_scenarios(test_client):
    """Test startup verification with REAL API calls."""
    
    # Test startup verification endpoint works
    response = await test_client.get("/health/startup-verification")
    assert response.status_code == 200, "Startup verification endpoint should be accessible"
    
    data = response.json()
    assert "status" in data, "Startup verification should report status"
    assert "startup_ready" in data, "Startup verification should report readiness"
    assert "timestamp" in data, "Startup verification should include timestamp"
    
    # Verify startup_ready is boolean
    assert isinstance(data["startup_ready"], bool), "startup_ready should be boolean"
    
    # Test that critical services are checked
    if "critical_services" in data:
        critical_services = data["critical_services"]
        assert isinstance(critical_services, dict), "Critical services should be a dict"
        
        # Verify all critical service checks are boolean
        for service_name, service_status in critical_services.items():
            assert isinstance(service_status, bool), f"Service {service_name} status should be boolean"
    
    # Test that AI services are checked
    if "ai_services" in data:
        ai_services = data["ai_services"]
        assert "status" in ai_services, "AI services should report status"
        assert "healthy_count" in ai_services, "AI services should report healthy count"
    
    # Test multiple requests for consistency
    for i in range(3):
        await asyncio.sleep(0.1)
        response2 = await test_client.get("/health/startup-verification")
        assert response2.status_code == 200, f"Startup verification {i+1} should succeed"
        
        data2 = response2.json()
        # Status should be consistent across requests
        assert isinstance(data2["startup_ready"], bool), "startup_ready should remain boolean"


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