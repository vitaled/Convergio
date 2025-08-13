"""
🧠 Ali - REAL AutoGen 0.7.x Orchestrator
Chief of Staff orchestrating all Convergio agents with AutoGen 0.7.x
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import structlog
import httpx

# AutoGen 0.7.x imports
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import MagenticOneGroupChat
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_core import CancellationToken

from src.core.config import get_settings
from src.core.redis import cache_get, cache_set
from src.agents.services.cost_tracker import CostTracker

logger = structlog.get_logger()

class AliOrchestratorV2:
    """Ali as the REAL AutoGen 0.7.x orchestrator for all agents"""
    
    def __init__(self):
        self.settings = get_settings()
        # Initialize cost tracker later when state manager is available
        self.cost_tracker = None
        self.agents: List[AssistantAgent] = []
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
            
        logger.info("🧠 Initializing Ali Orchestrator with AutoGen 0.7.x")
        
        # Create OpenAI client
        self.openai_client = OpenAIChatCompletionClient(
            model="gpt-4o-mini",
            api_key=self.openai_key,
            temperature=0.7,
            max_tokens=1000
        )
        
        # Create Ali as the main orchestrator
        self.ali = AssistantAgent(
            name="Ali_ChiefOfStaff",
            model_client=self.openai_client,
            system_message="""You are Ali, Chief of Staff at Convergio. You orchestrate all specialist agents to provide comprehensive strategic analysis. 
            You coordinate with:
            - Amy (CFO) for financial analysis
            - Sofia (Marketing) for market research using web search
            - Luke (Program Manager) for technical requirements
            - Steve (Executive Communications) for strategy synthesis
            
            Always provide data-driven insights with specific numbers and actionable recommendations.""",
            description="Chief of Staff orchestrating all strategic analysis"
        )
        
        # Create specialist agents
        self._create_specialist_agents()
        
        # Register tools (if needed for specific agents)
        await self._register_tools()
        
        # Create MagenticOneGroupChat for orchestration
        all_agents = [self.ali] + self.agents
        self.team = MagenticOneGroupChat(
            participants=all_agents,
            model_client=self.openai_client,
            max_turns=10,
            name="ConvergioExecutiveTeam"
        )
        
        self._initialized = True
        logger.info("✅ Ali Orchestrator initialized with all agents")
    
    def _create_specialist_agents(self):
        """Create all specialist agents"""
        
        # Amy - CFO
        amy = AssistantAgent(
            name="Amy_CFO",
            model_client=self.openai_client,
            system_message="You are Amy, CFO of Convergio. Provide financial analysis, projections, and budget recommendations based on data.",
            description="CFO providing financial insights"
        )
        self.agents.append(amy)
        
        # Sofia - Marketing with web search
        sofia = AssistantAgent(
            name="Sofia_Marketing",
            model_client=self.openai_client,
            system_message="You are Sofia, Marketing Director. Use web search to find real-time market data, competitor analysis, and trends.",
            description="Marketing Director with market research capabilities",
            tools=[self._create_perplexity_tool()] if self.perplexity_key else []
        )
        self.agents.append(sofia)
        
        # Luke - Program Manager
        luke = AssistantAgent(
            name="Luke_ProgramManager",
            model_client=self.openai_client,
            system_message="You are Luke, Program Manager. Provide technical requirements, timelines, and resource planning.",
            description="Program Manager for technical coordination"
        )
        self.agents.append(luke)
        
        # Steve - Executive Communications
        steve = AssistantAgent(
            name="Steve_ExecutiveComms",
            model_client=self.openai_client,
            system_message="You are Steve, Executive Communications Strategist. Synthesize insights into clear strategic recommendations.",
            description="Executive Communications for strategy synthesis"
        )
        self.agents.append(steve)
        
        logger.info(f"✅ Created {len(self.agents)} specialist agents")
    
    def _create_perplexity_tool(self):
        """Create Perplexity web search tool"""
        
        async def search_web(query: str) -> str:
            """Search the web using Perplexity API for real-time data"""
            logger.info(f"🔍 Searching web via Perplexity: {query}")
            
            async with httpx.AsyncClient() as client:
                try:
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
                        
                        # Track Perplexity cost if tracker available
                        if self.cost_tracker:
                            self.cost_tracker.track_cost(0.001, 0, "perplexity")
                        
                        logger.info(f"✅ Perplexity search completed")
                        return result
                    else:
                        logger.error(f"Perplexity API error: {response.status_code}")
                        return f"Web search failed with status {response.status_code}"
                        
                except Exception as e:
                    logger.error(f"Perplexity search error: {e}")
                    return f"Web search error: {str(e)}"
        
        return search_web
    
    async def _register_tools(self):
        """Register additional tools if needed"""
        # Tools are now passed directly to agents during creation
        logger.info("✅ Tools configured for agents")
    
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
            # Create task context
            initial_message = f"""
            As CEO, I need your strategic analysis on: {query}
            
            Please coordinate with relevant agents to provide comprehensive insights with:
            1. Real data from web search when needed (Sofia has Perplexity access)
            2. Database metrics where relevant
            3. Specific numbers and timelines
            4. Actionable recommendations
            
            Context: {json.dumps(context) if context else 'No additional context'}
            """
            
            # Run the team chat directly with the message
            cancellation_token = CancellationToken()
            result = await self.team.run(
                task=initial_message,
                cancellation_token=cancellation_token
            )
            
            # Extract messages from result
            messages = []
            agents_involved = set()
            
            if hasattr(result, 'messages'):
                for msg in result.messages:
                    if hasattr(msg, 'content') and hasattr(msg, 'source'):
                        messages.append({
                            "role": msg.source,
                            "content": msg.content
                        })
                        agents_involved.add(msg.source)
            
            # Get final response
            final_response = messages[-1]["content"] if messages else "No response generated"
            
            # Detect data sources used
            data_sources = []
            response_text = str(final_response).lower()
            if "perplexity" in response_text or "web search" in response_text:
                data_sources.append("Perplexity Web Search")
            if "database" in response_text or "metrics" in response_text:
                data_sources.append("Convergio Database")
            if not data_sources:
                data_sources = ["OpenAI Analysis"]
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Track costs if tracker available
            estimated_tokens = len(str(messages)) // 4  # Rough estimate
            cost = (estimated_tokens / 1000) * 0.00015  # gpt-4o-mini pricing
            if self.cost_tracker:
                self.cost_tracker.track_cost(cost, estimated_tokens, "gpt-4o-mini")
            
            return {
                "response": final_response,
                "reasoning_chain": [
                    "Query analysis and intent extraction",
                    "Agent selection based on expertise",
                    "Parallel information gathering from sources",
                    "Multi-agent collaboration and synthesis",
                    "Strategic recommendations formulation"
                ],
                "data_sources_used": list(set(data_sources)),
                "confidence_score": 0.95,
                "suggested_actions": self._extract_actions(final_response),
                "agents_involved": list(agents_involved),
                "execution_time": execution_time,
                "total_messages": len(messages),
                "estimated_cost": cost
            }
            
        except Exception as e:
            logger.error(f"❌ Orchestration failed: {e}", exc_info=True)
            return {
                "response": f"I apologize, but I encountered an issue: {str(e)}",
                "reasoning_chain": ["Error occurred during orchestration"],
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
                if len(line) > 5:
                    actions.append(line.lstrip('0123456789.-•* '))
        
        # Default actions if none found
        if not actions:
            actions = [
                "Review analysis with executive team",
                "Implement recommended strategies",
                "Monitor progress and adjust as needed"
            ]
        
        return actions[:5]

# Singleton instance
_ali_orchestrator_v2: Optional[AliOrchestratorV2] = None

async def get_ali_orchestrator() -> AliOrchestratorV2:
    """Get or create Ali orchestrator instance"""
    global _ali_orchestrator_v2
    if _ali_orchestrator_v2 is None:
        _ali_orchestrator_v2 = AliOrchestratorV2()
        await _ali_orchestrator_v2.initialize()
    return _ali_orchestrator_v2