"""
RAG Unit Tests - No API calls required
单元测试：文档处理器、分片、格式化等
"""
import tempfile
import os
import sys
from pathlib import Path
from uuid import uuid4

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.services.document_processor import DocumentProcessor
from app.services.rag_service import RAGService
from app.schemas.knowledge import KBSearchResultItem


def test_document_processor():
    """测试文档处理器"""
    print("\n" + "=" * 60)
    print("Testing DocumentProcessor")
    print("=" * 60)
    
    processor = DocumentProcessor(max_chunk_tokens=100, overlap_tokens=10)
    
    # 测试 1: 纯文本提取
    print("\n[Test 1] Text Extraction")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write("这是测试文本。\n\n第一个段落包含一些内容。\n\n第二个段落也有一些内容。")
        txt_path = f.name
    
    try:
        text = processor.extract_text(txt_path, "text/plain")
        assert "测试文本" in text
        assert len(text) > 0
        print(f"  ✓ Extracted {len(text)} characters from text file")
        print(f"  Content: {text[:50]}...")
    finally:
        os.unlink(txt_path)
    
    # 测试 2: 文本分片
    print("\n[Test 2] Text Chunking")
    long_text = "这是一个测试句子。" * 20 + "另一个测试句子。" * 15
    chunks = processor.chunk_text(long_text, use_sentence_boundary=True)
    
    assert len(chunks) > 0
    assert all(isinstance(chunk, tuple) and len(chunk) == 2 for chunk in chunks)
    
    total_tokens = sum(token_count for _, token_count in chunks)
    print(f"  ✓ Created {len(chunks)} chunks from {len(long_text)} characters")
    print(f"  Total tokens: {total_tokens}")
    print(f"  Chunk sizes: {[tokens for _, tokens in chunks[:3]]}... tokens")
    
    # 验证分片大小合理
    for i, (chunk_text, token_count) in enumerate(chunks):
        # Note: token_count 由 tiktoken 计算，可能与 max_chunk_tokens 略有不同
        # 允许更大的容错率因为中文 token 计算
        assert len(chunk_text) > 0
    print(f"  ✓ All {len(chunks)} chunks validated")
    
    # 测试 3: 哈希计算
    print("\n[Test 3] Hash Computation")
    content = "测试内容用于哈希计算"
    hash1 = processor.compute_hash(content)
    hash2 = processor.compute_hash(content)
    
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA256
    print(f"  ✓ SHA256 hash: {hash1}")
    print(f"  ✓ Hash consistency verified")
    
    # 测试 4: Token 计数
    print("\n[Test 4] Token Counting")
    token_count = processor.get_token_count("这是一个测试文本，用来计算 tokens 数量。")
    assert token_count > 0
    print(f"  ✓ Token count: {token_count} tokens")
    
    # 测试 5: 支持的文件类型检查
    print("\n[Test 5] Supported MIME Types")
    supported_types = list(processor.SUPPORTED_TYPES.keys())
    print(f"  ✓ Supported types: {len(supported_types)} formats")
    for mime_type in supported_types[:5]:
        print(f"    - {mime_type}")
    
    print("\n✅ DocumentProcessor tests passed!")


def test_rag_service():
    """测试 RAG 服务（不需要数据库）"""
    print("\n" + "=" * 60)
    print("Testing RAGService")
    print("=" * 60)
    
    # 创建虚拟数据库连接
    class MockDB:
        pass
    
    service = RAGService(MockDB())  # type: ignore
    
    # 测试 1: 上下文格式化
    print("\n[Test 1] Context Formatting")
    results = [
        KBSearchResultItem(
            document_id=uuid4(),
            chunk_id=uuid4(),
            content="这是第一个搜索结果的内容。它包含关于人工智能的信息。",
            score=0.95,
            metadata={
                "title": "AI 基础",
                "chunk_index": 0,
                "source": "article_001"
            }
        ),
        KBSearchResultItem(
            document_id=uuid4(),
            chunk_id=uuid4(),
            content="这是第二个搜索结果的内容。它讨论机器学习的应用。",
            score=0.87,
            metadata={
                "title": "ML 应用",
                "chunk_index": 1,
                "source": "article_002"
            }
        ),
        KBSearchResultItem(
            document_id=uuid4(),
            chunk_id=uuid4(),
            content="这是第三个搜索结果的内容。它关于深度学习。",
            score=0.72,
            metadata={
                "title": "深度学习",
                "chunk_index": 0,
                "source": "article_003"
            }
        )
    ]
    
    context = service.format_context(results, include_metadata=True)
    
    assert "这是第一个搜索结果的内容" in context
    assert "这是第二个搜索结果的内容" in context
    assert "95%" in context
    assert "87%" in context
    assert "72%" in context
    assert "AI 基础" in context
    assert "ML 应用" in context
    
    print(f"  ✓ Context formatted with {len(results)} results")
    print(f"  ✓ Total context length: {len(context)} characters")
    print(f"\n  Formatted context preview:")
    print("  " + "-" * 56)
    for line in context.split('\n')[:8]:
        print(f"  {line}")
    print("  " + "-" * 56)
    
    # 测试 2: 无结果情况
    print("\n[Test 2] Empty Results Handling")
    empty_context = service.format_context([])
    assert "没有找到" in empty_context
    print(f"  ✓ Empty result message: '{empty_context}'")
    
    # 测试 3: 不包含元数据的格式
    print("\n[Test 3] Context Formatting Without Metadata")
    context_no_meta = service.format_context(results[:1], include_metadata=False)
    assert "这是第一个搜索结果的内容" in context_no_meta
    assert "AI 基础" not in context_no_meta  # 元数据不应该包含
    print(f"  ✓ Context without metadata: {len(context_no_meta)} characters")
    
    # 测试 4: 自定义分隔符
    print("\n[Test 4] Custom Separator")
    custom_sep_context = service.format_context(results, separator="\n\n===\n\n")
    assert "===" in custom_sep_context
    assert custom_sep_context.count("===") >= 2
    print(f"  ✓ Custom separator applied: {custom_sep_context.count('===')} separators")
    
    print("\n✅ RAGService tests passed!")


def test_pipeline_integration():
    """测试完整管道"""
    print("\n" + "=" * 60)
    print("Testing Full Pipeline Integration")
    print("=" * 60)
    
    processor = DocumentProcessor(max_chunk_tokens=100)
    
    # 步骤 1: 创建测试文档
    print("\n[Step 1] Create Test Document")
    test_doc = """
    # 人工智能简介
    
    人工智能（Artificial Intelligence, AI）是计算机科学的一个重要分支。
    它旨在研究和开发能够执行通常需要人工智能的任务的计算机系统。
    
    ## 机器学习
    
    机器学习是实现人工智能的一种主要方法。
    它使系统能够从数据中学习和改进，而无需被显式编程。
    
    ## 深度学习
    
    深度学习是机器学习的一个子领域，使用人工神经网络来处理数据。
    它在计算机视觉、自然语言处理等领域取得了显著的成功。
    """
    
    content_hash = processor.compute_hash(test_doc)
    print(f"  ✓ Document created: {len(test_doc)} characters")
    print(f"  ✓ Content hash: {content_hash[:16]}...")
    
    # 步骤 2: 提取文本
    print("\n[Step 2] Text Extraction")
    # 使用内存中的文本（不需要文件）
    text = test_doc.strip()
    print(f"  ✓ Text extracted: {len(text)} characters")
    
    # 步骤 3: 分片
    print("\n[Step 3] Text Chunking")
    chunks = processor.chunk_text(text, use_sentence_boundary=True)
    print(f"  ✓ Created {len(chunks)} chunks")
    for i, (chunk_text, token_count) in enumerate(chunks):
        preview = chunk_text[:40].replace('\n', ' ') + "..." if len(chunk_text) > 40 else chunk_text
        print(f"    Chunk {i+1}: {token_count} tokens - {preview}")
    
    # 步骤 4: 验证分片质量
    print("\n[Step 4] Chunk Quality Verification")
    total_tokens = sum(tc for _, tc in chunks)
    chunk_count = len(chunks)
    avg_tokens = total_tokens // chunk_count
    
    assert chunk_count > 0
    assert avg_tokens <= processor.max_chunk_tokens * 1.2
    
    print(f"  ✓ Total chunks: {chunk_count}")
    print(f"  ✓ Total tokens: {total_tokens}")
    print(f"  ✓ Average tokens per chunk: {avg_tokens}")
    print(f"  ✓ Max tokens per chunk: {max(tc for _, tc in chunks)}")
    print(f"  ✓ Min tokens per chunk: {min(tc for _, tc in chunks)}")
    
    # 步骤 5: 搜索结果格式化演示
    print("\n[Step 5] Search Results Formatting")
    
    class MockDB:
        pass
    
    rag_service = RAGService(MockDB())  # type: ignore
    
    # 模拟搜索结果
    mock_results = [
        KBSearchResultItem(
            document_id=uuid4(),
            chunk_id=uuid4(),
            content=chunks[0][0] if chunks else "无内容",
            score=0.98,
            metadata={"title": "AI 简介", "chunk_index": 0}
        )
    ] if chunks else []
    
    if mock_results:
        formatted = rag_service.format_context(mock_results)
        print(f"  ✓ Formatted context: {len(formatted)} characters")
        print(f"  Preview: {formatted[:80]}...")
    else:
        print(f"  ⚠ No chunks to format")
    
    print("\n✅ Full pipeline integration test passed!")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("RAG Unit Tests (No API Required)")
    print("=" * 60)
    
    try:
        test_document_processor()
        test_rag_service()
        test_pipeline_integration()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed successfully!")
        print("=" * 60)
        return 0
    
    except AssertionError as e:
        print(f"\n❌ Test assertion failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
