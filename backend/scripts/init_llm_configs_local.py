#!/usr/bin/env python3
"""
Initialize LLM configurations in the database (local version).
Run this script to set up initial LLM provider configurations.

Usage:
    python backend/scripts/init_llm_configs_local.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directories to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir.parent))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.llm_config import LLMConfig
from app.core.database import Base
from sqlalchemy import select

# Default configurations to initialize
DEFAULT_CONFIGS = [
    {
        "provider": "openai",
        "model_name": "gpt-4-turbo-preview",
        "display_name": "GPT-4 Turbo",
        "api_key": "YOUR_OPENAI_API_KEY_HERE",
        "base_url": None,
        "is_active": False,  # Start inactive - user must fill in real API key
        "priority": 1,
        "description": "OpenAI's most capable model",
    },
    {
        "provider": "openai",
        "model_name": "gpt-3.5-turbo",
        "display_name": "GPT-3.5 Turbo",
        "api_key": "YOUR_OPENAI_API_KEY_HERE",
        "base_url": None,
        "is_active": False,
        "priority": 2,
        "description": "OpenAI's fast and efficient model",
    },
    {
        "provider": "anthropic",
        "model_name": "claude-3-sonnet-20240229",
        "display_name": "Claude 3 Sonnet",
        "api_key": "YOUR_ANTHROPIC_API_KEY_HERE",
        "base_url": None,
        "is_active": False,
        "priority": 3,
        "description": "Anthropic's balanced model",
    },
    {
        "provider": "anthropic",
        "model_name": "claude-3-opus-20240229",
        "display_name": "Claude 3 Opus",
        "api_key": "YOUR_ANTHROPIC_API_KEY_HERE",
        "base_url": None,
        "is_active": False,
        "priority": 4,
        "description": "Anthropic's most capable model",
    },
]


async def init_configs():
    """Initialize default LLM configurations."""
    # Use localhost instead of host.docker.internal for local development
    LOCAL_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/tenmuses"
    
    # Create local async engine
    engine = create_async_engine(
        LOCAL_DATABASE_URL,
        echo=False,
        future=True,
    )
    
    # Create local session maker
    AsyncSessionLocal = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSessionLocal() as session:
        print("🔄 Initializing LLM configurations...")
        
        for config_data in DEFAULT_CONFIGS:
            # Check if config already exists
            stmt = select(LLMConfig).where(
                (LLMConfig.provider == config_data["provider"]) &
                (LLMConfig.model_name == config_data["model_name"])
            )
            existing = await session.execute(stmt)
            if existing.scalar_one_or_none():
                print(f"⏭️  Skipping {config_data['display_name']} (already exists)")
                continue
            
            # Create new config
            config = LLMConfig(
                provider=config_data["provider"],
                model_name=config_data["model_name"],
                display_name=config_data["display_name"],
                base_url=config_data.get("base_url"),
                is_active=config_data.get("is_active", False),
                priority=config_data.get("priority", 100),
                description=config_data.get("description"),
            )
            config.set_api_key(config_data["api_key"])
            
            session.add(config)
            print(f"✅ Created {config_data['display_name']}")
        
        await session.commit()
        print("\n✨ Initialization complete!")
        print("⚠️  Note: Placeholder API keys were used. Update them via Admin UI at /llm-config")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_configs())
