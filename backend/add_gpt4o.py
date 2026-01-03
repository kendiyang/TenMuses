"""
添加 gpt-4o 模型配置
"""
import asyncio
from app.core.database import AsyncSessionLocal
from app.models.llm_provider import LLMProvider
from app.models.llm_model import LLMModel
from sqlalchemy import select

async def add_gpt4o():
    async with AsyncSessionLocal() as session:
        # Get OpenAI provider
        result = await session.execute(
            select(LLMProvider).where(LLMProvider.name == 'openai')
        )
        provider = result.scalar_one_or_none()
        
        if not provider:
            print("❌ OpenAI provider not found")
            return
        
        # Check if gpt-4o already exists
        result = await session.execute(
            select(LLMModel).where(LLMModel.model_name == 'gpt-4o')
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print("gpt-4o model already exists, updating to active...")
            existing.is_active = True
            await session.commit()
            print("✅ gpt-4o model activated")
            return
        
        # Create gpt-4o model
        model = LLMModel(
            provider_id=provider.id,
            model_name='gpt-4o',
            display_name='GPT-4o',
            model_family='GPT-4',
            version='gpt-4o',
            default_temperature=0.7,
            default_max_tokens=4096,
            default_top_p=1.0,
            context_window=128000,
            supports_streaming=True,
            supports_function_calling=True,
            supports_vision=True,
            supports_json_mode=True,
            is_active=True,
            priority=1
        )
        session.add(model)
        await session.commit()
        print(f"✅ Created gpt-4o model")
        print(f"   Model ID: {model.id}")
        print(f"   Provider: {provider.name}")

if __name__ == "__main__":
    asyncio.run(add_gpt4o())
