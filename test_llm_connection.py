#!/usr/bin/env python3
"""
简单测试脚本 - 验证LLM API连接和配置

测试 https://chrisapius.top/v1 和 API key 是否能正常调用模型
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.llm_provider import LLMProvider
from app.models.llm_model import LLMModel
from openai import AsyncOpenAI


async def test_llm_connection():
    """测试LLM连接"""
    print("=" * 70)
    print("LLM API 连接测试")
    print("=" * 70)
    print()
    
    # 1. 从数据库读取配置
    print("步骤 1: 从数据库读取配置...")
    async with AsyncSessionLocal() as session:
        # 获取OpenAI供应商
        stmt = select(LLMProvider).where(
            LLMProvider.name == "openai",
            LLMProvider.is_active == True
        )
        result = await session.execute(stmt)
        provider = result.scalar_one_or_none()
        
        if not provider:
            print("❌ 错误: 未找到激活的OpenAI供应商配置")
            return False
        
        print(f"✓ 供应商: {provider.display_name}")
        print(f"✓ Base URL: {provider.base_url}")
        api_key = provider.get_api_key()
        print(f"✓ API Key: {api_key[:20]}...")
        
        # 获取gpt-4o模型
        stmt = select(LLMModel).where(
            LLMModel.provider_id == provider.id,
            LLMModel.model_name == "gpt-4o",
            LLMModel.is_active == True
        )
        result = await session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            print("❌ 错误: 未找到激活的gpt-4o模型")
            return False
        
        print(f"✓ 模型: {model.display_name} ({model.model_name})")
        print()
    
    # 2. 创建OpenAI客户端
    print("步骤 2: 创建API客户端...")
    try:
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=provider.base_url
        )
        print("✓ 客户端创建成功")
        print()
    except Exception as e:
        print(f"❌ 客户端创建失败: {e}")
        return False
    
    # 3. 发送测试请求
    print("步骤 3: 发送测试请求...")
    print(f"请求: 'Hello, test message'")
    print()
    
    try:
        response = await client.chat.completions.create(
            model=model.model_name,
            messages=[
                {"role": "user", "content": "Hello, respond with exactly: 'API connection successful!'"}
            ],
            max_tokens=50,
            temperature=0.7,
            timeout=30.0
        )
        
        # 4. 检查响应
        print("步骤 4: 检查响应...")
        content = response.choices[0].message.content
        print(f"✓ 响应内容: {content}")
        print(f"✓ 使用的模型: {response.model}")
        print(f"✓ Token使用: {response.usage.total_tokens} (输入: {response.usage.prompt_tokens}, 输出: {response.usage.completion_tokens})")
        print()
        
        print("=" * 70)
        print("✅ 测试成功！API连接和配置正常工作")
        print("=" * 70)
        return True
        
    except Exception as e:
        print(f"❌ 请求失败: {type(e).__name__}: {e}")
        import traceback
        print("\n详细错误信息:")
        traceback.print_exc()
        print()
        print("=" * 70)
        print("❌ 测试失败！请检查:")
        print("  1. API key是否正确")
        print("  2. Base URL是否可访问 (尝试: curl -v https://chrisapius.top/v1)")
        print("  3. 网络连接是否正常")
        print("  4. 代理设置是否正确")
        print("=" * 70)
        return False


async def main():
    """主函数"""
    success = await test_llm_connection()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
