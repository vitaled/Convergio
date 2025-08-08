"""
Streaming Session Model
Defines session dataclasses used by streaming orchestrator.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import WebSocket


@dataclass
class StreamingSession:
    """Streaming session model compatible with StreamingOrchestrator usage"""
    session_id: str
    user_id: str
    agent_name: str
    websocket: WebSocket
    start_time: datetime
    last_activity: datetime
    message_count: int
    status: str  # 'active', 'paused', 'completed', 'error'
    metadata: Optional[Dict[str, Any]] = None


