#!/usr/bin/env python3
"""
Simple test to validate LLM API connectivity.
Reads configuration from database and tests API connection.
"""

import asyncio
import sys
import os
from pathlib import Path

# Ensure JWT_SECRET_KEY is set to match .env
os.environ.setdefault('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.llm_provider import LLMProvider
from app.models.llm_model import LLMModel
from openai import AsyncOpenAI


async def main():
    print("\n" + "="*70)
    print("🧪 LLM API 连接测试")
    print("="*70 + "\n")
    
    # Get configuration from database
    print("📍 步骤 1: 从数据库读取配置...")
    async with AsyncSessionLocal() as session:
        # Get OpenAI provider
        stmt = select(LLMProvider).where(LLMProvider.name == "openai")
        result = await session.execute(stmt)
        provider = result.scalar_one_or_none()
        
        if not provider:
            print("❌ 错误: 未找到 OpenAI 供应商")
            return False
        
        print(f"✓ 供应商: {provider.display_name}")
        print(f"✓ Base URL: {provider.base_url}")
        
        # Decrypt API key
        try:
            api_key = provider.get_api_key()
            print(f"✓ API Key: {api_key[:20]}...")
        except Exception as e:
            print(f"❌ 错误: 无法解密 API 密钥: {e}")
            return False
        
        # Get gpt-4o model
        stmt = select(LLMModel).where(
            LLMModel.provider_id == provider.id,
            LLMModel.model_name == "gpt-4o"
        )
        result = await session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            print("❌ 错误: 未找到 gpt-4o 模型")
            return False
        
        print(f"✓ 模型: {model.display_name} ({model.model_name})")
        print()
    
    # Test API connection
    print("📍 步骤 2: 测试 API 连接...")
    try:
        # Create AsyncOpenAI client with proper SSL verification
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=provider.base_url,
            http_client=None  # Use default HTTPS with proper SSL verification
        )
        print("✓ AsyncOpenAI 客户端创建成功")
        
        # Create a simple test message
        print("📍 步骤 3: 发送测试请求...")
        response = await client.chat.completions.create(
            model=model.model_name,
            messages=[
                {"role": "user", "content": "Hello, respond with exactly: 'API connection successful!'"}
            ],
            max_tokens=50,
            temperature=0.7
        )
        
        print("✓ 客户端请求成功")
        print(f"✓ 响应内容: {response.choices[0].message.content}")
        print()
        print("🎉 所有测试通过！API 连接正常")
        return True
        
    except Exception as e:
        print(f"❌ 请求失败: {type(e).__name__}: {e}")
        print()
        print("💡 调试建议:")
        print(f"   - 检查 API endpoint: {provider.base_url}")
        print(f"   - 检查 API key: {api_key[:20]}...")
        print(f"   - 检查 SSL 证书是否有效")
        print(f"   - 确保 https://chrisapius.top 的证书配置正确")
        print(f"   - 查看完整错误堆栈:")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
