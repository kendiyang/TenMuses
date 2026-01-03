"""LLM Client for unified multi-provider support."""
from typing import Optional, AsyncIterator, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.llm_config import LLMConfig

class LLMClient:
    """Unified LLM client supporting multiple providers with DB-driven configuration."""
    
    def __init__(self):
        self.clients_cache: Dict[str, Any] = {}  # Cache for client instances
        self.configs_cache: Dict[str, LLMConfig] = {}  # Cache for configs
        self._initialized = False
        
        # Fallback to env vars if database is not available
        if settings.OPENAI_API_KEY:
            openai_params = {
                "api_key": settings.OPENAI_API_KEY,
                "model": "gpt-4-turbo-preview",
                "temperature": 0.7,
                "streaming": True,
            }
            if settings.OPENAI_BASE_URL:
                openai_params["base_url"] = settings.OPENAI_BASE_URL
            self.clients_cache["openai_default"] = ChatOpenAI(**openai_params)
        
        if settings.ANTHROPIC_API_KEY:
            anthropic_params = {
                "api_key": settings.ANTHROPIC_API_KEY,
                "model": "claude-3-sonnet-20240229",
                "temperature": 0.7,
                "streaming": True,
            }
            if settings.ANTHROPIC_BASE_URL:
                anthropic_params["base_url"] = settings.ANTHROPIC_BASE_URL
            self.clients_cache["anthropic_default"] = ChatAnthropic(**anthropic_params)
    
    async def _load_configs_from_db(self) -> None:
        """Load all active LLM configs from database."""
        try:
            async with AsyncSessionLocal() as session:
                from sqlalchemy import select
                stmt = select(LLMConfig).where(LLMConfig.is_active == True)
                result = await session.execute(stmt)
                configs = result.scalars().all()
                
                for config in configs:
                    cache_key = f"{config.provider}_{config.model_name}"
                    self.configs_cache[cache_key] = config
                
                self._initialized = True
        except Exception as e:
            print(f"Warning: Could not load LLM configs from database: {e}")
            # Continue with env var fallback
    
    async def ensure_initialized(self) -> None:
        """Ensure configs are loaded from database."""
        if not self._initialized:
            await self._load_configs_from_db()
    
    def _build_client(self, config: LLMConfig) -> Any:
        """Build LLM client from LLMConfig."""
        api_key = config.get_api_key()
        
        if config.provider.lower() == "openai":
            params = {
                "api_key": api_key,
                "model": config.model_name,
                "temperature": 0.7,
                "streaming": True,
            }
            if config.base_url:
                params["base_url"] = config.base_url
            return ChatOpenAI(**params)
        
        elif config.provider.lower() == "anthropic":
            params = {
                "api_key": api_key,
                "model": config.model_name,
                "temperature": 0.7,
                "streaming": True,
            }
            if config.base_url:
                params["base_url"] = config.base_url
            return ChatAnthropic(**params)
        
        else:
            raise ValueError(f"Unsupported provider: {config.provider}")
    
    def get_client(self, provider: str = "openai", model: Optional[str] = None, **kwargs) -> Any:
        """
        Get LLM client for specified provider and model.
        First tries database configs, falls back to env vars.
        """
        # If model specified, try to find in cached configs
        if model:
            cache_key = f"{provider}_{model}"
            if cache_key in self.configs_cache:
                config = self.configs_cache[cache_key]
                # Create new client instance with custom params
                client = self._build_client(config)
                if kwargs:
                    # Re-create with additional kwargs (temperature, etc.)
                    params = {
                        "api_key": config.get_api_key(),
                        "model": config.model_name,
                        "streaming": True,
                    }
                    if config.base_url:
                        params["base_url"] = config.base_url
                    params.update(kwargs)
                    
                    if config.provider.lower() == "openai":
                        return ChatOpenAI(**params)
                    else:
                        return ChatAnthropic(**params)
                return client
        
        # Fallback to default clients from env vars
        fallback_key = f"{provider}_default"
        if fallback_key in self.clients_cache:
            return self.clients_cache[fallback_key]
        
        # Error: no client available
        provider_name = "OpenAI" if provider == "openai" else "Anthropic"
        raise ValueError(f"{provider_name} API key not configured (neither in DB nor env vars)")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def invoke(
        self,
        messages: list[BaseMessage],
        provider: str = "openai",
        model: Optional[str] = None,
        **kwargs
    ) -> BaseMessage:
        """Invoke LLM with retry logic."""
        await self.ensure_initialized()
        client = self.get_client(provider, model, **kwargs)
        return await client.ainvoke(messages)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def stream(
        self,
        messages: list[BaseMessage],
        provider: str = "openai",
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream LLM response with retry logic."""
        await self.ensure_initialized()
        client = self.get_client(provider, model, **kwargs)
        
        async for chunk in client.astream(messages):
            if hasattr(chunk, 'content'):
                yield chunk.content
    
    async def get_available_configs(self) -> list[LLMConfig]:
        """Get list of available active LLM configs."""
        await self.ensure_initialized()
        return list(self.configs_cache.values())

# Global LLM client instance
llm_client = LLMClient()
