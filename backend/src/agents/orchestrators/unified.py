"""
Unified Orchestrator Implementation
Consolidates all orchestration strategies into a single, efficient implementation
"""

import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator, Tuple
from datetime import datetime
import structlog

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.messages import TextMessage

from .base import BaseGroupChatOrchestrator
from ..services.groupchat.intelligent_router import IntelligentAgentRouter
from ..services.groupchat.rag import AdvancedRAGProcessor
from ..services.groupchat.per_turn_rag import PerTurnRAGInjector
from ..services.groupchat.metrics import extract_agents_used, estimate_cost
from ..services.agent_intelligence import AgentIntelligence
from ..security.ai_security_guardian import AISecurityGuardian
from ..services.agent_loader import DynamicAgentLoader
from ...core.ai_clients import get_autogen_client

logger = structlog.get_logger()


class UnifiedOrchestrator(BaseGroupChatOrchestrator):
    """
    Unified orchestrator that combines the best features from all existing orchestrators:
    - Intelligent routing from IntelligentAgentRouter
    - GroupChat for multi-agent scenarios
    - Direct agent conversation for efficiency
    - RAG support for context-aware responses
    - Safety gates for responsible AI
    - WebSocket streaming support
    - Cost and performance tracking
    """
    
    def __init__(self, name: str = "unified_orchestrator"):
        super().__init__(name)
        self.router = IntelligentAgentRouter()
        self.agent_intelligence = AgentIntelligence()
        self.agent_loader = DynamicAgentLoader()
        self.termination_markers = ["DONE", "TERMINATE", "END_CONVERSATION"]
        self.max_rounds = 10
        self.circuit_breaker = {
            "failures": 0,
            "threshold": 3,
            "is_open": False,
            "last_failure": None
        }
    
    async def initialize(
        self,
        agents_dir: str,
        model_client: Optional[Any] = None,
        **kwargs
    ) -> bool:
        """
        Initialize the unified orchestrator.
        
        Args:
            agents_dir: Path to agent definitions
            model_client: AI model client (creates one if not provided)
            **kwargs: Additional configuration
        
        Returns:
            Success status
        """
        try:
            # Initialize model client if not provided
            if model_client is None:
                model_client = get_autogen_client(provider="openai")
            self.model_client = model_client
            
            # Load agents from directory
            logger.info(f"📂 Loading agents from {agents_dir}")
            agent_configs = await self.agent_loader.load_agents_from_directory(agents_dir)
            
            # Create agent instances
            for config in agent_configs:
                agent = AssistantAgent(
                    name=config["name"],
                    model_client=self.model_client,
                    system_message=config.get("system_message", ""),
                    description=config.get("description", ""),
                    tools=config.get("tools", [])
                )
                self.agents[config["name"]] = agent
            
            logger.info(f"✅ Loaded {len(self.agents)} agents")
            
            # Initialize GroupChat for multi-agent scenarios
            if len(self.agents) > 1:
                self.group_chat = RoundRobinGroupChat(
                    participants=list(self.agents.values())
                )
            
            # Initialize RAG processor if enabled
            if kwargs.get("enable_rag", True):
                self.rag_processor = AdvancedRAGProcessor()
                await self.rag_processor.initialize()
            
            # Initialize safety guardian if enabled
            if kwargs.get("enable_safety", True):
                self.safety_guardian = AISecurityGuardian()
            
            # Mark as initialized
            self.is_initialized = True
            self.initialization_time = datetime.now()
            
            logger.info(f"✅ Unified orchestrator initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            self._handle_circuit_breaker_failure()
            return False
    
    async def orchestrate(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Process message through the unified orchestration system.
        
        Uses intelligent routing to determine the best approach:
        1. Single agent for focused queries (most efficient)
        2. Multi-agent GroupChat for complex queries
        3. Falls back gracefully on failures
        """
        
        # Check circuit breaker
        if self._is_circuit_open():
            return self._circuit_breaker_response()
        
        start_time = datetime.now()
        
        try:
            # Safety check if enabled
            if self.safety_guardian:
                safety_result = await self.safety_guardian.check_message(message)
                if not safety_result.is_safe:
                    return {
                        "response": safety_result.explanation,
                        "agents_used": ["safety_guardian"],
                        "turn_count": 0,
                        "duration_seconds": 0,
                        "blocked": True
                    }
            
            # Add RAG context if available
            enhanced_message = message
            if self.rag_processor and context:
                rag_context = await self.rag_processor.get_relevant_context(
                    message, 
                    context.get("document_ids", [])
                )
                if rag_context:
                    enhanced_message = f"{message}\n\nContext:\n{rag_context}"
            
            # Determine routing strategy
            should_use_single = self.router.should_use_single_agent(message)
            
            if should_use_single:
                # Route to single best agent
                result = await self._execute_single_agent(
                    enhanced_message, context, user_id, conversation_id
                )
            else:
                # Use multi-agent GroupChat
                result = await self._execute_multi_agent(
                    enhanced_message, context, user_id, conversation_id
                )
            
            # Update metrics
            duration = (datetime.now() - start_time).total_seconds()
            self.update_metrics(
                tokens_used=result.get("tokens", 0),
                cost=result.get("cost", 0.0),
                response_time=duration
            )
            
            # Reset circuit breaker on success
            self._reset_circuit_breaker()
            
            return result
            
        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            self._handle_circuit_breaker_failure()
            
            # Fallback response
            return {
                "response": "I encountered an issue processing your request. Please try again.",
                "agents_used": [],
                "turn_count": 0,
                "duration_seconds": (datetime.now() - start_time).total_seconds(),
                "error": str(e)
            }
    
    async def _execute_single_agent(
        self,
        message: str,
        context: Optional[Dict[str, Any]],
        user_id: str,
        conversation_id: str
    ) -> Dict[str, Any]:
        """Execute with a single agent for efficiency"""
        
        # Select best agent
        best_agent = self.router.select_best_agent(
            message,
            list(self.agents.values()),
            context
        )
        
        if not best_agent:
            # Fallback to first available agent
            best_agent = list(self.agents.values())[0]
        
        logger.info(f"🎯 Single agent execution: {best_agent.name}")
        
        # Get intelligent response
        response = await self.agent_intelligence.generate_intelligent_response(
            message,
            context,
            agent_name=best_agent.name
        )
        
        # Execute agent
        messages = []
        async for chunk in best_agent.run_stream(task=message):
            if hasattr(chunk, 'content'):
                messages.append(chunk)
        
        # Extract final response
        final_response = response or " ".join(
            msg.content for msg in messages 
            if hasattr(msg, 'content') and isinstance(msg.content, str)
        )
        
        return {
            "response": final_response,
            "agents_used": [best_agent.name],
            "turn_count": 1,
            "duration_seconds": 0,  # Will be set by caller
            "routing": "single_agent",
            "cost_breakdown": estimate_cost(messages)
        }
    
    async def _execute_multi_agent(
        self,
        message: str,
        context: Optional[Dict[str, Any]],
        user_id: str,
        conversation_id: str
    ) -> Dict[str, Any]:
        """Execute with multiple agents for complex queries"""
        
        logger.info("🤝 Multi-agent execution via GroupChat")
        
        if not self.group_chat:
            # Fallback to single agent if no group chat
            return await self._execute_single_agent(
                message, context, user_id, conversation_id
            )
        
        # Run group chat
        task_message = TextMessage(content=message, source="user")
        result = await self.group_chat.run(
            task=task_message,
            termination_condition=self._check_termination,
            max_turns=self.max_rounds
        )
        
        # Extract results
        messages = result.messages if hasattr(result, 'messages') else []
        agents_used = extract_agents_used(messages)
        
        # Get final response
        final_response = ""
        for msg in reversed(messages):
            if hasattr(msg, 'content') and isinstance(msg.content, str):
                # Skip user messages and termination markers
                if msg.source != "user" and not any(
                    marker in msg.content for marker in self.termination_markers
                ):
                    final_response = msg.content
                    break
        
        return {
            "response": final_response,
            "agents_used": agents_used,
            "turn_count": len(messages),
            "duration_seconds": 0,  # Will be set by caller
            "routing": "multi_agent",
            "cost_breakdown": estimate_cost(messages)
        }
    
    async def stream(
        self,
        message: str,
        websocket: Any,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream responses via WebSocket"""
        
        # Determine best agent for streaming
        best_agent = self.router.select_best_agent(
            message,
            list(self.agents.values()),
            context
        )
        
        if not best_agent:
            best_agent = list(self.agents.values())[0]
        
        logger.info(f"🔄 Streaming via {best_agent.name}")
        
        # Stream agent response
        async for chunk in best_agent.run_stream(task=message):
            if hasattr(chunk, 'content') and isinstance(chunk.content, str):
                # Send to websocket
                await websocket.send_json({
                    "type": "chunk",
                    "content": chunk.content,
                    "agent": best_agent.name
                })
                yield chunk.content
        
        # Send completion signal
        await websocket.send_json({
            "type": "complete",
            "agent": best_agent.name
        })
    
    def _check_termination(self, messages: List[Any]) -> bool:
        """Check if conversation should terminate"""
        if not messages:
            return False
        
        last_message = messages[-1]
        if hasattr(last_message, 'content') and isinstance(last_message.content, str):
            return any(
                marker in last_message.content 
                for marker in self.termination_markers
            )
        
        return len(messages) >= self.max_rounds
    
    def _is_circuit_open(self) -> bool:
        """Check if circuit breaker is open"""
        if not self.circuit_breaker["is_open"]:
            return False
        
        # Check if enough time has passed to retry
        if self.circuit_breaker["last_failure"]:
            time_since_failure = (
                datetime.now() - self.circuit_breaker["last_failure"]
            ).total_seconds()
            
            if time_since_failure > 60:  # 1 minute cooldown
                self._reset_circuit_breaker()
                return False
        
        return True
    
    def _handle_circuit_breaker_failure(self):
        """Handle a failure for circuit breaker"""
        self.circuit_breaker["failures"] += 1
        self.circuit_breaker["last_failure"] = datetime.now()
        
        if self.circuit_breaker["failures"] >= self.circuit_breaker["threshold"]:
            self.circuit_breaker["is_open"] = True
            logger.warning("⚠️ Circuit breaker opened due to repeated failures")
    
    def _reset_circuit_breaker(self):
        """Reset circuit breaker"""
        self.circuit_breaker["failures"] = 0
        self.circuit_breaker["is_open"] = False
        self.circuit_breaker["last_failure"] = None
    
    def _circuit_breaker_response(self) -> Dict[str, Any]:
        """Response when circuit breaker is open"""
        return {
            "response": "The system is temporarily unavailable. Please try again in a moment.",
            "agents_used": [],
            "turn_count": 0,
            "duration_seconds": 0,
            "circuit_breaker": "open"
        }