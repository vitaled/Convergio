"""
Orchestrator conversation handlers extracted for file size hygiene.
Implements conversation flow and direct agent conversation using the orchestrator instance.
"""

from datetime import datetime
from typing import Any, Dict, Optional, List
import uuid
import structlog

from autogen_agentchat.messages import TextMessage, HandoffMessage

from .metrics import extract_final_response, extract_agents_used, estimate_cost, serialize_chat_history
from .rag import build_memory_context as default_build_memory_context, AdvancedRAGProcessor
from .context import enhance_message_with_context
from .types import GroupChatResult
from .per_turn_rag import PerTurnRAGInjector, RAGEnhancedGroupChat, initialize_per_turn_rag
from ...utils.tracing import start_span
from ...security.ai_security_guardian import SecurityDecision


logger = structlog.get_logger()


async def orchestrate_conversation_impl(
    orchestrator,
    message: str,
    user_id: str,
    conversation_id: Optional[str],
    context: Optional[Dict[str, Any]],
    max_rounds: int,
    run_groupchat_stream_func,
    build_memory_context_func=default_build_memory_context,
) -> GroupChatResult:
    if not orchestrator.is_healthy():
        raise RuntimeError("Orchestrator not initialized")

    start_time = datetime.now()
    conversation_id = conversation_id or str(uuid.uuid4())

    # Import message classifier
    from .message_classifier import MessageClassifier
    
    # Classify the message to determine strategy
    msg_type, msg_metadata = MessageClassifier.classify_message(message)
    logger.info(f"📊 Message classified as: {msg_type}", metadata=msg_metadata)
    
    # Direct agent conversation path
    if context and 'agent_name' in context and context['agent_name']:
        agent_name = context['agent_name']
        if agent_name in orchestrator.agents:
            logger.info("🎯 Direct agent conversation requested", agent=agent_name)
            return await direct_agent_conversation_impl(orchestrator, agent_name, message, user_id, conversation_id, context)
    
    # Handle simple messages with single agent
    if msg_metadata.get('single_agent', False) and msg_type in ['greeting', 'simple_query']:
        # Use Ali (Chief of Staff) for simple responses
        agent_name = 'ali_chief_of_staff'
        if agent_name in orchestrator.agents:
            logger.info(f"🎯 Simple {msg_type} - routing to {agent_name}")
            return await direct_agent_conversation_impl(
                orchestrator, agent_name, message, user_id, conversation_id, 
                {**context, 'message_type': msg_type} if context else {'message_type': msg_type}
            )

    logger.info("🎯 Starting GroupChat conversation", 
                conversation_id=conversation_id, 
                user_id=user_id, 
                message_type=msg_type,
                message_length=len(message))

    # Cost & Safety gating
    if orchestrator.settings.cost_safety_enabled and orchestrator.cost_tracker is not None:
        budget = await orchestrator.cost_tracker.check_budget_limits(conversation_id)
        if not budget.get("can_proceed", True):
            logger.error("🚫 Budget limit reached", reason=budget.get("reason"))
            raise RuntimeError("Budget limit exceeded: conversation halted")

    if orchestrator.settings.cost_safety_enabled and orchestrator.security_guardian is not None:
        validation = await orchestrator.security_guardian.validate_prompt(message, user_id, context or {})
        if validation.decision == SecurityDecision.REJECT:
            logger.error("🚫 Security validation rejected prompt")
            raise RuntimeError("Prompt rejected by security policy")

    # Reset team state
    await orchestrator._reset_team_state()

    # Enhance and enrich with RAG
    enhanced_message = enhance_message_with_context(
        settings=orchestrator.settings,
        message=message,
        context=context,
    )

    try:
        if orchestrator.settings.rag_in_loop_enabled:
            with start_span("rag.build_context", {"user_id": user_id}):
                memory_msg = await build_memory_context_func(
                    orchestrator.memory_system,
                    user_id=user_id,
                    agent_id=None,
                    query=message,
                    limit=orchestrator.settings.rag_max_facts,
                    similarity_threshold=orchestrator.settings.rag_similarity_threshold,
                )
            if memory_msg:
                enhanced_message = f"{enhanced_message}\n\n{memory_msg.content}"
                logger.info("🧠 Enhanced with memory context")
    except Exception as e:
        logger.warning("⚠️ Memory retrieval failed", error=str(e))

    # Run groupchat
    logger.info("🔄 Running GroupChat conversation")
    run_metadata = {
        "conversation_id": conversation_id,
        "user_id": user_id,
        "mode": "groupchat",
        "context": context or {},
    }
    # Use message metadata to configure conversation
    effective_max_turns = min(
        msg_metadata.get('max_turns', 10),
        getattr(orchestrator.settings, 'autogen_max_turns', 10)
    )
    
    # Get appropriate termination markers for message type
    term_markers = MessageClassifier.get_termination_phrases(msg_type)
    
    # Shorter timeout for simple messages
    timeout_seconds = 30 if msg_type in ['greeting', 'simple_query'] else getattr(orchestrator.settings, 'autogen_timeout_seconds', 120)
    
    with start_span("groupchat.run", {"max_turns": effective_max_turns, "msg_type": msg_type, **run_metadata}):
        chat_messages, full_response = await run_groupchat_stream_func(
            orchestrator.group_chat,
            task=enhanced_message,
            observers=getattr(orchestrator, "observers", None),
            metadata={**run_metadata, "message_type": msg_type},
            hard_timeout_seconds=timeout_seconds,
            termination_markers=term_markers,
            max_events=max(1, effective_max_turns * 2),
        )

    # Extract details
    response = extract_final_response(chat_messages)
    agents_used = extract_agents_used(chat_messages)
    turn_count = len(chat_messages)

    # Cost tracking
    cost_breakdown = estimate_cost(chat_messages)
    try:
        if orchestrator.settings.cost_safety_enabled and orchestrator.cost_tracker is not None:
            with start_span("cost.track", {"conversation_id": conversation_id}):
                converted = {
                    "model": getattr(orchestrator.model_client, "model", orchestrator.settings.default_ai_model),
                    "total_tokens": int(cost_breakdown.get("estimated_tokens", 0)),
                    "total_cost_usd": float(cost_breakdown.get("total_cost_usd", cost_breakdown.get("total_cost", 0.0))),
                }
                await orchestrator.cost_tracker.track_conversation_cost(conversation_id, converted)
    except Exception as e:
        logger.warning("⚠️ Failed to track conversation cost", error=str(e))

    conversation_summary = await generate_conversation_summary_impl(orchestrator, type('ChatResult', (), { 'messages': chat_messages, 'response': full_response })())

    await store_conversation_impl(orchestrator, conversation_id, user_id, type('ChatResult', (), { 'messages': chat_messages, 'response': full_response })(), cost_breakdown)

    # Persist to memory system
    if orchestrator.memory_system:
        try:
            await orchestrator.memory_system.store_conversation(
                user_id=user_id,
                agent_id="group_chat",
                content=f"User: {message}\nResponse: {response}",
                metadata={
                    "conversation_id": conversation_id,
                    "agents_used": agents_used,
                    "turn_count": turn_count,
                    "cost": cost_breakdown.get("total_cost", 0)
                }
            )
            logger.info("🧠 Stored conversation in memory system")
        except Exception as e:
            logger.warning("⚠️ Memory storage failed", error=str(e))

    duration = (datetime.now() - start_time).total_seconds()
    # Notify observers end
    try:
        observers = getattr(orchestrator, "observers", None)
        if observers:
            summary = {
                "total_messages": len(chat_messages),
                "agents_used": agents_used,
                "response_preview": (response[:120] if isinstance(response, str) else ""),
                "duration_seconds": duration,
                "cost_breakdown": cost_breakdown,
                "turn_count": turn_count,
            }
            for obs in observers:
                try:
                    await obs.on_conversation_end(summary, run_metadata)
                except Exception:
                    pass
    except Exception:
        pass
    return GroupChatResult(
        response=response,
        agents_used=agents_used,
        turn_count=turn_count,
        duration_seconds=duration,
        cost_breakdown=cost_breakdown,
        timestamp=datetime.now().isoformat(),
        conversation_summary=conversation_summary,
        routing_decisions=[],
    )


async def direct_agent_conversation_impl(
    orchestrator, agent_name: str, message: str, user_id: str, conversation_id: str, context: Optional[Dict[str, Any]]
) -> GroupChatResult:
    start_time = datetime.now()
    try:
        agent = orchestrator.agents[agent_name]
        logger.info("🎯 Direct agent conversation starting", agent=agent_name, conversation_id=conversation_id, user_id=user_id)
        logger.info("🔄 Running direct agent conversation", agent=agent_name)
        # Notify observers start
        run_metadata = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "mode": "direct-agent",
            "agent_name": agent_name,
            "context": context or {},
        }
        try:
            observers = getattr(orchestrator, "observers", None)
            if observers:
                for obs in observers:
                    await obs.on_conversation_start({**run_metadata, "task": message})
        except Exception:
            pass

        response_content = ""
        try:
            async for response in agent.run_stream(task=message):
                if hasattr(response, 'messages') and response.messages:
                    for msg in response.messages:
                        if hasattr(msg, 'source') and msg.source == agent_name:
                            if hasattr(msg, 'content') and msg.content:
                                response_content = msg.content
                                break
                elif hasattr(response, 'content') and response.content:
                    response_content += response.content
                elif isinstance(response, str):
                    response_content += response
        except Exception as e:
            logger.warning(f"Error during agent streaming: {e}")
            response_content = ""

        if not response_content or response_content.strip() == "":
            agent_metadata = orchestrator.agent_metadata.get(agent_name, None)
            role = agent_metadata.role if agent_metadata else 'Agent'
            response_content = f"Ciao! Sono {agent_name} ({role}). Come posso aiutarti con: {message}"

        duration = datetime.now() - start_time
        # Notify observers end
        try:
            observers = getattr(orchestrator, "observers", None)
            if observers:
                summary = {
                    "total_messages": 1,
                    "agents_used": ["user", agent_name],
                    "response_preview": (response_content[:120] if isinstance(response_content, str) else ""),
                    "duration_seconds": duration.total_seconds(),
                    "cost_breakdown": {"total_cost": 0.01},
                    "turn_count": 1,
                }
                for obs in observers:
                    try:
                        await obs.on_conversation_end(summary, run_metadata)
                    except Exception:
                        pass
        except Exception:
            pass
        return GroupChatResult(
            response=response_content,
            agents_used=["user", agent_name],
            turn_count=1,
            duration_seconds=duration.total_seconds(),
            cost_breakdown={
                "total_cost": 0.01,
                "estimated_tokens": len(message + response_content) * 0.75,
                "cost_per_1k_tokens": 0.01,
                "currency": "USD",
            },
            timestamp=datetime.now().isoformat(),
            conversation_summary=f"Direct conversation with {agent_name}",
            routing_decisions=[f"Direct routing to {agent_name}"],
        )
    except Exception as e:
        logger.error("❌ Direct agent conversation failed", agent=agent_name, error=str(e), exc_info=True)
        duration = datetime.now() - start_time
        return GroupChatResult(
            response=f"Sorry, I'm having trouble connecting with {agent_name}. Please try again later. Error: {str(e)}",
            agents_used=["system"],
            turn_count=0,
            duration_seconds=duration.total_seconds(),
            cost_breakdown={"total_cost": 0.0, "estimated_tokens": 0},
            timestamp=datetime.now().isoformat(),
            conversation_summary="Direct conversation failed",
            routing_decisions=[f"Failed to route to {agent_name}"],
        )


async def generate_conversation_summary_impl(orchestrator, chat_result) -> str:
    if hasattr(chat_result, 'messages') and chat_result.messages:
        messages = [msg.content for msg in chat_result.messages if hasattr(msg, 'content')]
        return f"Conversation with {len(messages)} messages completed successfully."
    return "Conversation completed."


async def store_conversation_impl(orchestrator, conversation_id: str, user_id: str, chat_result, cost_breakdown: Dict[str, Any]) -> None:
    try:
        conversation_data = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "cost_breakdown": cost_breakdown,
            "chat_history": serialize_chat_history(getattr(chat_result, 'messages', [])),
            "status": "completed",
        }
        await orchestrator.state_manager.store_conversation(conversation_id, conversation_data)
    except Exception as e:
        logger.error("❌ Failed to store conversation", error=str(e))

