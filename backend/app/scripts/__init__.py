#!/usr/bin/env python3
"""
Database Migration Script - Add Knowledge Base Tables
Run: python -m app.scripts.migrate_003_knowledge_base
"""
import asyncio
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 从环境变量读取数据库 URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost:5432/tenmuses")

async def migrate_add_knowledge_base():
    """Add knowledge base tables and pgvector extension"""
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        # 1. 创建 pgvector 扩展
        print("📌 Creating pgvector extension...")
        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            print("✅ pgvector extension created")
        except Exception as e:
            print(f"⚠️  pgvector extension: {e}")
        
        # 2. 创建 kb_documents 表
        print("📌 Creating kb_documents table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS kb_documents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                workspace_id UUID,
                source_type VARCHAR(50) NOT NULL,
                source_url TEXT,
                filename VARCHAR(500),
                file_size INTEGER,
                content TEXT NOT NULL,
                content_hash VARCHAR(64),
                embedding VECTOR(1536),
                metadata JSONB DEFAULT '{}',
                chunk_count INTEGER DEFAULT 1,
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                CONSTRAINT kb_documents_status_check CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
            )
        """))
        print("✅ kb_documents table created")
        
        # 3. 创建 kb_chunks 表
        print("📌 Creating kb_chunks table...")
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS kb_chunks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                document_id UUID NOT NULL REFERENCES kb_documents(id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                token_count INTEGER,
                embedding VECTOR(1536),
                metadata JSONB DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("✅ kb_chunks table created")
        
        # 4. 创建索引
        print("📌 Creating indexes...")
        indexes = [
            ("idx_kb_documents_user", "kb_documents", ["user_id", "created_at"]),
            ("idx_kb_documents_status", "kb_documents", ["status"]),
            ("idx_kb_chunks_document", "kb_chunks", ["document_id", "chunk_index"]),
        ]
        
        for idx_name, table_name, columns in indexes:
            cols_str = ", ".join(columns)
            try:
                await conn.execute(text(f"""
                    CREATE INDEX IF NOT EXISTS {idx_name} 
                    ON {table_name} ({cols_str})
                """))
                print(f"  ✅ {idx_name}")
            except Exception as e:
                print(f"  ⚠️  {idx_name}: {e}")
        
        # 5. 创建向量索引 (HNSW)
        print("📌 Creating vector indexes (HNSW)...")
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_kb_documents_embedding 
                ON kb_documents USING hnsw (embedding vector_cosine_ops)
            """))
            print("  ✅ kb_documents embedding index")
        except Exception as e:
            print(f"  ⚠️  kb_documents embedding index: {e}")
        
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_kb_chunks_embedding 
                ON kb_chunks USING hnsw (embedding vector_cosine_ops)
            """))
            print("  ✅ kb_chunks embedding index")
        except Exception as e:
            print(f"  ⚠️  kb_chunks embedding index: {e}")
        
        await conn.commit()
    
    await engine.dispose()
    print("\n✨ Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(migrate_add_knowledge_base())
