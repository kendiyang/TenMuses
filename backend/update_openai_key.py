"""
更新数据库中 OpenAI provider 的 API key
"""
import asyncio
from app.core.database import AsyncSessionLocal
from app.models.llm_provider import LLMProvider
from sqlalchemy import select

async def update_openai_key():
    print("\n请输入你的 OpenAI API Key:")
    api_key = input("> ").strip()
    
    if not api_key:
        print("❌ API Key 不能为空")
        return
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(LLMProvider).where(LLMProvider.name == 'openai')
        )
        provider = result.scalar_one_or_none()
        
        if provider:
            # 使用 set_api_key 方法进行加密
            provider.set_api_key(api_key)
            provider.is_active = True
            await session.commit()
            print(f"✅ 已更新 OpenAI provider 的 API Key")
            print(f"   Provider ID: {provider.id}")
            print(f"   Base URL: {provider.base_url}")
            print(f"   Status: {'Active' if provider.is_active else 'Inactive'}")
            
            # 验证解密
            decrypted = provider.get_api_key()
            print(f"   验证: API key 长度 {len(decrypted)} 字符")
        else:
            print("❌ 未找到 OpenAI provider，请先运行初始化脚本")

if __name__ == "__main__":
    asyncio.run(update_openai_key())
