"""
Agent Factory
Creates AssistantAgent instances with appropriate tools and system messages.
"""

from typing import Dict
import structlog

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

from ..agent_loader import DynamicAgentLoader, AgentMetadata
from .agent_instructions import optimize_agent_prompt


logger = structlog.get_logger()


def create_business_agents(
    loader: DynamicAgentLoader,
    model_client: OpenAIChatCompletionClient,
) -> Dict[str, AssistantAgent]:
    agents: Dict[str, AssistantAgent] = {}

    for agent_id, metadata in loader.agent_metadata.items():
        original_prompt = loader._build_system_message(metadata)
        # Optimize prompts for conciseness
        system_message = optimize_agent_prompt(original_prompt)
        tools = _select_tools_for_agent(agent_id)
        agent = AssistantAgent(
            name=agent_id,
            model_client=model_client,
            system_message=system_message,
            tools=tools,
        )
        agents[agent_id] = agent
    logger.info("Business agents created with optimized prompts", count=len(agents))
    return agents


def _select_tools_for_agent(agent_id: str):
    try:
        from ...tools.convergio_tools import (
            CONVERGIO_TOOLS,
            BusinessIntelligenceTool,
            EngagementAnalyticsTool,
            VectorSearchTool,
            TalentsQueryTool,
            WebSearchTool,
            WebBrowseTool,
        )
        
        # Ali gets ALL tools including web access
        if agent_id == "ali_chief_of_staff":
            return CONVERGIO_TOOLS
        
        # Project Manager needs full Convergio database access
        if agent_id == "davide-project-manager":
            return [
                BusinessIntelligenceTool(), 
                EngagementAnalyticsTool(),
                TalentsQueryTool(),
                VectorSearchTool(),
                WebSearchTool(),  # For project research
            ]
        
        # Financial agents need web search for market data
        if agent_id in ["diana_performance_dashboard", "amy_cfo"]:
            return [
                BusinessIntelligenceTool(), 
                EngagementAnalyticsTool(),
                TalentsQueryTool(),  # Access to talent data
                WebSearchTool(),  # For current market data
            ]
        
        # Market/Strategy agents need web search and database access
        if any(term in agent_id.lower() for term in ["market", "strategy", "mckinsey", "investor"]):
            return [
                BusinessIntelligenceTool(), 
                VectorSearchTool(),
                TalentsQueryTool(),  # Access to talent data
                WebSearchTool(),  # For market research
                WebBrowseTool(),  # For reading articles
            ]
        
        # Data/Analysis agents get full database access
        if "data" in agent_id.lower() or "analysis" in agent_id.lower():
            return [
                BusinessIntelligenceTool(), 
                EngagementAnalyticsTool(),
                VectorSearchTool(), 
                TalentsQueryTool(),
                WebSearchTool(),  # For research
            ]
        
        # Technical agents need documentation and database access
        if any(term in agent_id.lower() for term in ["tech", "architect", "security", "dev"]):
            return [
                BusinessIntelligenceTool(), 
                VectorSearchTool(),
                TalentsQueryTool(),  # Access to talent data
                WebSearchTool(),  # For technical docs
                WebBrowseTool(),  # For reading documentation
            ]
        
        # Default: Give all agents basic database access + web search
        return [
            TalentsQueryTool(),  # All agents can query talent data
            VectorSearchTool(),  # All agents can search knowledge base
            WebSearchTool()      # All agents can search web
        ]
        
    except Exception as e:
        logger.warning("Tool selection failed", agent_id=agent_id, error=str(e))
    return []


