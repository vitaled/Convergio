"""
🎭 Convergio - REAL Agent Orchestrator Integration
Complete integration of the original agents service with AutoGen
"""

import asyncio
import structlog
from typing import Any, Dict, Optional, List

from core.config import get_settings
from core.redis import get_redis_client
from agents.orchestrators.unified import UnifiedOrchestrator
from agents.orchestrators.base import OrchestratorRegistry
from agents.services.redis_state_manager import RedisStateManager  
from agents.services.cost_tracker import CostTracker
from agents.memory.autogen_memory_system import AutoGenMemorySystem
from agents.observability.otel_observer import OtelAutoGenObserver

logger = structlog.get_logger()


class RealAgentOrchestrator:
    """REAL Agent Orchestrator using the complete original agents system."""
    
    def __init__(self):
        """Initialize with REAL components."""
        self.settings = get_settings()
        
        # Use the UnifiedOrchestrator as the primary orchestrator
        self.state_manager: RedisStateManager = None
        self.cost_tracker: CostTracker = None
        self.orchestrator: UnifiedOrchestrator = None
        self.memory_system: AutoGenMemorySystem = None
        self.registry = OrchestratorRegistry()
        # Use absolute path for agent definitions
        import os
        backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.agents_directory: str = os.path.join(backend_dir, "src", "agents", "definitions")
        
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the REAL agent system."""
        try:
            logger.info("🚀 Initializing REAL Agent System (Complete Migration)")
            
            # Ensure Redis is initialized
            try:
                redis_client = get_redis_client()
            except RuntimeError as e:
                if "Redis not initialized" in str(e):
                    logger.info("🔄 Redis not initialized, initializing now...")
                    from core.redis import init_redis
                    await init_redis()
                    redis_client = get_redis_client()
                else:
                    raise
            
            redis_url = self.settings.REDIS_URL
            
            # Initialize REAL components from agents service
            self.state_manager = RedisStateManager(redis_url)
            self.cost_tracker = CostTracker(self.state_manager)
            
            # Initialize Memory System with Redis persistence  
            self.memory_system = AutoGenMemorySystem()
            # Memory system is initialized in constructor - no initialize() method
            
            # Initialize the UnifiedOrchestrator (no kwargs supported in __init__)
            self.orchestrator = UnifiedOrchestrator()
            
            # Initialize services
            await self.state_manager.initialize()
            # UnifiedOrchestrator requires agents_dir on initialize
            init_ok = await self.orchestrator.initialize(
                agents_dir=self.agents_directory,
                enable_rag=True,
                enable_safety=True
            )
            if not init_ok:
                raise RuntimeError("UnifiedOrchestrator failed to initialize")
            
            self._initialized = True
            logger.info("✅ REAL Agent System initialized successfully")
            
        except Exception as e:
            logger.error("❌ Failed to initialize REAL Agent System", error=str(e))
            raise
    
    async def orchestrate_conversation(
        self,
        message: str,
        user_id: str,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Orchestrate conversation using REAL agent system."""
        
        if not self._initialized:
            await self.initialize()
        
        logger.info("🎭 REAL Agent Conversation",
                   user_id=user_id,
                   message_preview=message[:100])
        
        # Use the UnifiedOrchestrator API
        result = await self.orchestrator.orchestrate(
            message=message,
            user_id=user_id,
            conversation_id=conversation_id,
            context=context or {}
        )
        
        logger.info("✅ REAL Agent Conversation completed",
                   agents_used=len(result.get("agents_used", [])),
                   cost_usd=result.get("cost_breakdown", {}).get("total_cost_usd", 0))
        
        return result
    
    async def process_agent_message(
        self,
        agent_name: str,
        message: str,
        conversation_id: Optional[str] = None,
        debug_mode: bool = False
    ) -> Dict[str, Any]:
        """Process message with specific agent (for debugging)."""
        
        if not self._initialized:
            await self.initialize()
            
        logger.info("🐛 Processing agent message", 
                   agent_name=agent_name, 
                   debug_mode=debug_mode,
                   message_preview=message[:50])
        
        if debug_mode:
            # Enhanced logging for debug mode
            logger.info("🔍 Debug mode enabled - detailed agent interaction logging")
        
        # Use orchestrator to handle the specific agent interaction
        # The orchestrator will route to the appropriate agent
        result = await self.orchestrator.orchestrate(
            message=f"Agent {agent_name}: {message}",
            user_id="debug_user",
            conversation_id=conversation_id,
            context={"debug_mode": debug_mode, "target_agent": agent_name}
        )
        
        return {
            "agent_name": agent_name,
            "conversation_id": conversation_id,
            "debug_mode": debug_mode,
            "result": result,
            "agents_used": result.get("agents_used", []),
            "cost": result.get("cost_breakdown", {})
        }
    
    async def get_available_agents(self) -> Dict[str, Any]:
        """Get all available agents from REAL system."""
        if not self._initialized:
            await self.initialize()
        
        agent_names = self.orchestrator.list_agents()
        return {"agents": agent_names, "total": len(agent_names)}
    
    def list_agents(self) -> List[str]:
        """List all agent IDs."""
        if not self._initialized or not self.orchestrator:
            return []
        return self.orchestrator.list_agents()
    
    def get_agent(self, agent_id: str):
        """Get a specific agent by ID."""
        if not self._initialized or not self.orchestrator:
            return None
        return self.orchestrator.agents.get(agent_id)
    
    def get_agent_metadata(self, agent_key: str):
        """Get original metadata for an agent - delegates to UnifiedOrchestrator."""
        if not self._initialized or not self.orchestrator:
            return None
        return self.orchestrator.get_agent_metadata(agent_key)
    
    def list_agents_with_metadata(self):
        """Get list of agents with their original metadata - delegates to UnifiedOrchestrator."""
        if not self._initialized or not self.orchestrator:
            return {}
        return self.orchestrator.list_agents_with_metadata()
    
    async def reload_agents(self) -> Dict[str, Any]:
        """Reload agents in REAL system."""
        if not self._initialized:
            await self.initialize()
        
        # Reinitialize the unified orchestrator to reload agent definitions
        ok = await self.orchestrator.initialize(agents_dir=self.agents_directory, enable_rag=True, enable_safety=True)
        return {"reloaded": ok}
    
    def is_healthy(self) -> bool:
        """Check if REAL system is healthy."""
        return (self._initialized and 
                self.orchestrator is not None and
                (self.orchestrator.is_healthy() if hasattr(self.orchestrator, "is_healthy") else True))
    
    async def close(self) -> None:
        """Close REAL system."""
        if self.state_manager:
            await self.state_manager.close()


# Global REAL orchestrator instance
real_orchestrator = RealAgentOrchestrator()


async def initialize_agents() -> None:
    """Initialize the REAL agent system."""
    await real_orchestrator.initialize()


async def get_agent_orchestrator() -> RealAgentOrchestrator:
    """Get the REAL agent orchestrator."""
    if not real_orchestrator._initialized:
        await real_orchestrator.initialize()
    return real_orchestrator


# Backward-compatibility shim for tests that import OrchestratorAgent
class OrchestratorAgent:  # noqa: D401 - compatibility shim
    """Minimal shim to satisfy legacy tests; delegates to RealAgentOrchestrator."""
    def __init__(self):
        self._real = real_orchestrator
    
    async def initialize(self):
        await self._real.initialize()
    
    async def run(self, message: str, user_id: str = "test_user", context: Optional[Dict[str, Any]] = None):
        return await self._real.orchestrate_conversation(message=message, user_id=user_id, context=context or {})

    # Legacy method name expected by tests
    async def coordinate(self, message: str, context: Optional[Dict[str, Any]] = None):
        result = await self._real.orchestrate_conversation(message=message, user_id="test_user", context=context or {})
        # Normalize minimal legacy shape
        if isinstance(result, dict) and ("messages" in result or "content" in result):
            return result
        return {"content": str(result)}


# Backward-compatibility shim for tests that patch autogen ConversableAgent in this module
class ConversableAgent:  # minimal shim for patch target in tests
    def __init__(self, *args, **kwargs):
        pass
    async def initiate_chat(self, *args, **kwargs):
        return {"messages": [{"content": "", "role": "assistant"}], "cost": {"total": 0}, "agent": "shim"}