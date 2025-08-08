"""
Streaming runner utilities for agent response streaming.
"""

import asyncio
import json
from typing import AsyncGenerator
from datetime import datetime
from uuid import uuid4

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage, HandoffMessage

from .response_types import StreamingResponse


async def stream_agent_response(
    agent: AssistantAgent,
    message: str,
    session,
    logger,
) -> AsyncGenerator[StreamingResponse, None]:
    """Stream agent response in real-time chunks, mapping events to response types."""
    try:
        text_message = TextMessage(content=message, source="user")
        response_content = ""
        chunk_buffer = ""
        logger.info("🔄 Starting agent.run_stream() processing")
        response_count = 0
        async for response in agent.run_stream(task=text_message):
            response_count += 1
            if hasattr(response, 'messages') and response.messages:
                for msg in response.messages:
                    # Tool call detection
                    if hasattr(msg, 'tool_name') or hasattr(msg, 'arguments'):
                        tool_name = getattr(msg, 'tool_name', 'tool')
                        arguments = getattr(msg, 'arguments', {})
                        yield StreamingResponse(
                            chunk_id=str(uuid4()),
                            session_id=session.session_id,
                            agent_name=session.agent_name,
                            chunk_type='tool_call',
                            content=json.dumps({"tool": tool_name, "arguments": arguments}),
                            timestamp=datetime.utcnow(),
                        )
                        continue

                    # Tool result detection
                    if hasattr(msg, 'result') or hasattr(msg, 'output'):
                        result_payload = getattr(msg, 'result', getattr(msg, 'output', ''))
                        yield StreamingResponse(
                            chunk_id=str(uuid4()),
                            session_id=session.session_id,
                            agent_name=session.agent_name,
                            chunk_type='tool_result',
                            content=str(result_payload),
                            timestamp=datetime.utcnow(),
                        )
                        continue

                    # Handoff detection
                    if isinstance(msg, HandoffMessage):
                        target = getattr(msg, 'target', 'unknown')
                        yield StreamingResponse(
                            chunk_id=str(uuid4()),
                            session_id=session.session_id,
                            agent_name=session.agent_name,
                            chunk_type='handoff',
                            content=f"handoff_to:{target}",
                            timestamp=datetime.utcnow(),
                        )
                        continue

                    # Default text content streaming
                    if hasattr(msg, 'content') and msg.content:
                        content = msg.content
                        words = content.split()
                        for wi, word in enumerate(words):
                            chunk_buffer += word + " "
                            if (wi > 0 and wi % 4 == 0) or word.endswith(('.', '!', '?')):
                                if chunk_buffer.strip():
                                    yield StreamingResponse(
                                        chunk_id=str(uuid4()),
                                        session_id=session.session_id,
                                        agent_name=session.agent_name,
                                        chunk_type='text',
                                        content=chunk_buffer.strip(),
                                        timestamp=datetime.utcnow(),
                                    )
                                    response_content += chunk_buffer
                                    chunk_buffer = ""
                                    await asyncio.sleep(0.05)
                        if chunk_buffer.strip():
                            yield StreamingResponse(
                                chunk_id=str(uuid4()),
                                session_id=session.session_id,
                                agent_name=session.agent_name,
                                chunk_type='text',
                                content=chunk_buffer.strip(),
                                timestamp=datetime.utcnow(),
                            )
                            response_content += chunk_buffer
                            chunk_buffer = ""
                break
            break
        logger.info("🎯 Finished processing %s responses", response_count)
    except Exception as e:
        logger.error("❌ Agent streaming error", error=str(e))
        yield StreamingResponse(
            chunk_id=str(uuid4()),
            session_id=session.session_id,
            agent_name=session.agent_name,
            chunk_type='error',
            content=f"Streaming error: {str(e)}",
            timestamp=datetime.utcnow()
        )


