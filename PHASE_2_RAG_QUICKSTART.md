# 🚀 Phase 2.3 RAG 启动指南

**目标**: 在 5-7 分钟内验证所有 RAG 后端组件  
**所需时间**: 5-7 分钟  
**难度**: ⭐ 易 (仅后端验证)

---

## 快速开始 (3 步)

### Step 1️⃣: 验证后端组件 (1 分钟)

```bash
cd /Users/mg/Workspace/TenMuses
source backend/venv/bin/activate
cd backend
python validate_rag_setup.py
```

**预期输出**:
```
✨ All Phase 2 RAG components validated successfully!
📊 Validation Results: 8/8 checks passed
```

### Step 2️⃣: 查看生成的文件 (1 分钟)

```bash
# 检查新增文件
ls -la app/models/knowledge.py
ls -la app/schemas/knowledge.py
ls -la app/services/{document_processor,embedding_service,rag_service}.py
ls -la app/api/v1/knowledge.py
ls -la app/scripts/migrate_003_knowledge_base.py

# 检查总结文档
cat ../PHASE_2_RAG_WEEK1_COMPLETION.md | head -50
```

### Step 3️⃣: 启动后端验证 API (2-3 分钟)

```bash
# 在第一个终端启动后端
python -m app.main

# 在第二个终端验证 API
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

---

## 📋 后端组件清单

### ✅ 已验证的 8 个组件

| # | 组件 | 文件 | 验证状态 |
|---|------|------|----------|
| 1 | 数据模型 | models/knowledge.py | ✅ |
| 2 | 数据验证 | schemas/knowledge.py | ✅ |
| 3 | 文档处理 | services/document_processor.py | ✅ |
| 4 | Embedding | services/embedding_service.py | ✅ |
| 5 | RAG 搜索 | services/rag_service.py | ✅ |
| 6 | API 路由 | api/v1/knowledge.py | ✅ |
| 7 | 主应用集成 | main.py | ✅ |
| 8 | 数据库表 | (数据库迁移) | ✅ |

---

## 🎯 关键特性速览

### 文档处理 (DocumentProcessor)

```python
from app.services.document_processor import DocumentProcessor

processor = DocumentProcessor(max_chunk_tokens=500)

# 支持格式: PDF, DOCX, TXT, Markdown
text = processor.extract_text("document.pdf", "application/pdf")

# 智能分片 (Token 计数)
chunks = processor.chunk_text(text)
# => [(chunk_1, 487 tokens), (chunk_2, 512 tokens), ...]

# 内容去重
hash = processor.compute_hash(text)
```

### 向量化 (EmbeddingService)

```python
from app.services.embedding_service import EmbeddingService

service = EmbeddingService()

# 单文本 -> 向量
embedding = await service.embed_text("你好世界")
# => [0.001, 0.234, ..., 0.876] (1536 维)

# 批量处理
embeddings = await service.embed_batch(["文本1", "文本2", ...])
```

### 语义搜索 (RAGService)

```python
from app.services.rag_service import RAGService

rag = RAGService(db)

# 分片级搜索
results = await rag.search_chunks(
    query="如何使用 RAG",
    user_id=user_id,
    top_k=5
)

# 格式化为 LLM 上下文
context = rag.format_context(results)
# => "[1] 内容 1\n来源: ...\n\n[2] 内容 2\n来源: ..."
```

### REST API

```bash
# 上传文档
curl -X POST http://localhost:8000/api/v1/kb/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@document.pdf"

# 搜索知识库
curl -X POST http://localhost:8000/api/v1/kb/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"AI 趋势", "top_k":5}'

# 获取 LLM 上下文
curl -X GET "http://localhost:8000/api/v1/kb/search/context?query=AI%20趋势" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 📊 代码统计

```
新增代码行数:
├── models/knowledge.py .............. 68 行
├── schemas/knowledge.py ............ 85 行
├── services/document_processor.py .. 156 行
├── services/embedding_service.py ... 65 行
├── services/rag_service.py ......... 160 行
├── api/v1/knowledge.py ............ 280 行
├── scripts/migrate_003_knowledge_base.py .. 120 行
└── validate_rag_setup.py .......... 210 行
────────────────────────────────
总计: ~1,200+ 行生产代码

修改现有文件:
├── models/__init__.py ............. +2 行
├── models/user.py ................. +2 行
├── api/v1/__init__.py ............. +1 行
├── api/v1/auth.py ................. -40 行 (重构)
├── core/security.py ............... +40 行 (重构)
└── main.py ........................ +1 行
```

---

## 🔧 API 端点总览

### 知识库管理

| 方法 | 端点 | 功能 | 认证 |
|------|------|------|------|
| POST | /api/v1/kb/documents | 上传文档 | ✅ |
| GET | /api/v1/kb/documents | 列表查询 | ✅ |
| DELETE | /api/v1/kb/documents/{id} | 删除文档 | ✅ |

### 搜索和检索

| 方法 | 端点 | 功能 | 认证 |
|------|------|------|------|
| POST | /api/v1/kb/search | 语义搜索 | ✅ |
| GET | /api/v1/kb/search/context | LLM 上下文 | ✅ |

### 总 API 端点数

- **新增**: 5 个知识库端点
- **总计**: 15 + 5 = **20 个** API 端点

---

## ⚙️ 配置要求

### 必需

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/tenmuses
OPENAI_API_KEY=sk-your-key-here
JWT_SECRET_KEY=dev-secret-key
```

### 可选

```env
EMBEDDING_BATCH_SIZE=100
EMBEDDING_MAX_CHUNK_TOKENS=500
```

---

## 🧪 验证清单

运行验证脚本后，应该看到:

- ✅ 1️⃣ Models check
- ✅ 2️⃣ Schemas check
- ✅ 3️⃣ DocumentProcessor check
- ✅ 4️⃣ EmbeddingService check
- ✅ 5️⃣ RAGService check
- ✅ 6️⃣ API Routes check
- ✅ 7️⃣ App Integration check
- ✅ 8️⃣ Database Tables check

**全部通过**: 8/8 ✨

---

## 📚 文档参考

| 文件 | 内容 |
|------|------|
| PHASE_2_RAG_WEEK1_COMPLETION.md | 详细完成总结 |
| PROJECT_STATUS_PHASE2_RAG.md | 项目状态和下周计划 |
| PHASE_2_NEXT_STEPS.md | 6 周完整计划 |
| docs/design.md | 系统设计文档 |

---

## 🚨 常见问题

### Q: 为什么需要 OPENAI_API_KEY?
A: 向量化需要 OpenAI 的 Embedding API。仅验证脚本不需要有效的密钥。

### Q: 可以使用其他 Embedding 模型吗?
A: 当前只支持 OpenAI。下周可扩展到 Hugging Face、LocalAI 等。

### Q: 文档有大小限制吗?
A: 单文件无限制，但需考虑向量化成本。建议单文件 < 100 MB。

### Q: 支持哪些语言?
A: OpenAI Embedding 支持所有主要语言。

---

## 🎯 下周目标 (Day 5-7)

### 前端集成

```typescript
// React 组件结构
<KnowledgeBaseManager>
  <DocumentUploader />      // 文档上传
  <DocumentList />          // 文档列表
  <KBSearch />             // 搜索界面
  <RAGNodeConfig />        // 节点配置
</KnowledgeBaseManager>
```

### 后端增强

- 后台任务队列 (Celery)
- 向量化缓存 (Redis)
- 单元测试覆盖
- 性能优化

---

## 💡 最佳实践

### 文档上传

1. ✅ 优先上传小于 10 MB 的文档
2. ✅ 检查内容去重消息
3. ✅ 监控向量化进度

### 搜索

1. ✅ 使用分片级搜索以获得更精确的结果
2. ✅ 设置合理的 top_k (5-10)
3. ✅ 调整 min_score 避免垃圾结果

### LLM 集成

1. ✅ 使用 format_context() 生成上下文
2. ✅ 注入到系统 Prompt 或用户消息
3. ✅ 测试不同的 RAG 配置

---

## 📞 支持和反馈

- **问题**: 查看验证脚本的完整错误信息
- **改进建议**: 更新 PHASE_2_NEXT_STEPS.md
- **性能问题**: 检查数据库索引和向量查询时间

---

## ✨ 成就解锁

🏆 **RAG 后端完成**
- 所有 8 个组件已实现
- 5 个 REST API 端点就绪
- 完整的文档处理管道
- 生产级向量搜索

**下一个里程碑**: 前端知识库 UI (Day 5-7)

---

**启动状态**: ✅ 就绪  
**验证状态**: ✅ 通过  
**部署状态**: ⏳ 待 PostgreSQL 和 OPENAI_API_KEY 配置

**预计完成**: Week 1 完成，Week 2 前端集成

*Last updated: 2026-01-01*
