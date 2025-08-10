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
    
    # GPT-5 model info for August 2025 release
    model_info = None
    if settings.default_ai_model in ["gpt-5", "gpt-5-mini", "gpt-5-nano"]:
        # Pricing for GPT-5 models (August 2025)
        model_info = {
            "gpt-5": {
                "prompt_price_per_1k": 0.00125,  # $1.25/million input
                "completion_price_per_1k": 0.01,   # $10/million output
                "vision": True,  # GPT-5 supports vision
                "function_calling": True,  # GPT-5 supports function calling
                "json_output": True,  # GPT-5 supports JSON output
                "family": "openai"  # Model family
            },
            "gpt-5-mini": {
                "prompt_price_per_1k": 0.001,     # Estimated
                "completion_price_per_1k": 0.005,  # Estimated
                "vision": True,  # GPT-5-mini supports vision
                "function_calling": True,  # GPT-5-mini supports function calling
                "json_output": True,  # GPT-5-mini supports JSON output
                "family": "openai"  # Model family
            },
            "gpt-5-nano": {
                "prompt_price_per_1k": 0.0005,    # Estimated cheapest tier
                "completion_price_per_1k": 0.002,  # Estimated cheapest tier
                "vision": False,  # GPT-5-nano doesn't support vision
                "function_calling": True,  # GPT-5-nano supports function calling
                "json_output": True,  # GPT-5-nano supports JSON output
                "family": "openai"  # Model family
            }
        }.get(settings.default_ai_model, {
            "prompt_price_per_1k": 0.0005,
            "completion_price_per_1k": 0.002,
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "family": "openai"
        })
    
    client = OpenAIChatCompletionClient(
        model=settings.default_ai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base or None,
        model_info=model_info,
    )
    logger.info("Model client initialized", model=settings.default_ai_model)
    return client


def initialize_agent_loader(agents_directory: str) -> tuple[DynamicAgentLoader, Dict[str, AgentMetadata]]:
    loader = DynamicAgentLoader(agents_directory)
    metadata: Dict[str, AgentMetadata] = loader.scan_and_load_agents()
    logger.info("Agent loader initialized", agent_count=len(metadata))
    return loader, metadata


