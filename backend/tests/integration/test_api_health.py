#!/usr/bin/env python3
"""
Integration tests for API health endpoints
"""

import pytest
import asyncio
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from src.main import app


class TestAPIHealth:
    """Test API health check endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return AsyncClient(app=app, base_url="http://test")
    
    @pytest.mark.asyncio
    async def test_basic_health_endpoint(self, client):
        """Test basic health check endpoint"""
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "service" in data
        assert data["service"] == "convergio-ai"
    
    @pytest.mark.asyncio 
    async def test_system_health_endpoint(self, client):
        """Test comprehensive system health endpoint"""
        with patch('src.api.health.check_database_health', new_callable=AsyncMock) as mock_db, \
             patch('src.api.health.check_redis_health', new_callable=AsyncMock) as mock_redis:
            
            # Mock healthy responses
            mock_db.return_value = {"status": "healthy", "response_time": 0.05}
            mock_redis.return_value = {"status": "healthy", "response_time": 0.02}
            
            response = await client.get("/api/v1/health/system")
            assert response.status_code == 200
            
            data = response.json()
            assert "overall_status" in data
            assert "components" in data
            assert "database" in data["components"]
            assert "redis" in data["components"]
    
    @pytest.mark.asyncio
    async def test_agent_health_endpoint(self, client):
        """Test agent system health endpoint"""
        with patch('src.agents.services.agent_loader.AgentLoader.load_all_agents', new_callable=AsyncMock) as mock_agents:
            # Mock successful agent loading
            mock_agents.return_value = [f"agent_{i}" for i in range(41)]
            
            response = await client.get("/api/v1/health/agents")
            assert response.status_code == 200
            
            data = response.json()
            assert "agent_status" in data
            assert "total_agents" in data
            assert "healthy_agents" in data
    
    @pytest.mark.asyncio
    async def test_health_with_database_failure(self, client):
        """Test health endpoint behavior when database is down"""
        with patch('src.api.health.check_database_health', new_callable=AsyncMock) as mock_db:
            # Mock database failure
            mock_db.return_value = {"status": "unhealthy", "error": "Connection failed"}
            
            response = await client.get("/api/v1/health/system")
            # Should still return 200 but with unhealthy status
            assert response.status_code == 200
            
            data = response.json()
            assert data["overall_status"] == "degraded"
            assert data["components"]["database"]["status"] == "unhealthy"
    
    @pytest.mark.asyncio
    async def test_health_endpoint_performance(self, client):
        """Test that health endpoints respond quickly"""
        import time
        
        start_time = time.time()
        response = await client.get("/api/v1/health")
        end_time = time.time()
        
        assert response.status_code == 200
        # Health check should be very fast (under 1 second)
        assert (end_time - start_time) < 1.0
    
    @pytest.mark.asyncio
    async def test_readiness_endpoint(self, client):
        """Test readiness probe endpoint"""
        with patch('src.api.health.check_all_dependencies', new_callable=AsyncMock) as mock_deps:
            mock_deps.return_value = True
            
            response = await client.get("/api/v1/health/ready")
            assert response.status_code == 200
            
            data = response.json()
            assert data["ready"] is True
    
    @pytest.mark.asyncio
    async def test_liveness_endpoint(self, client):
        """Test liveness probe endpoint"""
        response = await client.get("/api/v1/health/live")
        assert response.status_code == 200
        
        data = response.json()
        assert "alive" in data
        assert data["alive"] is True
        assert "uptime" in data
    
    @pytest.mark.asyncio
    async def test_health_metrics_format(self, client):
        """Test that health endpoints return properly formatted metrics"""
        response = await client.get("/api/v1/health")
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
            response = await client.get("/api/v1/health")
            return response.status_code
        
        # Make 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # All requests should succeed
        assert all(status_code == 200 for status_code in results)