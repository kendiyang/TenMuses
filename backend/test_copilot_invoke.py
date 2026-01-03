#!/usr/bin/env python3
"""
Copilot 模型调用验证脚本
检查 Copilot 服务是否能正常调用 LLM 模型
"""

import asyncio
import sys
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加后端路径
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from app.core.database import AsyncSessionLocal
from app.services.llm_client import llm_client
from app.models.llm_provider import LLMProvider
from app.models.llm_model import LLMModel
from sqlalchemy import select
from langchain_core.messages import HumanMessage, SystemMessage


async def test_database_config():
    """检查数据库中的 LLM 配置"""
    print("\n" + "="*80)
    print("📋 步骤 1: 检查数据库中的 LLM 配置")
    print("="*80)
    
    try:
        async with AsyncSessionLocal() as session:
            # 查询 providers
            provider_stmt = select(LLMProvider).where(LLMProvider.is_active == True)
            result = await session.execute(provider_stmt)
            providers = result.scalars().all()
            
            if not providers:
                print("❌ 数据库中没有激活的 LLM Provider")
                return False
            
            print(f"✅ 找到 {len(providers)} 个激活的 Provider:")
            for provider in providers:
                print(f"   - {provider.name} ({provider.display_name})")
                print(f"     Base URL: {provider.base_url}")
                print(f"     API Key: {'***' + provider.get_api_key()[-10:] if provider.get_api_key() else 'None'}")
            
            # 查询 models
            model_stmt = select(LLMModel).where(LLMModel.is_active == True)
            result = await session.execute(model_stmt)
            models = result.scalars().all()
            
            if not models:
                print("\n❌ 数据库中没有激活的 LLM Model")
                return False
            
            print(f"\n✅ 找到 {len(models)} 个激活的 Model:")
            for model in models:
                print(f"   - {model.model_name} ({model.display_name})")
                print(f"     Provider ID: {model.provider_id}")
            
            return len(providers) > 0 and len(models) > 0
            
    except Exception as e:
        print(f"❌ 数据库查询失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_llm_client_initialization():
    """测试 LLM Client 初始化"""
    print("\n" + "="*80)
    print("📋 步骤 2: 初始化 LLM Client")
    print("="*80)
    
    try:
        await llm_client.ensure_initialized()
        
        models = await llm_client.get_available_models()
        
        if not models:
            print("❌ LLM Client 没有加载任何模型")
            return False
        
        print(f"✅ LLM Client 成功初始化，加载 {len(models)} 个模型:")
        for model_info in models:
            print(f"   - {model_info['model_name']} (ID: {model_info['model_id'][:8]}...)")
            print(f"     Provider: {model_info['provider_name']}")
            print(f"     Display Name: {model_info['display_name']}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM Client 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_invoke_llm():
    """测试调用 LLM"""
    print("\n" + "="*80)
    print("📋 步骤 3: 测试调用 LLM (非流式)")
    print("="*80)
    
    try:
        # 准备消息
        messages = [
            SystemMessage(content="You are a helpful assistant. Respond in Chinese."),
            HumanMessage(content="请简短地介绍一下 TenMuses 是什么"),
        ]
        
        # 使用 provider+model 方式调用
        print("🔄 调用 LLM (使用 provider='openai', model='gpt-4o')...")
        
        response = await llm_client.invoke(
            messages=messages,
            provider="openai",
            model="gpt-4o",
            temperature=0.7,
            max_tokens=100
        )
        
        print(f"✅ LLM 调用成功！")
        print(f"   Response: {response.content[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM 调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_stream_llm():
    """测试流式调用 LLM"""
    print("\n" + "="*80)
    print("📋 步骤 4: 测试流式调用 LLM")
    print("="*80)
    
    try:
        # 准备消息
        messages = [
            SystemMessage(content="You are a helpful assistant. Respond in Chinese."),
            HumanMessage(content="请列出 TenMuses 的三个主要特性"),
        ]
        
        print("🔄 流式调用 LLM (使用 provider='openai', model='gpt-4o')...")
        print("   收到的内容:")
        
        full_response = ""
        token_count = 0
        
        async for token in llm_client.stream(
            messages=messages,
            provider="openai",
            model="gpt-4o",
            temperature=0.7,
            max_tokens=150
        ):
            full_response += token
            token_count += 1
            print(token, end="", flush=True)
        
        print(f"\n\n✅ 流式调用成功！")
        print(f"   总共收到 {token_count} 个 token")
        
        return True
        
    except Exception as e:
        print(f"❌ 流式调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_copilot_service():
    """测试 Copilot 服务"""
    print("\n" + "="*80)
    print("📋 步骤 5: 测试 Copilot 本地服务")
    print("="*80)
    
    try:
        from app.services.copilot_local_service import CopilotLocalService, AIModel
        
        # 测试本地智能模型
        print("🔄 初始化 Copilot 本地服务 (local-smart 模型)...")
        copilot = CopilotLocalService(model=AIModel.LOCAL_SMART)
        
        chat_history = []
        response = await copilot.chat(
            message="TenMuses 是什么?",
            chat_history=chat_history,
            workflow_context=None
        )
        
        print(f"✅ Copilot 本地服务调用成功！")
        print(f"   Response: {response[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Copilot 服务调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_copilot_stream_service():
    """测试 Copilot 流式服务"""
    print("\n" + "="*80)
    print("📋 步骤 6: 测试 Copilot 流式服务")
    print("="*80)
    
    try:
        from app.services.copilot_stream_service import CopilotStreamService
        
        print("🔄 初始化 Copilot 流式服务...")
        copilot_stream = CopilotStreamService(provider="openai", model="gpt-4o")
        
        print("🔄 流式调用 Copilot...")
        print("   收到的内容:")
        
        token_count = 0
        async for event in copilot_stream.stream_chat(
            message="请描述 AI 助手的作用",
            chat_history=[],
            workflow_context=None
        ):
            # 处理不同类型的事件
            if event.type == "token":
                content = event.get("content", "")
                print(content, end="", flush=True)
                token_count += 1
            elif event.type == "chat_completed":
                print(f"\n\n✅ 流式聊天完成！")
                print(f"   总共收到 {token_count} 个 token")
        
        return True
        
    except Exception as e:
        print(f"❌ Copilot 流式服务调用失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("🔍 Copilot 模型调用验证测试")
    print("="*80)
    print("这个脚本验证 Copilot 服务是否能正常调用 LLM 模型")
    
    results = {}
    
    # 步骤 1: 检查数据库配置
    results["Database Config"] = await test_database_config()
    
    if not results["Database Config"]:
        print("\n❌ 数据库配置不正确，停止测试")
        return results
    
    # 步骤 2: LLM Client 初始化
    results["LLM Client Init"] = await test_llm_client_initialization()
    
    if not results["LLM Client Init"]:
        print("\n❌ LLM Client 初始化失败，停止测试")
        return results
    
    # 步骤 3: 测试 invoke
    results["LLM Invoke"] = await test_invoke_llm()
    
    # 步骤 4: 测试 stream
    results["LLM Stream"] = await test_stream_llm()
    
    # 步骤 5: 测试 Copilot 本地服务
    results["Copilot Local"] = await test_copilot_service()
    
    # 步骤 6: 测试 Copilot 流式服务
    results["Copilot Stream"] = await test_copilot_stream_service()
    
    # 输出总结
    print("\n" + "="*80)
    print("📊 测试结果总结")
    print("="*80)
    
    all_passed = True
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {test_name}")
        if not result:
            all_passed = False
    
    print("="*80)
    if all_passed:
        print("🎉 所有测试通过！Copilot 模型调用功能正常")
    else:
        print("⚠️  某些测试失败，请检查错误信息")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
