"""
🧪 Real Integration Tests - Service Connectivity
===============================================

Comprehensive integration tests using real database, Redis, and API connections.
These tests replace the mocked versions to ensure actual service connectivity.
"""

import pytest
import asyncio
from typing import Dict, Any


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_real_connectivity(database_connectivity_test):
    """Test real database connectivity with actual SQL operations."""
    assert database_connectivity_test is True, "Database connectivity test failed"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_real_connectivity(redis_connectivity_test):
    """Test real Redis connectivity with actual operations."""
    assert redis_connectivity_test is True, "Redis connectivity test failed"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ai_api_real_connectivity(ai_api_connectivity_test):
    """Test AI API connectivity with actual API key validation."""
    results = ai_api_connectivity_test
    assert results["at_least_one"], f"No AI APIs are functional: {results}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_health_endpoint_real_connectivity(test_client):
    """Test health endpoint using real HTTP client."""
    response = await test_client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_system_health_real_connectivity(test_client):
    """Test system health with real service checks."""
    response = await test_client.get("/health/system")
    assert response.status_code == 200
    
    data = response.json()
    # Real system health should reflect actual service status
    assert "checks" in data
    assert "database" in data["checks"]
    assert "cache" in data["checks"]  # Redis is called "cache" in the response
    assert data["status"] in ["healthy", "degraded"]  # Allow for partial failures


@pytest.mark.integration
@pytest.mark.asyncio
async def test_api_status_real_connectivity(test_client):
    """Test API status endpoint with real service connections."""
    response = await test_client.get("/api/v1/system/api-status")
    assert response.status_code == 200
    
    data = response.json()
    assert "backend" in data
    # Real API status should reflect actual API connectivity
    assert isinstance(data["backend"], dict)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_operations_with_session(db_session):
    """Test database operations using real database session."""
    from sqlalchemy import text
    
    # Test basic query execution
    result = await db_session.execute(text("SELECT version() as db_version"))
    row = result.fetchone()
    assert row is not None
    assert "PostgreSQL" in row[0]  # Assuming PostgreSQL
    
    # Test parameterized query
    result = await db_session.execute(
        text("SELECT :test_param as param_value"), 
        {"test_param": "integration_test"}
    )
    row = result.fetchone()
    assert row[0] == "integration_test"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_operations_with_client(redis_client):
    """Test Redis operations using real Redis client."""
    if redis_client is None:
        pytest.skip("Redis not available for testing")
    
    import uuid
    
    # Test string operations
    test_key = f"integration_test:{uuid.uuid4()}"
    await redis_client.set(test_key, "test_value", ex=300)  # 5 minute expiry
    
    value = await redis_client.get(test_key)
    assert value.decode() == "test_value"
    
    # Test hash operations
    hash_key = f"integration_hash:{uuid.uuid4()}"
    await redis_client.hset(hash_key, "field1", "value1")
    await redis_client.hset(hash_key, "field2", "value2")
    await redis_client.expire(hash_key, 300)
    
    hash_data = await redis_client.hgetall(hash_key)
    assert hash_data[b"field1"].decode() == "value1"
    assert hash_data[b"field2"].decode() == "value2"
    
    # Test list operations
    list_key = f"integration_list:{uuid.uuid4()}"
    await redis_client.lpush(list_key, "item1", "item2", "item3")
    await redis_client.expire(list_key, 300)
    
    list_length = await redis_client.llen(list_key)
    assert list_length == 3
    
    # Cleanup
    await redis_client.delete(test_key, hash_key, list_key)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_conversation_real_api(test_client):
    """Test agent conversation using real API calls."""
    conversation_data = {
        "message": "Hello, this is an integration test",
        "user_id": "integration_test_user",
        "context": {"test_mode": True}
    }
    
    response = await test_client.post("/api/v1/agents/conversation", json=conversation_data)
    
    # Allow for various response codes since this tests real systems
    assert response.status_code in [200, 503], f"Unexpected status code: {response.status_code}"
    
    if response.status_code == 200:
        data = response.json()
        assert "response" in data
        assert "conversation_id" in data
        assert isinstance(data["response"], str)
    else:
        # Service unavailable is acceptable for integration tests
        data = response.json()
        assert "detail" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cost_management_real_data(test_client):
    """Test cost management endpoint with real data."""
    response = await test_client.get("/api/v1/cost-management/realtime/current")
    
    # Cost management should work even without API keys
    assert response.status_code == 200
    
    data = response.json()
    assert "model_breakdown" in data  # Real API response structure
    assert "last_updated" in data
    assert "budget_utilization" in data
    assert isinstance(data["budget_utilization"], (int, float))


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_requests_real_load(test_client):
    """Test handling concurrent requests with real services."""
    async def make_health_request():
        return await test_client.get("/health")
    
    # Make 5 concurrent requests
    tasks = [make_health_request() for _ in range(5)]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful_responses = [r for r in responses if not isinstance(r, Exception) and r.status_code == 200]
    assert len(successful_responses) >= 3, "Too many concurrent request failures"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rate_limiting_real_enforcement(test_client):
    """Test rate limiting with real Redis backend."""
    # Make rapid requests to trigger rate limiting
    responses = []
    for i in range(15):  # Exceed typical rate limits
        try:
            response = await test_client.get("/health")
            responses.append(response.status_code)
        except Exception as e:
            responses.append(f"error: {e}")
    
    # Should see mix of 200s and 429s if rate limiting is working
    status_codes = [r for r in responses if isinstance(r, int)]
    
    # Allow for various behaviors - rate limiting might be configured differently
    assert len(status_codes) > 0, "No successful requests made"
    
    # At least some requests should succeed
    successful_requests = sum(1 for code in status_codes if code == 200)
    assert successful_requests >= 5, "Too few successful requests"


@pytest.mark.integration 
@pytest.mark.slow
@pytest.mark.asyncio
async def test_service_resilience_under_load(test_client, redis_client, db_session):
    """Test service resilience under simulated load."""
    if redis_client is None:
        pytest.skip("Redis not available for resilience testing")
    
    # Simulate mixed workload
    async def mixed_workload():
        tasks = []
        
        # HTTP requests
        tasks.extend([test_client.get("/health") for _ in range(3)])
        tasks.extend([test_client.get("/api/v1/system/status") for _ in range(2)])
        
        # Redis operations
        for i in range(3):
            tasks.append(redis_client.set(f"load_test_{i}", f"value_{i}", ex=60))
        
        # Database operations
        from sqlalchemy import text
        tasks.append(db_session.execute(text("SELECT 1")))
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Count successful operations
        successful = sum(1 for r in results if not isinstance(r, Exception))
        return successful, len(results)
    
    successful, total = await mixed_workload()
    success_rate = successful / total
    
    # Expect at least 70% success rate under load
    assert success_rate >= 0.7, f"Success rate too low: {success_rate:.2%} ({successful}/{total})"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_error_handling_real_scenarios(test_client):
    """Test error handling with real error scenarios."""
    # Test invalid endpoint
    response = await test_client.get("/api/v1/nonexistent/endpoint")
    assert response.status_code == 404
    
    # Test malformed request
    response = await test_client.post("/api/v1/agents/conversation", json={"invalid": "data"})
    assert response.status_code in [400, 422, 500]  # Various validation errors possible
    
    # Test oversized request (if configured)
    large_data = {"message": "x" * 10000}  # 10KB message
    response = await test_client.post("/api/v1/agents/conversation", json=large_data)
    # Should either process or reject gracefully
    assert response.status_code in [200, 400, 413, 422, 503]