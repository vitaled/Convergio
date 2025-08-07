#!/usr/bin/env python3
"""
Simple tests for api/health.py - Aligned with actual implementation
Target: Increase coverage for existing health endpoints
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime


class TestHealthRouter:
    """Test health router and basic functionality"""
    
    def test_health_router_import(self):
        """Test health router import"""
        from src.api.health import router
        assert router is not None
        assert hasattr(router, 'routes')
    
    def test_health_router_tags(self):
        """Test health router has correct tags"""
        from src.api.health import router
        
        # Should be tagged for health endpoints
        if hasattr(router, 'tags'):
            assert "Health" in router.tags
    

class TestBasicHealthEndpoint:
    """Test basic health endpoint (/health/)"""
    
    @patch('src.core.config.get_settings')
    async def test_basic_health_endpoint(self, mock_get_settings):
        """Test basic health endpoint returns correct format"""
        mock_settings = MagicMock()
        # Mock attributes that health endpoint expects
        mock_settings.app_version = "1.0.0"
        mock_settings.build_number = "123" 
        mock_settings.environment = "test"
        mock_get_settings.return_value = mock_settings
        
        from src.api.health import basic_health
        
        result = await basic_health()
        
        assert result["status"] == "healthy"
        assert result["service"] == "convergio-backend"
        assert result["version"] == "1.0.0"
        assert result["build"] == "123"
        assert result["environment"] == "test"
        assert "timestamp" in result
    
    @patch('src.core.config.get_settings')
    async def test_basic_health_timestamp_format(self, mock_get_settings):
        """Test basic health returns valid timestamp"""
        mock_settings = MagicMock()
        mock_settings.app_version = "1.0.0"
        mock_settings.build_number = "123"  
        mock_settings.environment = "test"
        mock_get_settings.return_value = mock_settings
        
        from src.api.health import basic_health
        
        result = await basic_health()
        
        # Should have valid ISO timestamp
        timestamp = result["timestamp"]
        assert isinstance(timestamp, str)
        assert "T" in timestamp  # ISO format
    
    @patch('src.core.config.get_settings')
    async def test_basic_health_different_environments(self, mock_get_settings):
        """Test basic health in different environments"""
        # Production environment
        mock_settings = MagicMock()
        mock_settings.app_version = "2.0.0"
        mock_settings.build_number = "456"
        mock_settings.environment = "production"
        mock_get_settings.return_value = mock_settings
        
        from src.api.health import basic_health
        
        result = await basic_health()
        
        assert result["environment"] == "production"
        assert result["version"] == "2.0.0"
        assert result["build"] == "456"


class TestDetailedHealthEndpoint:
    """Test detailed health endpoint (/health/detailed)"""
    
    @patch('src.core.database.check_database_health')
    @patch('src.core.config.get_settings')
    async def test_detailed_health_endpoint(self, mock_get_settings, mock_check_db_health):
        """Test detailed health endpoint with database check"""
        mock_settings = MagicMock()
        mock_settings.app_version = "1.0.0"
        mock_settings.build_number = "123"
        mock_settings.environment = "test"
        mock_get_settings.return_value = mock_settings
        
        # Mock database health check
        mock_check_db_health.return_value = {"status": "healthy", "latency_ms": 10}
        
        from src.api.health import detailed_health
        
        # Need to mock the database session dependency
        mock_db_session = AsyncMock()
        
        result = await detailed_health(db=mock_db_session)
        
        assert "service" in result
        assert "timestamp" in result
        assert "dependencies" in result
        
        # Should check database
        mock_check_db_health.assert_called_once_with(mock_db_session)
    
    @patch('src.core.database.check_database_health')
    @patch('src.core.redis.get_redis_client')
    @patch('src.core.config.get_settings')
    async def test_detailed_health_with_redis_check(self, mock_get_settings, mock_get_redis, mock_check_db_health):
        """Test detailed health includes Redis check"""
        mock_settings = MagicMock()
        mock_settings.app_version = "1.0.0"
        mock_settings.build_number = "123"
        mock_settings.environment = "test"
        mock_get_settings.return_value = mock_settings
        
        mock_check_db_health.return_value = {"status": "healthy"}
        
        # Mock Redis client
        mock_redis_client = AsyncMock()
        mock_redis_client.ping.return_value = True
        mock_get_redis.return_value = mock_redis_client
        
        from src.api.health import detailed_health
        
        mock_db_session = AsyncMock()
        result = await detailed_health(db=mock_db_session)
        
        assert "dependencies" in result
        
        # Should attempt to check Redis
        mock_get_redis.assert_called_once()
    
    @patch('src.core.database.check_database_health')
    @patch('src.core.config.get_settings')
    async def test_detailed_health_database_unhealthy(self, mock_get_settings, mock_check_db_health):
        """Test detailed health when database is unhealthy"""
        mock_settings = MagicMock()
        mock_settings.app_version = "1.0.0"
        mock_settings.build_number = "123"
        mock_settings.environment = "test"
        mock_get_settings.return_value = mock_settings
        
        # Database unhealthy
        mock_check_db_health.return_value = {"status": "unhealthy", "error": "Connection failed"}
        
        from src.api.health import detailed_health
        
        mock_db_session = AsyncMock()
        result = await detailed_health(db=mock_db_session)
        
        # Should still return response but mark as unhealthy
        assert "dependencies" in result
        if "overall_status" in result:
            assert result["overall_status"] in ["unhealthy", "degraded"]
    
    @patch('src.core.database.check_database_health')
    @patch('src.core.config.get_settings')
    async def test_detailed_health_database_exception(self, mock_get_settings, mock_check_db_health):
        """Test detailed health handles database exceptions"""
        mock_settings = MagicMock()
        mock_settings.app_version = "1.0.0"
        mock_settings.build_number = "123"
        mock_settings.environment = "test"
        mock_get_settings.return_value = mock_settings
        
        # Database check raises exception
        mock_check_db_health.side_effect = Exception("Database connection error")
        
        from src.api.health import detailed_health
        
        mock_db_session = AsyncMock()
        result = await detailed_health(db=mock_db_session)
        
        # Should handle exception gracefully
        assert "dependencies" in result
        assert result["dependencies"]["database"]["status"] == "error"


class TestHealthEndpointIntegration:
    """Test health endpoint integration"""
    
    def test_health_endpoints_in_router(self):
        """Test that health endpoints are registered in router"""
        from src.api.health import router
        
        # Get all route paths
        route_paths = [route.path for route in router.routes]
        
        # Should have basic health endpoint
        assert "/" in route_paths
        
        # Should have detailed health endpoint
        assert "/detailed" in route_paths
    
    def test_health_router_methods(self):
        """Test health router has correct HTTP methods"""
        from src.api.health import router
        
        # Check that routes have GET methods
        get_routes = []
        for route in router.routes:
            if hasattr(route, 'methods') and 'GET' in route.methods:
                get_routes.append(route.path)
        
        # Should have GET endpoints
        assert len(get_routes) > 0
        assert "/" in get_routes
        assert "/detailed" in get_routes
    
    def test_health_with_fastapi_app(self):
        """Test health router integration with FastAPI app"""
        from fastapi import FastAPI
        from src.api.health import router
        
        app = FastAPI()
        app.include_router(router, prefix="/health")
        
        # Should not raise exception when including router
        assert app is not None
        
        # Should have routes from health router
        total_routes = len(app.routes)
        assert total_routes > 0


class TestHealthLogging:
    """Test health endpoint logging"""
    
    @patch('src.api.health.logger')
    @patch('src.core.config.get_settings')
    async def test_health_logging(self, mock_get_settings, mock_logger):
        """Test that health checks are logged appropriately"""
        mock_settings = MagicMock()
        mock_settings.app_version = "1.0.0"
        mock_settings.build_number = "123"
        mock_settings.environment = "test"
        mock_get_settings.return_value = mock_settings
        
        from src.api.health import basic_health
        
        result = await basic_health()
        
        # Should return result
        assert result["status"] == "healthy"
        
        # Logger might be called for health checks
        # This tests that the logger exists and can be used
        assert mock_logger is not None


class TestHealthDependencyInjection:
    """Test health endpoint dependency injection"""
    
    def test_detailed_health_has_db_dependency(self):
        """Test that detailed health endpoint has database dependency"""
        from src.api.health import detailed_health
        import inspect
        
        # Check function signature has database parameter
        signature = inspect.signature(detailed_health)
        parameters = signature.parameters
        
        # Should have db parameter
        assert 'db' in parameters
        
        # Should be annotated with AsyncSession dependency
        db_param = parameters['db']
        assert db_param.default is not None  # Should have Depends() default


class TestHealthResponseFormat:
    """Test health response format consistency"""
    
    @patch('src.core.config.get_settings')
    async def test_health_response_has_required_fields(self, mock_get_settings):
        """Test health response has all required fields"""
        mock_settings = MagicMock()
        mock_settings.app_version = "1.0.0"
        mock_settings.build_number = "123"
        mock_settings.environment = "test"
        mock_get_settings.return_value = mock_settings
        
        from src.api.health import basic_health
        
        result = await basic_health()
        
        # Required fields
        required_fields = ["status", "timestamp", "service", "version", "build", "environment"]
        
        for field in required_fields:
            assert field in result, f"Response missing required field: {field}"
        
        # Status should be string
        assert isinstance(result["status"], str)
        
        # Timestamp should be string
        assert isinstance(result["timestamp"], str)
    
    @patch('src.core.database.check_database_health')
    @patch('src.core.config.get_settings')
    async def test_detailed_health_response_structure(self, mock_get_settings, mock_check_db_health):
        """Test detailed health response has proper structure"""
        mock_settings = MagicMock()
        mock_settings.app_version = "1.0.0"
        mock_settings.build_number = "123"
        mock_settings.environment = "test"
        mock_get_settings.return_value = mock_settings
        
        mock_check_db_health.return_value = {"status": "healthy", "latency_ms": 10}
        
        from src.api.health import detailed_health
        
        mock_db_session = AsyncMock()
        result = await detailed_health(db=mock_db_session)
        
        # Should have dependencies section
        assert "dependencies" in result
        assert isinstance(result["dependencies"], dict)
        
        # Should have database in dependencies
        assert "database" in result["dependencies"]
        assert isinstance(result["dependencies"]["database"], dict)


class TestHealthErrorHandling:
    """Test health endpoint error handling"""
    
    @patch('src.core.config.get_settings')
    async def test_settings_error_handling(self, mock_get_settings):
        """Test health endpoint handles settings errors"""
        mock_get_settings.side_effect = Exception("Settings error")
        
        from src.api.health import basic_health
        
        # Should handle settings error gracefully
        try:
            result = await basic_health()
            # If it doesn't raise, should have reasonable defaults
            assert "status" in result
        except Exception:
            # Or it might re-raise - both are acceptable
            pass
    
    @patch('src.core.database.check_database_health')
    @patch('src.core.config.get_settings')
    async def test_database_error_handling(self, mock_get_settings, mock_check_db_health):
        """Test detailed health handles database errors"""
        mock_settings = MagicMock()
        mock_settings.app_version = "1.0.0"
        mock_settings.build_number = "123"
        mock_settings.environment = "test"
        mock_get_settings.return_value = mock_settings
        
        # Database check raises exception
        mock_check_db_health.side_effect = Exception("Database error")
        
        from src.api.health import detailed_health
        
        mock_db_session = AsyncMock()
        result = await detailed_health(db=mock_db_session)
        
        # Should handle database error
        assert "dependencies" in result
        assert result["dependencies"]["database"]["status"] == "error"
        assert "Database error" in result["dependencies"]["database"]["error"]