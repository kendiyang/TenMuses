#!/usr/bin/env python3
"""
Initialize LLM configurations in the database.
This script sets up LLMProvider and LLMModel tables with proper API keys and base URLs.

Usage:
    python backend/scripts/init_llm_configs.py

Environment variables:
    OPENAI_API_KEY - OpenAI API key
    OPENAI_BASE_URL - OpenAI base URL (optional, defaults to https://api.openai.com/v1)
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directories to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir.parent))

from app.core.database import AsyncSessionLocal
from app.models.llm_provider import LLMProvider
from app.models.llm_model import LLMModel
from sqlalchemy import select

# Get API key and base URL from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-wvbHvCfLHCvCf0kHEB8xTOInLVfZtDe4rNB0FiHQxgbQ0OhY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://chrisapius.top/v1")

print(f"\n📋 Using configuration:")
print(f"   API Key: {OPENAI_API_KEY[:20]}..." if len(OPENAI_API_KEY) > 20 else f"   API Key: {OPENAI_API_KEY}")
print(f"   Base URL: {OPENAI_BASE_URL}")
print()


async def init_configs():
    """Initialize LLM provider and models."""
    async with AsyncSessionLocal() as session:
        print("🔄 Initializing LLM configurations...")
        
        # Check if OpenAI provider already exists
        stmt = select(LLMProvider).where(LLMProvider.name == "openai")
        existing_provider = await session.execute(stmt)
        provider = existing_provider.scalar_one_or_none()
        
        if not provider:
            # Create OpenAI provider
            provider = LLMProvider(
                name="openai",
                display_name="OpenAI (Custom)",
                api_key_encrypted="",  # Will be set via set_api_key()
                base_url=OPENAI_BASE_URL,
                is_active=True,
                priority=1,
                description="OpenAI API provider with custom base URL",
            )
            provider.set_api_key(OPENAI_API_KEY)
            session.add(provider)
            await session.flush()  # Flush to get the provider ID
            print(f"✅ Created OpenAI provider: {provider.display_name}")
        else:
            print(f"⏭️  Provider 'openai' already exists, updating API key and base_url...")
            provider.set_api_key(OPENAI_API_KEY)
            provider.base_url = OPENAI_BASE_URL
            provider.is_active = True
        
        # Models to initialize
        models_config = [
            {
                "model_name": "gpt-4o",
                "display_name": "GPT-4o",
                "model_family": "gpt-4",
                "version": "latest",
                "context_window": 128000,
                "supports_streaming": True,
                "supports_function_calling": True,
                "supports_vision": True,
                "supports_json_mode": True,
                "cost_per_1k_input_tokens": 0.005,
                "cost_per_1k_output_tokens": 0.015,
                "is_active": True,
                "priority": 1,
                "description": "Most capable multimodal model with 128K context window",
                "tags": "latest,multimodal,high-performance",
            },
            {
                "model_name": "text-embedding-3-large",
                "display_name": "Text Embedding 3 Large",
                "model_family": "embedding",
                "version": "latest",
                "context_window": 8191,
                "supports_streaming": False,
                "supports_function_calling": False,
                "supports_vision": False,
                "supports_json_mode": False,
                "cost_per_1k_input_tokens": 0.02,
                "cost_per_1k_output_tokens": 0.0,
                "is_active": True,
                "priority": 2,
                "description": "Large embedding model with 3072 dimensions",
                "tags": "embedding,latest",
            },
        ]
        
        # Create or update models
        for model_config in models_config:
            stmt = select(LLMModel).where(
                (LLMModel.provider_id == provider.id) &
                (LLMModel.model_name == model_config["model_name"])
            )
            existing_model = await session.execute(stmt)
            model = existing_model.scalar_one_or_none()
            
            if not model:
                model = LLMModel(
                    provider_id=provider.id,
                    **model_config
                )
                session.add(model)
                print(f"✅ Created model: {model_config['display_name']}")
            else:
                print(f"⏭️  Skipping {model_config['display_name']} (already exists)")
        
        await session.commit()
        print("\n✨ Initialization complete!")
        print(f"✅ Provider configured: {provider.display_name}")
        print(f"✅ Base URL: {provider.base_url}")
        print(f"✅ API Key configured: {OPENAI_API_KEY[:20]}...")
        print(f"✅ Models configured: GPT-4o, Text Embedding 3 Large")


if __name__ == "__main__":
    asyncio.run(init_configs())
