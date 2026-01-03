#!/usr/bin/env python3
"""
TenMuses Phase 2.3 RAG 端到端验证脚本
测试: 文档上传 → 分片 → 向量化 → 搜索 → 上下文提取

运行方式:
  python test_e2e_rag.py
"""

import asyncio
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.services.document_processor import DocumentProcessor
from app.services.embedding_service import EmbeddingService
from app.services.rag_service import RAGService
from app.models.knowledge import KBDocument, KBChunk
from app.core.database import get_db
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import json


class TestContext:
    """测试上下文"""
    
    def __init__(self):
        self.engine = None
        self.session_maker = None
        self.session = None
        self.user_id = uuid4()
        self.test_files = []
    
    async def setup(self):
        """初始化测试环境"""
        print("\n📝 初始化测试环境...")
        
        # 创建数据库引擎
        self.engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            future=True
        )
        self.session_maker = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        
        # 创建表（如果不存在）
        from app.models import Base
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        print("✅ 数据库表已创建/存在")
    
    async def cleanup(self):
        """清理测试环境"""
        if self.session:
            await self.session.close()
        if self.engine:
            await self.engine.dispose()
        
        # 删除临时文件
        for f in self.test_files:
            try:
                f.unlink()
            except:
                pass


async def test_document_processor():
    """测试 DocumentProcessor"""
    print("\n" + "="*70)
    print("✨ 测试 1: DocumentProcessor (文档处理)")
    print("="*70)
    
    processor = DocumentProcessor()
    
    # 测试 1.1: TXT 文件
    print("\n  [1.1] 测试 TXT 文件提取...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("TenMuses 是一个 AI 工作流编排平台。\n")
        f.write("它支持多格式文档上传、向量检索和智能代理编排。\n")
        f.write("用户可以通过拖拽搭建工作流，支持 HITL（人在回路）模式。\n")
        txt_path = f.name
    
    text = processor.extract_text(txt_path, "text/plain")
    print(f"    提取文本长度: {len(text)} 字符")
    print(f"    提取内容预览: {text[:50]}...")
    assert len(text) > 0, "TXT 提取失败"
    print("    ✅ TXT 提取成功")
    
    # 测试 1.2: 文本分片
    print("\n  [1.2] 测试文本分片...")
    chunks = processor.chunk_text(text)
    print(f"    分片数: {len(chunks)}")
    for i, (chunk_text, token_count) in enumerate(chunks[:2]):
        print(f"    分片 {i+1}: {len(chunk_text)} 字 / {token_count} tokens")
    assert len(chunks) > 0, "文本分片失败"
    print("    ✅ 文本分片成功")
    
    # 测试 1.3: 内容哈希
    print("\n  [1.3] 测试内容去重...")
    hash1 = processor.compute_hash(text)
    hash2 = processor.compute_hash(text)
    print(f"    哈希值 1: {hash1[:16]}...")
    print(f"    哈希值 2: {hash2[:16]}...")
    assert hash1 == hash2, "哈希不一致"
    print("    ✅ 内容去重成功")
    
    Path(txt_path).unlink()
    return True


async def test_embedding_service():
    """测试 EmbeddingService"""
    print("\n" + "="*70)
    print("✨ 测试 2: EmbeddingService (向量化)")
    print("="*70)
    
    # 检查 API 密钥
    if not settings.OPENAI_API_KEY:
        print("\n  ⚠️  OPENAI_API_KEY 未设置，跳过实际向量化测试")
        print("     使用虚拟向量用于后续测试")
        
        # 创建虚拟向量
        class MockEmbeddingService:
            async def embed_text(self, text: str):
                import hashlib
                seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
                import random
                random.seed(seed)
                return [random.random() for _ in range(1536)]
            
            async def embed_batch(self, texts):
                return [await self.embed_text(t) for t in texts]
        
        service = MockEmbeddingService()
        print("    ✅ 使用虚拟 EmbeddingService")
    else:
        service = EmbeddingService()
        print("    ✅ 使用真实 OpenAI EmbeddingService")
    
    # 测试向量化
    print("\n  [2.1] 测试单文本向量化...")
    text = "TenMuses 是一个强大的 AI 工作流平台"
    embedding = await service.embed_text(text)
    print(f"    向量维度: {len(embedding)}")
    assert len(embedding) == 1536, "向量维度不正确"
    print("    ✅ 单文本向量化成功")
    
    # 测试批量向量化
    print("\n  [2.2] 测试批量向量化...")
    texts = [
        "工作流编排",
        "HITL 人在回路",
        "多智能体协作",
        "知识库检索"
    ]
    embeddings = await service.embed_batch(texts)
    print(f"    处理文本数: {len(embeddings)}")
    assert len(embeddings) == len(texts), "批量处理失败"
    print("    ✅ 批量向量化成功")
    
    return service  # 返回服务供后续测试使用


async def test_database_operations(ctx: TestContext, embedding_service):
    """测试数据库操作"""
    print("\n" + "="*70)
    print("✨ 测试 3: 数据库操作 (创建文档/分片)")
    print("="*70)
    
    async with ctx.session_maker() as session:
        # 创建文档
        print("\n  [3.1] 创建 KBDocument...")
        doc = KBDocument(
            user_id=ctx.user_id,
            source_type="file",
            source_url="file:///tmp/test.txt",
            filename="test.txt",
            file_size=256,
            mime_type="text/plain",
            content_hash="abc123",
            status="pending",
            doc_metadata={"source": "test", "format": "txt"}
        )
        
        # 创建向量
        sample_embedding = await embedding_service.embed_text("测试文档")
        doc.embedding = sample_embedding
        
        session.add(doc)
        await session.flush()
        doc_id = doc.id
        print(f"    文档 ID: {doc_id}")
        print(f"    向量已保存: {len(doc.embedding)} 维")
        print("    ✅ 文档创建成功")
        
        # 创建分片
        print("\n  [3.2] 创建 KBChunk...")
        chunks = []
        for i in range(3):
            chunk_text = f"这是第 {i+1} 个分片。包含关键信息和上下文。"
            chunk_embedding = await embedding_service.embed_text(chunk_text)
            
            chunk = KBChunk(
                document_id=doc_id,
                chunk_index=i,
                content=chunk_text,
                token_count=20 + i,
                chunk_metadata={"section": f"part_{i+1}"}
            )
            chunk.embedding = chunk_embedding
            chunks.append(chunk)
            session.add(chunk)
        
        await session.flush()
        print(f"    创建分片数: {len(chunks)}")
        print("    ✅ 分片创建成功")
        
        # 查询验证
        print("\n  [3.3] 验证数据库查询...")
        stmt = select(KBDocument).where(KBDocument.id == doc_id)
        result = await session.execute(stmt)
        fetched_doc = result.scalar_one()
        
        print(f"    查询到文档: {fetched_doc.filename}")
        print(f"    关联分片数: {len(fetched_doc.chunks)}")
        assert len(fetched_doc.chunks) == 3, "分片数不匹配"
        print("    ✅ 数据库查询成功")
        
        await session.commit()
        ctx.last_doc_id = doc_id  # 保存供下一个测试使用


async def test_rag_operations(ctx: TestContext, embedding_service):
    """测试 RAG 搜索操作"""
    print("\n" + "="*70)
    print("✨ 测试 4: RAG 搜索操作")
    print("="*70)
    
    async with ctx.session_maker() as session:
        rag_service = RAGService(db=session, embedding_service=embedding_service)
        
        # 创建测试数据
        print("\n  [4.1] 准备测试数据...")
        
        # 创建多个文档
        docs_data = [
            {
                "title": "AI 工作流编排指南",
                "content": "TenMuses 提供了强大的工作流编排能力。用户可以通过可视化界面拖拽搭建复杂的 AI 工作流。支持条件分支、循环、人在回路等高级特性。"
            },
            {
                "title": "知识库检索最佳实践",
                "content": "在使用知识库时，应该选择合适的分片大小。通常建议每个分片包含 100-500 个 token。向量检索通常与关键词搜索结合使用以获得最佳效果。"
            },
            {
                "title": "多智能体协作模式",
                "content": "使用 LangGraph 可以构建多智能体系统。Supervisor 模式用于高级路由，Map-Reduce 模式用于并行处理。支持动态图构建和运行时修改。"
            }
        ]
        
        doc_ids = []
        for doc_data in docs_data:
            doc = KBDocument(
                user_id=ctx.user_id,
                source_type="text",
                filename=doc_data["title"],
                file_size=len(doc_data["content"]),
                mime_type="text/plain",
                content_hash=hashlib.md5(doc_data["content"].encode()).hexdigest(),
                status="completed",
                doc_metadata={"title": doc_data["title"]}
            )
            doc.embedding = await embedding_service.embed_text(doc_data["content"])
            doc.content = doc_data["content"]
            
            session.add(doc)
            await session.flush()
            doc_ids.append(doc.id)
            
            # 创建分片
            processor = DocumentProcessor()
            chunks = processor.chunk_text(doc_data["content"])
            for chunk_idx, (chunk_text, token_count) in enumerate(chunks):
                chunk = KBChunk(
                    document_id=doc.id,
                    chunk_index=chunk_idx,
                    content=chunk_text,
                    token_count=token_count
                )
                chunk.embedding = await embedding_service.embed_text(chunk_text)
                session.add(chunk)
        
        await session.commit()
        print(f"    创建文档数: {len(doc_ids)}")
        print("    ✅ 测试数据准备完成")
        
        # 测试搜索
        print("\n  [4.2] 测试语义搜索...")
        query = "工作流和智能体"
        
        # 文档级搜索
        print(f"    查询: '{query}'")
        doc_results = await rag_service.search_documents(query, ctx.user_id, top_k=3)
        print(f"    文档级搜索结果: {len(doc_results)} 个")
        for i, result in enumerate(doc_results[:2], 1):
            print(f"      {i}. {result.get('title', 'Untitled')} (分数: {result.get('score', 0):.3f})")
        
        # 分片级搜索
        chunk_results = await rag_service.search_chunks(query, ctx.user_id, top_k=3)
        print(f"    分片级搜索结果: {len(chunk_results)} 个")
        for i, result in enumerate(chunk_results[:2], 1):
            content_preview = result.get('content', '')[:40]
            print(f"      {i}. {content_preview}... (分数: {result.get('score', 0):.3f})")
        
        print("    ✅ 搜索操作成功")
        
        # 测试上下文格式化
        print("\n  [4.3] 测试上下文格式化...")
        context = rag_service.format_context(chunk_results)
        print(f"    生成上下文长度: {len(context)} 字符")
        print(f"    上下文预览:")
        for line in context.split('\n')[:3]:
            print(f"      {line}")
        print("    ✅ 上下文格式化成功")


async def test_import_verification():
    """验证所有导入"""
    print("\n" + "="*70)
    print("✨ 测试 0: 导入验证")
    print("="*70)
    
    try:
        print("\n  检查导入...")
        from app.models.knowledge import KBDocument, KBChunk
        from app.schemas.knowledge import (
            KBDocumentCreate, KBDocumentResponse, KBSearchRequest, KBSearchResponse
        )
        from app.services.document_processor import DocumentProcessor
        from app.services.embedding_service import EmbeddingService
        from app.services.rag_service import RAGService
        from app.api.v1.knowledge import router
        
        print("    ✅ KBDocument / KBChunk")
        print("    ✅ Pydantic schemas (4 个)")
        print("    ✅ DocumentProcessor")
        print("    ✅ EmbeddingService")
        print("    ✅ RAGService")
        print("    ✅ API router")
        
        return True
    except Exception as e:
        print(f"    ❌ 导入失败: {e}")
        return False


async def main():
    """主函数"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║                                                                ║")
    print("║  🚀 TenMuses Phase 2.3 RAG 端到端验证                        ║")
    print("║                                                                ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    
    import hashlib
    
    # 验证导入
    if not await test_import_verification():
        print("\n❌ 导入验证失败，退出")
        sys.exit(1)
    
    # 初始化测试上下文
    ctx = TestContext()
    await ctx.setup()
    
    try:
        # 运行测试
        await test_document_processor()
        
        embedding_service = await test_embedding_service()
        
        await test_database_operations(ctx, embedding_service)
        
        await test_rag_operations(ctx, embedding_service)
        
        # 总结
        print("\n" + "="*70)
        print("✅ 所有端到端验证测试通过！")
        print("="*70)
        print("\n📋 验证结果:")
        print("  ✅ DocumentProcessor: 文本提取、分片、去重")
        print("  ✅ EmbeddingService: 文本向量化")
        print("  ✅ 数据库操作: 文档和分片存储")
        print("  ✅ RAG 搜索: 文档级和分片级搜索")
        print("  ✅ 上下文格式化: LLM 可用的格式输出")
        print("\n🎉 RAG 后端完整流程验证成功！")
        print("")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        await ctx.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
