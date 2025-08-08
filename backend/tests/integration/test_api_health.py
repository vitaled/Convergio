#!/usr/bin/env python3
"""
Integration tests for API health endpoints
"""

import os
import sys
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
import pytest_asyncio
from unittest.mock import patch, AsyncMock

# Ensure backend root is on sys.path for importing src.*
_BACKEND_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _BACKEND_PATH not in sys.path:
    sys.path.insert(0, _BACKEND_PATH)
from src.main import app


class TestAPIHealth:
    """Test API health check endpoints"""
    
    @pytest_asyncio.fixture
    async def client(self):
        """Create test client using ASGITransport (httpx >= 0.28)"""
        # Override DB dependency to avoid real init
        from src.core.database import get_db_session
        async def _fake_db():
            class _D: ...
            yield _D()
        app.dependency_overrides[get_db_session] = _fake_db
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_basic_health_endpoint(self, client):
        """Test basic health check endpoint"""
        response = await client.get("/health/")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "service" in data
        assert data["service"] in ["convergio-backend", "convergio-ai"]
    
    @pytest.mark.asyncio 
    async def test_system_health_endpoint(self, client):
        """Test comprehensive system health endpoint"""
        with patch('src.api.health.check_database_health', new_callable=AsyncMock) as mock_db, \
             patch('src.api.health.get_redis_client') as mock_get_redis:
            
            # Mock healthy responses
            mock_db.return_value = {"status": "healthy", "response_time": 0.05}
            class _Redis:
                async def ping(self):
                    return True
            mock_get_redis.return_value = _Redis()
            
            response = await client.get("/health/detailed")
            assert response.status_code == 200
            
            data = response.json()
            assert "status" in data
            assert "checks" in data
            assert "database" in data["checks"]
            assert "redis" in data["checks"]
    
    @pytest.mark.asyncio
    async def test_agent_health_endpoint(self, client):
        """Test agent system health endpoint"""
        response = await client.get("/health/agents")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "orchestrator_ready" in data
    
    @pytest.mark.asyncio
    async def test_health_with_database_failure(self, client):
        """Test health endpoint behavior when database is down"""
        with patch('src.api.health.check_database_health', new_callable=AsyncMock) as mock_db:
            # Mock database failure
            mock_db.return_value = {"status": "unhealthy", "error": "Connection failed"}
            
            response = await client.get("/health/detailed")
            # Should still return 200 but with unhealthy status
            assert response.status_code == 200
            
            data = response.json()
            assert data["status"] in ["degraded", "unhealthy"]
            assert data["checks"]["database"]["status"] == "unhealthy"
    
    @pytest.mark.asyncio
    async def test_health_endpoint_performance(self, client):
        """Test that health endpoints respond quickly"""
        import time
        
        start_time = time.time()
        response = await client.get("/health/")
        end_time = time.time()
        
        assert response.status_code == 200
        # Health check should be very fast (under 1 second)
        assert (end_time - start_time) < 1.0
    
    @pytest.mark.asyncio
    async def test_readiness_endpoint(self, client):
        """Test readiness-like behavior via detailed endpoint"""
        response = await client.get("/health/detailed")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_liveness_endpoint(self, client):
        """Test liveness probe endpoint"""
        response = await client.get("/health/")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
    
    @pytest.mark.asyncio
    async def test_health_metrics_format(self, client):
        """Test that health endpoints return properly formatted metrics"""
        response = await client.get("/health/")
        assert response.status_code == 200
        
        data = response.json()
        # Check for required fields
        required_fields = ["status", "timestamp", "service", "version"]
        for field in required_fields:
            assert field in data
        
        # Validate timestamp format (ISO 8601)
        import datetime
        try:
            datetime.datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
        except ValueError:
            pytest.fail("Invalid timestamp format")
    
    @pytest.mark.asyncio
    async def test_concurrent_health_requests(self, client):
        """Test health endpoint under concurrent load"""
        async def make_request():
            response = await client.get("/health/")
            return response.status_code
        
        # Make 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All requests should succeed
        assert all(status_code == 200 for status_code in results)