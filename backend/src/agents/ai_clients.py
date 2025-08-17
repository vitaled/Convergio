"""
Centralized AI Client Management
Provides consistent access to AI models with proper headers, batch operations, and model selection
"""

import os
from typing import List, Dict, Any, Optional, Union, AsyncGenerator
import asyncio
import structlog
import httpx
from autogen_ext.models.openai import OpenAIChatCompletionClient

from agents.utils.config import get_settings
from api.user_keys import get_user_api_key, get_user_default_model

logger = structlog.get_logger()
settings = get_settings()


class AIClientManager:
    """Centralized manager for all AI client operations"""
    
    def __init__(self):
        self._clients = {}
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize available AI clients based on configured API keys"""
        
        # OpenAI client
        if settings.openai_api_key or os.getenv("OPENAI_API_KEY"):
            self._clients["openai"] = {
                "type": "openai",
                "api_key": settings.openai_api_key or os.getenv("OPENAI_API_KEY"),
                "base_url": settings.openai_api_base,
                "default_model": settings.default_ai_model
            }
        
        # Perplexity client (for web search)
        if os.getenv("PERPLEXITY_API_KEY"):
            self._clients["perplexity"] = {
                "type": "perplexity",
                "api_key": os.getenv("PERPLEXITY_API_KEY"),
                "base_url": "https://api.perplexity.ai",
                "default_model": "sonar"
            }
        
        # Anthropic client (if configured)
        if os.getenv("ANTHROPIC_API_KEY"):
            self._clients["anthropic"] = {
                "type": "anthropic",
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
                "base_url": "https://api.anthropic.com",
                "default_model": "claude-3-opus-20240229"
            }
    
    def get_autogen_client(
        self, 
        provider: str = "openai",
        model: Optional[str] = None,
        request: Optional[Any] = None
    ) -> OpenAIChatCompletionClient:
        """Get AutoGen-compatible client for agent operations"""
        
        # Check user-specific API key if request provided
        api_key = None
        if request:
            api_key = get_user_api_key(request, provider)
            model = model or get_user_default_model(request)
        
        # Fallback to system API key
        if not api_key and provider in self._clients:
            api_key = self._clients[provider]["api_key"]
        
        if not api_key:
            raise ValueError(f"No API key configured for provider: {provider}")
        
        # Create AutoGen client
        client_params = {
            "model": model or self._clients.get(provider, {}).get("default_model", "gpt-4o-mini"),
            "api_key": api_key,
        }
        
        # Add base URL if not standard OpenAI
        if provider != "openai" or settings.openai_api_base:
            base_url = self._clients.get(provider, {}).get("base_url")
            if base_url:
                client_params["base_url"] = base_url
        
        return OpenAIChatCompletionClient(**client_params)
    
    async def get_embedding(
        self,
        text: str,
        model: str = "text-embedding-3-small",
        provider: str = "openai"
    ) -> List[float]:
        """Get embedding vector for text"""
        
        if provider not in self._clients:
            raise ValueError(f"Provider {provider} not configured")
        
        client_config = self._clients[provider]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{client_config.get('base_url', 'https://api.openai.com')}/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {client_config['api_key']}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "input": text
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["data"][0]["embedding"]
            else:
                raise Exception(f"Embedding failed: {response.status_code}")
    
    async def batch_embeddings(
        self,
        texts: List[str],
        model: str = "text-embedding-3-small",
        provider: str = "openai",
        batch_size: int = 100
    ) -> List[List[float]]:
        """Get embeddings for multiple texts with batching"""
        
        embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # Get embeddings for batch
            batch_tasks = [
                self.get_embedding(text, model, provider)
                for text in batch
            ]
            
            batch_embeddings = await asyncio.gather(*batch_tasks)
            embeddings.extend(batch_embeddings)
            
            # Small delay between batches to avoid rate limits
            if i + batch_size < len(texts):
                await asyncio.sleep(0.1)
        
        return embeddings
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        provider: str = "openai",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        stream: bool = False,
        request: Optional[Any] = None
    ) -> Union[str, AsyncGenerator]:
        """Unified chat completion across providers"""
        
        # Get API key
        api_key = None
        if request:
            api_key = get_user_api_key(request, provider)
            model = model or get_user_default_model(request)
        
        if not api_key and provider in self._clients:
            api_key = self._clients[provider]["api_key"]
        
        if not api_key:
            raise ValueError(f"No API key for provider: {provider}")
        
        # Use default model if not specified
        if not model:
            model = self._clients.get(provider, {}).get("default_model", "gpt-4o-mini")
        
        # Build request based on provider
        if provider == "anthropic":
            return await self._anthropic_completion(
                messages, model, api_key, temperature, max_tokens, stream
            )
        elif provider == "perplexity":
            return await self._perplexity_completion(
                messages, model, api_key, temperature, max_tokens, stream
            )
        else:
            # Default to OpenAI-compatible API
            return await self._openai_completion(
                messages, model, api_key, temperature, max_tokens, stream, provider
            )
    
    async def _openai_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        api_key: str,
        temperature: float,
        max_tokens: int,
        stream: bool,
        provider: str
    ) -> Union[str, AsyncGenerator]:
        """OpenAI-compatible completion"""
        
        base_url = self._clients.get(provider, {}).get("base_url", "https://api.openai.com")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": stream
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                raise Exception(f"Chat completion failed: {response.status_code}")
    
    async def _anthropic_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        api_key: str,
        temperature: float,
        max_tokens: int,
        stream: bool
    ) -> str:
        """Anthropic Claude completion"""
        
        # Convert messages to Anthropic format
        system_message = ""
        claude_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                claude_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "system": system_message,
                    "messages": claude_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["content"][0]["text"]
            else:
                raise Exception(f"Claude completion failed: {response.status_code}")
    
    async def _perplexity_completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        api_key: str,
        temperature: float,
        max_tokens: int,
        stream: bool
    ) -> str:
        """Perplexity completion with web search"""
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.perplexity.ai/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                raise Exception(f"Perplexity completion failed: {response.status_code}")
    
    def get_available_providers(self) -> List[str]:
        """Get list of configured providers"""
        return list(self._clients.keys())
    
    def get_provider_info(self, provider: str) -> Dict[str, Any]:
        """Get information about a specific provider"""
        if provider in self._clients:
            info = self._clients[provider].copy()
            # Don't expose API key
            info.pop("api_key", None)
            return info
        return {}


# Singleton instance
_ai_client_manager = None


def get_ai_client_manager() -> AIClientManager:
    """Get singleton AI client manager"""
    global _ai_client_manager
    if _ai_client_manager is None:
        _ai_client_manager = AIClientManager()
    return _ai_client_manager


# Convenience functions
async def get_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """Convenience function for getting embeddings"""
    manager = get_ai_client_manager()
    return await manager.get_embedding(text, model)


async def batch_embeddings(texts: List[str], model: str = "text-embedding-3-small") -> List[List[float]]:
    """Convenience function for batch embeddings"""
    manager = get_ai_client_manager()
    return await manager.batch_embeddings(texts, model)


def get_autogen_client(provider: str = "openai", model: Optional[str] = None) -> OpenAIChatCompletionClient:
    """Convenience function for getting AutoGen client"""
    manager = get_ai_client_manager()
    return manager.get_autogen_client(provider, model)