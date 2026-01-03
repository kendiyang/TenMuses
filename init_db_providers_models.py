#!/usr/bin/env python3
"""
初始化数据库供应商和模型配置脚本

此脚本用于初始化 TenMuses 系统的 LLM 供应商和模型配置：
1. 创建 OpenAI 供应商配置（API密钥和base_url）
2. 创建两个模型：gpt-4o 和 text-embedding-3-large
3. 将所有配置写入数据库

使用方法：
    python init_db_providers_models.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import uuid

# 添加 backend 到路径
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.llm_provider import LLMProvider
from app.models.llm_model import LLMModel
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# 配置数据
# ============================================================================

PROVIDER_CONFIG = {
    "name": "openai",
    "display_name": "OpenAI (Custom)",
    "api_key": "sk-wvbHvCfLHCvCf0kHEB8xTOInLVfZtDe4rNB0FiHQxgbQ0OhY",
    "base_url": "https://chrisapivip.com/v1",
    "is_active": True,
    "priority": 10,
    "description": "自定义 OpenAI API 供应商配置，使用 chrisapivip.com 代理",
    "icon_url": "https://openai.com/favicon.ico"
}

MODELS_CONFIG = [
    {
        "model_name": "gpt-4o",
        "display_name": "GPT-4o",
        "model_family": "gpt-4",
        "version": "2024-05-13",
        "default_temperature": 0.7,
        "default_max_tokens": 4096,
        "default_top_p": 1.0,
        "context_window": 128000,
        "supports_streaming": True,
        "supports_function_calling": True,
        "supports_vision": True,
        "supports_json_mode": True,
        "cost_per_1k_input_tokens": 0.005,
        "cost_per_1k_output_tokens": 0.015,
        "is_active": True,
        "priority": 10,
        "description": "GPT-4o 是 OpenAI 最新的旗舰模型，支持文本和视觉输入"
    },
    {
        "model_name": "text-embedding-3-large",
        "display_name": "Text Embedding 3 Large",
        "model_family": "embedding",
        "version": "3",
        "default_temperature": 0.0,  # embedding 模型不使用 temperature
        "default_max_tokens": None,  # embedding 模型没有 max_tokens
        "default_top_p": None,
        "context_window": 8191,
        "supports_streaming": False,  # embedding 不支持流式
        "supports_function_calling": False,
        "supports_vision": False,
        "supports_json_mode": False,
        "cost_per_1k_input_tokens": 0.00013,
        "cost_per_1k_output_tokens": 0.0,  # embedding 无输出成本
        "is_active": True,
        "priority": 20,
        "description": "OpenAI 第三代大型向量嵌入模型，输出维度 3072"
    }
]


# ============================================================================
# 数据库初始化函数
# ============================================================================

async def create_or_update_provider(session, config: dict) -> LLMProvider:
    """
    创建或更新供应商配置
    
    如果供应商已存在，则更新其配置；否则创建新的供应商。
    """
    # 检查供应商是否已存在
    result = await session.execute(
        select(LLMProvider).where(LLMProvider.name == config["name"])
    )
    provider = result.scalar_one_or_none()
    
    if provider:
        logger.info(f"供应商 '{config['name']}' 已存在，正在更新...")
        
        # 更新现有供应商
        provider.display_name = config["display_name"]
        provider.set_api_key(config["api_key"])  # 使用加密方法
        provider.base_url = config["base_url"]
        provider.is_active = config["is_active"]
        provider.priority = config["priority"]
        provider.description = config.get("description")
        provider.icon_url = config.get("icon_url")
        provider.updated_at = datetime.utcnow()
        
        logger.info(f"✓ 供应商 '{config['name']}' 已更新")
    else:
        logger.info(f"创建新供应商 '{config['name']}'...")
        
        # 创建新供应商
        provider = LLMProvider(
            id=uuid.uuid4(),
            name=config["name"],
            display_name=config["display_name"],
            base_url=config["base_url"],
            is_active=config["is_active"],
            priority=config["priority"],
            description=config.get("description"),
            icon_url=config.get("icon_url"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        provider.set_api_key(config["api_key"])  # 使用加密方法
        session.add(provider)
        
        logger.info(f"✓ 供应商 '{config['name']}' 已创建")
    
    return provider


async def create_or_update_model(
    session,
    provider: LLMProvider,
    model_config: dict
) -> LLMModel:
    """
    创建或更新模型配置
    
    如果模型已存在（相同 provider_id 和 model_name），则更新；否则创建新模型。
    """
    # 检查模型是否已存在
    result = await session.execute(
        select(LLMModel).where(
            LLMModel.provider_id == provider.id,
            LLMModel.model_name == model_config["model_name"]
        )
    )
    model = result.scalar_one_or_none()
    
    if model:
        logger.info(f"  模型 '{model_config['model_name']}' 已存在，正在更新...")
        
        # 更新现有模型
        model.display_name = model_config["display_name"]
        model.model_family = model_config.get("model_family")
        model.version = model_config.get("version")
        model.default_temperature = model_config["default_temperature"]
        model.default_max_tokens = model_config.get("default_max_tokens")
        model.default_top_p = model_config.get("default_top_p")
        model.context_window = model_config.get("context_window")
        model.supports_streaming = model_config["supports_streaming"]
        model.supports_function_calling = model_config["supports_function_calling"]
        model.supports_vision = model_config["supports_vision"]
        model.supports_json_mode = model_config["supports_json_mode"]
        model.cost_per_1k_input_tokens = model_config.get("cost_per_1k_input_tokens")
        model.cost_per_1k_output_tokens = model_config.get("cost_per_1k_output_tokens")
        model.is_active = model_config["is_active"]
        model.priority = model_config["priority"]
        model.description = model_config.get("description")
        model.updated_at = datetime.utcnow()
        
        logger.info(f"  ✓ 模型 '{model_config['model_name']}' 已更新")
    else:
        logger.info(f"  创建新模型 '{model_config['model_name']}'...")
        
        # 创建新模型
        model = LLMModel(
            id=uuid.uuid4(),
            provider_id=provider.id,
            model_name=model_config["model_name"],
            display_name=model_config["display_name"],
            model_family=model_config.get("model_family"),
            version=model_config.get("version"),
            default_temperature=model_config["default_temperature"],
            default_max_tokens=model_config.get("default_max_tokens"),
            default_top_p=model_config.get("default_top_p"),
            context_window=model_config.get("context_window"),
            supports_streaming=model_config["supports_streaming"],
            supports_function_calling=model_config["supports_function_calling"],
            supports_vision=model_config["supports_vision"],
            supports_json_mode=model_config["supports_json_mode"],
            cost_per_1k_input_tokens=model_config.get("cost_per_1k_input_tokens"),
            cost_per_1k_output_tokens=model_config.get("cost_per_1k_output_tokens"),
            is_active=model_config["is_active"],
            priority=model_config["priority"],
            description=model_config.get("description"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(model)
        
        logger.info(f"  ✓ 模型 '{model_config['model_name']}' 已创建")
    
    return model


async def init_database():
    """
    初始化数据库配置的主函数
    """
    logger.info("=" * 70)
    logger.info("TenMuses - 数据库供应商和模型初始化脚本")
    logger.info("=" * 70)
    logger.info("")
    
    async with AsyncSessionLocal() as session:
        try:
            # 步骤 1: 创建或更新供应商
            logger.info("步骤 1: 初始化供应商配置")
            logger.info("-" * 70)
            provider = await create_or_update_provider(session, PROVIDER_CONFIG)
            logger.info("")
            
            # 步骤 2: 创建或更新模型
            logger.info("步骤 2: 初始化模型配置")
            logger.info("-" * 70)
            models = []
            for model_config in MODELS_CONFIG:
                model = await create_or_update_model(session, provider, model_config)
                models.append(model)
            logger.info("")
            
            # 步骤 3: 提交到数据库
            logger.info("步骤 3: 保存到数据库")
            logger.info("-" * 70)
            await session.commit()
            logger.info("✓ 所有配置已成功写入数据库")
            logger.info("")
            
            # 步骤 4: 显示摘要
            logger.info("=" * 70)
            logger.info("初始化完成摘要")
            logger.info("=" * 70)
            logger.info(f"供应商名称: {provider.name}")
            logger.info(f"供应商显示名: {provider.display_name}")
            logger.info(f"Base URL: {provider.base_url}")
            logger.info(f"API Key: {PROVIDER_CONFIG['api_key'][:20]}... (已加密存储)")
            logger.info(f"供应商 ID: {provider.id}")
            logger.info(f"激活状态: {'✓ 是' if provider.is_active else '✗ 否'}")
            logger.info("")
            logger.info(f"已配置模型数: {len(models)}")
            for i, model in enumerate(models, 1):
                logger.info(f"  {i}. {model.display_name} ({model.model_name})")
                logger.info(f"     - 模型系列: {model.model_family}")
                logger.info(f"     - 上下文窗口: {model.context_window} tokens")
                logger.info(f"     - 支持流式: {'✓' if model.supports_streaming else '✗'}")
                logger.info(f"     - 支持函数调用: {'✓' if model.supports_function_calling else '✗'}")
                logger.info(f"     - 支持视觉: {'✓' if model.supports_vision else '✗'}")
                logger.info(f"     - 模型 ID: {model.id}")
                logger.info("")
            
            logger.info("=" * 70)
            logger.info("✓ 初始化成功！现在可以使用这些配置进行测试。")
            logger.info("=" * 70)
            
        except Exception as e:
            await session.rollback()
            logger.error("")
            logger.error("=" * 70)
            logger.error("✗ 初始化失败")
            logger.error("=" * 70)
            logger.error(f"错误信息: {e}")
            logger.error("")
            logger.error("请检查：")
            logger.error("  1. 数据库连接是否正常")
            logger.error("  2. 数据库表是否已创建")
            logger.error("  3. JWT_SECRET_KEY 环境变量是否已设置（用于加密）")
            logger.error("")
            raise


async def list_current_config():
    """
    列出当前数据库中的所有供应商和模型配置
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("当前数据库配置")
    logger.info("=" * 70)
    
    async with AsyncSessionLocal() as session:
        try:
            # 查询所有供应商
            result = await session.execute(
                select(LLMProvider).order_by(LLMProvider.priority)
            )
            providers = result.scalars().all()
            
            if not providers:
                logger.info("数据库中没有找到供应商配置")
                return
            
            logger.info(f"找到 {len(providers)} 个供应商：")
            logger.info("")
            
            for provider in providers:
                status = "✓ 激活" if provider.is_active else "✗ 未激活"
                logger.info(f"{status} | {provider.display_name}")
                logger.info(f"  名称: {provider.name}")
                logger.info(f"  Base URL: {provider.base_url}")
                logger.info(f"  API Key: {'已设置 (加密)' if provider.api_key_encrypted else '未设置'}")
                logger.info(f"  优先级: {provider.priority}")
                
                # 查询该供应商的所有模型
                result = await session.execute(
                    select(LLMModel)
                    .where(LLMModel.provider_id == provider.id)
                    .order_by(LLMModel.priority)
                )
                models = result.scalars().all()
                
                if models:
                    logger.info(f"  模型 ({len(models)}):")
                    for model in models:
                        model_status = "✓" if model.is_active else "✗"
                        logger.info(f"    {model_status} {model.display_name} ({model.model_name})")
                        logger.info(f"       上下文: {model.context_window} tokens")
                else:
                    logger.info("  模型: 无")
                
                logger.info("")
                
        except Exception as e:
            logger.error(f"查询配置时出错: {e}")
            raise


# ============================================================================
# 主函数
# ============================================================================

async def main():
    """主入口函数"""
    try:
        # 初始化数据库
        await init_database()
        
        # 列出当前配置（验证）
        await list_current_config()
        
    except Exception as e:
        logger.error(f"脚本执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
