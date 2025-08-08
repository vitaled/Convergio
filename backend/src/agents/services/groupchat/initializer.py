"""
GroupChat Initializer
Sets up model client and agent loader for AutoGen GroupChat.
"""

from typing import Dict
import structlog

from autogen_ext.models.openai import OpenAIChatCompletionClient

from ..agent_loader import DynamicAgentLoader, AgentMetadata
from ...utils.config import get_settings


logger = structlog.get_logger()


def initialize_model_client() -> OpenAIChatCompletionClient:
    settings = get_settings()
    client = OpenAIChatCompletionClient(
        model=settings.default_ai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base or None,
    )
    logger.info("Model client initialized", model=settings.default_ai_model)
    return client


def initialize_agent_loader(agents_directory: str) -> tuple[DynamicAgentLoader, Dict[str, AgentMetadata]]:
    loader = DynamicAgentLoader(agents_directory)
    metadata: Dict[str, AgentMetadata] = loader.scan_and_load_agents()
    logger.info("Agent loader initialized", agent_count=len(metadata))
    return loader, metadata


