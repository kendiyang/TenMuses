#!/usr/bin/env python3
"""
清理数据库中的旧模型配置，只保留 gpt-4o 和 text-embedding-3-large

Usage:
    python backend/scripts/cleanup_old_models.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directories to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir.parent))

from app.core.database import AsyncSessionLocal
from app.models.llm_config import LLMConfig
from sqlalchemy import select, delete

# Models to keep
KEEP_MODELS = ["gpt-4o", "text-embedding-3-large"]


async def cleanup_old_models():
    """Delete all models except gpt-4o and text-embedding-3-large."""
    async with AsyncSessionLocal() as session:
        print("🔄 Cleaning up old LLM model configurations...")
        
        # Get all configs
        stmt = select(LLMConfig)
        result = await session.execute(stmt)
        all_configs = result.scalars().all()
        
        deleted_count = 0
        kept_count = 0
        
        for config in all_configs:
            if config.model_name not in KEEP_MODELS:
                print(f"🗑️  Deleting: {config.display_name} ({config.model_name})")
                await session.delete(config)
                deleted_count += 1
            else:
                print(f"✅ Keeping: {config.display_name} ({config.model_name})")
                kept_count += 1
        
        await session.commit()
        
        print(f"\n✨ Cleanup complete!")
        print(f"   Kept: {kept_count} models")
        print(f"   Deleted: {deleted_count} models")
        
        if kept_count == 0:
            print("\n⚠️  No models remaining. Run init_llm_configs.py to initialize.")


if __name__ == "__main__":
    asyncio.run(cleanup_old_models())
