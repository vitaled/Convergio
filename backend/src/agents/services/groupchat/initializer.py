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
    
    # Build client params
    # Note: temperature, top_p, max_tokens should be passed when creating agents, not to the client
    client_params = {
        "model": settings.default_ai_model,  # This should be a string like "gpt-4o-mini"
        "api_key": settings.openai_api_key,
    }
    
    # Only add model_info for non-standard models
    # gpt-4o-mini is a standard OpenAI model, so we shouldn't need model_info
    # If AutoGen doesn't recognize it, we can add model_info
    if "gpt-4o-mini" in settings.default_ai_model:
        # Try without model_info first for standard OpenAI models
        pass
    else:
        # For custom or unrecognized models, provide model info
        model_info = {
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "family": "openai",
            "structured_output": True,
        }
        client_params["model_info"] = model_info
    
    # Only add base_url if it's actually set
    if settings.openai_api_base and settings.openai_api_base.strip():
        client_params["base_url"] = settings.openai_api_base
    
    # Debug logging - show actual model value to catch quote issues
    logger.info("🔍 Creating OpenAIChatCompletionClient", 
                model=client_params.get("model"),
                model_repr=repr(client_params.get("model")),  # Show repr to see quotes
                has_base_url="base_url" in client_params,
                params_keys=list(client_params.keys()))
    
    try:
        client = OpenAIChatCompletionClient(**client_params)
    except ValueError as e:
        logger.error("❌ OpenAIChatCompletionClient creation failed", 
                    error=str(e),
                    model=client_params.get("model"))
        # Try again without optional params for debugging
        minimal_params = {
            "model": settings.default_ai_model,
            "api_key": settings.openai_api_key,
        }
        logger.info("🔄 Retrying with minimal params", params=minimal_params)
        client = OpenAIChatCompletionClient(**minimal_params)
    
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


