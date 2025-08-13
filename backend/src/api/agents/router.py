"""
Main router for AI Agents API
Consolidates all agent-related endpoints
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

import structlog
from fastapi import APIRouter, Depends, HTTPException, WebSocket, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from src.core.redis import cache_get
from src.agents.orchestrator import get_agent_orchestrator
from src.agents.services.streaming_orchestrator import get_streaming_orchestrator
from src.agents.services.groupchat.selection_metrics import get_selection_metrics
from src.api.user_keys import get_user_api_key

from .models import (
    AgentExecutionRequest,
    AgentExecutionResponse,
    AgentStatusResponse,
    OrchestrationRequest,
    ConversationRequest,
    ProjectRequest,
    StreamingConversationRequest,
    AgentInfo,
    EcosystemStatus,
    ApprovalRequest,
    FeatureFlag
)
from .websocket_manager import connection_manager, streaming_manager
from .conversation_handler import (
    handle_conversation,
    handle_streaming_conversation,
    handle_websocket_conversation,
    handle_streaming_websocket
)
from .project_manager import (
    handle_project_request,
    get_project_status,
    list_projects
)
from .orchestrator_management import router as orchestrator_router

logger = structlog.get_logger()
router = APIRouter(tags=["AI Agents"])

# Include sub-routers
router.include_router(orchestrator_router)


# ==================== Agent Management Endpoints ====================

@router.get("/list", response_model=List[AgentInfo])
async def list_agents(
    db: AsyncSession = Depends(get_db_session)
) -> List[AgentInfo]:
    """List all available AI agents"""
    
    # Get agents from orchestrator
    orchestrator = await get_agent_orchestrator()
    agents = orchestrator.list_agents()
    
    # Convert to AgentInfo models
    agent_list = []
    for agent_id in agents:
        agent = orchestrator.get_agent(agent_id)
        if agent:
            agent_list.append(AgentInfo(
                id=agent_id,
                name=agent.name,
                description=agent.description or "",
                capabilities=getattr(agent, "capabilities", []),
                status="available",
                model=getattr(agent, "model", None),
                tools=getattr(agent, "tools", [])
            ))
    
    return agent_list


@router.get("/ecosystem", response_model=EcosystemStatus)
async def get_ecosystem_status(
    db: AsyncSession = Depends(get_db_session)
) -> EcosystemStatus:
    """Get the status of the entire agent ecosystem"""
    
    orchestrator = await get_agent_orchestrator()
    agents = orchestrator.list_agents()
    
    # Build ecosystem status
    agent_infos = []
    for agent_id in agents:
        agent = orchestrator.get_agent(agent_id)
        if agent:
            agent_infos.append(AgentInfo(
                id=agent_id,
                name=agent.name,
                description=agent.description or "",
                capabilities=getattr(agent, "capabilities", []),
                status="available",
                model=getattr(agent, "model", None),
                tools=getattr(agent, "tools", [])
            ))
    
    return EcosystemStatus(
        total_agents=len(agents),
        available_agents=len(agents),
        busy_agents=0,
        agents=agent_infos,
        orchestrator_status="healthy" if orchestrator.is_healthy() else "unhealthy",
        memory_system_status="healthy",
        vector_db_status="healthy",
        redis_status="healthy"
    )


# ==================== Conversation Endpoints ====================

@router.post("/conversation")
async def create_conversation(
    request: ConversationRequest,
    req: Request,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Create a new conversation with AI agents"""
    return await handle_conversation(request, req, db)


@router.post("/conversation/stream")
async def create_streaming_conversation(
    request: StreamingConversationRequest,
    req: Request
) -> Dict[str, Any]:
    """Create a streaming conversation with AI agents"""
    return await handle_streaming_conversation(request, req)


@router.websocket("/ws/conversation/{conversation_id}")
async def websocket_conversation(
    websocket: WebSocket,
    conversation_id: str,
    user_id: Optional[str] = None
):
    """WebSocket endpoint for real-time conversation"""
    await handle_websocket_conversation(websocket, conversation_id, user_id)


@router.websocket("/ws/streaming/{stream_id}")
async def websocket_streaming(
    websocket: WebSocket,
    stream_id: str
):
    """WebSocket endpoint for streaming responses"""
    await handle_streaming_websocket(websocket, stream_id)


# ==================== Project Management Endpoints ====================

@router.post("/project")
async def create_project(
    request: ProjectRequest,
    req: Request,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Create a new project with AI agents"""
    return await handle_project_request(request, req, db)


@router.get("/projects")
async def get_projects(
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
) -> List[Dict[str, Any]]:
    """List all projects"""
    return await list_projects(user_id, db)


@router.get("/project/{project_id}")
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Get a specific project"""
    return await get_project_status(project_id, db)


# ==================== Orchestration Endpoints ====================

@router.post("/orchestrate", response_model=AgentExecutionResponse)
async def orchestrate_agents(
    request: OrchestrationRequest,
    req: Request,
    db: AsyncSession = Depends(get_db_session)
) -> AgentExecutionResponse:
    """Orchestrate multiple agents for a complex task"""
    
    execution_id = str(uuid4())
    
    try:
        orchestrator = await get_agent_orchestrator()
        
        # Add user API key to context
        context = request.context or {}
        user_api_key = get_user_api_key(req, "openai")
        if user_api_key:
            context["user_api_key"] = user_api_key
        
        # Execute orchestration
        result = await orchestrator.orchestrate(
            message=request.message,
            context=context,
            user_id=request.user_id,
            conversation_id=request.conversation_id
        )
        
        return AgentExecutionResponse(
            execution_id=execution_id,
            agent_id="orchestrator",
            status="completed",
            result=result,
            duration_ms=int(result.get("duration_seconds", 0) * 1000)
        )
        
    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        return AgentExecutionResponse(
            execution_id=execution_id,
            agent_id="orchestrator",
            status="failed",
            error=str(e)
        )


# ==================== Execution Endpoints ====================

@router.post("/execute", response_model=AgentExecutionResponse)
async def execute_agent(
    request: AgentExecutionRequest,
    req: Request,
    db: AsyncSession = Depends(get_db_session)
) -> AgentExecutionResponse:
    """Execute a specific agent with a task"""
    
    execution_id = str(uuid4())
    
    try:
        orchestrator = await get_agent_orchestrator()
        agent = orchestrator.get_agent(request.agent_id)
        
        if not agent:
            raise HTTPException(
                status_code=404,
                detail=f"Agent {request.agent_id} not found"
            )
        
        # Execute agent
        start_time = datetime.now()
        result = await agent.run(task=request.task)
        duration = (datetime.now() - start_time).total_seconds()
        
        return AgentExecutionResponse(
            execution_id=execution_id,
            agent_id=request.agent_id,
            status="completed",
            result=result,
            duration_ms=int(duration * 1000)
        )
        
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        return AgentExecutionResponse(
            execution_id=execution_id,
            agent_id=request.agent_id,
            status="failed",
            error=str(e)
        )


@router.get("/status/{execution_id}", response_model=AgentStatusResponse)
async def get_execution_status(
    execution_id: str,
    db: AsyncSession = Depends(get_db_session)
) -> AgentStatusResponse:
    """Get the status of an agent execution"""
    
    # Try to get from cache
    cache_key = f"execution:{execution_id}"
    cached_data = await cache_get(cache_key)
    
    if cached_data:
        data = json.loads(cached_data)
        return AgentStatusResponse(**data)
    
    # If not found, return pending status
    return AgentStatusResponse(
        execution_id=execution_id,
        agent_id="unknown",
        status="not_found"
    )


# ==================== Metrics and Monitoring ====================

@router.get("/selection-metrics")
async def get_agent_selection_metrics() -> Dict[str, Any]:
    """Get metrics about agent selection and performance"""
    
    metrics = get_selection_metrics()
    return metrics.get_summary()


@router.get("/streaming/health")
async def get_streaming_health() -> Dict[str, Any]:
    """Get health status of streaming system"""
    
    orchestrator = get_streaming_orchestrator()
    
    return {
        "status": "healthy" if orchestrator.is_initialized else "not_initialized",
        "active_streams": len(streaming_manager.get_active_streams()),
        "active_connections": connection_manager.get_connection_count(),
        "timestamp": datetime.now().isoformat()
    }


@router.get("/streaming/sessions")
async def get_streaming_sessions() -> Dict[str, Any]:
    """Get information about active streaming sessions"""
    
    return {
        "active_streams": streaming_manager.get_active_streams(),
        "active_clients": connection_manager.get_active_clients(),
        "total_connections": connection_manager.get_connection_count(),
        "timestamp": datetime.now().isoformat()
    }


# ==================== Feature Flags and Configuration ====================

@router.get("/feature-flags", response_model=List[FeatureFlag])
async def get_feature_flags() -> List[FeatureFlag]:
    """Get all feature flags"""
    
    # In production, these would come from a configuration service
    return [
        FeatureFlag(
            name="multi_agent_routing",
            enabled=True,
            description="Enable intelligent multi-agent routing"
        ),
        FeatureFlag(
            name="streaming_responses",
            enabled=True,
            description="Enable streaming responses via WebSocket"
        ),
        FeatureFlag(
            name="batch_embeddings",
            enabled=True,
            description="Use batch embeddings for cost optimization"
        ),
        FeatureFlag(
            name="circuit_breaker",
            enabled=True,
            description="Enable circuit breaker for orchestrator resilience"
        )
    ]


# ==================== Approval Management ====================

@router.get("/approvals", response_model=List[ApprovalRequest])
async def get_pending_approvals(
    db: AsyncSession = Depends(get_db_session)
) -> List[ApprovalRequest]:
    """Get all pending approval requests"""
    
    # In production, this would query the database
    # For now, return empty list
    return []


@router.post("/approvals/{approval_id}/approve")
async def approve_request(
    approval_id: str,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Approve a pending request"""
    
    return {
        "approval_id": approval_id,
        "status": "approved",
        "timestamp": datetime.now().isoformat()
    }


@router.post("/approvals/{approval_id}/deny")
async def deny_request(
    approval_id: str,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
) -> Dict[str, Any]:
    """Deny a pending request"""
    
    return {
        "approval_id": approval_id,
        "status": "denied",
        "reason": reason,
        "timestamp": datetime.now().isoformat()
    }