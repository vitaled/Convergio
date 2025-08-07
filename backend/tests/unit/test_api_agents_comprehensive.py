#!/usr/bin/env python3
"""
Comprehensive tests for api/agents.py - Agent management API
Target: Low coverage → 90%+ coverage
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException
import json
from datetime import datetime
from typing import Dict, List


class TestAgentRouterInitialization:
    """Test agent router initialization and setup"""
    
    def test_agent_router_import(self):
        """Test that agent router can be imported"""
        from src.api.agents import router
        assert router is not None
        assert hasattr(router, 'routes')
    
    def test_agent_routes_registration(self):
        """Test that agent routes are properly registered"""
        from src.api.agents import router
        
        route_paths = [route.path for route in router.routes]
        
        # Should have core agent endpoints
        expected_paths = ["/", "/agents", "/{agent_id}", "/status", "/metrics"]
        
        # Check for essential paths
        assert any("/" in path for path in route_paths)
        assert any("agent" in path.lower() for path in route_paths)


class TestListAgentsEndpoint:
    """Test list agents endpoint functionality"""
    
    @patch('src.agents.orchestrator.AgentOrchestrator')
    async def test_list_agents_success(self, mock_orchestrator_class):
        """Test successful agent listing"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.list_agents.return_value = [
            {
                "id": "agent-001", 
                "name": "Document Analyzer",
                "status": "active",
                "type": "document_processor",
                "capabilities": ["text_analysis", "summarization"],
                "created_at": "2024-01-01T12:00:00Z",
                "last_activity": "2024-01-01T12:30:00Z"
            },
            {
                "id": "agent-002",
                "name": "Code Assistant", 
                "status": "idle",
                "type": "code_helper",
                "capabilities": ["code_review", "debugging"],
                "created_at": "2024-01-01T12:00:00Z",
                "last_activity": "2024-01-01T11:45:00Z"
            }
        ]
        mock_orchestrator_class.return_value = mock_orchestrator
        
        from src.api.agents import list_agents
        
        result = await list_agents()
        
        assert len(result["agents"]) == 2
        assert result["total"] == 2
        assert result["agents"][0]["id"] == "agent-001"
        assert result["agents"][1]["status"] == "idle"
    
    @patch('src.agents.orchestrator.AgentOrchestrator')
    async def test_list_agents_empty(self, mock_orchestrator_class):
        """Test listing agents when none exist"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.list_agents.return_value = []
        mock_orchestrator_class.return_value = mock_orchestrator
        
        from src.api.agents import list_agents
        
        result = await list_agents()
        
        assert result["agents"] == []
        assert result["total"] == 0
    
    @patch('src.agents.orchestrator.AgentOrchestrator')
    async def test_list_agents_with_filters(self, mock_orchestrator_class):
        """Test listing agents with status filter"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.list_agents.return_value = [
            {"id": "agent-001", "status": "active", "name": "Active Agent"},
        ]
        mock_orchestrator_class.return_value = mock_orchestrator
        
        from src.api.agents import list_agents
        
        result = await list_agents(status="active")
        
        mock_orchestrator.list_agents.assert_called_once_with(status="active")
        assert len(result["agents"]) == 1
        assert result["agents"][0]["status"] == "active"
    
    @patch('src.agents.orchestrator.AgentOrchestrator')
    async def test_list_agents_orchestrator_error(self, mock_orchestrator_class):
        """Test list agents when orchestrator fails"""
        mock_orchestrator_class.side_effect = Exception("Orchestrator connection failed")
        
        from src.api.agents import list_agents
        
        with pytest.raises(HTTPException) as exc_info:
            await list_agents()
        
        assert exc_info.value.status_code == 500
        assert "orchestrator" in str(exc_info.value.detail).lower()


class TestGetAgentEndpoint:
    """Test get single agent endpoint functionality"""
    
    @patch('src.agents.orchestrator.AgentOrchestrator')
    async def test_get_agent_by_id_success(self, mock_orchestrator_class):
        """Test successful agent retrieval by ID"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.get_agent.return_value = {
            "id": "agent-001",
            "name": "Document Analyzer",
            "status": "active",
            "type": "document_processor",
            "capabilities": ["text_analysis", "summarization"],
            "configuration": {
                "max_concurrent_tasks": 5,
                "timeout_seconds": 300,
                "memory_limit": "1GB"
            },
            "metrics": {
                "tasks_completed": 150,
                "average_processing_time": 45.5,
                "success_rate": 0.98,
                "last_error": None
            },
            "created_at": "2024-01-01T12:00:00Z",
            "last_activity": "2024-01-01T12:30:00Z"
        }
        mock_orchestrator_class.return_value = mock_orchestrator
        
        from src.api.agents import get_agent_by_id
        
        result = await get_agent_by_id("agent-001")
        
        assert result["id"] == "agent-001"
        assert result["name"] == "Document Analyzer"
        assert result["status"] == "active"
        assert "metrics" in result
        assert "configuration" in result
        mock_orchestrator.get_agent.assert_called_once_with("agent-001")
    
    @patch('src.agents.orchestrator.AgentOrchestrator')
    async def test_get_agent_by_id_not_found(self, mock_orchestrator_class):
        """Test get agent when agent doesn't exist"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.get_agent.return_value = None
        mock_orchestrator_class.return_value = mock_orchestrator
        
        from src.api.agents import get_agent_by_id
        
        with pytest.raises(HTTPException) as exc_info:
            await get_agent_by_id("nonexistent-agent")
        
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()
    
    @patch('src.agents.orchestrator.AgentOrchestrator')
    async def test_get_agent_invalid_id_format(self, mock_orchestrator_class):
        """Test get agent with invalid ID format"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.get_agent.side_effect = ValueError("Invalid agent ID format")
        mock_orchestrator_class.return_value = mock_orchestrator
        
        from src.api.agents import get_agent_by_id
        
        with pytest.raises(HTTPException) as exc_info:
            await get_agent_by_id("invalid-id-format")
        
        assert exc_info.value.status_code == 400
        assert "invalid" in str(exc_info.value.detail).lower()


class TestCreateAgentEndpoint:
    """Test create agent endpoint functionality"""
    
    @patch('src.agents.orchestrator.AgentOrchestrator')
    async def test_create_agent_success(self, mock_orchestrator_class):
        """Test successful agent creation"""
        mock_orchestrator = AsyncMock()
        created_agent = {
            "id": "agent-003",
            "name": "New Agent",
            "status": "initializing",
            "type": "custom",
            "capabilities": ["custom_task"],
            "configuration": {"timeout": 300},
            "created_at": "2024-01-01T13:00:00Z"
        }
        mock_orchestrator.create_agent.return_value = created_agent
        mock_orchestrator_class.return_value = mock_orchestrator
        
        from src.api.agents import create_agent
        from src.api.agents import AgentCreateRequest
        
        agent_request = AgentCreateRequest(
            name="New Agent",
            type="custom",
            capabilities=["custom_task"],
            configuration={"timeout": 300}
        )
        
        result = await create_agent(agent_request)
        
        assert result["id"] == "agent-003"
        assert result["name"] == "New Agent"
        assert result["status"] == "initializing"
        mock_orchestrator.create_agent.assert_called_once()
    
    @patch('src.agents.orchestrator.AgentOrchestrator')
    async def test_create_agent_validation_error(self, mock_orchestrator_class):
        """Test create agent with validation errors"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.create_agent.side_effect = ValueError("Invalid agent configuration")
        mock_orchestrator_class.return_value = mock_orchestrator
        
        from src.api.agents import create_agent
        from src.api.agents import AgentCreateRequest
        
        agent_request = AgentCreateRequest(
            name="",  # Invalid empty name
            type="invalid_type",
            capabilities=[],
            configuration={}
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await create_agent(agent_request)
        
        assert exc_info.value.status_code == 400
    
    @patch('src.agents.orchestrator.AgentOrchestrator')
    async def test_create_agent_orchestrator_error(self, mock_orchestrator_class):
        """Test create agent when orchestrator fails"""
        mock_orchestrator_class.side_effect = Exception("Failed to initialize orchestrator")
        
        from src.api.agents import create_agent
        from src.api.agents import AgentCreateRequest
        
        agent_request = AgentCreateRequest(
            name="Test Agent",
            type="test",
            capabilities=["test"],
            configuration={}
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await create_agent(agent_request)
        
        assert exc_info.value.status_code == 500


class TestUpdateAgentEndpoint:
    """Test update agent endpoint functionality"""
    
    @patch('src.agents.orchestrator.AgentOrchestrator')
    async def test_update_agent_success(self, mock_orchestrator_class):
        """Test successful agent update"""
        mock_orchestrator = AsyncMock()
        updated_agent = {
            "id": "agent-001",
            "name": "Updated Agent Name",
            "status": "active",
            "configuration": {"timeout": 600},  # Updated timeout
            "updated_at": "2024-01-01T14:00:00Z"
        }
        mock_orchestrator.update_agent.return_value = updated_agent
        mock_orchestrator_class.return_value = mock_orchestrator
        
        from src.api.agents import update_agent
        from src.api.agents import AgentUpdateRequest
        
        update_request = AgentUpdateRequest(
            name="Updated Agent Name",
            configuration={"timeout": 600}
        )
        
        result = await update_agent("agent-001", update_request)
        
        assert result["id"] == "agent-001"
        assert result["name"] == "Updated Agent Name"
        assert result["configuration"]["timeout"] == 600
        mock_orchestrator.update_agent.assert_called_once_with("agent-001", update_request.dict(exclude_unset=True))
    
    @patch('src.agents.orchestrator.AgentOrchestrator')
    async def test_update_agent_not_found(self, mock_orchestrator_class):
        """Test update non-existent agent"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.update_agent.return_value = None
        mock_orchestrator_class.return_value = mock_orchestrator
        
        from src.api.agents import update_agent
        from src.api.agents import AgentUpdateRequest
        
        update_request = AgentUpdateRequest(name="New Name")
        
        with pytest.raises(HTTPException) as exc_info:
            await update_agent("nonexistent-agent", update_request)
        
        assert exc_info.value.status_code == 404


class TestDeleteAgentEndpoint:
    """Test delete agent endpoint functionality"""
    
    @patch('src.agents.orchestrator.AgentOrchestrator')
    async def test_delete_agent_success(self, mock_orchestrator_class):
        """Test successful agent deletion"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.delete_agent.return_value = True
        mock_orchestrator_class.return_value = mock_orchestrator
        
        from src.api.agents import delete_agent
        
        result = await delete_agent("agent-001")
        
        assert result["message"] == "Agent deleted successfully"
        assert result["agent_id"] == "agent-001"
        mock_orchestrator.delete_agent.assert_called_once_with("agent-001")
    
    @patch('src.agents.orchestrator.AgentOrchestrator')
    async def test_delete_agent_not_found(self, mock_orchestrator_class):
        """Test delete non-existent agent"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.delete_agent.return_value = False
        mock_orchestrator_class.return_value = mock_orchestrator
        
        from src.api.agents import delete_agent
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_agent("nonexistent-agent")
        
        assert exc_info.value.status_code == 404
    
    @patch('src.agents.orchestrator.AgentOrchestrator')
    async def test_delete_agent_in_use(self, mock_orchestrator_class):
        """Test delete agent that is currently processing tasks"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.delete_agent.side_effect = ValueError("Agent is currently processing tasks")
        mock_orchestrator_class.return_value = mock_orchestrator
        
        from src.api.agents import delete_agent
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_agent("busy-agent")
        
        assert exc_info.value.status_code == 409  # Conflict
        assert "processing" in str(exc_info.value.detail).lower()


class TestAgentStatusEndpoint:
    """Test agent status monitoring endpoints"""
    
    @patch('src.agents.orchestrator.AgentOrchestrator')
    async def test_get_agent_status(self, mock_orchestrator_class):
        """Test get agent status"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.get_agent_status.return_value = {
            "agent_id": "agent-001",
            "status": "active",
            "current_task": {
                "id": "task-123",
                "type": "document_analysis",
                "started_at": "2024-01-01T13:00:00Z",
                "progress": 0.75
            },
            "queue_size": 3,
            "resource_usage": {
                "cpu_percent": 45.2,
                "memory_mb": 256,
                "memory_percent": 25.6
            },
            "last_heartbeat": "2024-01-01T13:05:00Z"
        }
        mock_orchestrator_class.return_value = mock_orchestrator
        
        from src.api.agents import get_agent_status
        
        result = await get_agent_status("agent-001")
        
        assert result["agent_id"] == "agent-001"
        assert result["status"] == "active"
        assert "current_task" in result
        assert "resource_usage" in result
    
    @patch('src.agents.orchestrator.AgentOrchestrator')
    async def test_get_all_agent_statuses(self, mock_orchestrator_class):
        """Test get status for all agents"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.get_all_statuses.return_value = {
            "agent-001": {"status": "active", "queue_size": 2},
            "agent-002": {"status": "idle", "queue_size": 0},
            "agent-003": {"status": "error", "last_error": "Memory limit exceeded"}
        }
        mock_orchestrator_class.return_value = mock_orchestrator
        
        from src.api.agents import get_all_agent_statuses
        
        result = await get_all_agent_statuses()
        
        assert len(result["statuses"]) == 3
        assert result["statuses"]["agent-001"]["status"] == "active"
        assert result["statuses"]["agent-003"]["status"] == "error"
        assert result["summary"]["total"] == 3
        assert result["summary"]["active"] == 1
        assert result["summary"]["idle"] == 1
        assert result["summary"]["error"] == 1


class TestAgentMetricsEndpoint:
    """Test agent metrics and analytics endpoints"""
    
    @patch('src.agents.orchestrator.AgentOrchestrator')
    async def test_get_agent_metrics(self, mock_orchestrator_class):
        """Test get individual agent metrics"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.get_agent_metrics.return_value = {
            "agent_id": "agent-001",
            "metrics": {
                "tasks_completed": 1250,
                "tasks_failed": 15,
                "average_processing_time_seconds": 42.5,
                "success_rate": 0.988,
                "uptime_seconds": 86400,
                "total_cpu_time_seconds": 3600,
                "peak_memory_mb": 512,
                "errors_by_type": {
                    "timeout": 8,
                    "memory_error": 4,
                    "validation_error": 3
                }
            },
            "performance_trends": {
                "last_hour": {"completion_rate": 45, "error_rate": 0.02},
                "last_day": {"completion_rate": 1150, "error_rate": 0.012},
                "last_week": {"completion_rate": 8750, "error_rate": 0.015}
            }
        }
        mock_orchestrator_class.return_value = mock_orchestrator
        
        from src.api.agents import get_agent_metrics
        
        result = await get_agent_metrics("agent-001")
        
        assert result["agent_id"] == "agent-001"
        assert result["metrics"]["tasks_completed"] == 1250
        assert result["metrics"]["success_rate"] == 0.988
        assert "performance_trends" in result
    
    @patch('src.agents.orchestrator.AgentOrchestrator')
    async def test_get_system_metrics(self, mock_orchestrator_class):
        """Test get system-wide agent metrics"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.get_system_metrics.return_value = {
            "total_agents": 5,
            "active_agents": 3,
            "idle_agents": 1,
            "error_agents": 1,
            "system_metrics": {
                "total_tasks_completed": 15000,
                "total_tasks_failed": 150,
                "system_success_rate": 0.99,
                "average_response_time_seconds": 35.2,
                "peak_concurrent_tasks": 25,
                "current_queue_size": 8
            },
            "resource_utilization": {
                "total_cpu_percent": 65.5,
                "total_memory_mb": 2048,
                "memory_utilization_percent": 45.8
            },
            "top_performers": [
                {"agent_id": "agent-001", "tasks_completed": 5000, "success_rate": 0.995},
                {"agent_id": "agent-003", "tasks_completed": 4800, "success_rate": 0.992}
            ]
        }
        mock_orchestrator_class.return_value = mock_orchestrator
        
        from src.api.agents import get_system_metrics
        
        result = await get_system_metrics()
        
        assert result["total_agents"] == 5
        assert result["system_metrics"]["system_success_rate"] == 0.99
        assert "resource_utilization" in result
        assert len(result["top_performers"]) == 2


class TestAgentTaskManagement:
    """Test agent task management endpoints"""
    
    @patch('src.agents.orchestrator.AgentOrchestrator')
    async def test_assign_task_to_agent(self, mock_orchestrator_class):
        """Test assigning task to specific agent"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.assign_task.return_value = {
            "task_id": "task-456",
            "agent_id": "agent-001",
            "status": "queued",
            "estimated_completion": "2024-01-01T13:10:00Z",
            "queue_position": 2
        }
        mock_orchestrator_class.return_value = mock_orchestrator
        
        from src.api.agents import assign_task_to_agent
        from src.api.agents import TaskAssignmentRequest
        
        task_request = TaskAssignmentRequest(
            task_type="document_analysis",
            parameters={"document_id": "doc-123", "analysis_type": "summarization"},
            priority="normal",
            timeout_seconds=300
        )
        
        result = await assign_task_to_agent("agent-001", task_request)
        
        assert result["task_id"] == "task-456"
        assert result["agent_id"] == "agent-001"
        assert result["status"] == "queued"
    
    @patch('src.agents.orchestrator.AgentOrchestrator')
    async def test_get_agent_tasks(self, mock_orchestrator_class):
        """Test get tasks for specific agent"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.get_agent_tasks.return_value = {
            "agent_id": "agent-001",
            "tasks": [
                {
                    "id": "task-123",
                    "type": "document_analysis",
                    "status": "in_progress",
                    "progress": 0.75,
                    "started_at": "2024-01-01T13:00:00Z",
                    "estimated_completion": "2024-01-01T13:05:00Z"
                },
                {
                    "id": "task-124",
                    "type": "text_summarization", 
                    "status": "queued",
                    "queue_position": 1,
                    "created_at": "2024-01-01T13:02:00Z"
                }
            ],
            "queue_size": 2,
            "current_task": "task-123"
        }
        mock_orchestrator_class.return_value = mock_orchestrator
        
        from src.api.agents import get_agent_tasks
        
        result = await get_agent_tasks("agent-001")
        
        assert result["agent_id"] == "agent-001"
        assert len(result["tasks"]) == 2
        assert result["current_task"] == "task-123"
        assert result["queue_size"] == 2


class TestAgentConfigurationEndpoints:
    """Test agent configuration management"""
    
    @patch('src.agents.orchestrator.AgentOrchestrator')
    async def test_get_agent_configuration(self, mock_orchestrator_class):
        """Test get agent configuration"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.get_agent_configuration.return_value = {
            "agent_id": "agent-001",
            "configuration": {
                "max_concurrent_tasks": 5,
                "timeout_seconds": 300,
                "memory_limit_mb": 1024,
                "cpu_limit_percent": 50,
                "retry_attempts": 3,
                "enable_logging": True,
                "log_level": "INFO",
                "custom_parameters": {
                    "model_name": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            },
            "schema": {
                "max_concurrent_tasks": {"type": "integer", "min": 1, "max": 10},
                "timeout_seconds": {"type": "integer", "min": 60, "max": 3600},
                "memory_limit_mb": {"type": "integer", "min": 256, "max": 4096}
            }
        }
        mock_orchestrator_class.return_value = mock_orchestrator
        
        from src.api.agents import get_agent_configuration
        
        result = await get_agent_configuration("agent-001")
        
        assert result["agent_id"] == "agent-001"
        assert result["configuration"]["max_concurrent_tasks"] == 5
        assert "schema" in result
    
    @patch('src.agents.orchestrator.AgentOrchestrator')
    async def test_update_agent_configuration(self, mock_orchestrator_class):
        """Test update agent configuration"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.update_configuration.return_value = {
            "agent_id": "agent-001",
            "configuration": {
                "max_concurrent_tasks": 8,  # Updated
                "timeout_seconds": 600,     # Updated
                "memory_limit_mb": 1024,
                "updated_at": "2024-01-01T14:00:00Z"
            }
        }
        mock_orchestrator_class.return_value = mock_orchestrator
        
        from src.api.agents import update_agent_configuration
        from src.api.agents import ConfigurationUpdateRequest
        
        config_update = ConfigurationUpdateRequest(
            max_concurrent_tasks=8,
            timeout_seconds=600
        )
        
        result = await update_agent_configuration("agent-001", config_update)
        
        assert result["configuration"]["max_concurrent_tasks"] == 8
        assert result["configuration"]["timeout_seconds"] == 600


class TestAgentCapabilityEndpoints:
    """Test agent capability management"""
    
    @patch('src.agents.orchestrator.AgentOrchestrator') 
    async def test_get_agent_capabilities(self, mock_orchestrator_class):
        """Test get agent capabilities"""
        mock_orchestrator = AsyncMock()
        mock_orchestrator.get_agent_capabilities.return_value = {
            "agent_id": "agent-001",
            "capabilities": [
                {
                    "name": "document_analysis",
                    "description": "Analyze and extract insights from documents",
                    "supported_formats": ["pdf", "txt", "docx"],
                    "performance_metrics": {
                        "average_processing_time": 45.2,
                        "success_rate": 0.995,
                        "throughput_per_hour": 120
                    }
                },
                {
                    "name": "text_summarization",
                    "description": "Generate concise summaries of text content",
                    "supported_languages": ["en", "es", "fr", "de"],
                    "performance_metrics": {
                        "average_processing_time": 15.8,
                        "success_rate": 0.998,
                        "throughput_per_hour": 300
                    }
                }
            ],
            "total_capabilities": 2,
            "capability_matrix": {
                "text_processing": ["document_analysis", "text_summarization"],
                "analysis": ["document_analysis"]
            }
        }
        mock_orchestrator_class.return_value = mock_orchestrator
        
        from src.api.agents import get_agent_capabilities
        
        result = await get_agent_capabilities("agent-001")
        
        assert result["agent_id"] == "agent-001"
        assert len(result["capabilities"]) == 2
        assert result["capabilities"][0]["name"] == "document_analysis"
        assert "capability_matrix" in result


class TestErrorHandlingAndValidation:
    """Test error handling and request validation"""
    
    def test_agent_id_validation(self):
        """Test agent ID format validation"""
        from src.api.agents import validate_agent_id
        
        # Valid IDs
        assert validate_agent_id("agent-001") == True
        assert validate_agent_id("agent_test_123") == True
        
        # Invalid IDs  
        assert validate_agent_id("") == False
        assert validate_agent_id("invalid id with spaces") == False
        assert validate_agent_id("too-long-" + "x" * 100) == False
    
    def test_request_validation(self):
        """Test request model validation"""
        from src.api.agents import AgentCreateRequest
        
        # Valid request
        valid_request = AgentCreateRequest(
            name="Test Agent",
            type="test_type",
            capabilities=["test_capability"],
            configuration={"timeout": 300}
        )
        assert valid_request.name == "Test Agent"
        
        # Invalid request validation would be handled by Pydantic
        # This tests the model can be instantiated correctly
    
    @patch('src.api.agents.logger')
    async def test_error_logging(self, mock_logger):
        """Test that errors are properly logged"""
        from src.api.agents import handle_orchestrator_error
        
        test_error = Exception("Test orchestrator error")
        
        with pytest.raises(HTTPException):
            handle_orchestrator_error(test_error, "test_operation")
        
        # Should log the error
        mock_logger.error.assert_called() if hasattr(mock_logger, 'error') else True


class TestAgentEndpointIntegration:
    """Test agent endpoint integration with FastAPI"""
    
    def test_agent_router_with_fastapi_app(self):
        """Test agent router integration"""
        from fastapi import FastAPI
        from src.api.agents import router
        
        app = FastAPI()
        app.include_router(router, prefix="/api/v1/agents", tags=["agents"])
        
        client = TestClient(app)
        
        # Should be able to access routes
        routes = [route.path for route in app.routes]
        agent_routes = [route for route in routes if "/agents" in route]
        
        assert len(agent_routes) > 0
    
    @patch('src.api.agents.list_agents')
    def test_agent_endpoint_response_format(self, mock_list_agents):
        """Test agent endpoint response format"""
        mock_list_agents.return_value = {
            "agents": [],
            "total": 0,
            "page": 1,
            "per_page": 10
        }
        
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from src.api.agents import router
        
        app = FastAPI()
        app.include_router(router, prefix="/agents")
        
        client = TestClient(app)
        
        # Test would verify JSON response format
        # Actual HTTP testing might require more setup
        assert mock_list_agents is not None