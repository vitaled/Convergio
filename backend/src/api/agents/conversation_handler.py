"""
Conversation handlers for agent interactions
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

import structlog
from fastapi import HTTPException, Request, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from src.agents.orchestrator import get_agent_orchestrator
from src.agents.services.streaming_orchestrator import get_streaming_orchestrator
from src.agents.services.groupchat.selection_metrics import get_selection_metrics
from src.core.redis import cache_get, cache_set
from src.api.user_keys import get_user_api_key
from .models import ConversationRequest, StreamingConversationRequest
from .websocket_manager import connection_manager, streaming_manager

logger = structlog.get_logger()


async def handle_conversation(
    request: ConversationRequest,
    req: Request,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Handle a conversation request with agents.
    
    Args:
        request: Conversation request details
        req: FastAPI request object
        db: Database session
    
    Returns:
        Conversation response
    """
    
    conversation_id = request.conversation_id or str(uuid4())
    user_id = request.user_id or "anonymous"
    
    logger.info(
        f"📝 Starting conversation",
        conversation_id=conversation_id,
        user_id=user_id,
        mode=request.mode
    )
    
    try:
        # Get orchestrator (mode selection handled internally)
        orchestrator = await get_agent_orchestrator()
        
        if not orchestrator.is_healthy():
            raise HTTPException(
                status_code=503,
                detail="Agent orchestrator is not available"
            )
        
        # Add user API key to context if available
        context = request.context or {}
        user_api_key = get_user_api_key(req, "openai")
        if user_api_key:
            context["user_api_key"] = user_api_key
        
        # Check if a specific agent is requested in the context
        target_agent = context.get("agent_name")
        if target_agent:
            # Route to specific agent if requested
            logger.info(f"🎯 Routing to specific agent: {target_agent}")
            # Pass target_agent in context without modifying message
            result = await orchestrator.orchestrate_conversation(
                message=request.message,
                user_id=user_id,
                conversation_id=conversation_id,
                context={**context, "target_agent": target_agent}
            )
        else:
            # Execute conversation normally
            result = await orchestrator.orchestrate_conversation(
                message=request.message,
                user_id=user_id,
                conversation_id=conversation_id,
                context=context
            )
        
        # Cache conversation for continuity
        cache_key = f"conversation:{conversation_id}"
        await cache_set(
            cache_key,
            json.dumps({
                "user_id": user_id,
                "messages": result.get("messages", []),
                "context": context,
                "timestamp": datetime.now().isoformat()
            }),
            ttl=3600  # 1 hour TTL
        )
        
        # Track metrics (temporarily disabled)
        # metrics = get_selection_metrics()
        # metrics.record_conversation(
        #     conversation_id=conversation_id,
        #     agents_used=result.get("agents_used", []),
        #     duration=result.get("duration_seconds", 0),
        #     turn_count=result.get("turn_count", 0)
        # )
        
        logger.info(
            f"✅ Conversation completed",
            conversation_id=conversation_id,
            agents_used=result.get("agents_used"),
            turn_count=result.get("turn_count")
        )
        
        return {
            "conversation_id": conversation_id,
            "response": result.get("response"),
            "agents_used": result.get("agents_used", []),
            "turn_count": result.get("turn_count", 0),
            "duration_seconds": result.get("duration_seconds", 0),
            "cost_breakdown": result.get("cost_breakdown", {}),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Conversation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Conversation failed: {str(e)}"
        )


async def handle_streaming_conversation(
    request: StreamingConversationRequest,
    req: Request
) -> Dict[str, Any]:
    """
    Handle a streaming conversation request.
    
    Args:
        request: Streaming conversation request
        req: FastAPI request object
    
    Returns:
        Stream initialization response
    """
    
    conversation_id = request.conversation_id or str(uuid4())
    user_id = request.user_id or "anonymous"
    
    logger.info(
        f"🔄 Starting streaming conversation",
        conversation_id=conversation_id,
        user_id=user_id
    )
    
    try:
        # Get streaming orchestrator
        orchestrator = get_streaming_orchestrator()
        
        if not orchestrator.is_initialized:
            # Initialize if needed
            await orchestrator.initialize()
        
        # Add user API key to context
        context = request.context or {}
        user_api_key = get_user_api_key(req, "openai")
        if user_api_key:
            context["user_api_key"] = user_api_key
        
        # Start streaming (actual streaming happens via WebSocket)
        stream_id = f"stream_{conversation_id}"
        
        # Store stream metadata
        await cache_set(
            f"stream:{stream_id}",
            json.dumps({
                "conversation_id": conversation_id,
                "user_id": user_id,
                "message": request.message,
                "context": context,
                "started_at": datetime.now().isoformat()
            }),
            expire=300  # 5 minutes TTL
        )
        
        return {
            "stream_id": stream_id,
            "conversation_id": conversation_id,
            "websocket_url": f"/api/v1/agents/ws/streaming/{stream_id}",
            "message": "Connect to WebSocket URL to receive streaming responses"
        }
        
    except Exception as e:
        logger.error(f"Streaming setup failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to setup streaming: {str(e)}"
        )


async def handle_websocket_conversation(
    websocket: WebSocket,
    conversation_id: str,
    user_id: Optional[str] = None
):
    """
    Handle WebSocket-based conversation.
    
    Args:
        websocket: WebSocket connection
        conversation_id: Conversation ID
        user_id: Optional user ID
    """
    
    user_id = user_id or "anonymous"
    
    # Connect WebSocket
    await connection_manager.connect(
        websocket,
        conversation_id,
        {"user_id": user_id}
    )
    
    try:
        # Get orchestrator
        orchestrator = await get_agent_orchestrator()
        
        # Send initial greeting
        await websocket.send_json({
            "type": "system",
            "message": "Connected to Convergio AI Agents",
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat()
        })
        
        # Handle messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_json()
                
                if data.get("type") == "ping":
                    # Handle ping
                    await websocket.send_json({"type": "pong"})
                    continue
                
                message = data.get("message", "")
                if not message:
                    continue
                
                # Send typing indicator
                await websocket.send_json({
                    "type": "typing",
                    "agent": "system"
                })
                
                # Process message
                result = await orchestrator.orchestrate_conversation(
                    message=message,
                    user_id=user_id,
                    conversation_id=conversation_id,
                    context=data.get("context", {})
                )
                
                # Send response
                await websocket.send_json({
                    "type": "response",
                    "message": result.get("response"),
                    "agents_used": result.get("agents_used", []),
                    "turn_count": result.get("turn_count", 0),
                    "timestamp": datetime.now().isoformat()
                })
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                
    finally:
        connection_manager.disconnect(websocket)
        logger.info(f"WebSocket disconnected: {conversation_id}")


async def handle_streaming_websocket(
    websocket: WebSocket,
    stream_id: str
):
    """
    Handle WebSocket streaming for agent responses.
    
    Args:
        websocket: WebSocket connection
        stream_id: Stream ID
    """
    
    # Get stream metadata
    stream_data = await cache_get(f"stream:{stream_id}")
    if not stream_data:
        await websocket.close(code=1008, reason="Stream not found")
        return
    
    stream_info = json.loads(stream_data)
    
    # Connect WebSocket
    await streaming_manager.start_stream(
        stream_id,
        websocket,
        stream_info
    )
    
    try:
        # Get streaming orchestrator
        orchestrator = get_streaming_orchestrator()
        
        # Stream response
        async for chunk in orchestrator.stream_response(
            message=stream_info["message"],
            user_id=stream_info["user_id"],
            conversation_id=stream_info["conversation_id"],
            context=stream_info.get("context", {})
        ):
            await streaming_manager.send_chunk(
                stream_id,
                chunk.get("content", ""),
                chunk.get("agent")
            )
        
        # Complete stream
        await streaming_manager.end_stream(stream_id, complete=True)
        
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        await streaming_manager.end_stream(stream_id, complete=False, error=str(e))