"""
GraphFlow dataclasses and type definitions.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Any, Optional


@dataclass
class WorkflowStep:
    step_id: str
    agent_name: str
    step_type: str
    description: str
    inputs: List[str]
    outputs: List[str]
    conditions: Optional[Dict[str, Any]] = None
    timeout_seconds: int = 300


@dataclass
class BusinessWorkflow:
    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    entry_points: List[str]
    exit_conditions: Dict[str, str]
    metadata: Dict[str, Any]


@dataclass
class WorkflowExecution:
    execution_id: str
    workflow_id: str
    status: str
    current_step: Optional[str]
    step_results: Dict[str, Any]
    start_time: datetime
    end_time: Optional[datetime]
    error_message: Optional[str]
    user_id: str


