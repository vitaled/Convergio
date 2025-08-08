"""
Streaming Orchestrator for Real-time Agent Responses
WebSocket-based streaming integration with AutoGen agents for immediate feedback
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime
from dataclasses import asdict
import structlog
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage, HandoffMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

from src.core.config import settings
from src.agents.memory.autogen_memory_system import AutoGenMemorySystem
from src.core.redis import get_redis_client
from src.agents.services.streaming.response_types import StreamingResponse
from src.agents.services.streaming.session import StreamingSession
from src.agents.services.streaming.runner import stream_agent_response

logger = structlog.get_logger()

 

class StreamingOrchestrator:
    """Orchestrates real-time streaming responses from AI agents"""
    
    def __init__(self):
        self.active_sessions: Dict[str, StreamingSession] = {}
        self.memory_system = AutoGenMemorySystem()
        self.redis_client = None
        self._initialized = False
        self._heartbeat_tasks: Dict[str, asyncio.Task] = {}
        self.heartbeat_interval_sec: float = 10.0
        
    async def initialize(self):
        """Initialize streaming orchestrator"""
        logger.info("🌊 Initializing Streaming Orchestrator")
        
        # Initialize Redis for session persistence
        self.redis_client = get_redis_client()
        
        # Memory system is already initialized in constructor
        # No need to call initialize() - it doesn't exist
        
        self._initialized = True
        logger.info("✅ Streaming Orchestrator initialized")

    async def create_streaming_session(
        self,
        websocket: WebSocket,
        user_id: str,
        agent_name: str,
        session_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new streaming session"""
        
        session_id = str(uuid4())
        
        session = StreamingSession(
            session_id=session_id,
            user_id=user_id,
            agent_name=agent_name,
            websocket=websocket,
            start_time=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            message_count=0,
            status='active'
        )
        
        self.active_sessions[session_id] = session
        # Start heartbeat task
        self._start_heartbeat(session)
        
        # Send session created confirmation
        await self._send_streaming_response(
            session,
            StreamingResponse(
                chunk_id=str(uuid4()),
                session_id=session_id,
                agent_name=agent_name,
                chunk_type='status',
                content='session_created',
                timestamp=datetime.utcnow(),
                metadata={'context': session_context}
            )
        )
        
        logger.info(f"🌊 Created streaming session", 
                   session_id=session_id, agent_name=agent_name, user_id=user_id)
        
        return session_id

    async def process_streaming_message(
        self,
        session_id: str,
        message: str,
        message_context: Optional[Dict[str, Any]] = None
    ):
        """Process a message with streaming responses"""
        
        session = self.active_sessions.get(session_id)
        if not session:
            logger.warning(f"⚠️ Session not found: {session_id}")
            return
            
        try:
            session.last_activity = datetime.utcnow()
            session.message_count += 1
            session.status = 'active'
            
            # Send thinking status
            await self._send_streaming_response(
                session,
                StreamingResponse(
                    chunk_id=str(uuid4()),
                    session_id=session_id,
                    agent_name=session.agent_name,
                    chunk_type='thinking',
                    content=f'{session.agent_name} is analyzing your request...',
                    timestamp=datetime.utcnow()
                )
            )
            
            # Get agent metadata using the correct API
            from src.agents.services.agent_loader import DynamicAgentLoader
            loader = DynamicAgentLoader("src/agents/definitions")
            agent_metadata = loader.scan_and_load_agents()
            
            if session.agent_name not in agent_metadata:
                await self._send_error(session, f"Agent {session.agent_name} not found")
                return
            
            agent_meta = agent_metadata[session.agent_name]
            
            # Create OpenAI client with streaming - using most economical available model
            client = OpenAIChatCompletionClient(
                model="gpt-4o-mini",  # Most economical proven stable model
                api_key=settings.OPENAI_API_KEY,
            )
            
            # Create agent using the loader's method to build system message
            system_message = loader._build_system_message(agent_meta)
            agent = AssistantAgent(
                name=session.agent_name,
                model_client=client,
                system_message=system_message
            )
            
            # Get conversation context using available method
            conversation_context = ""
            try:
                # Try to get relevant context from memory system
                context_entries = await self.memory_system.retrieve_relevant_context(
                    user_id=session.user_id,
                    query=message,
                    limit=3
                )
                if context_entries:
                    conversation_context = f"\n\nRelevant context: {json.dumps(context_entries[:2])}"
            except Exception as e:
                logger.warning(f"⚠️ Memory context retrieval failed: {e}")
            
            # Prepare context message
            context_message = message + conversation_context
            
            # Process with streaming with guaranteed response
            has_generated_content = False
            # Simple backpressure: small send buffer window
            send_buffer: List[StreamingResponse] = []
            
            try:
                async for chunk in stream_agent_response(agent, context_message, session, logger):
                    send_buffer.append(chunk)
                    # Flush buffer to avoid overfilling
                    if len(send_buffer) >= 5 or chunk.chunk_type in ('tool_call','tool_result','handoff'):
                        while send_buffer:
                            await self._send_streaming_response(session, send_buffer.pop(0))
                    if chunk.chunk_type == 'text':
                        has_generated_content = True
            except Exception as streaming_error:
                logger.error(f"❌ Agent streaming failed: {streaming_error}")
            
            # No fallback: rely solely on AutoGen streaming; if no content, the client receives status/error events only
                
            # Flush any remaining buffered chunks
            try:
                while send_buffer:
                    await self._send_streaming_response(session, send_buffer.pop(0))
            except Exception:
                send_buffer.clear()

            # Send completion status
            await self._send_streaming_response(
                session,
                StreamingResponse(
                    chunk_id=str(uuid4()),
                    session_id=session_id,
                    agent_name=session.agent_name,
                    chunk_type='complete',
                    content='Response completed',
                    timestamp=datetime.utcnow()
                )
            )
            
            # Store conversation in memory using available method
            try:
                user_msg = TextMessage(content=message, source="user")
                await self.memory_system.store_conversation_message(
                    conversation_id=session.session_id,
                    agent_id=session.agent_name,
                    user_id=session.user_id,
                    message=user_msg,
                    context=message_context or {}
                )
                logger.info("✅ Stored conversation in memory")
            except Exception as mem_error:
                logger.warning(f"⚠️ Memory storage failed: {mem_error}")
            
        except Exception as e:
            logger.error(f"❌ Streaming processing error", error=str(e), session_id=session_id)
            await self._send_error(session, f"Processing error: {str(e)}")

    

    async def _send_streaming_response(
        self,
        session: StreamingSession,
        response: StreamingResponse
    ):
        """Send streaming response via WebSocket"""
        
        try:
            # Map chunk_type to standardized event names for WS3 protocol
            event_map = {
                "text": "delta",
                "thinking": "agent_status",
                "complete": "final",
                "error": "error",
                "status": "status",
                "tool_call": "tool_call",
                "tool_result": "tool_result",
                "handoff": "handoff",
            }
            mapped_event = event_map.get(response.chunk_type, "delta")
            data = {
                "type": "streaming_response",
                "event": mapped_event,
                "data": asdict(response)
            }
            
            # Convert datetime to ISO string
            if 'timestamp' in data['data']:
                data['data']['timestamp'] = response.timestamp.isoformat()
            
            await session.websocket.send_json(data)
            
        except WebSocketDisconnect:
            logger.info(f"🌊 Client disconnected from session {session.session_id}")
            await self.close_session(session.session_id)
        except Exception as e:
            logger.error(f"❌ Failed to send streaming response", error=str(e))

    async def _send_error(self, session: StreamingSession, error_message: str):
        """Send error response to client"""
        
        error_response = StreamingResponse(
            chunk_id=str(uuid4()),
            session_id=session.session_id,
            agent_name=session.agent_name,
            chunk_type='error',
            content=error_message,
            timestamp=datetime.utcnow()
        )
        
        await self._send_streaming_response(session, error_response)
        session.status = 'error'

    async def close_session(self, session_id: str):
        """Close a streaming session"""
        
        session = self.active_sessions.get(session_id)
        if session:
            try:
                # Send session closed message
                close_response = StreamingResponse(
                    chunk_id=str(uuid4()),
                    session_id=session_id,
                    agent_name=session.agent_name,
                    chunk_type='status',
                    content='session_closed',
                    timestamp=datetime.utcnow()
                )
                
                await self._send_streaming_response(session, close_response)
                
            except:
                pass  # Client may have already disconnected
            finally:
                # Cancel heartbeat task if running
                task = self._heartbeat_tasks.pop(session_id, None)
                if task:
                    task.cancel()
                # Remove from active sessions
                del self.active_sessions[session_id]
                logger.info(f"🌊 Closed streaming session {session_id}")

    async def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get list of active streaming sessions"""
        
        return [
            {
                "session_id": session.session_id,
                "user_id": session.user_id,
                "agent_name": session.agent_name,
                "status": session.status,
                "start_time": session.start_time.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "message_count": session.message_count
            }
            for session in self.active_sessions.values()
        ]

    async def cleanup_inactive_sessions(self, max_idle_minutes: int = 30):
        """Clean up inactive sessions"""
        
        current_time = datetime.utcnow()
        inactive_sessions = []
        
        for session_id, session in self.active_sessions.items():
            idle_minutes = (current_time - session.last_activity).total_seconds() / 60
            
            if idle_minutes > max_idle_minutes:
                inactive_sessions.append(session_id)
        
        for session_id in inactive_sessions:
            await self.close_session(session_id)
            logger.info(f"🧹 Cleaned up inactive session {session_id}")
        
        return len(inactive_sessions)

    def _start_heartbeat(self, session: StreamingSession) -> None:
        async def _hb():
            try:
                while session.session_id in self.active_sessions:
                    await asyncio.sleep(self.heartbeat_interval_sec)
                    # Session may have been closed during sleep
                    if session.session_id not in self.active_sessions:
                        break
                    hb = StreamingResponse(
                        chunk_id=str(uuid4()),
                        session_id=session.session_id,
                        agent_name=session.agent_name,
                        chunk_type='status',
                        content='heartbeat',
                        timestamp=datetime.utcnow(),
                        metadata={"status": session.status}
                    )
                    await self._send_streaming_response(session, hb)
            except asyncio.CancelledError:
                return
            except Exception as e:
                logger.warning("⚠️ Heartbeat error", error=str(e))

        self._heartbeat_tasks[session.session_id] = asyncio.create_task(_hb())

# Global streaming orchestrator instance - lazy loaded
streaming_orchestrator = None

def get_streaming_orchestrator() -> StreamingOrchestrator:
    """Get or create the global streaming orchestrator instance"""
    global streaming_orchestrator
    if streaming_orchestrator is None:
        streaming_orchestrator = StreamingOrchestrator()
    return streaming_orchestrator
