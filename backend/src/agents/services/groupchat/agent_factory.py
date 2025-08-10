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
        )
        if agent_id == "ali_chief_of_staff":
            return CONVERGIO_TOOLS
        if agent_id in ["diana_performance_dashboard", "amy_cfo"]:
            return [BusinessIntelligenceTool(), EngagementAnalyticsTool()]
        if "data" in agent_id.lower() or "analysis" in agent_id.lower():
            return [VectorSearchTool(), TalentsQueryTool()]
    except Exception as e:
        logger.warning("Tool selection failed", agent_id=agent_id, error=str(e))
    return []


