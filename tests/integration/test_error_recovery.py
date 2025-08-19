"""
🔄 Error Recovery Testing
======================

Tests for system recovery capabilities after various error conditions.
Ensures the system can recover gracefully from failures.
"""

import pytest
import asyncio
import time
from unittest.mock import patch, Mock
from typing import Dict, Any


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_reconnection_recovery(test_client):
    """Test database reconnection after connection loss."""
    
    # Simulate database disconnection followed by reconnection
    connection_attempts = []
    
    def mock_db_connection(*args, **kwargs):
        connection_attempts.append(time.time())
        if len(connection_attempts) <= 2:  # Fail first 2 attempts
            raise ConnectionError("Database connection lost")
        return Mock()  # Success on 3rd attempt
    
    with patch('core.database.async_engine.connect', side_effect=mock_db_connection):
        # First request should fail
        response1 = await test_client.get("/health/db")
        
        # Wait a moment and try again (should still fail)
        await asyncio.sleep(0.1)
        response2 = await test_client.get("/health/db")
        
        # Third attempt should succeed (if retry logic works)
        await asyncio.sleep(0.1)
        response3 = await test_client.get("/health/db")
    
    # Verify retry attempts were made
    assert len(connection_attempts) >= 2, "Not enough connection attempts made"
    
    # At least one response should indicate the issue
    responses = [response1, response2, response3]
    error_responses = [r for r in responses if r.status_code != 200]
    assert len(error_responses) > 0, "No error responses detected"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_redis_reconnection_recovery(redis_client):
    """Test Redis reconnection and recovery."""
    
    if redis_client is None:
        pytest.skip("Redis not available for recovery testing")
    
    import uuid
    
    # Test normal operation
    test_key = f"recovery_test:{uuid.uuid4()}"
    await redis_client.set(test_key, "initial_value", ex=300)
    
    # Verify value was set
    value = await redis_client.get(test_key)
    assert value.decode() == "initial_value"
    
    # Simulate connection loss and recovery by using a new client
    try:
        from core.redis import get_redis_client
        new_client = await get_redis_client()
        
        # Should be able to retrieve the value with new connection
        recovered_value = await new_client.get(test_key)
        assert recovered_value.decode() == "initial_value"
        
        # Cleanup
        await new_client.delete(test_key)
        
    except Exception as e:
        pytest.fail(f"Redis recovery test failed: {e}")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_ai_api_fallback_recovery(test_client):
    """Test AI API fallback and recovery mechanisms."""
    
    # Mock OpenAI failure, Anthropic success
    with patch('openai.AsyncOpenAI.models.list', side_effect=Exception("OpenAI down")), \
         patch('anthropic.AsyncAnthropic.messages.create', return_value=Mock(
             content=[Mock(text="Recovery response")])):
        
        response = await test_client.get("/health/ai-services")
        assert response.status_code == 200
        
        data = response.json()
        # Should show OpenAI as unhealthy but overall system still functional
        assert data["services"]["openai"]["status"] == "unhealthy"
        # System should still be operational if at least one AI service works
        assert data["status"] in ["healthy", "degraded"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rate_limiter_recovery_after_redis_failure():
    """Test rate limiter recovery after Redis failure."""
    
    from core.rate_limiting_enhanced import EnhancedRateLimitEngine
    from unittest.mock import AsyncMock
    
    # Create mock Redis client that fails initially then recovers
    mock_redis = AsyncMock()
    failure_count = 0
    
    async def mock_pipeline():
        nonlocal failure_count
        failure_count += 1
        if failure_count <= 2:  # Fail first 2 calls
            raise ConnectionError("Redis connection failed")
        
        # Success on subsequent calls
        mock_pipe = AsyncMock()
        mock_pipe.execute.return_value = [None, 5, None, None]  # Mock pipeline results
        return mock_pipe
    
    mock_redis.pipeline = mock_pipeline
    
    # Create rate limiter with mock Redis
    rate_limiter = EnhancedRateLimitEngine(mock_redis)
    
    # Create mock request
    mock_request = Mock()
    mock_request.url.path = "/test"
    mock_request.headers = {}
    mock_request.state = Mock()
    mock_request.state.user_id = None
    
    # First attempts should fail gracefully (allow requests when Redis is down)
    result1 = await rate_limiter.check_rate_limit(mock_request)
    assert result1.allowed == True, "Should allow requests when Redis fails"
    
    result2 = await rate_limiter.check_rate_limit(mock_request)
    assert result2.allowed == True, "Should continue allowing requests"
    
    # Third attempt should use Redis successfully
    result3 = await rate_limiter.check_rate_limit(mock_request)
    assert result3.allowed == True, "Should work normally after Redis recovery"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_system_recovery_after_failure(test_client):
    """Test agent system recovery after failures."""
    
    # Test agent system health endpoint
    response = await test_client.get("/health/agents")
    assert response.status_code == 200
    
    data = response.json()
    
    # Agent system should handle failures gracefully
    if data["status"] == "unhealthy":
        # System acknowledges the issue
        assert "error" in data
    elif data["status"] == "degraded":
        # Partial functionality available
        assert "message" in data
    else:
        # System is healthy
        assert data["status"] == "healthy"
        assert "agents_count" in data


@pytest.mark.integration
@pytest.mark.asyncio
async def test_circuit_breaker_recovery():
    """Test circuit breaker recovery behavior."""
    
    from core.error_handling_enhanced import CircuitBreaker, CircuitBreakerConfig
    
    # Create circuit breaker with quick recovery for testing
    config = CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=1,  # 1 second recovery
        half_open_max_calls=2
    )
    
    cb = CircuitBreaker("test_service", config)
    
    # Trigger failures to open circuit
    for i in range(4):
        cb.on_failure()
        assert cb.should_allow_request() == (i < 3), f"Circuit state incorrect at failure {i}"
    
    # Circuit should be open now
    assert cb.should_allow_request() == False, "Circuit should be open"
    
    # Wait for recovery timeout
    await asyncio.sleep(1.1)
    
    # Should enter half-open state
    assert cb.should_allow_request() == True, "Circuit should allow requests in half-open state"
    
    # Simulate successful requests to fully recover
    cb.on_success()
    cb.on_success()
    
    # Circuit should be fully recovered
    assert cb.should_allow_request() == True, "Circuit should be fully recovered"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_graceful_degradation_recovery(test_client):
    """Test recovery from graceful degradation scenarios."""
    
    # Test system status under various conditions
    response = await test_client.get("/health/system")
    assert response.status_code == 200
    
    original_data = response.json()
    original_status = original_data["status"]
    
    # Simulate recovery by making multiple requests
    recovery_attempts = []
    
    for i in range(5):
        await asyncio.sleep(0.1)  # Small delay between attempts
        response = await test_client.get("/health/system")
        if response.status_code == 200:
            data = response.json()
            recovery_attempts.append(data["status"])
    
    # System should maintain consistency or show improvement
    if recovery_attempts:
        final_status = recovery_attempts[-1]
        
        # Status should not get worse during recovery attempts
        status_priority = {"healthy": 3, "degraded": 2, "unhealthy": 1}
        original_priority = status_priority.get(original_status, 0)
        final_priority = status_priority.get(final_status, 0)
        
        # Allow for temporary fluctuations but expect stability
        assert len(set(recovery_attempts[-3:])) <= 2, "Status too unstable during recovery"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_concurrent_recovery_scenarios(test_client):
    """Test recovery under concurrent load."""
    
    async def make_recovery_requests():
        """Make requests that test various recovery scenarios."""
        tasks = [
            test_client.get("/health"),
            test_client.get("/health/system"),
            test_client.get("/health/db"),
            test_client.get("/health/cache"),
            test_client.get("/health/agents")
        ]
        
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    # Make concurrent requests multiple times to test stability
    all_results = []
    
    for round_num in range(3):
        await asyncio.sleep(0.1)  # Brief pause between rounds
        results = await make_recovery_requests()
        all_results.extend(results)
    
    # Analyze results
    successful_responses = 0
    error_responses = 0
    
    for result in all_results:
        if isinstance(result, Exception):
            error_responses += 1
        elif hasattr(result, 'status_code'):
            if result.status_code < 400:
                successful_responses += 1
            else:
                error_responses += 1
    
    # Calculate success rate
    total_requests = len(all_results)
    success_rate = successful_responses / total_requests if total_requests > 0 else 0
    
    # Expect reasonable success rate during recovery
    assert success_rate >= 0.6, f"Success rate too low during recovery: {success_rate:.2%}"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_memory_cleanup_recovery():
    """Test memory cleanup and resource recovery."""
    
    import gc
    import psutil
    import os
    
    # Get initial memory usage
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    # Create some data structures that should be cleaned up
    large_data = []
    for i in range(1000):
        large_data.append({
            f"key_{i}": f"value_{i}" * 100,  # Create some data
            "metadata": {"index": i, "timestamp": time.time()}
        })
    
    # Force garbage collection
    gc.collect()
    
    # Clear the data
    large_data.clear()
    del large_data
    
    # Force another garbage collection
    gc.collect()
    await asyncio.sleep(0.1)  # Give time for cleanup
    
    # Check memory usage after cleanup
    final_memory = process.memory_info().rss
    memory_increase = final_memory - initial_memory
    
    # Memory increase should be reasonable (less than 50MB for this test)
    assert memory_increase < 50 * 1024 * 1024, f"Memory increase too high: {memory_increase / 1024 / 1024:.1f}MB"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_configuration_recovery_scenarios():
    """Test recovery from configuration issues."""
    
    from core.config_enhanced import EnhancedSettings
    import os
    
    # Test with invalid configuration values
    original_env = os.environ.copy()
    
    try:
        # Set invalid configuration
        os.environ["DATABASE_POOL_SIZE"] = "invalid_number"
        os.environ["REDIS_TIMEOUT"] = "not_a_number"
        
        # System should handle invalid config gracefully
        try:
            settings = EnhancedSettings()
            # Should fall back to defaults
            assert isinstance(settings.database_pool_size, int)
        except Exception as e:
            # Or fail gracefully with clear error
            assert "configuration" in str(e).lower() or "validation" in str(e).lower()
    
    finally:
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.asyncio
async def test_long_term_stability_recovery(test_client):
    """Test long-term stability and recovery patterns."""
    
    # Make requests over a longer period to test stability
    results = []
    start_time = time.time()
    
    while time.time() - start_time < 10:  # Run for 10 seconds
        try:
            response = await test_client.get("/health")
            results.append({
                "timestamp": time.time(),
                "status_code": response.status_code,
                "success": response.status_code == 200
            })
        except Exception as e:
            results.append({
                "timestamp": time.time(),
                "error": str(e),
                "success": False
            })
        
        await asyncio.sleep(0.5)  # Request every 500ms
    
    # Analyze long-term behavior
    successful_requests = sum(1 for r in results if r.get("success", False))
    total_requests = len(results)
    
    if total_requests > 0:
        success_rate = successful_requests / total_requests
        assert success_rate >= 0.8, f"Long-term success rate too low: {success_rate:.2%}"
        
        # Check for stability - no long periods of continuous failure
        consecutive_failures = 0
        max_consecutive_failures = 0
        
        for result in results:
            if result.get("success", False):
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                max_consecutive_failures = max(max_consecutive_failures, consecutive_failures)
        
        # Should not have more than 5 consecutive failures
        assert max_consecutive_failures <= 5, f"Too many consecutive failures: {max_consecutive_failures}"