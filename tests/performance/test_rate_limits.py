"""
Performance Tests - Rate limiting validation
Tests rate limiting, throttling, and circuit breaker patterns
"""

import pytest
import asyncio
import time
from typing import List
from unittest.mock import Mock, patch
import redis

from core.rate_limiting import RateLimiter, TokenBucket


class TestRateLimiting:
    """Test suite for rate limiting features"""
    
    @pytest.fixture
    def rate_limiter(self):
        """Initialize rate limiter"""
        return RateLimiter(
            requests_per_second=10,
            burst_size=20,
            redis_client=Mock(spec=redis.Redis)
        )
    
    @pytest.fixture
    def token_bucket(self):
        """Initialize token bucket"""
        return TokenBucket(
            capacity=10,
            refill_rate=5,  # 5 tokens per second
        )
    
    def test_token_bucket_initialization(self, token_bucket):
        """Test token bucket starts with full capacity"""
        assert token_bucket.tokens == 10
        assert token_bucket.capacity == 10
        assert token_bucket.refill_rate == 5
    
    def test_token_bucket_consumption(self, token_bucket):
        """Test token consumption"""
        # Consume 5 tokens
        assert token_bucket.consume(5) == True
        assert token_bucket.tokens == 5
        
        # Try to consume more than available
        assert token_bucket.consume(6) == False
        assert token_bucket.tokens == 5  # Unchanged
        
        # Consume remaining
        assert token_bucket.consume(5) == True
        assert token_bucket.tokens == 0
    
    def test_token_bucket_refill(self, token_bucket):
        """Test token refill over time"""
        # Consume all tokens
        token_bucket.consume(10)
        assert token_bucket.tokens == 0
        
        # Wait for refill
        time.sleep(1.1)  # Wait for 1 second
        token_bucket.refill()
        
        # Should have ~5 tokens (5 per second)
        assert 4 <= token_bucket.tokens <= 6
    
    def test_rate_limiter_allow_request(self, rate_limiter):
        """Test rate limiter allows requests within limits"""
        client_id = "test_client"
        
        # First 10 requests should be allowed (rate limit)
        for i in range(10):
            assert rate_limiter.allow_request(client_id) == True
        
        # 11th request should be denied
        assert rate_limiter.allow_request(client_id) == False
    
    def test_rate_limiter_burst_capacity(self, rate_limiter):
        """Test burst capacity allows temporary spikes"""
        client_id = "burst_client"
        
        # Burst size is 20, so 20 rapid requests should be allowed
        results = []
        for i in range(25):
            results.append(rate_limiter.allow_request(client_id))
        
        # First 20 should be True (burst capacity)
        assert sum(results[:20]) == 20
        # Remaining should be False
        assert sum(results[20:]) == 0
    
    @pytest.mark.asyncio
    async def test_concurrent_rate_limiting(self, rate_limiter):
        """Test rate limiting under concurrent load"""
        client_id = "concurrent_client"
        
        async def make_request():
            return rate_limiter.allow_request(client_id)
        
        # Create 50 concurrent requests
        tasks = [make_request() for _ in range(50)]
        results = await asyncio.gather(*tasks)
        
        # Only burst_size (20) should succeed
        assert sum(results) == 20
    
    def test_per_user_rate_limiting(self, rate_limiter):
        """Test independent rate limits per user"""
        client1 = "user1"
        client2 = "user2"
        
        # Use up client1's quota
        for i in range(10):
            rate_limiter.allow_request(client1)
        
        # Client1 should be blocked
        assert rate_limiter.allow_request(client1) == False
        
        # Client2 should still have quota
        assert rate_limiter.allow_request(client2) == True
    
    def test_per_endpoint_rate_limiting(self, rate_limiter):
        """Test different rate limits per endpoint"""
        client = "test_client"
        
        # Different endpoints should have independent limits
        endpoints = ["/api/chat", "/api/search", "/api/analyze"]
        
        for endpoint in endpoints:
            for i in range(5):
                key = f"{client}:{endpoint}"
                assert rate_limiter.allow_request(key) == True
    
    def test_rate_limit_headers(self, rate_limiter):
        """Test rate limit headers for client feedback"""
        client_id = "header_client"
        
        # Make some requests
        for i in range(5):
            rate_limiter.allow_request(client_id)
        
        headers = rate_limiter.get_rate_limit_headers(client_id)
        
        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers
        assert "X-RateLimit-Reset" in headers
        
        assert headers["X-RateLimit-Limit"] == "10"
        assert headers["X-RateLimit-Remaining"] == "5"
    
    def test_graceful_degradation(self, rate_limiter):
        """Test graceful degradation when rate limited"""
        client_id = "degraded_client"
        
        # Exhaust rate limit
        for i in range(20):
            rate_limiter.allow_request(client_id)
        
        # Should return 429 status with retry-after
        response = rate_limiter.get_rate_limit_response(client_id)
        
        assert response["status_code"] == 429
        assert "Retry-After" in response["headers"]
        assert response["body"]["error"] == "Rate limit exceeded"
        assert "retry_after" in response["body"]
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_pattern(self):
        """Test circuit breaker for service protection"""
        from src.core.circuit_breaker import CircuitBreaker
        
        breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=1,
            expected_exception=Exception
        )
        
        # Simulate failures
        for i in range(5):
            with pytest.raises(Exception):
                breaker.call(lambda: (_ for _ in ()).throw(Exception("Service error")))
        
        # Circuit should be open
        assert breaker.state == "open"
        
        # Further calls should fail fast
        with pytest.raises(Exception, match="Circuit breaker is open"):
            breaker.call(lambda: "success")
        
        # Wait for recovery
        await asyncio.sleep(1.1)
        
        # Circuit should be half-open
        assert breaker.state == "half-open"
    
    def test_distributed_rate_limiting(self):
        """Test rate limiting across multiple instances"""
        
        # Mock Redis for distributed state
        mock_redis = Mock(spec=redis.Redis)
        mock_redis.incr.return_value = 5
        mock_redis.expire.return_value = True
        mock_redis.ttl.return_value = 60
        
        limiter1 = RateLimiter(redis_client=mock_redis)
        limiter2 = RateLimiter(redis_client=mock_redis)
        
        client_id = "distributed_client"
        
        # Both limiters should share state via Redis
        limiter1.allow_request(client_id)
        limiter2.allow_request(client_id)
        
        # Redis should have been called
        assert mock_redis.incr.called
        assert mock_redis.expire.called
    
    def test_sliding_window_rate_limit(self):
        """Test sliding window algorithm for smooth rate limiting"""
        
        from src.core.rate_limiting import SlidingWindowRateLimiter
        
        limiter = SlidingWindowRateLimiter(
            requests_per_minute=60,
            window_size=60  # 60 seconds
        )
        
        client_id = "sliding_client"
        
        # Make 30 requests
        for i in range(30):
            assert limiter.allow_request(client_id) == True
        
        # Wait 30 seconds
        time.sleep(30)
        
        # Should be able to make 30 more (sliding window)
        for i in range(30):
            assert limiter.allow_request(client_id) == True
        
        # 61st request should fail
        assert limiter.allow_request(client_id) == False


@pytest.mark.performance
class TestRateLimitPerformance:
    """Performance benchmarks for rate limiting"""
    
    def test_rate_limit_overhead(self, benchmark):
        """Benchmark rate limiting overhead"""
        limiter = RateLimiter()
        client_id = "perf_client"
        
        def check_rate_limit():
            return limiter.allow_request(client_id)
        
        # Should complete in < 1ms
        result = benchmark(check_rate_limit)
        assert benchmark.stats['mean'] < 0.001  # < 1ms
    
    @pytest.mark.asyncio
    async def test_high_concurrency_performance(self):
        """Test performance under high concurrency"""
        limiter = RateLimiter(requests_per_second=1000)
        
        start = time.time()
        
        # 10,000 concurrent requests
        tasks = []
        for i in range(10000):
            client_id = f"client_{i % 100}"  # 100 unique clients
            tasks.append(limiter.allow_request_async(client_id))
        
        results = await asyncio.gather(*tasks)
        
        duration = time.time() - start
        
        # Should complete in reasonable time
        assert duration < 5.0  # < 5 seconds for 10k requests
        
        # Rate limiting should be applied
        allowed = sum(results)
        assert allowed < 10000  # Not all requests allowed