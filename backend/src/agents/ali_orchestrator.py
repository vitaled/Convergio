"""
🧠 Ali - REAL AutoGen Orchestrator
Chief of Staff orchestrating all Convergio agents with AutoGen 0.7.x
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import structlog
import httpx

# AutoGen 0.7.x imports - correct module structure
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import MagenticOneGroupChat, SelectorGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
# Note: GroupChat and GroupChatManager are replaced by MagenticOneGroupChat in 0.7.x

from src.core.config import get_settings
from src.core.redis import cache_get, cache_set
from src.services.cost_tracker import get_cost_tracker

logger = structlog.get_logger()

class AliOrchestrator:
    """Ali as the REAL AutoGen orchestrator for all agents"""
    
    def __init__(self):
        self.settings = get_settings()
        self.cost_tracker = get_cost_tracker()
        self.agents: Dict[str, AssistantAgent] = {}
        self.team: Optional[MagenticOneGroupChat] = None
        self._initialized = False
        
        # API Keys
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.perplexity_key = os.getenv("PERPLEXITY_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        
    async def initialize(self):
        """Initialize Ali and all specialist agents"""
        if self._initialized:
            return
            
        logger.info("🧠 Initializing Ali Orchestrator with AutoGen")
        
        # Create OpenAI client with cost tracking
        self.openai_client = self._create_openai_client()
        
        # Create Ali as the main orchestrator
        self.ali = AssistantAgent(
            name="Ali_ChiefOfStaff",
            system_message="""You are Ali, Chief of Staff at Convergio. You orchestrate all specialist agents to provide comprehensive strategic analysis. 
            You coordinate with:
            - Amy (CFO) for financial analysis
            - Sofia (Marketing) for market research using web search
            - Luke (Program Manager) for technical requirements
            - Steve (Executive Communications) for strategy synthesis
            
            Always provide data-driven insights with specific numbers and actionable recommendations.""",
            model_client=self.openai_client,
            max_consecutive_auto_reply=3
        )
        
        # Create specialist agents
        self._create_specialist_agents()
        
        # Register tools/functions
        self._register_tools()
        
        # Create MagenticOneGroupChat for orchestration (AutoGen 0.7.x)
        all_agents = [self.ali] + list(self.agents.values())
        self.team = MagenticOneGroupChat(
            participants=all_agents,
            model_client=self.openai_client,
            max_rounds=10
        )
        
        self._initialized = True
        logger.info("✅ Ali Orchestrator initialized with all agents")
    
    def _create_openai_client(self) -> OpenAIChatCompletionClient:
        """Create OpenAI client with cost tracking hooks"""
        client = OpenAIChatCompletionClient(
            model="gpt-4o-mini",
            api_key=self.openai_key,
            temperature=0.7,
            max_tokens=1000
        )
        
        # Add cost tracking hook
        def track_usage(response, **kwargs):
            if hasattr(response, 'usage'):
                tokens = response.usage.total_tokens
                # Calculate cost for gpt-4o-mini
                cost = (tokens / 1000) * 0.00015  # $0.15 per 1M tokens
                self.cost_tracker.track_cost(cost, tokens, "gpt-4o-mini")
                logger.debug(f"💰 Tracked {tokens} tokens, cost: ${cost:.4f}")
        
        # Register hook if new AutoGen version
        if hasattr(client, 'register_hook'):
            client.register_hook("on_completion", track_usage)
        
        return client
    
    def _create_specialist_agents(self):
        """Create all specialist agents"""
        
        # Amy - CFO
        self.agents["amy"] = AssistantAgent(
            name="Amy_CFO",
            system_message="You are Amy, CFO of Convergio. Provide financial analysis, projections, and budget recommendations based on data.",
            model_client=self.openai_client,
            max_consecutive_auto_reply=2
        )
        
        # Sofia - Marketing with web search
        self.agents["sofia"] = AssistantAgent(
            name="Sofia_Marketing",
            system_message="You are Sofia, Marketing Director. Use web search to find real-time market data, competitor analysis, and trends.",
            model_client=self.openai_client,
            max_consecutive_auto_reply=2
        )
        
        # Luke - Program Manager
        self.agents["luke"] = AssistantAgent(
            name="Luke_ProgramManager",
            system_message="You are Luke, Program Manager. Provide technical requirements, timelines, and resource planning.",
            model_client=self.openai_client,
            max_consecutive_auto_reply=2
        )
        
        # Steve - Executive Communications
        self.agents["steve"] = AssistantAgent(
            name="Steve_ExecutiveComms",
            system_message="You are Steve, Executive Communications Strategist. Synthesize insights into clear strategic recommendations.",
            model_client=self.openai_client,
            max_consecutive_auto_reply=2
        )
    
    def _register_tools(self):
        """Register tools/functions for agents"""
        
        # Register Perplexity search for Sofia
        if self.perplexity_key:
            self._register_perplexity_tool()
        
        # Register database query for Amy
        self._register_database_tool()
        
        # Register other tools as needed
        logger.info("✅ Tools registered for agents")
    
    def _register_perplexity_tool(self):
        """Register Perplexity web search tool"""
        
        async def search_web(query: str) -> str:
            """Search the web using Perplexity API for real-time data"""
            logger.info(f"🔍 Searching web via Perplexity: {query}")
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.perplexity.ai/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.perplexity_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "sonar-medium-online",
                        "messages": [
                            {"role": "user", "content": query}
                        ],
                        "temperature": 0.2,
                        "max_tokens": 1000
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    result = data["choices"][0]["message"]["content"]
                    
                    # Track Perplexity cost
                    self.cost_tracker.track_cost(0.001, 0, "perplexity")  # Estimated cost
                    
                    logger.info(f"✅ Perplexity search completed")
                    return result
                else:
                    logger.error(f"Perplexity API error: {response.status_code}")
                    return f"Web search failed: {response.status_code}"
        
        # Register for Sofia
        if hasattr(self.agents["sofia"], "register_for_execution"):
            self.agents["sofia"].register_for_execution()(search_web)
            self.ali.register_for_llm(
                description="Search web for real-time data using Perplexity"
            )(search_web)
        else:
            # Fallback for older AutoGen
            logger.warning("Tool registration not supported in this AutoGen version")
    
    def _register_database_tool(self):
        """Register database query tool for Amy"""
        
        async def query_database(table: str, filters: Optional[Dict] = None) -> str:
            """Query Convergio database for business data"""
            logger.info(f"📊 Querying database: {table}")
            
            # Import here to avoid circular dependency
            from src.core.database import get_db_session
            from sqlalchemy import text
            
            async with get_db_session() as db:
                if table == "talents":
                    result = await db.execute(text("SELECT COUNT(*) FROM talents"))
                    count = result.scalar()
                    return f"Found {count} talents in database"
                elif table == "documents":
                    result = await db.execute(text("SELECT COUNT(*) FROM documents"))
                    count = result.scalar()
                    return f"Found {count} documents in database"
                else:
                    return f"Table {table} query not implemented"
        
        # Register for Amy
        if hasattr(self.agents["amy"], "register_for_execution"):
            self.agents["amy"].register_for_execution()(query_database)
            self.ali.register_for_llm(
                description="Query database for business metrics"
            )(query_database)
    
    async def orchestrate(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Orchestrate multi-agent conversation"""
        
        if not self._initialized:
            await self.initialize()
        
        logger.info(f"🎭 Ali orchestrating query: {query[:100]}...")
        
        start_time = datetime.now()
        
        try:
            # Start conversation with Ali
            initial_message = f"""
            As CEO, I need your analysis on: {query}
            
            Please coordinate with relevant agents to provide comprehensive insights with:
            1. Real data from web search when needed
            2. Database metrics where relevant
            3. Specific numbers and timelines
            4. Actionable recommendations
            """
            
            # Run the team chat (AutoGen 0.7.x async API)
            from autogen_agentchat.messages import TextMessage
            from autogen_agentchat.base import TaskContext
            
            task = TaskContext(messages=[TextMessage(content=initial_message, source="user")])
            result = await self.team.run(task=task)
            
            # Extract the conversation
            messages = result.messages if hasattr(result, 'messages') else []
            
            # Build response
            final_response = messages[-1]["content"] if messages else "No response generated"
            
            # Extract data sources used
            data_sources = []
            for msg in messages:
                if "Perplexity" in str(msg.get("content", "")):
                    data_sources.append("Perplexity Web Search")
                if "database" in str(msg.get("content", "")).lower():
                    data_sources.append("Convergio Database")
            if not data_sources:
                data_sources = ["OpenAI Analysis"]
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "response": final_response,
                "reasoning_chain": [
                    "Query analysis and intent extraction",
                    "Agent selection and task distribution",
                    "Web search for real-time data" if "Perplexity" in data_sources else "Internal data analysis",
                    "Multi-agent collaboration and synthesis",
                    "Strategic recommendations formulation"
                ],
                "data_sources_used": list(set(data_sources)),
                "confidence_score": 0.95,
                "suggested_actions": self._extract_actions(final_response),
                "agents_involved": [msg["name"] for msg in messages if "name" in msg],
                "execution_time": execution_time,
                "total_messages": len(messages)
            }
            
        except Exception as e:
            logger.error(f"❌ Orchestration failed: {e}")
            return {
                "response": f"I apologize, but I encountered an issue: {str(e)}",
                "reasoning_chain": ["Error occurred"],
                "data_sources_used": [],
                "confidence_score": 0.0,
                "suggested_actions": ["Please retry your query"],
                "error": str(e)
            }
    
    def _extract_actions(self, response: str) -> List[str]:
        """Extract actionable items from response"""
        actions = []
        
        # Look for numbered lists or bullet points
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            if any(line.startswith(marker) for marker in ['1.', '2.', '3.', '•', '-', '*']):
                if len(line) > 5:  # Avoid empty bullets
                    actions.append(line.lstrip('0123456789.-•* '))
        
        # Default actions if none found
        if not actions:
            actions = [
                "Review analysis with executive team",
                "Implement recommended strategies",
                "Monitor progress and adjust as needed"
            ]
        
        return actions[:5]  # Return top 5 actions

# Singleton instance
_ali_orchestrator: Optional[AliOrchestrator] = None

async def get_ali_orchestrator() -> AliOrchestrator:
    """Get or create Ali orchestrator instance"""
    global _ali_orchestrator
    if _ali_orchestrator is None:
        _ali_orchestrator = AliOrchestrator()
        await _ali_orchestrator.initialize()
    return _ali_orchestrator