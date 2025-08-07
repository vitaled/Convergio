#!/usr/bin/env python3
"""
Unit tests for core API endpoints
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from httpx import AsyncClient
from fastapi import status

# Note: These tests use mocking to achieve high coverage without external dependencies


class TestHealthEndpoints:
    """Test health check endpoints with mocking"""
    
    @pytest.mark.asyncio
    async def test_basic_health_endpoint_success(self):
        """Test basic health endpoint returns 200"""
        from src.api.health import basic_health
        
        result = await basic_health()
        
        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert result["service"] == "convergio-ai"
    
    @pytest.mark.asyncio
    @patch('src.api.health.check_database_health')
    @patch('src.api.health.check_redis_health')
    async def test_system_health_all_healthy(self, mock_redis, mock_db):
        """Test system health when all components are healthy"""
        # Mock healthy responses
        mock_db.return_value = {"status": "healthy", "response_time": 0.05}
        mock_redis.return_value = {"status": "healthy", "response_time": 0.02}
        
        from src.api.health import system_health
        
        result = await system_health()
        
        assert result["overall_status"] == "healthy"
        assert result["components"]["database"]["status"] == "healthy"
        assert result["components"]["redis"]["status"] == "healthy"
    
    @pytest.mark.asyncio
    @patch('src.api.health.check_database_health')
    @patch('src.api.health.check_redis_health')
    async def test_system_health_database_down(self, mock_redis, mock_db):
        """Test system health when database is down"""
        mock_db.return_value = {"status": "unhealthy", "error": "Connection failed"}
        mock_redis.return_value = {"status": "healthy", "response_time": 0.02}
        
        from src.api.health import system_health
        
        result = await system_health()
        
        assert result["overall_status"] == "degraded"
        assert result["components"]["database"]["status"] == "unhealthy"


class TestAgentManagement:
    """Test agent management endpoints with mocking"""
    
    @pytest.mark.asyncio
    @patch('src.api.agent_management.AgentLoader')
    async def test_list_agents_success(self, mock_loader):
        """Test listing all agents"""
        # Mock agent loader
        mock_instance = AsyncMock()
        mock_instance.load_all_agents.return_value = [
            {"id": "ali", "name": "Ali", "role": "Chief of Staff"},
            {"id": "amy", "name": "Amy", "role": "CFO"}
        ]
        mock_loader.return_value = mock_instance
        
        from src.api.agent_management import list_agents
        
        result = await list_agents()
        
        assert len(result["agents"]) == 2
        assert result["agents"][0]["name"] == "Ali"
    
    @pytest.mark.asyncio
    @patch('src.api.agent_management.AgentLoader')
    async def test_get_agent_by_id_success(self, mock_loader):
        """Test getting specific agent by ID"""
        mock_instance = AsyncMock()
        mock_instance.get_agent_by_id.return_value = {
            "id": "ali", 
            "name": "Ali", 
            "role": "Chief of Staff",
            "expertise": "Coordination and strategic planning"
        }
        mock_loader.return_value = mock_instance
        
        from src.api.agent_management import get_agent_by_id
        
        result = await get_agent_by_id("ali")
        
        assert result["agent"]["name"] == "Ali"
        assert result["agent"]["role"] == "Chief of Staff"
    
    @pytest.mark.asyncio
    @patch('src.api.agent_management.AgentLoader')
    async def test_get_agent_by_id_not_found(self, mock_loader):
        """Test getting non-existent agent"""
        mock_instance = AsyncMock()
        mock_instance.get_agent_by_id.return_value = None
        mock_loader.return_value = mock_instance
        
        from src.api.agent_management import get_agent_by_id
        
        with pytest.raises(Exception):  # Should raise 404 or similar
            await get_agent_by_id("nonexistent")


class TestCostManagement:
    """Test cost management endpoints"""
    
    @pytest.mark.asyncio
    @patch('src.api.cost_management.CostTracker')
    async def test_get_current_usage(self, mock_tracker):
        """Test getting current usage statistics"""
        mock_instance = AsyncMock()
        mock_instance.get_current_usage.return_value = {
            "total_cost": 15.50,
            "tokens_used": 50000,
            "requests_made": 150
        }
        mock_tracker.return_value = mock_instance
        
        from src.api.cost_management import get_current_usage
        
        result = await get_current_usage()
        
        assert result["usage"]["total_cost"] == 15.50
        assert result["usage"]["tokens_used"] == 50000
    
    @pytest.mark.asyncio
    @patch('src.api.cost_management.CostTracker')
    async def test_get_cost_breakdown(self, mock_tracker):
        """Test getting detailed cost breakdown"""
        mock_instance = AsyncMock()
        mock_instance.get_breakdown_by_agent.return_value = {
            "ali": {"cost": 5.25, "requests": 50},
            "amy": {"cost": 3.75, "requests": 30}
        }
        mock_tracker.return_value = mock_instance
        
        from src.api.cost_management import get_cost_breakdown
        
        result = await get_cost_breakdown()
        
        assert "ali" in result["breakdown"]
        assert result["breakdown"]["ali"]["cost"] == 5.25


class TestAnalytics:
    """Test analytics endpoints"""
    
    @pytest.mark.asyncio
    @patch('src.api.analytics.get_system_metrics')
    async def test_system_analytics(self, mock_metrics):
        """Test system analytics endpoint"""
        mock_metrics.return_value = {
            "active_sessions": 12,
            "total_agents": 41,
            "avg_response_time": 1.2
        }
        
        from src.api.analytics import get_system_analytics
        
        result = await get_system_analytics()
        
        assert result["metrics"]["active_sessions"] == 12
        assert result["metrics"]["total_agents"] == 41
    
    @pytest.mark.asyncio
    @patch('src.api.analytics.get_agent_performance')
    async def test_agent_performance(self, mock_performance):
        """Test agent performance metrics"""
        mock_performance.return_value = {
            "ali": {"avg_response_time": 0.8, "success_rate": 0.98},
            "amy": {"avg_response_time": 1.1, "success_rate": 0.96}
        }
        
        from src.api.analytics import get_agent_performance
        
        result = await get_agent_performance()
        
        assert result["performance"]["ali"]["success_rate"] == 0.98
        assert result["performance"]["amy"]["avg_response_time"] == 1.1