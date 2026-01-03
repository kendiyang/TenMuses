#!/usr/bin/env python3
"""
Database migration for Knowledge Base (RAG) tables
Supports PostgreSQL with pgvector extension
"""
import asyncio
import logging
import sys
from pathlib import Path

# 添加项目路径到 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool
from app.core.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class KnowledgeBaseMigration:
    """知识库数据库迁移"""
    
    def __init__(self):
        self.engine = None
        self.db_url = settings.DATABASE_URL
    
    async def connect(self):
        """创建数据库连接"""
        self.engine = create_async_engine(
            self.db_url,
            echo=False,
            poolclass=NullPool
        )
    
    async def close(self):
        """关闭数据库连接"""
        if self.engine:
            await self.engine.dispose()
    
    async def enable_pgvector(self, session: AsyncSession):
        """启用 pgvector 扩展"""
        try:
            await session.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await session.commit()
            logger.info("✓ pgvector extension enabled")
        except Exception as e:
            logger.error(f"Failed to enable pgvector: {e}")
            raise
    
    async def create_kb_documents_table(self, session: AsyncSession):
        """创建知识库文档表"""
        sql = """
        CREATE TABLE IF NOT EXISTS kb_documents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL,
            title VARCHAR(255) NOT NULL,
            content TEXT,
            content_hash VARCHAR(64) UNIQUE NOT NULL,
            doc_metadata JSONB DEFAULT '{}',
            embedding vector(1536),
            status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
            chunk_count INTEGER DEFAULT 0,
            processed_at TIMESTAMP WITHOUT TIME ZONE,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_user_id FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE
        )
        """
        try:
            await session.execute(text(sql))
            await session.commit()
            logger.info("✓ kb_documents table created")
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to create kb_documents table: {e}")
            raise
    
    async def create_kb_chunks_table(self, session: AsyncSession):
        """创建知识库分片表"""
        sql = """
        CREATE TABLE IF NOT EXISTS kb_chunks (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            document_id UUID NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            token_count INTEGER DEFAULT 0,
            embedding vector(1536),
            chunk_metadata JSONB DEFAULT '{}',
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_document_id FOREIGN KEY (document_id) REFERENCES kb_documents(id) ON DELETE CASCADE,
            CONSTRAINT unique_chunk_per_doc UNIQUE (document_id, chunk_index)
        )
        """
        try:
            await session.execute(text(sql))
            await session.commit()
            logger.info("✓ kb_chunks table created")
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to create kb_chunks table: {e}")
            raise
    
    async def create_indexes(self, session: AsyncSession):
        """创建索引以优化查询性能"""
        indexes = [
            # kb_documents 索引
            "CREATE INDEX IF NOT EXISTS idx_kb_documents_user_id ON kb_documents(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_kb_documents_status ON kb_documents(status)",
            "CREATE INDEX IF NOT EXISTS idx_kb_documents_created_at ON kb_documents(created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_kb_documents_content_hash ON kb_documents(content_hash)",
            
            # pgvector HNSW 索引用于高效的向量搜索
            "CREATE INDEX IF NOT EXISTS idx_kb_documents_embedding ON kb_documents USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=200)",
            
            # kb_chunks 索引
            "CREATE INDEX IF NOT EXISTS idx_kb_chunks_document_id ON kb_chunks(document_id)",
            "CREATE INDEX IF NOT EXISTS idx_kb_chunks_created_at ON kb_chunks(created_at DESC)",
            
            # pgvector HNSW 索引
            "CREATE INDEX IF NOT EXISTS idx_kb_chunks_embedding ON kb_chunks USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=200)",
        ]
        
        try:
            for idx_sql in indexes:
                await session.execute(text(idx_sql))
            await session.commit()
            logger.info("✓ All indexes created")
        except Exception as e:
            await session.rollback()
            logger.warning(f"Some indexes may already exist: {e}")
    
    async def verify_schema(self, session: AsyncSession) -> bool:
        """验证数据库架构"""
        try:
            # 检查表是否存在
            tables_check = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('kb_documents', 'kb_chunks')
            )
            """
            
            result = await session.execute(text(tables_check))
            exists = result.scalar()
            
            if exists:
                logger.info("✓ Knowledge base tables verified")
                return True
            else:
                logger.error("✗ Knowledge base tables not found")
                return False
        except Exception as e:
            logger.error(f"Failed to verify schema: {e}")
            return False
    
    async def run_migration(self):
        """执行完整迁移"""
        await self.connect()
        
        try:
            async with self.engine.begin() as conn:
                async def _run(session):
                    # 1. 启用 pgvector
                    await self.enable_pgvector(session)
                    
                    # 2. 创建表
                    await self.create_kb_documents_table(session)
                    await self.create_kb_chunks_table(session)
                    
                    # 3. 创建索引
                    await self.create_indexes(session)
                    
                    # 4. 验证
                    verified = await self.verify_schema(session)
                    
                    if verified:
                        logger.info("✅ Knowledge base migration completed successfully")
                        return True
                    else:
                        logger.error("❌ Knowledge base migration verification failed")
                        return False
                
                # 创建会话并执行迁移
                from sqlalchemy.ext.asyncio import AsyncSession as SessionClass
                async with SessionClass(conn) as session:
                    return await _run(session)
        
        finally:
            await self.close()


async def main():
    """主函数"""
    migration = KnowledgeBaseMigration()
    
    try:
        logger.info("Starting Knowledge Base migration...")
        success = await migration.run_migration()
        
        if success:
            logger.info("✅ All migrations completed")
            return 0
        else:
            logger.error("❌ Migration failed")
            return 1
    
    except Exception as e:
        logger.error(f"❌ Migration error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
