"""
GraphFlow execution helpers.
"""

import json
from dataclasses import asdict
from datetime import datetime
from typing import Dict, Any, Callable
import structlog

from autogen_agentchat.teams import DiGraphBuilder, GraphFlow
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

from src.core.config import settings
from src.agents.services.agent_loader import agent_loader

from .definitions import BusinessWorkflow, WorkflowExecution

logger = structlog.get_logger()


async def create_execution_graph(workflow: BusinessWorkflow) -> DiGraphBuilder:
    builder = DiGraphBuilder()
    step_agents = {}
    for step in workflow.steps:
        agent_config = await agent_loader.get_agent_config(step.agent_name) or {
            "name": step.agent_name,
            "description": f"Agent for {step.step_type}",
            "model": "gpt-4",
        }
        client = OpenAIChatCompletionClient(model=agent_config.get("model", "gpt-4"), api_key=settings.OPENAI_API_KEY)
        agent = AssistantAgent(
            name=f"{step.step_id}_agent",
            model_client=client,
            system_message=(
                f"You are {step.agent_name} working on: {step.description}\n\n"
                f"Your role: {step.step_type}\n"
                f"Expected inputs: {', '.join(step.inputs)}\n"
                f"Expected outputs: {', '.join(step.outputs)}\n\n"
                "Provide structured, actionable responses that clearly address the required outputs."
            ),
        )
        step_agents[step.step_id] = agent
        builder.add_node(agent)
    for step in workflow.steps:
        current_agent = step_agents[step.step_id]
        for dependent_step in workflow.steps:
            if any(output in dependent_step.inputs for output in step.outputs):
                dependent_agent = step_agents[dependent_step.step_id]
                builder.add_edge(current_agent, dependent_agent)
    return builder


async def save_execution_state(redis_client, execution: WorkflowExecution) -> None:
    if not redis_client:
        return
    key = f"workflow_execution:{execution.execution_id}"
    data = asdict(execution)
    if data.get("start_time"):
        data["start_time"] = data["start_time"].isoformat()
    if data.get("end_time"):
        data["end_time"] = data["end_time"].isoformat()
    await redis_client.setex(key, 86400, json.dumps(data, default=str))


