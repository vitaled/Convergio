"""
CONVERGIO 2029 - MODERN AUTOGEN GROUPCHAT ORCHESTRATOR
Replaces custom agent swarm with AutoGen GroupChat for better collaboration
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import uuid

import structlog
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat
from autogen_agentchat.messages import HandoffMessage, TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient

from agents.services.cost_tracker import CostTracker
from agents.services.redis_state_manager import RedisStateManager
from agents.services.agent_loader import DynamicAgentLoader, AgentMetadata
from agents.services.groupchat.initializer import initialize_model_client, initialize_agent_loader
from agents.services.groupchat.agent_factory import create_business_agents
from agents.services.groupchat.selection_policy import select_key_agents
from agents.services.groupchat.runner import run_groupchat_stream
# Decision planning
from agents.services.decision_engine import DecisionEngine, DecisionPlan
from agents.services.observability.telemetry import get_telemetry, TelemetryContext
from agents.services.groupchat.metrics import (
    extract_final_response,
    extract_agents_used,
    estimate_cost,
    serialize_chat_history,
)
from agents.services.groupchat.setup import create_groupchat
from agents.services.groupchat.rag import build_memory_context, AdvancedRAGProcessor
from agents.services.groupchat.context import enhance_message_with_context
from agents.services.groupchat.orchestrator_conversation import orchestrate_conversation_impl, direct_agent_conversation_impl
from agents.services.groupchat.per_turn_rag import PerTurnRAGInjector, initialize_per_turn_rag
from agents.services.groupchat.turn_by_turn_selector import IntelligentSpeakerSelector as TurnSelector
from agents.utils.config import get_settings
from agents.utils.tracing import start_span
from agents.security.ai_security_guardian import AISecurityGuardian, SecurityDecision
from agents.tools.backend_api_client import query_talents_count, query_engagements_summary, query_dashboard_stats, query_skills_overview
from agents.tools.vector_search_client import get_vector_client, embed_text, search_similar
from agents.services.hitl.approval_store import ApprovalStore
from agents.services.decision_engine import DecisionEngine

logger = structlog.get_logger()

from agents.services.groupchat.types import GroupChatResult

class ModernGroupChatOrchestrator:
    """Modern AutoGen GroupChat orchestrator for Convergio agents."""
    
    def __init__(self, 
                 state_manager: RedisStateManager, 
                 cost_tracker: CostTracker,
                 agents_directory: str = None,
                 memory_system=None,
                 observers: Optional[list] = None):
        """Initialize Modern GroupChat Orchestrator."""
        self.state_manager = state_manager
        self.memory_system = memory_system
        self.cost_tracker = cost_tracker
        self.settings = get_settings()
        self.security_guardian: Optional[AISecurityGuardian] = AISecurityGuardian() if self.settings.cost_safety_enabled else None
        self.approval_store: Optional[ApprovalStore] = ApprovalStore() if self.settings.hitl_enabled else None
        
        # Core components
        self.agent_loader: DynamicAgentLoader = None
        self.agents: Dict[str, AssistantAgent] = {}
        self.agent_metadata: Dict[str, AgentMetadata] = {}
        
        # GroupChat components
        self.group_chat: SelectorGroupChat = None
        
        # Model client
        self.model_client: OpenAIChatCompletionClient = None
        
        # RAG components
        self.rag_processor: Optional[AdvancedRAGProcessor] = None
        self.per_turn_rag_injector: Optional[PerTurnRAGInjector] = None
        
        # Speaker selection components
        self.intelligent_selector: Optional[TurnSelector] = None
        
        # Configuration
        self.agents_directory = agents_directory or "agents/src/agents"
        self._initialized = False
        # Observers for telemetry
        self.observers = observers or []
        # Decision engine
        self._decision_engine = DecisionEngine()
        self._last_decision_plan: Optional[DecisionPlan] = None
    
    async def initialize(self) -> None:
        """Initialize the modern GroupChat ecosystem."""
        try:
            logger.info("🚀 Initializing Modern AutoGen GroupChat Orchestrator")
            
            # Initialize model client
            await self._initialize_model_client()
            
            # Load all agent definitions
            await self._initialize_agent_loader()
            
            # Create business agents
            await self._create_business_agents()
            
            # Initialize RAG components if enabled
            await self._initialize_rag_components()
            
            # Initialize speaker selection if enabled
            await self._initialize_speaker_selection()
            
            # Setup GroupChat
            await self._setup_group_chat()
            
            self._initialized = True
            logger.info(
                "✅ Modern GroupChat Orchestrator initialized successfully",
                total_agents=len(self.agents),
                group_chat_size=len(self.agents) if self.group_chat else 0
            )
            
        except Exception as e:
            logger.error("❌ Failed to initialize GroupChat Orchestrator", error=str(e))
            raise
    
    def is_healthy(self) -> bool:
        """Check if orchestrator is healthy."""
        return (self._initialized and 
                self.group_chat is not None and
                self.model_client is not None)
    
    async def _initialize_model_client(self) -> None:
        """Initialize the OpenAI model client."""
        try:
            self.model_client = initialize_model_client()
        except Exception as e:
            logger.error("❌ Failed to initialize model client", error=str(e))
            raise

    async def _initialize_agent_loader(self) -> None:
        """Initialize the dynamic agent loader."""
        self.agent_loader, self.agent_metadata = initialize_agent_loader(self.agents_directory)
    

    
    async def _create_business_agents(self) -> None:
        """Create business-specific agents from metadata."""
        try:
            self.agents = create_business_agents(self.agent_loader, self.model_client)
        except Exception as e:
            logger.error("❌ Failed to create business agents", error=str(e))
            raise
    
    async def _initialize_rag_components(self) -> None:
        """Initialize RAG components for per-turn context injection."""
        try:
            if self.settings.rag_in_loop_enabled and self.memory_system:
                # Initialize RAG processor
                self.rag_processor = AdvancedRAGProcessor(
                    memory_system=self.memory_system,
                    settings=self.settings
                )
                
                # Initialize per-turn RAG injector
                self.per_turn_rag_injector = initialize_per_turn_rag(
                    rag_processor=self.rag_processor,
                    memory_system=self.memory_system,
                    settings=self.settings
                )
                
                logger.info("📚 RAG components initialized for per-turn injection")
            else:
                logger.info("📚 RAG disabled or memory system not available")
        except Exception as e:
            logger.error("❌ Failed to initialize RAG components", error=str(e))
            # Non-critical, continue without RAG
    
    async def _initialize_speaker_selection(self) -> None:
        """Initialize intelligent speaker selection."""
        try:
            if self.settings.speaker_policy_enabled:
                # Initialize intelligent selector
                self.intelligent_selector = TurnSelector()
                
                logger.info("🎯 Intelligent speaker selection initialized")
            else:
                logger.info("🎯 Speaker selection using default policy")
        except Exception as e:
            logger.error("❌ Failed to initialize speaker selection", error=str(e))
            # Non-critical, continue with default selection
    
    async def _setup_group_chat(self) -> None:
        """Setup the main GroupChat with all agents."""
        try:
            # Select participants honoring speaker policy flag
            all_agents_list = list(self.agents.values())
            if self.settings.speaker_policy_enabled:
                key_agents = select_key_agents(all_agents_list)
                logger.info("🗣️ Speaker policy enabled", selected=len(key_agents))
            else:
                key_agents = all_agents_list
                logger.info("🗣️ Speaker policy disabled, using all agents", total=len(key_agents))

            # Create SelectorGroupChat using settings-driven max_turns
            # Use enhanced GroupChat with turn-by-turn features if enabled
            self.group_chat = create_groupchat(
                participants=key_agents,
                model_client=self.model_client,
                max_turns=self.settings.autogen_max_turns,
                rag_injector=self.per_turn_rag_injector,
                enable_per_turn_rag=(self.settings.rag_in_loop_enabled and self.per_turn_rag_injector is not None),
                enable_turn_by_turn_selection=(self.settings.speaker_policy_enabled and self.intelligent_selector is not None),
                intelligent_selector=self.intelligent_selector
            )
            
            logger.info("👥 GroupChat setup complete", 
                       agents=len(key_agents),
                       agent_names=[agent.name for agent in key_agents])
            
        except Exception as e:
            logger.error("❌ Failed to setup GroupChat", error=str(e))
            raise
    

    
    # Speaker selection migrated to groupchat/selection_policy.py
    
    async def _reset_team_state(self) -> None:
        """Reset AutoGen team state to allow new conversations."""
        try:
            # Check if group chat exists and is running
            if self.group_chat is not None:
                # Try to stop the team if it's running
                try:
                    # In AutoGen 0.7.1, we need to reset by recreating the group chat
                    logger.info("🔄 Resetting AutoGen team state")
                    await self._setup_group_chat()
                    logger.info("✅ AutoGen team state reset successfully")
                except Exception as reset_error:
                    logger.warning("⚠️ Team reset warning (continuing)", error=str(reset_error))
                    # Continue anyway - sometimes this is expected
        except Exception as e:
            logger.error("❌ Failed to reset team state", error=str(e))
            # Don't raise - let the conversation attempt to continue
    
    # Model configuration handled via initializer and settings
    
    async def orchestrate_conversation(
        self,
        message: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        max_rounds: int = 5
    ) -> GroupChatResult:
        """Orchestrate a conversation using GroupChat."""
        if not self.is_healthy():
            raise RuntimeError("Orchestrator not initialized")
        
        start_time = datetime.now()
        conversation_id = conversation_id or str(uuid.uuid4())
        
        try:
            telemetry = get_telemetry()
            telemetry_ctx = TelemetryContext(conversation_id=conversation_id, user_id=user_id)
            # Check if user wants direct agent conversation
            if context and 'agent_name' in context and context['agent_name']:
                agent_name = context['agent_name']
                if agent_name in self.agents:
                    logger.info("🎯 Direct agent conversation requested", agent=agent_name)
                    return await self._direct_agent_conversation(agent_name, message, user_id, conversation_id, context)
            
            logger.info("🎯 Starting GroupChat conversation", 
                       conversation_id=conversation_id,
                       user_id=user_id,
                       message_length=len(message))
            
            # WS6: Human-in-the-Loop gating when flagged by context
            if self.settings.hitl_enabled and self.approval_store is not None:
                requires_approval = bool((context or {}).get("requires_approval", False))
                if requires_approval:
                    logger.info("🛑 HITL approval required", conversation_id=conversation_id)
                    self.approval_store.request_approval(
                        request_id=conversation_id,
                        user_id=user_id,
                        action="groupchat_conversation",
                        metadata={"message_preview": message[:120]}
                    )
                    raise RuntimeError("Approval required: conversation paused pending human approval")
            
            # WS7: Cost & Safety gating
            if self.settings.cost_safety_enabled and self.cost_tracker is not None:
                budget = await self.cost_tracker.check_budget_limits(conversation_id)
                if telemetry:
                    try:
                        from agents.observability.telemetry import ConvergioTelemetry
                        self._record_budget_status_telemetry(telemetry, telemetry_ctx, budget)
                        telemetry.record_budget_event(
                            status=str(budget.get("status", "unknown")),
                            remaining_usd=float(budget.get("remaining_budget_usd", 0.0)),
                            limit_usd=float(budget.get("daily_limit_usd", 0.0)),
                            context=telemetry_ctx,
                        )
                    except Exception:
                        pass
                if not budget.get("can_proceed", True):
                    logger.error("🚫 Budget limit reached", reason=budget.get("reason"))
                    raise RuntimeError("Budget limit exceeded: conversation halted")

            if self.settings.cost_safety_enabled and self.security_guardian is not None:
                validation = await self.security_guardian.validate_prompt(message, user_id, context or {})
                if validation.decision == SecurityDecision.REJECT:
                    logger.error("🚫 Security validation rejected prompt")
                    raise RuntimeError("Prompt rejected by security policy")

            # Decision Engine planning (behind flag)
            self._last_decision_plan = None
            previous_model = None
            previous_max_turns = None
            if getattr(self.settings, "decision_engine_enabled", False):
                try:
                    plan = self._decision_engine.plan(message, context or {})
                    self._last_decision_plan = plan
                    # Emit a decision event using selection decision channel
                    if telemetry:
                        try:
                            telemetry.record_selection_decision(selected_agent="decision_engine", reason="execution_plan", confidence=1.0, context=telemetry_ctx)
                            telemetry.record_decision_made({
                                "sources": plan.sources,
                                "tools": plan.tools,
                                "model": plan.model,
                                "max_turns": plan.max_turns,
                                "budget_usd": plan.budget_usd,
                            }, telemetry_ctx)
                        except Exception:
                            pass
                    # Apply model and max_turns from plan for this conversation
                    previous_model = getattr(self.settings, 'default_ai_model', None)
                    previous_max_turns = getattr(self.group_chat, 'max_turns', None) if self.group_chat else None
                    if plan.model and plan.model != previous_model:
                        try:
                            from agents.groupchat.initializer import initialize_model_client
                            # Temporarily override default model for this run
                            self.settings.default_ai_model = plan.model  # type: ignore[attr-defined]
                            self.model_client = initialize_model_client()
                            await self._setup_group_chat()
                        except Exception as e:
                            logger.warning("Could not switch model per plan; continuing with default", error=str(e))
                    if self.group_chat and plan.max_turns:
                        try:
                            self.group_chat.max_turns = plan.max_turns
                        except Exception:
                            pass
                except Exception as e:
                    logger.warning("Decision planning failed; continuing with defaults", error=str(e))

            result = await orchestrate_conversation_impl(
                orchestrator=self,
                message=message,
                user_id=user_id,
                conversation_id=conversation_id,
                context=context,
                max_rounds=max_rounds,
                run_groupchat_stream_func=run_groupchat_stream,
                build_memory_context_func=build_memory_context,
            )
            logger.info("✅ GroupChat conversation completed", conversation_id=conversation_id, duration=result.duration_seconds, agents_used=result.agents_used, cost=result.cost_breakdown.get('total_cost', 0))
            # Restore model and max_turns if overridden by plan
            try:
                if previous_model is not None and getattr(self.settings, 'default_ai_model', None) != previous_model:
                    self.settings.default_ai_model = previous_model  # type: ignore[attr-defined]
                    self.model_client = initialize_model_client()
                    await self._setup_group_chat()
                if self.group_chat and previous_max_turns is not None:
                    self.group_chat.max_turns = previous_max_turns
            except Exception:
                pass
            return result
            
        except Exception as e:
            logger.error("❌ GroupChat conversation failed",
                        conversation_id=conversation_id,
                        error=str(e))
            raise
    
    async def _direct_agent_conversation(
        self, 
        agent_name: str, 
        message: str, 
        user_id: str, 
        conversation_id: str,
        context: Optional[Dict[str, Any]]
    ) -> GroupChatResult:
        """Have a direct conversation with a specific agent bypassing GroupChat."""
        start_time = datetime.now()
        
        result = await direct_agent_conversation_impl(self, agent_name, message, user_id, conversation_id, context)
        return result

    # Message context enhancement migrated to groupchat/context.py
    
    # Response extraction migrated to groupchat/metrics.py
    
    # Agent usage extraction migrated to groupchat/metrics.py
    
    # Cost estimation migrated to groupchat/metrics.py
    
    async def _generate_conversation_summary(self, chat_result) -> str:
        """Generate a summary of the conversation."""
        if hasattr(chat_result, 'messages') and chat_result.messages:
            # Use text analyzer to generate summary
            messages = [msg.content for msg in chat_result.messages if hasattr(msg, 'content')]
            conversation_text = "\n".join(messages)
            
            summary_prompt = f"Summarize this business conversation in 2-3 sentences:\n\n{conversation_text}"
            
            # For now, return a simple summary
            return f"Conversation with {len(messages)} messages completed successfully."
        
        return "Conversation completed."
    
    async def _store_conversation(self, conversation_id: str, user_id: str, chat_result, cost_breakdown: Dict[str, Any]) -> None:
        """Store conversation in Redis."""
        try:
            conversation_data = {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "cost_breakdown": cost_breakdown,
                "chat_history": serialize_chat_history(getattr(chat_result, 'messages', [])),
                "status": "completed"
            }
            
            await self.state_manager.store_conversation(conversation_id, conversation_data)
            
        except Exception as e:
            logger.error("❌ Failed to store conversation", error=str(e))
    
    # Chat history serialization migrated to groupchat/metrics.py
    
    async def get_ecosystem_status(self) -> Dict[str, Any]:
        """Get current ecosystem status."""
        return {
            "status": "healthy" if self.is_healthy() else "unhealthy",
            "total_agents": len(self.agents),
            "group_chat_size": len(self.group_chat.agents) if self.group_chat else 0,
            "specialized_agents": ["text_analyzer", "retrieve_agent"],
            "business_agents": [name for name in self.agents.keys() 
                              if name not in ["text_analyzer", "retrieve_agent"]],
            "initialized": self._initialized,
            "timestamp": datetime.now().isoformat()
        }
    
    async def reload_agents(self) -> Dict[str, Any]:
        """Reload all agents."""
        try:
            logger.info("🔄 Reloading agents")
            
            # Reinitialize
            self._initialized = False
            self.agents.clear()
            
            await self.initialize()
            
            return {
                "status": "success",
                "message": "Agents reloaded successfully",
                "total_agents": len(self.agents),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("❌ Failed to reload agents", error=str(e))
            return {
                "status": "error",
                "message": f"Failed to reload agents: {str(e)}",
                "timestamp": datetime.now().isoformat()
            } 

    def _record_budget_status_telemetry(self, telemetry, telemetry_ctx: TelemetryContext, budget: Dict[str, Any]):
        try:
            remaining = float(budget.get("remaining_budget_usd", 0.0))
            limit = float(budget.get("daily_limit_usd", 0.0))
            status = str(budget.get("status", "unknown"))
            telemetry.record_budget_status(remaining, limit, status, telemetry_ctx)
        except Exception:
            pass 