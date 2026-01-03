"""
RAG Integration Test
端到端测试：文档上传 → 向量化 → 搜索 → 上下文生成
"""
import asyncio
import os
import tempfile
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.knowledge import KBDocument, KBChunk, Base
from app.services.embedding_service import EmbeddingService, EmbeddingServiceException
from app.services.document_processor import DocumentProcessor
from app.services.rag_service import RAGService
from uuid import uuid4


class TestRAGPipeline:
    """RAG 完整流程测试"""
    
    @pytest.fixture
    async def db_session(self):
        """创建测试数据库会话"""
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
            future=True
        )
        
        async with engine.begin() as conn:
            # SQLite 不支持 pgvector，但可以测试基本流程
            await conn.run_sync(Base.metadata.create_all)
        
        AsyncSessionLocal = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        async with AsyncSessionLocal() as session:
            yield session
        
        await engine.dispose()
    
    async def test_embedding_service(self):
        """测试向量化服务"""
        print("\n=== Testing EmbeddingService ===")
        
        service = EmbeddingService()
        
        # 测试单个文本
        text = "这是一个测试文本"
        embedding = await service.embed_text(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)
        print(f"✓ Single text embedding: {len(embedding)} dimensions")
        
        # 测试批量文本
        texts = [
            "第一个文档的内容",
            "第二个文档的内容",
            "第三个文档的内容"
        ]
        embeddings = await service.embed_batch(texts)
        
        assert len(embeddings) == 3
        assert all(len(e) == 1536 for e in embeddings)
        print(f"✓ Batch embedding: {len(embeddings)} texts × {len(embeddings[0])} dimensions")
        
        # 测试连接验证
        verified = await service.verify_connection()
        assert verified
        print("✓ API connection verified")
    
    def test_document_processor(self):
        """测试文档处理器"""
        print("\n=== Testing DocumentProcessor ===")
        
        processor = DocumentProcessor(max_chunk_tokens=100)
        
        # 测试纯文本提取
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("这是测试文本。\n\n第一个段落。\n\n第二个段落。")
            txt_path = f.name
        
        try:
            text = processor.extract_text(txt_path, "text/plain")
            assert "测试文本" in text
            print(f"✓ Text extraction: {len(text)} characters")
        finally:
            os.unlink(txt_path)
        
        # 测试分片
        long_text = "这是一个较长的文本。" * 50
        chunks = processor.chunk_text(long_text)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, tuple) and len(chunk) == 2 for chunk in chunks)
        total_tokens = sum(count for _, count in chunks)
        print(f"✓ Chunking: {len(chunks)} chunks, {total_tokens} total tokens")
        
        # 测试哈希计算
        content = "测试内容"
        hash1 = processor.compute_hash(content)
        hash2 = processor.compute_hash(content)
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256
        print(f"✓ Hash computation: {hash1[:16]}...")
        
        # 测试 Token 计数
        token_count = processor.get_token_count("这是一个测试文本")
        assert token_count > 0
        print(f"✓ Token counting: {token_count} tokens")
    
    async def test_rag_service_format(self):
        """测试 RAG 服务的上下文格式化"""
        print("\n=== Testing RAG Service ===")
        
        from app.schemas.knowledge import KBSearchResultItem
        
        # 创建测试结果
        results = [
            KBSearchResultItem(
                document_id=uuid4(),
                chunk_id=uuid4(),
                content="这是第一个搜索结果",
                score=0.95,
                metadata={"title": "文档1", "chunk_index": 0}
            ),
            KBSearchResultItem(
                document_id=uuid4(),
                chunk_id=uuid4(),
                content="这是第二个搜索结果",
                score=0.87,
                metadata={"title": "文档2", "chunk_index": 1}
            )
        ]
        
        # 创建虚拟 RAG 服务（仅测试格式化）
        class MockDB:
            pass
        
        service = RAGService(MockDB())  # type: ignore
        
        # 测试格式化
        context = service.format_context(results)
        
        assert "这是第一个搜索结果" in context
        assert "这是第二个搜索结果" in context
        assert "95%" in context
        assert "87%" in context
        print(f"✓ Context formatting:\n{context[:100]}...")
        
        # 测试无结果情况
        empty_context = service.format_context([])
        assert "没有找到" in empty_context
        print(f"✓ Empty result handling: '{empty_context}'")
    
    async def test_pipeline_integration(self):
        """测试完整管道"""
        print("\n=== Testing Full Pipeline ===")
        
        processor = DocumentProcessor(max_chunk_tokens=100)
        embedding_service = EmbeddingService()
        
        # 步骤 1: 提取文本
        sample_text = """
        人工智能（AI）是计算机科学的一个分支。
        它试图了解智能的本质，是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统的一门新的技术科学。
        
        机器学习是实现人工智能的一种方式。
        它专注于开发能够从数据中学习的计算机程序。
        """
        
        print(f"✓ Step 1: Text extraction ({len(sample_text)} characters)")
        
        # 步骤 2: 分片
        chunks = processor.chunk_text(sample_text)
        print(f"✓ Step 2: Chunking ({len(chunks)} chunks)")
        
        # 步骤 3: 向量化
        chunk_texts = [text for text, _ in chunks]
        embeddings = await embedding_service.embed_batch(chunk_texts)
        print(f"✓ Step 3: Embedding ({len(embeddings)} embeddings)")
        
        # 步骤 4: 哈希计算
        content_hash = processor.compute_hash(sample_text)
        print(f"✓ Step 4: Hashing ({content_hash[:16]}...)")
        
        # 验证
        assert len(chunks) == len(embeddings)
        assert all(isinstance(e, list) for e in embeddings)
        print("\n✅ Full pipeline integration test passed")


async def run_tests():
    """运行所有测试"""
    print("=" * 60)
    print("RAG Integration Tests")
    print("=" * 60)
    
    test = TestRAGPipeline()
    
    try:
        # 测试向量化服务
        await test.test_embedding_service()
        
        # 测试文档处理器
        test.test_document_processor()
        
        # 测试 RAG 服务
        await test.test_rag_service_format()
        
        # 测试完整管道
        await test.test_pipeline_integration()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        return 0
    
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_tests())
    sys.exit(exit_code)
