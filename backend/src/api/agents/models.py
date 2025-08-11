"""
Pydantic models for AI Agents API
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentExecutionRequest(BaseModel):
    """Request for agent execution"""
    agent_id: str
    task: str
    parameters: Dict[str, Any] = {}
    context: Dict[str, Any] = {}
    timeout: int = 60


class AgentExecutionResponse(BaseModel):
    """Response from agent execution"""
    execution_id: str
    agent_id: str
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None


class AgentStatusResponse(BaseModel):
    """Agent status response"""
    execution_id: str
    agent_id: str
    status: str
    progress: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class OrchestrationRequest(BaseModel):
    """Request for multi-agent orchestration"""
    message: str
    context: Optional[Dict[str, Any]] = None
    mode: str = "adaptive"  # adaptive, sequential, parallel
    max_agents: int = 3
    require_consensus: bool = False
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None


class ConversationRequest(BaseModel):
    """Request for conversation with agents"""
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    mode: str = "autogen"  # autogen, graphflow, swarm
    context: Optional[Dict[str, Any]] = None


class ProjectRequest(BaseModel):
    """Request for project management"""
    project_type: str
    project_name: str
    description: str
    requirements: List[str]
    constraints: Optional[List[str]] = []
    budget: Optional[float] = None
    timeline_days: Optional[int] = None
    user_id: Optional[str] = None


class StreamingConversationRequest(BaseModel):
    """Request for streaming conversation"""
    message: str
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    stream: bool = True


class AgentInfo(BaseModel):
    """Information about an agent"""
    id: str
    name: str
    description: str
    capabilities: List[str]
    status: str = "available"
    model: Optional[str] = None
    tools: List[str] = Field(default_factory=list)


class EcosystemStatus(BaseModel):
    """Status of the agent ecosystem"""
    total_agents: int
    available_agents: int
    busy_agents: int
    agents: List[AgentInfo]
    orchestrator_status: str
    memory_system_status: str
    vector_db_status: str
    redis_status: str


class ApprovalRequest(BaseModel):
    """Approval request for sensitive operations"""
    id: str
    operation: str
    agent_id: str
    details: Dict[str, Any]
    risk_level: str
    created_at: datetime
    expires_at: datetime
    status: str = "pending"


class FeatureFlag(BaseModel):
    """Feature flag configuration"""
    name: str
    enabled: bool
    description: str
    rollout_percentage: Optional[float] = None
    conditions: Optional[Dict[str, Any]] = None