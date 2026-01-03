"""
数据迁移脚本: 从旧的 llm_configs 表迁移到新的 llm_providers 和 llm_models 表

运行方式:
    cd backend
    python -m app.scripts.migrate_llm_config_to_provider_model

注意:
    - 运行前请备份数据库
    - 迁移完成后会保留旧表，验证无误后手动删除
"""

import asyncio
import sys
from sqlalchemy import select, text, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal, engine, Base
from app.models.llm_config import LLMConfig
from app.models.llm_provider import LLMProvider
from app.models.llm_model import LLMModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_tables():
    """创建新表"""
    logger.info("Creating new tables (llm_providers and llm_models)...")
    async with engine.begin() as conn:
        # 只创建新表，不删除旧表
        await conn.run_sync(Base.metadata.create_all)
    logger.info("✓ New tables created")


async def migrate_data():
    """执行数据迁移"""
    async with AsyncSessionLocal() as session:
        try:
            # 1. 查询所有旧配置
            logger.info("Loading existing llm_configs...")
            stmt = select(LLMConfig).order_by(LLMConfig.provider, LLMConfig.priority)
            result = await session.execute(stmt)
            old_configs = result.scalars().all()
            
            if not old_configs:
                logger.info("No existing configs found to migrate")
                return
            
            logger.info(f"Found {len(old_configs)} configs to migrate")
            
            # 2. 按供应商分组
            providers_data = {}
            for config in old_configs:
                if config.provider not in providers_data:
                    providers_data[config.provider] = {
                        "config": config,  # 使用第一个配置作为供应商配置
                        "models": []
                    }
                providers_data[config.provider]["models"].append(config)
            
            logger.info(f"Identified {len(providers_data)} unique providers")
            
            # 3. 创建供应商记录
            provider_map = {}  # provider_name -> LLMProvider对象
            
            for provider_name, data in providers_data.items():
                first_config = data["config"]
                
                # 检查供应商是否已存在
                existing_provider = await session.execute(
                    select(LLMProvider).where(LLMProvider.name == provider_name)
                )
                provider = existing_provider.scalar_one_or_none()
                
                if not provider:
                    provider = LLMProvider(
                        name=provider_name,
                        display_name=first_config.display_name.split("-")[0].strip() if "-" in first_config.display_name else provider_name.capitalize(),
                        is_active=first_config.is_active,
                        priority=first_config.priority,
                        description=f"Migrated from llm_configs table",
                        base_url=first_config.base_url,
                    )
                    # 复制加密的API密钥
                    provider.api_key_encrypted = first_config.api_key_encrypted
                    
                    session.add(provider)
                    await session.flush()
                    logger.info(f"  ✓ Created provider: {provider_name}")
                else:
                    logger.info(f"  - Provider already exists: {provider_name}")
                
                provider_map[provider_name] = provider
            
            # 4. 创建模型记录
            models_created = 0
            for provider_name, data in providers_data.items():
                provider = provider_map[provider_name]
                
                for config in data["models"]:
                    # 检查模型是否已存在
                    existing_model = await session.execute(
                        select(LLMModel).where(
                            LLMModel.provider_id == provider.id,
                            LLMModel.model_name == config.model_name
                        )
                    )
                    model = existing_model.scalar_one_or_none()
                    
                    if not model:
                        # 解析模型系列（例如 gpt-4-turbo-preview -> gpt-4）
                        model_family = None
                        if "gpt-4" in config.model_name.lower():
                            model_family = "gpt-4"
                        elif "gpt-3.5" in config.model_name.lower():
                            model_family = "gpt-3.5"
                        elif "claude-3" in config.model_name.lower():
                            model_family = "claude-3"
                        elif "claude-2" in config.model_name.lower():
                            model_family = "claude-2"
                        
                        model = LLMModel(
                            provider_id=provider.id,
                            model_name=config.model_name,
                            display_name=config.display_name,
                            model_family=model_family,
                            default_temperature=0.7,
                            is_active=config.is_active,
                            priority=config.priority,
                            description=config.description or f"Migrated from llm_configs",
                            supports_streaming=True,
                        )
                        
                        session.add(model)
                        models_created += 1
                        logger.info(f"    ✓ Created model: {config.model_name}")
                    else:
                        logger.info(f"    - Model already exists: {config.model_name}")
            
            # 5. 提交所有更改
            await session.commit()
            logger.info(f"\n✓ Migration completed successfully!")
            logger.info(f"  - Providers created/updated: {len(provider_map)}")
            logger.info(f"  - Models created: {models_created}")
            
        except Exception as e:
            await session.rollback()
            logger.error(f"✗ Migration failed: {e}")
            raise


async def verify_migration():
    """验证迁移结果"""
    async with AsyncSessionLocal() as session:
        # 统计新表数据
        providers_count = await session.scalar(select(func.count(LLMProvider.id)))
        models_count = await session.scalar(select(func.count(LLMModel.id)))
        
        logger.info(f"\nVerification:")
        logger.info(f"  - Providers in new table: {providers_count}")
        logger.info(f"  - Models in new table: {models_count}")
        
        # 查询旧表数据
        old_configs_count = await session.scalar(select(func.count(LLMConfig.id)))
        logger.info(f"  - Configs in old table: {old_configs_count}")
        
        # 显示详细信息
        providers = await session.execute(
            select(LLMProvider).order_by(LLMProvider.priority)
        )
        
        logger.info(f"\nProviders detail:")
        for provider in providers.scalars():
            models = await session.execute(
                select(LLMModel).where(LLMModel.provider_id == provider.id)
            )
            models_list = models.scalars().all()
            logger.info(f"  - {provider.display_name} ({provider.name}): {len(models_list)} models")
            for model in models_list:
                logger.info(f"    - {model.display_name} ({model.model_name})")


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("LLM Config Migration Tool")
    logger.info("=" * 60)
    logger.info("")
    
    try:
        # 步骤1: 创建新表
        await create_tables()
        logger.info("")
        
        # 步骤2: 迁移数据
        logger.info("Starting data migration...")
        await migrate_data()
        logger.info("")
        
        # 步骤3: 验证
        await verify_migration()
        logger.info("")
        
        logger.info("=" * 60)
        logger.info("✓ All steps completed successfully!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Verify the migrated data in new tables")
        logger.info("  2. Test the application with new models")
        logger.info("  3. Once confirmed, you can drop the old 'llm_configs' table:")
        logger.info("     DROP TABLE llm_configs;")
        logger.info("")
        
    except Exception as e:
        logger.error(f"\n✗ Migration failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
