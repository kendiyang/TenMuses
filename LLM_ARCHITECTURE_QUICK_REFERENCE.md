# 🚀 LLM 架构迁移 - 快速参考指南

## 📌 要点速览

### ✅ 迁移完成
- **所有 LLM 调用** 现在使用 `LLMClient` 统一接口
- **零硬编码密钥** - 所有凭证来自环境或数据库
- **完整的 LangChain 集成** - OpenAI 和 Anthropic 嵌入和模型

---

## 🎯 代码使用模式

### 模式 1: 同步 LLM 调用

```python
from app.services.llm_client import llm_client

result = await llm_client.invoke(
    messages=[HumanMessage(content="...")],
    provider="openai",  # 或 "anthropic"
    model="gpt-4-turbo-preview"
)
```

### 模式 2: 流式 LLM 调用

```python
from app.services.llm_client import llm_client

async for chunk in llm_client.stream(
    messages=[HumanMessage(content="...")],
    provider="openai",
    model="gpt-4-turbo-preview"
):
    print(chunk.content, end="")
```

### 模式 3: 向量化和嵌入

```python
from app.services.embedding_service import EmbeddingService

embedding_service = EmbeddingService(
    provider="openai",
    model="text-embedding-3-small"
)

embeddings = await embedding_service.embed_documents(texts)
```

### 模式 4: RAG 检索

```python
from app.services.rag_service import RAGService

rag_service = RAGService()

results = await rag_service.search(
    query="AI trends",
    user_id=user_id,
    top_k=5
)
```

---

## 📂 关键文件位置

| 文件 | 用途 |
|------|------|
| `backend/app/services/llm_client.py` | 核心 LLM 统一接口 |
| `backend/app/services/embedding_service.py` | 向量化服务 |
| `backend/app/services/rag_service.py` | RAG 检索服务 |
| `backend/app/services/langgraph_service.py` | LangGraph 工作流 |
| `backend/app/services/executor_library.py` | 节点执行器 |
| `backend/app/services/copilot_stream_service.py` | Copilot 流式服务 |

---

## 🔧 配置

### 环境变量

```bash
# .env 文件
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1  # 可选
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_BASE_URL=https://api.anthropic.com  # 可选
```

### 数据库配置

```python
# 或通过数据库存储（见 config_service.py）
# 使用 init-llm-config.py 初始化
```

---

## 🚫 避免以下做法

```python
# ❌ 错误：直接导入 AsyncOpenAI
from openai import AsyncOpenAI
client = AsyncOpenAI(api_key="sk-...")

# ❌ 错误：直接调用 API
response = await client.chat.completions.create(...)

# ❌ 错误：硬编码密钥
embedder = OpenAIEmbeddings(api_key="sk-...")
```

---

## ✅ 正确做法

```python
# ✅ 正确：使用 LLMClient
from app.services.llm_client import llm_client

result = await llm_client.invoke(
    messages=[HumanMessage(content="...")],
    provider="openai",
    model="gpt-4-turbo-preview"
)

# ✅ 正确：使用 EmbeddingService
from app.services.embedding_service import EmbeddingService

service = EmbeddingService(provider="openai")
embeddings = await service.embed_documents(texts)
```

---

## 📊 架构概览

```
┌─────────────────────────────────────────────┐
│         API Routes / Controllers            │
│  (websocket.py, workflows.py, dynamic.py)   │
└──────────────┬──────────────────────────────┘
               │
       ┌───────┴───────┐
       │               │
┌──────▼────────┐  ┌──▼─────────────────┐
│  Services     │  │  Executors         │
│  ├─ langgraph │  │  ├─ LLMNode        │
│  ├─ rag       │  │  ├─ ToolNode       │
│  ├─ document  │  │  ├─ RouterNode     │
│  └─ copilot   │  │  └─ MapNode        │
└──────┬────────┘  └──┬─────────────────┘
       │               │
       └───────┬───────┘
               │
        ┌──────▼─────────────────┐
        │  LLMClient (Core)      │
        │  ├─ ChatOpenAI         │
        │  ├─ ChatAnthropic      │
        │  └─ Fallbacks          │
        └──────┬─────────────────┘
               │
       ┌───────┴──────────┐
       │                  │
    ┌──▼───────┐   ┌──────▼────┐
    │ OpenAI   │   │ Anthropic  │
    │ API      │   │ API        │
    └──────────┘   └────────────┘
```

---

## 🧪 测试示例

```python
# tests/test_llm_integration.py
import pytest
from app.services.llm_client import llm_client
from langchain_core.messages import HumanMessage

@pytest.mark.asyncio
async def test_llm_invoke():
    result = await llm_client.invoke(
        messages=[HumanMessage(content="Hello")],
        provider="openai"
    )
    assert result is not None
    assert len(result) > 0

@pytest.mark.asyncio  
async def test_llm_stream():
    chunks = []
    async for chunk in llm_client.stream(
        messages=[HumanMessage(content="Hello")],
        provider="openai"
    ):
        chunks.append(chunk)
    assert len(chunks) > 0
```

---

## 🆘 故障排查

### 问题：`ModuleNotFoundError: No module named 'openai'`
**解决方案**: 使用 `LLMClient`，它已集成 OpenAI 库

### 问题：API 密钥未找到
**解决方案**: 
1. 检查 `.env` 文件中的 `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`
2. 或运行 `init-llm-config.py` 初始化数据库配置

### 问题：嵌入服务失败
**解决方案**: 确保使用 `EmbeddingService`，不是直接的 OpenAI 嵌入

---

## 📚 相关文档

- [LLM_MIGRATION_COMPLETE_REPORT.md](./LLM_MIGRATION_COMPLETE_REPORT.md) - 完整迁移报告
- [LLM_MIGRATION_GUIDE.md](./LLM_MIGRATION_GUIDE.md) - 详细迁移指南
- [backend/app/services/llm_client.py](./backend/app/services/llm_client.py) - 实现细节

---

**最后更新**: 2024年  
**状态**: ✅ 生产就绪
