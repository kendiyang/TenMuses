#!/usr/bin/env python3
"""
Test script to verify LLM database configuration functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.database import AsyncSessionLocal
from app.services.config_service import ConfigService
from app.core.config import settings
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_config_operations():
    """Test all configuration operations."""
    
    logger.info("=" * 60)
    logger.info("Testing LLM Database Configuration")
    logger.info("=" * 60)
    
    async with AsyncSessionLocal() as session:
        try:
            # Test 1: Save OpenAI configuration
            logger.info("\n[Test 1] Saving OpenAI configuration...")
            
            test_openai_key = "sk-test-openai-key-12345"
            openai_config = await ConfigService.save_provider_config(
                session,
                provider="openai",
                model_name="gpt-4-turbo-preview",
                api_key=test_openai_key,
                base_url="https://api.openai.com/v1",
                display_name="Test OpenAI Config",
                description="Test configuration",
                priority=10,
            )
            await session.flush()
            logger.info(f"✓ OpenAI config saved with ID: {openai_config.id}")
            
            # Test 2: Retrieve OpenAI configuration
            logger.info("\n[Test 2] Retrieving OpenAI configuration...")
            config_dict = await ConfigService.get_openai_config(session, use_env_fallback=False)
            
            if config_dict["api_key"] == test_openai_key:
                logger.info("✓ OpenAI config retrieved successfully")
                logger.info(f"  - API Key (first 20 chars): {config_dict['api_key'][:20]}...")
                logger.info(f"  - Base URL: {config_dict['base_url']}")
            else:
                logger.error("✗ OpenAI config API key mismatch!")
                return False
            
            # Test 3: Get provider config
            logger.info("\n[Test 3] Getting OpenAI provider configuration object...")
            provider_config = await ConfigService.get_provider_config(session, "openai")
            
            if provider_config:
                logger.info(f"✓ Provider config retrieved")
                logger.info(f"  - Provider: {provider_config.provider}")
                logger.info(f"  - Model: {provider_config.model_name}")
                logger.info(f"  - Display Name: {provider_config.display_name}")
                logger.info(f"  - Is Active: {provider_config.is_active}")
                logger.info(f"  - Priority: {provider_config.priority}")
            else:
                logger.error("✗ Provider config not found!")
                return False
            
            # Test 4: List all providers
            logger.info("\n[Test 4] Listing all providers...")
            providers = await ConfigService.list_providers(session, active_only=False)
            logger.info(f"✓ Found {len(providers)} provider(s)")
            for provider in providers:
                status = "✓" if provider.is_active else "✗"
                logger.info(f"  {status} {provider.provider.upper()} - {provider.model_name}")
            
            # Test 5: Toggle provider status
            logger.info("\n[Test 5] Toggling provider status...")
            toggled_config = await ConfigService.toggle_provider(session, "openai", is_active=False)
            
            if toggled_config and not toggled_config.is_active:
                logger.info("✓ Provider disabled successfully")
            else:
                logger.error("✗ Failed to toggle provider!")
                return False
            
            # Test 6: Re-enable provider
            logger.info("\n[Test 6] Re-enabling provider...")
            toggled_config = await ConfigService.toggle_provider(session, "openai", is_active=True)
            
            if toggled_config and toggled_config.is_active:
                logger.info("✓ Provider re-enabled successfully")
            else:
                logger.error("✗ Failed to re-enable provider!")
                return False
            
            # Test 7: Save Anthropic configuration
            logger.info("\n[Test 7] Saving Anthropic configuration...")
            
            test_anthropic_key = "sk-test-anthropic-key-12345"
            anthropic_config = await ConfigService.save_provider_config(
                session,
                provider="anthropic",
                model_name="claude-3-sonnet-20240229",
                api_key=test_anthropic_key,
                base_url=None,
                display_name="Test Anthropic Config",
                description="Test Anthropic configuration",
                priority=20,
            )
            await session.flush()
            logger.info(f"✓ Anthropic config saved with ID: {anthropic_config.id}")
            
            # Test 8: Get Anthropic configuration
            logger.info("\n[Test 8] Retrieving Anthropic configuration...")
            anthropic_dict = await ConfigService.get_anthropic_config(session, use_env_fallback=False)
            
            if anthropic_dict["api_key"] == test_anthropic_key:
                logger.info("✓ Anthropic config retrieved successfully")
                logger.info(f"  - API Key (first 20 chars): {anthropic_dict['api_key'][:20]}...")
                logger.info(f"  - Base URL: {anthropic_dict.get('base_url', 'None (using default)')}")
            else:
                logger.error("✗ Anthropic config API key mismatch!")
                return False
            
            # Test 9: Update configuration
            logger.info("\n[Test 9] Updating OpenAI configuration...")
            updated_key = "sk-updated-openai-key-99999"
            updated_config = await ConfigService.save_provider_config(
                session,
                provider="openai",
                model_name="gpt-4",
                api_key=updated_key,
                base_url="https://api.openai.com/v1",
                display_name="Updated OpenAI Config",
                priority=5,
            )
            await session.flush()
            logger.info("✓ OpenAI configuration updated")
            logger.info(f"  - New model: {updated_config.model_name}")
            logger.info(f"  - New priority: {updated_config.priority}")
            
            # Test 10: Verify updated config
            logger.info("\n[Test 10] Verifying updated configuration...")
            updated_dict = await ConfigService.get_openai_config(session, use_env_fallback=False)
            
            if updated_dict["api_key"] == updated_key:
                logger.info("✓ Updated configuration verified")
            else:
                logger.error("✗ Updated configuration not applied!")
                return False
            
            # Commit all changes
            await session.commit()
            
            logger.info("\n" + "=" * 60)
            logger.info("✓ All tests passed!")
            logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            logger.error(f"\n✗ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            await session.rollback()
            return False


async def main():
    """Main entry point."""
    success = await test_config_operations()
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
