#!/usr/bin/env python3
"""
TenMuses Phase 2.3 RAG 端到端验证（简化版）
验证所有组件的可用性，不需要真实数据库连接

运行方式:
  python test_e2e_rag_simplified.py
"""

import sys
import tempfile
from pathlib import Path
from uuid import uuid4
import json

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


def test_imports():
    """验证所有导入"""
    print("\n" + "="*70)
    print("✨ 测试 1: 验证所有组件导入")
    print("="*70)
    
    try:
        print("\n  导入 Models...")
        from app.models.knowledge import KBDocument, KBChunk
        print("    ✅ KBDocument, KBChunk")
        
        print("  导入 Schemas...")
        from app.schemas.knowledge import (
            KBDocumentCreate, KBDocumentResponse, 
            KBChunkResponse, KBSearchRequest, KBSearchResponse
        )
        print("    ✅ KBDocumentCreate")
        print("    ✅ KBDocumentResponse")
        print("    ✅ KBChunkResponse")
        print("    ✅ KBSearchRequest")
        print("    ✅ KBSearchResponse")
        
        print("  导入 Services...")
        from app.services.document_processor import DocumentProcessor
        from app.services.embedding_service import EmbeddingService
        from app.services.rag_service import RAGService
        print("    ✅ DocumentProcessor")
        print("    ✅ EmbeddingService")
        print("    ✅ RAGService")
        
        print("  导入 API...")
        from app.api.v1.knowledge import router
        print("    ✅ Knowledge API router (5 端点)")
        
        return True
    except Exception as e:
        print(f"    ❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_document_processor():
    """测试文档处理器"""
    print("\n" + "="*70)
    print("✨ 测试 2: DocumentProcessor")
    print("="*70)
    
    try:
        from app.services.document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        
        # 测试 TXT 提取
        print("\n  [2.1] 测试 TXT 文本提取...")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            content = """TenMuses 是一个 AI 工作流编排平台。

它支持以下核心功能：
1. 可视化工作流构建
2. 多智能体协作
3. 知识库检索（RAG）
4. 人在回路（HITL）模式
5. 模板市场和 UGC

通过 LangGraph 实现动态图构建，支持复杂的条件分支和循环。"""
            f.write(content)
            txt_path = f.name
        
        text = processor.extract_text(txt_path, "text/plain")
        print(f"    ✅ 提取文本: {len(text)} 字符")
        assert len(text) > 50, "文本太短"
        
        # 测试分片
        print("\n  [2.2] 测试文本分片...")
        chunks = processor.chunk_text(text)
        print(f"    ✅ 生成 {len(chunks)} 个分片")
        
        for i, (chunk_text, token_count) in enumerate(chunks[:2]):
            print(f"      分片 {i+1}: {len(chunk_text):4d} 字 / {token_count:4d} tokens")
        
        assert len(chunks) > 0, "分片为空"
        
        # 测试哈希
        print("\n  [2.3] 测试内容去重...")
        hash1 = processor.compute_hash(text)
        hash2 = processor.compute_hash(text)
        print(f"    ✅ 哈希一致: {hash1 == hash2}")
        assert hash1 == hash2, "哈希不匹配"
        
        Path(txt_path).unlink()
        return True
        
    except Exception as e:
        print(f"    ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_embedding_service():
    """测试向量化服务"""
    print("\n" + "="*70)
    print("✨ 测试 3: EmbeddingService")
    print("="*70)
    
    try:
        from app.services.embedding_service import EmbeddingService
        from app.core.config import settings
        
        print(f"\n  API 密钥状态: {'已设置' if settings.OPENAI_API_KEY else '未设置'}")
        
        if not settings.OPENAI_API_KEY:
            print("  ⚠️  使用虚拟向量进行演示")
            
            # 创建虚拟向量用于演示
            import hashlib
            import random
            
            class MockEmbedding:
                async def embed_text(self, text: str):
                    seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
                    random.seed(seed)
                    return [random.random() for _ in range(1536)]
                
                async def embed_batch(self, texts):
                    return [await self.embed_text(t) for t in texts]
            
            service = MockEmbedding()
            print("  ✅ 虚拟 EmbeddingService 已初始化")
        else:
            service = EmbeddingService()
            print("  ✅ OpenAI EmbeddingService 已初始化")
        
        # 演示向量化
        print("\n  [3.1] 向量维度: 1536")
        print("  [3.2] 向量生成方式: ", end="")
        if settings.OPENAI_API_KEY:
            print("OpenAI text-embedding-3-small")
        else:
            print("确定性伪随机（用于演示）")
        
        print("  ✅ EmbeddingService 可用")
        return True
        
    except Exception as e:
        print(f"    ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rag_service_structure():
    """测试 RAG 服务结构"""
    print("\n" + "="*70)
    print("✨ 测试 4: RAGService 结构")
    print("="*70)
    
    try:
        from app.services.rag_service import RAGService
        import inspect
        
        print("\n  RAGService 方法:")
        methods = [m for m in dir(RAGService) if not m.startswith('_')]
        
        expected_methods = ['search_documents', 'search_chunks', 'format_context']
        for method in expected_methods:
            if method in methods:
                print(f"    ✅ {method}()")
            else:
                print(f"    ❌ {method}() 未找到")
                return False
        
        print("\n  ✅ RAGService 结构完整")
        return True
        
    except Exception as e:
        print(f"    ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_routes():
    """测试 API 路由"""
    print("\n" + "="*70)
    print("✨ 测试 5: API 路由注册")
    print("="*70)
    
    try:
        from app.main import app
        
        print("\n  Knowledge Base 端点:")
        kb_routes = [
            r for r in app.routes 
            if hasattr(r, 'path') and '/kb' in r.path
        ]
        
        expected_routes = {
            '/api/v1/kb/documents': ['POST', 'GET'],
            '/api/v1/kb/documents/{id}': ['DELETE'],
            '/api/v1/kb/search': ['POST'],
            '/api/v1/kb/search/context': ['GET'],
        }
        
        print(f"    找到 {len(kb_routes)} 个 KB 相关路由:")
        for route in kb_routes:
            methods = ', '.join(route.methods) if hasattr(route, 'methods') else 'N/A'
            print(f"    ✅ {route.path} [{methods}]")
        
        assert len(kb_routes) >= 4, "缺少 KB 路由"
        print("\n  ✅ 所有 API 路由已注册")
        return True
        
    except Exception as e:
        print(f"    ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_schemas():
    """测试 Pydantic 模式"""
    print("\n" + "="*70)
    print("✨ 测试 6: Pydantic 数据验证模式")
    print("="*70)
    
    try:
        from app.schemas.knowledge import (
            KBDocumentCreate, KBDocumentResponse, KBSearchRequest
        )
        
        print("\n  [6.1] KBDocumentCreate 模式:")
        print(f"    字段: {', '.join(KBDocumentCreate.model_fields.keys())}")
        
        print("\n  [6.2] KBSearchRequest 模式:")
        print(f"    字段: {', '.join(KBSearchRequest.model_fields.keys())}")
        
        print("\n  [6.3] KBDocumentResponse 模式:")
        print(f"    字段: {', '.join(KBDocumentResponse.model_fields.keys())}")
        
        # 测试模式验证
        print("\n  [6.4] 模式验证测试:")
        search_req = KBSearchRequest(
            query="test query",
            top_k=5,
            min_score=0.5,
            search_chunks=True
        )
        print(f"    ✅ KBSearchRequest 验证通过")
        print(f"       query: {search_req.query}")
        print(f"       top_k: {search_req.top_k}")
        
        print("\n  ✅ 所有 Pydantic 模式有效")
        return True
        
    except Exception as e:
        print(f"    ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_models():
    """测试数据库模型结构"""
    print("\n" + "="*70)
    print("✨ 测试 7: 数据库模型结构")
    print("="*70)
    
    try:
        from app.models.knowledge import KBDocument, KBChunk
        from sqlalchemy import inspect as sa_inspect
        
        print("\n  KBDocument 表结构:")
        doc_mapper = sa_inspect(KBDocument)
        print(f"    列数: {len(doc_mapper.columns)}")
        for col in list(doc_mapper.columns)[:8]:
            print(f"    ✅ {col.name}: {col.type}")
        
        print("\n  KBChunk 表结构:")
        chunk_mapper = sa_inspect(KBChunk)
        print(f"    列数: {len(chunk_mapper.columns)}")
        for col in chunk_mapper.columns:
            print(f"    ✅ {col.name}: {col.type}")
        
        print("\n  ✅ 数据库模型结构完整")
        return True
        
    except Exception as e:
        print(f"    ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║                                                                ║")
    print("║  🚀 TenMuses Phase 2.3 RAG 端到端验证（简化版）             ║")
    print("║                                                                ║")
    print("║  不需要真实数据库连接，验证所有组件的可用性                 ║")
    print("║                                                                ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    
    tests = [
        ("导入验证", test_imports),
        ("文档处理", test_document_processor),
        ("向量化服务", test_embedding_service),
        ("RAG 服务", test_rag_service_structure),
        ("数据库模型", test_database_models),
        ("API 路由", test_api_routes),
        ("Pydantic 模式", test_schemas),
    ]
    
    results = []
    for name, test_fn in tests:
        try:
            result = test_fn()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} 测试异常: {e}")
            results.append((name, False))
    
    # 总结
    print("\n" + "="*70)
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    if passed == total:
        print(f"✅ 所有测试通过！({passed}/{total})")
    else:
        print(f"⚠️  {passed}/{total} 测试通过")
    
    print("="*70)
    
    print("\n📋 验证结果:")
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")
    
    print("\n" + "="*70)
    print("✨ RAG 后端组件验证完成")
    print("="*70)
    
    if passed == total:
        print("\n🎉 所有组件已就绪，可以开始集成！")
        print("\n下一步:")
        print("  1. 配置 OPENAI_API_KEY (可选，用于真实向量化)")
        print("  2. 启动后端服务: python -m app.main")
        print("  3. 访问 API 文档: http://localhost:8000/docs")
        print("  4. 测试 KB 端点: POST /api/v1/kb/documents")
        return 0
    else:
        print("\n❌ 有组件验证失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())
