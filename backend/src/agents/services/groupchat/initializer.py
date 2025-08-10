"""
GroupChat Initializer
Sets up model client and agent loader for AutoGen GroupChat.
"""

from typing import Dict
import structlog
import logging

from autogen_ext.models.openai import OpenAIChatCompletionClient

from ..agent_loader import DynamicAgentLoader, AgentMetadata
from ...utils.config import get_settings


logger = structlog.get_logger()

# Configure detailed OpenAI logging
openai_logger = logging.getLogger("openai")
openai_logger.setLevel(logging.DEBUG)
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.DEBUG)

# Create console handler for OpenAI conversations
if not openai_logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '🤖 OPENAI-%(name)s [%(levelname)s] %(asctime)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    openai_logger.addHandler(console_handler)
    httpx_logger.addHandler(console_handler)
    openai_logger.propagate = False
    httpx_logger.propagate = False


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
                "structured_output": True,  # GPT-5 supports structured output
                "family": "openai"  # Model family
            },
            "gpt-5-mini": {
                "prompt_price_per_1k": 0.001,     # Estimated
                "completion_price_per_1k": 0.005,  # Estimated
                "vision": True,  # GPT-5-mini supports vision
                "function_calling": True,  # GPT-5-mini supports function calling
                "json_output": True,  # GPT-5-mini supports JSON output
                "structured_output": True,  # GPT-5-mini supports structured output
                "family": "openai"  # Model family
            },
            "gpt-5-nano": {
                "prompt_price_per_1k": 0.0005,    # Estimated cheapest tier
                "completion_price_per_1k": 0.002,  # Estimated cheapest tier
                "vision": False,  # GPT-5-nano doesn't support vision
                "function_calling": True,  # GPT-5-nano supports function calling
                "json_output": True,  # GPT-5-nano supports JSON output
                "structured_output": True,  # GPT-5-nano supports structured output
                "family": "openai"  # Model family
            }
        }.get(settings.default_ai_model, {
            "prompt_price_per_1k": 0.0005,
            "completion_price_per_1k": 0.002,
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "structured_output": True,
            "family": "openai"
        })
    
    # Import token optimizer for model params
    from .token_optimizer import TokenOptimizer
    
    # Get optimized parameters for token reduction
    optimized_params = TokenOptimizer.optimize_model_params()
    
    client = OpenAIChatCompletionClient(
        model=settings.default_ai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base or None,
        model_info=model_info,
        temperature=optimized_params.get("temperature", 0.3),
        max_tokens=optimized_params.get("max_tokens", 150),
        top_p=optimized_params.get("top_p", 0.9),
    )
    
    # Enable detailed conversation logging
    logger.info("🔍 CONVERSATION LOGGING ENABLED", 
               model=settings.default_ai_model,
               debug_level="FULL_OPENAI_CONVERSATIONS")
    
    return client


def initialize_agent_loader(agents_directory: str) -> tuple[DynamicAgentLoader, Dict[str, AgentMetadata]]:
    loader = DynamicAgentLoader(agents_directory)
    metadata: Dict[str, AgentMetadata] = loader.scan_and_load_agents()
    logger.info("Agent loader initialized", agent_count=len(metadata))
    return loader, metadata


