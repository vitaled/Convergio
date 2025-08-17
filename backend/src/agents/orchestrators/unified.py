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
from .resilience import CircuitBreaker, CircuitBreakerConfig, CircuitState, HealthMonitor
from agents.services.groupchat.intelligent_router import IntelligentAgentRouter
# from agents.services.groupchat.rag import AdvancedRAGProcessor  # TODO: Implement
# from agents.services.groupchat.per_turn_rag import PerTurnRAGInjector  # TODO: Implement
from agents.services.groupchat.metrics import extract_agents_used, estimate_cost
from agents.services.agent_intelligence import AgentIntelligence
from agents.security.ai_security_guardian import AISecurityGuardian
from agents.services.agent_loader import DynamicAgentLoader
from agents.tools.web_search_tool import get_web_tools
from agents.tools.database_tools import get_database_tools
from agents.tools.vector_search_tool import get_vector_tools
from core.ai_clients import get_autogen_client

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
        self.agent_intelligence = AgentIntelligence(agent_name=name)
        self.agent_loader = None
        self.termination_markers = ["DONE", "TERMINATE", "END_CONVERSATION"]
        self.max_rounds = 10
        
        # Enhanced circuit breaker with configurable settings
        circuit_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60,
            success_threshold=3
        )
        self.circuit_breaker = CircuitBreaker(name, circuit_config)
        
        # Health monitoring
        self.health_monitor = HealthMonitor(check_interval=30)
    
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
            
            # Load agents from directory using DynamicAgentLoader
            logger.info(f"📂 Loading agents from {agents_dir}")
            self.agent_loader = DynamicAgentLoader(agents_dir)
            self.agent_loader.scan_and_load_agents()
            
            # Prepare tools BEFORE creating agents
            all_tools = []
            all_tools.extend(get_web_tools())
            all_tools.extend(get_database_tools())
            all_tools.extend(get_vector_tools())
            
            logger.info(f"🔧 Prepared {len(all_tools)} tools for agents")
            
            # Create AutoGen AssistantAgent instances WITH TOOLS
            self.agents = self.agent_loader.create_autogen_agents(
                model_client=self.model_client,
                tools=all_tools  # Pass tools to agent creation
            )
                    
            logger.info(f"✅ Loaded {len(self.agents)} agents with {len(all_tools)} tools integrated")
            
            # Initialize GroupChat for multi-agent scenarios
            if len(self.agents) > 1:
                self.group_chat = RoundRobinGroupChat(
                    participants=list(self.agents.values())
                )
            
            # Initialize RAG processor if enabled (disabled - missing implementation)
            if kwargs.get("enable_rag", False):  # Disabled by default
                # TODO: Implement AdvancedRAGProcessor
                # self.rag_processor = AdvancedRAGProcessor()
                pass
            
            # Initialize safety guardian if enabled
            if kwargs.get("enable_safety", True):
                self.safety_guardian = AISecurityGuardian()
            
            # Mark as initialized
            self.is_initialized = True
            self.initialization_time = datetime.now()
            
            # Start health monitoring
            await self.health_monitor.start({self.name: self})
            
            logger.info(f"✅ Unified orchestrator initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            # Circuit breaker tracks failures automatically
            return False
    
    def get_agent_metadata(self, agent_key: str):
        """Get original metadata for an agent"""
        if not self.agent_loader:
            return None
        return self.agent_loader.agent_metadata.get(agent_key)
    
    def list_agents_with_metadata(self):
        """Get list of agents with their original metadata"""
        if not self.agent_loader:
            return {}
        return self.agent_loader.agent_metadata
    
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
        
        # Check circuit breaker state
        if self.circuit_breaker.state == CircuitState.OPEN:
            return self._circuit_breaker_response()
        
        start_time = datetime.now()
        
        try:
            # Safety check if enabled
            if self.safety_guardian:
                safety_result = await self.safety_guardian.validate_prompt(message, user_id)
                if not safety_result.execution_authorized:
                    return {
                        "response": f"Security validation failed: {', '.join(safety_result.violations)}",
                        "agents_used": ["safety_guardian"],
                        "turn_count": 0,
                        "duration_seconds": 0,
                        "blocked": True
                    }
            
            # Add RAG context if available (disabled for now - missing implementation)
            enhanced_message = message
            # TODO: Re-enable when AdvancedRAGProcessor is implemented
            # if self.rag_processor and context:
            #     rag_context = await self.rag_processor.get_relevant_context(
            #         message, 
            #         context.get("document_ids", [])
            #     )
            #     if rag_context:
            #         enhanced_message = f"{message}\n\nContext:\n{rag_context}"
            
            # Check if a specific agent is requested
            target_agent = context.get("target_agent") if context else None
            
            # Determine routing strategy (force single agent if target is specified)
            should_use_single = target_agent or self.router.should_use_single_agent(message)
            
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
            
            # Circuit breaker tracks success automatically
            
            return result
            
        except Exception as e:
            logger.error(f"Orchestration failed: {e}", exc_info=True)
            # Circuit breaker tracks failures automatically
            
            # Fallback response with more details
            return {
                "response": f"I encountered an issue processing your request: {str(e)}",
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
        
        # Check if a specific agent is requested
        target_agent_name = context.get("target_agent") if context else None
        best_agent = None
        
        if target_agent_name:
            logger.info(f"🔍 Looking for target agent: {target_agent_name}")
            logger.info(f"🔍 Available agents: {list(self.agents.keys())[:5]}")
            
            # Try to find the requested agent
            best_agent = self.agents.get(target_agent_name)
            if not best_agent:
                # Try with underscores converted from hyphens
                target_agent_name_alt = target_agent_name.replace('-', '_')
                best_agent = self.agents.get(target_agent_name_alt)
            
            if best_agent:
                logger.info(f"✅ Using requested agent: {best_agent.name}")
            else:
                logger.warning(f"⚠️ Requested agent not found: {target_agent_name}, available: {list(self.agents.keys())}")
                # Fall through to normal selection
        
        if not best_agent:
            # Select best agent normally
            best_agent = self.router.select_best_agent(
                message,
                list(self.agents.values()),
                context
            )
        
        if not best_agent:
            # Fallback to first available agent
            best_agent = list(self.agents.values())[0]
        
        logger.info(f"🎯 Single agent execution: {best_agent.name}")
        
        # Skip agent_intelligence for now - it's overriding agent responses
        # TODO: Fix agent_intelligence to respect agent personality
        # response = await self.agent_intelligence.generate_intelligent_response(
        #     message,
        #     context
        # )
        
        # Execute agent WITH TOOLS using AutoGen 0.7.x API
        messages = []
        try:
            from autogen_agentchat.messages import TextMessage
            task_message = TextMessage(content=message, source="user")
            
            # Run the agent - tools should now work since they're passed at creation
            result = await best_agent.run(task=task_message)
            
            # Extract response from result
            if hasattr(result, 'messages'):
                messages = result.messages
                # Get the last agent message
                final_response = ""
                for msg in reversed(messages):
                    if hasattr(msg, 'source') and msg.source == best_agent.name:
                        final_response = msg.content
                        break
                
                if not final_response:
                    # Try to get any message with content
                    for msg in reversed(messages):
                        if hasattr(msg, 'content') and msg.content:
                            final_response = msg.content
                            break
                            
                if not final_response:
                    final_response = "Agent executed but no response generated"
            else:
                final_response = str(result)
                
        except Exception as e:
            logger.error(f"Agent execution failed: {e}", exc_info=True)
            final_response = f"AGENT EXECUTION ERROR: {str(e)}"
        
        return {
            "response": final_response,
            "agents_used": [best_agent.name],
            "turn_count": 1,
            "duration_seconds": 0,  # Will be set by caller
            "routing": "single_agent",
            "cost_breakdown": estimate_cost(messages if isinstance(messages, list) else [])
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
            "cost_breakdown": estimate_cost(messages if isinstance(messages, list) else [])
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
    
    async def health(self) -> bool:
        """Check orchestrator health"""
        return self.is_initialized and self.circuit_breaker.state != CircuitState.OPEN
    
    def get_circuit_status(self) -> Dict[str, Any]:
        """Get circuit breaker status"""
        return self.circuit_breaker.get_status()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health monitoring status"""
        return self.health_monitor.get_health_status()
    
    async def shutdown(self):
        """Shutdown orchestrator and cleanup resources"""
        await self.health_monitor.stop()
        logger.info("Orchestrator shutdown complete")
    
    def _circuit_breaker_response(self) -> Dict[str, Any]:
        """Response when circuit breaker is open"""
        return {
            "response": "The system is temporarily unavailable. Please try again in a moment.",
            "agents_used": [],
            "turn_count": 0,
            "duration_seconds": 0,
            "circuit_breaker": "open",
            "circuit_status": self.circuit_breaker.get_status()
        }