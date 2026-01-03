#!/usr/bin/env python3
"""
Initialize LLM configurations in the database.
Run this script after starting the backend to seed configuration data.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.services.config_service import ConfigService
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def init_llm_configs():
    """Initialize LLM configurations from environment variables."""
    
    async with AsyncSessionLocal() as session:
        try:
            # Initialize OpenAI if API key is set
            if settings.OPENAI_API_KEY:
                logger.info("Initializing OpenAI configuration...")
                config = await ConfigService.save_provider_config(
                    session,
                    provider="openai",
                    model_name="gpt-4-turbo-preview",
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_BASE_URL or None,
                    display_name="OpenAI GPT-4 Turbo",
                    description="OpenAI's GPT-4 Turbo model for advanced reasoning",
                    priority=10,
                )
                logger.info(f"✓ OpenAI configuration saved: {config.id}")
            else:
                logger.warning("OPENAI_API_KEY not set, skipping OpenAI configuration")
            
            # Initialize Anthropic if API key is set
            if settings.ANTHROPIC_API_KEY:
                logger.info("Initializing Anthropic configuration...")
                config = await ConfigService.save_provider_config(
                    session,
                    provider="anthropic",
                    model_name="claude-3-sonnet-20240229",
                    api_key=settings.ANTHROPIC_API_KEY,
                    base_url=settings.ANTHROPIC_BASE_URL or None,
                    display_name="Anthropic Claude 3 Sonnet",
                    description="Anthropic's Claude 3 Sonnet model",
                    priority=20,
                )
                logger.info(f"✓ Anthropic configuration saved: {config.id}")
            else:
                logger.warning("ANTHROPIC_API_KEY not set, skipping Anthropic configuration")
            
            await session.commit()
            logger.info("✓ LLM configurations initialized successfully")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"Error initializing LLM configurations: {e}")
            raise


async def list_llm_configs():
    """List all LLM configurations."""
    
    async with AsyncSessionLocal() as session:
        try:
            providers = await ConfigService.list_providers(session, active_only=False)
            
            if not providers:
                logger.info("No LLM configurations found in database")
                return
            
            logger.info(f"Found {len(providers)} LLM configuration(s):")
            for config in providers:
                status = "✓ ACTIVE" if config.is_active else "✗ INACTIVE"
                logger.info(
                    f"  {status} | {config.provider.upper()} | {config.model_name} | "
                    f"Priority: {config.priority}"
                )
        except Exception as e:
            logger.error(f"Error listing LLM configurations: {e}")
            raise


async def main():
    """Main entry point."""
    logger.info("TenMuses LLM Configuration Manager")
    logger.info("=" * 50)
    
    # Initialize configurations
    await init_llm_configs()
    
    logger.info("")
    
    # List all configurations
    await list_llm_configs()
    
    logger.info("=" * 50)
    logger.info("Done!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
