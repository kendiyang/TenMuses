"""
Configuration service for reading LLM and system configs from database.
"""

from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.llm_config import LLMConfig
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class ConfigService:
    """Service for managing configurations from database."""
    
    @staticmethod
    async def get_openai_config(
        db_session: AsyncSession,
        use_env_fallback: bool = True
    ) -> Dict[str, Optional[str]]:
        """
        Get OpenAI configuration from database.
        
        Args:
            db_session: Database session
            use_env_fallback: If True, fall back to environment variables
        
        Returns:
            Dictionary with 'api_key' and 'base_url' keys
        """
        try:
            # Query for OpenAI config from database
            query = select(LLMConfig).where(
                LLMConfig.provider == "openai",
                LLMConfig.is_active == True
            ).order_by(LLMConfig.priority.asc())
            
            result = await db_session.execute(query)
            config = result.scalar_one_or_none()
            
            if config:
                logger.info(f"Loaded OpenAI config from database: {config.model_name}")
                return {
                    "api_key": config.get_api_key(),
                    "base_url": config.base_url or settings.OPENAI_BASE_URL or None,
                }
        except Exception as e:
            logger.warning(f"Error loading OpenAI config from database: {e}")
        
        # Fall back to environment variables if requested
        if use_env_fallback:
            logger.info("Using OpenAI config from environment variables")
            return {
                "api_key": settings.OPENAI_API_KEY or None,
                "base_url": settings.OPENAI_BASE_URL or None,
            }
        
        return {
            "api_key": None,
            "base_url": None,
        }
    
    @staticmethod
    async def get_anthropic_config(
        db_session: AsyncSession,
        use_env_fallback: bool = True
    ) -> Dict[str, Optional[str]]:
        """
        Get Anthropic configuration from database.
        
        Args:
            db_session: Database session
            use_env_fallback: If True, fall back to environment variables
        
        Returns:
            Dictionary with 'api_key' and 'base_url' keys
        """
        try:
            # Query for Anthropic config from database
            query = select(LLMConfig).where(
                LLMConfig.provider == "anthropic",
                LLMConfig.is_active == True
            ).order_by(LLMConfig.priority.asc())
            
            result = await db_session.execute(query)
            config = result.scalar_one_or_none()
            
            if config:
                logger.info(f"Loaded Anthropic config from database: {config.model_name}")
                return {
                    "api_key": config.get_api_key(),
                    "base_url": config.base_url or settings.ANTHROPIC_BASE_URL or None,
                }
        except Exception as e:
            logger.warning(f"Error loading Anthropic config from database: {e}")
        
        # Fall back to environment variables if requested
        if use_env_fallback:
            logger.info("Using Anthropic config from environment variables")
            return {
                "api_key": settings.ANTHROPIC_API_KEY or None,
                "base_url": settings.ANTHROPIC_BASE_URL or None,
            }
        
        return {
            "api_key": None,
            "base_url": None,
        }
    
    @staticmethod
    async def get_provider_config(
        db_session: AsyncSession,
        provider: str,
        use_env_fallback: bool = True
    ) -> Optional[LLMConfig]:
        """
        Get LLM provider configuration from database.
        
        Args:
            db_session: Database session
            provider: Provider name (e.g., 'openai', 'anthropic')
            use_env_fallback: If True, fall back to environment variables
        
        Returns:
            LLMConfig object or None
        """
        try:
            query = select(LLMConfig).where(
                LLMConfig.provider == provider.lower(),
                LLMConfig.is_active == True
            ).order_by(LLMConfig.priority.asc())
            
            result = await db_session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error loading {provider} config from database: {e}")
            return None
    
    @staticmethod
    async def list_providers(
        db_session: AsyncSession,
        active_only: bool = True
    ) -> list:
        """
        List all available LLM provider configurations.
        
        Args:
            db_session: Database session
            active_only: Only return active configs
        
        Returns:
            List of LLMConfig objects
        """
        try:
            query = select(LLMConfig)
            if active_only:
                query = query.where(LLMConfig.is_active == True)
            query = query.order_by(LLMConfig.priority.asc())
            
            result = await db_session.execute(query)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error listing providers from database: {e}")
            return []
    
    @staticmethod
    async def save_provider_config(
        db_session: AsyncSession,
        provider: str,
        model_name: str,
        api_key: str,
        base_url: Optional[str] = None,
        display_name: Optional[str] = None,
        description: Optional[str] = None,
        priority: int = 100,
    ) -> LLMConfig:
        """
        Save or update LLM provider configuration in database.
        
        Args:
            db_session: Database session
            provider: Provider name (e.g., 'openai', 'anthropic')
            model_name: Model name (e.g., 'gpt-4-turbo-preview')
            api_key: API key (will be encrypted)
            base_url: Optional custom base URL
            display_name: Display name for UI
            description: Description
            priority: Priority/order for display
        
        Returns:
            Saved LLMConfig object
        """
        try:
            # Check if config exists
            query = select(LLMConfig).where(
                LLMConfig.provider == provider.lower()
            )
            result = await db_session.execute(query)
            config = result.scalar_one_or_none()
            
            if config:
                # Update existing
                config.model_name = model_name
                config.set_api_key(api_key)
                config.base_url = base_url
                if display_name:
                    config.display_name = display_name
                if description:
                    config.description = description
                config.priority = priority
                logger.info(f"Updated {provider} config in database")
            else:
                # Create new
                config = LLMConfig(
                    provider=provider.lower(),
                    model_name=model_name,
                    display_name=display_name or f"{provider.capitalize()} Config",
                    base_url=base_url,
                    description=description,
                    priority=priority,
                )
                config.set_api_key(api_key)
                db_session.add(config)
                logger.info(f"Created {provider} config in database")
            
            await db_session.flush()
            return config
        except Exception as e:
            logger.error(f"Error saving {provider} config to database: {e}")
            raise
    
    @staticmethod
    async def toggle_provider(
        db_session: AsyncSession,
        provider: str,
        is_active: bool = True
    ) -> Optional[LLMConfig]:
        """
        Toggle provider active status.
        
        Args:
            db_session: Database session
            provider: Provider name
            is_active: Whether to activate or deactivate
        
        Returns:
            Updated LLMConfig or None
        """
        try:
            query = select(LLMConfig).where(
                LLMConfig.provider == provider.lower()
            )
            result = await db_session.execute(query)
            config = result.scalar_one_or_none()
            
            if config:
                config.is_active = is_active
                await db_session.flush()
                logger.info(f"Toggled {provider} active status to {is_active}")
                return config
        except Exception as e:
            logger.error(f"Error toggling {provider} status: {e}")
        
        return None
