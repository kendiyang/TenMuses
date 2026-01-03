#!/usr/bin/env python3
"""
清理供应商表中的旧模型，只保留 gpt-4o 和 text-embedding-3-large
删除整个 Anthropic 供应商
"""

import asyncio
import sys
from pathlib import Path

# Add parent directories to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir.parent))

from app.core.database import AsyncSessionLocal
from app.models.llm_provider import LLMProvider
from app.models.llm_model import LLMModel
from sqlalchemy import select

# Models to keep
KEEP_MODELS = ["gpt-4o", "text-embedding-3-large"]


async def cleanup_old_models():
    """Delete old models and providers."""
    async with AsyncSessionLocal() as session:
        print("🔄 Cleaning up old models and providers...")
        
        # Get all models
        stmt = select(LLMModel)
        result = await session.execute(stmt)
        all_models = result.scalars().all()
        
        deleted_count = 0
        kept_count = 0
        
        for model in all_models:
            if model.model_name not in KEEP_MODELS:
                print(f"🗑️  Deleting model: {model.display_name} ({model.model_name})")
                await session.delete(model)
                deleted_count += 1
            else:
                print(f"✅ Keeping model: {model.display_name} ({model.model_name})")
                kept_count += 1
        
        # Delete Anthropic provider (cascade will delete its models)
        stmt = select(LLMProvider).where(LLMProvider.name == "anthropic")
        result = await session.execute(stmt)
        anthropic = result.scalar_one_or_none()
        
        if anthropic:
            print(f"🗑️  Deleting provider: {anthropic.display_name}")
            await session.delete(anthropic)
        
        await session.commit()
        
        print(f"\n✨ Cleanup complete!")
        print(f"   Models kept: {kept_count}")
        print(f"   Models deleted: {deleted_count}")


if __name__ == "__main__":
    asyncio.run(cleanup_old_models())
