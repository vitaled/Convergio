"""
GroupChat Runner
Utilities to run GroupChat streaming and collect messages and response.

Observer-aware: allows passing observers and run metadata so external systems
can subscribe to stream events without coupling to AutoGen internals.
"""

from typing import List, Tuple, Any, Dict, Iterable, Optional
import time

from ...observability.autogen_observer import AutoGenObserver


async def run_groupchat_stream(
    group_chat,
    task: str,
    *,
    observers: Optional[Iterable[AutoGenObserver]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    hard_timeout_seconds: Optional[int] = None,
    termination_markers: Optional[List[str]] = None,
    max_events: Optional[int] = None,
) -> Tuple[List[Any], str]:
    messages: List[Any] = []
    full_response = ""
    agents_involved = set()  # Track which agents actually responded
    run_meta = metadata or {}
    start_ts = time.monotonic()
    term_markers = [m.lower() for m in (termination_markers or [
        "final answer", "final response", "conclusion", "end_of_conversation", "terminate"
    ])]
    # Notify observers of conversation start (idempotent for direct use)
    if observers:
        for obs in observers:
            try:
                await obs.on_conversation_start({**run_meta, "task": task, "mode": run_meta.get("mode", "groupchat")})
            except Exception:
                pass

    # Proper async generator handling to prevent "generator didn't stop after throw()" errors
    stream_iterator = None
    try:
        import structlog
        logger = structlog.get_logger()
        logger.info("🚀 Starting GroupChat stream", task=task[:100])
        
        stream_iterator = aiter(group_chat.run_stream(task=task))
        
        while True:
            try:
                response = await anext(stream_iterator)
                messages.append(response)
                
                # Debug logging to understand response structure
                logger.debug("📨 GroupChat response", 
                           has_content=hasattr(response, "content"),
                           content_preview=str(response.content)[:100] if hasattr(response, "content") else None,
                           response_type=type(response).__name__,
                           source=getattr(response, "source", None))
                
                # Track which agent is responding
                agent_source = getattr(response, "source", None)
                if agent_source and agent_source != "user":
                    agents_involved.add(agent_source)
                    logger.debug(f"🤖 Agent {agent_source} is responding")
                
                # Skip user messages when building response
                if hasattr(response, "source") and response.source == "user":
                    logger.debug("Skipping user message in response")
                    continue
                    
                if hasattr(response, "content") and response.content:
                    # Don't include the original task in the response
                    if response.content.strip() != task.strip():
                        full_response += response.content
                    # Early termination: content markers
                    try:
                        content_l = response.content.lower()
                        if any(marker in content_l for marker in term_markers):
                            break
                    except Exception:
                        pass
                elif hasattr(response, "text") and response.text:
                    # Fallback for different message format
                    full_response += response.text
                elif hasattr(response, "message") and response.message:
                    # Another fallback format
                    full_response += response.message
                        
                # Max events guard
                if max_events is not None and len(messages) >= max_events:
                    break
                    
                # Hard timeout guard
                if hard_timeout_seconds is not None and (time.monotonic() - start_ts) >= hard_timeout_seconds:
                    # Append a gentle termination notice
                    try:
                        from autogen_agentchat.messages import TextMessage
                        messages.append(TextMessage(content="[conversation truncated due to timeout]", source="system"))
                    except Exception:
                        pass
                    break
                    
                if observers:
                    for obs in observers:
                        try:
                            await obs.on_model_stream_event(response, run_meta)
                        except Exception:
                            pass
                            
            except StopAsyncIteration:
                # Natural end of stream
                break
                
    except Exception as e:
        # Log the exception but continue gracefully
        import logging
        logging.exception(f"Error in groupchat stream: {e}")
        
    finally:
        # Properly close async iterator to prevent generator errors
        if stream_iterator is not None:
            try:
                if hasattr(stream_iterator, 'aclose'):
                    await stream_iterator.aclose()
            except Exception:
                pass  # Ignore cleanup errors
    
    # If no response was captured but we have messages, try to extract content
    if not full_response and messages:
        logger.warning("⚠️ No response captured from GroupChat, extracting from messages")
        for msg in messages:
            if hasattr(msg, "content") and msg.content:
                full_response = msg.content
                break
            elif hasattr(msg, "text") and msg.text:
                full_response = msg.text
                break
            elif hasattr(msg, "message") and msg.message:
                full_response = msg.message
                break
        
        # Last resort - if still no response, return empty string
        if not full_response:
            logger.error("❌ No valid response from GroupChat, returning empty response")
            full_response = ""
    
    # Log which agents were involved
    logger.info("✅ GroupChat stream completed", 
               agents_involved=list(agents_involved),
               response_length=len(full_response))
    
    # Store agents_involved in messages metadata for extraction
    if messages and agents_involved:
        # Add a metadata message with agents info
        try:
            from autogen_agentchat.messages import TextMessage
            metadata_msg = TextMessage(
                content="[agents_metadata]",
                source="system"
            )
            # Store as attribute for easier extraction
            metadata_msg.agents_involved = list(agents_involved)
            messages.append(metadata_msg)
        except Exception as e:
            logger.warning(f"Could not add metadata message: {e}")
    
    return messages, full_response


