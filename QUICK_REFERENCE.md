# TenMuses RAG 集成 - 快速参考手册

## 🎯 当前状态（2026-01-01）

**Phase**: 2.3 RAG 集成  
**Progress**: 48% overall (Phase 2.3 Week 2 Day 3 完成)  
**Status**: ✅ 后端验证完成 + 前端框架就绪

---

## ⚡ 5 分钟快速开始

### 验证后端是否工作 ✅

```bash
cd backend
python test_e2e_rag_simplified.py
# 期望输出: 7/7 tests passed ✅
```

### 启动完整系统

```bash
# Terminal 1: 后端
cd backend
source venv/bin/activate
python -m app.main
# 访问: http://localhost:8000/docs

# Terminal 2: 前端
cd frontend
npm run dev
# 访问: http://localhost:3000/knowledge-base
```

---

## 📂 核心文件位置

### 后端 RAG 组件
| 文件 | 用途 |
|------|------|
| `backend/app/models/knowledge.py` | 数据模型 (KBDocument, KBChunk) |
| `backend/app/schemas/knowledge.py` | 请求/响应验证 (Pydantic) |
| `backend/app/services/document_processor.py` | 文本提取、分片、去重 |
| `backend/app/services/embedding_service.py` | 向量化服务 |
| `backend/app/services/rag_service.py` | 搜索和上下文生成 |
| `backend/app/api/v1/knowledge.py` | REST API 端点 (5 个) |

### 前端知识库 UI
| 文件 | 组件 |
|------|------|
| `frontend/src/app/knowledge-base/page.tsx` | 主页面 |
| `frontend/src/components/knowledge/DocumentsList.tsx` | 文档列表 |
| `frontend/src/components/knowledge/UploadSection.tsx` | 文件上传 |
| `frontend/src/components/knowledge/SearchSection.tsx` | 搜索参数 |
| `frontend/src/components/knowledge/SearchResults.tsx` | 结果展示 |
| `frontend/src/components/knowledge/DocumentDetail.tsx` | 文档详情 |

### 工作流集成
| 文件 | 用途 |
|------|------|
| `frontend/src/components/canvas/RagNodeConfig.tsx` | RAG 节点配置UI |

---

## 🔌 API 端点速查

### 文档管理
```
POST   /api/v1/kb/documents              上传文档
GET    /api/v1/kb/documents              列出文档 (分页)
DELETE /api/v1/kb/documents/{document_id} 删除文档
```

### 搜索
```
POST   /api/v1/kb/search                 语义搜索
       body: {
         "query": "搜索词",
         "top_k": 5,
         "min_score": 0.5,
         "search_chunks": false  // true=分片级, false=文档级
       }

GET    /api/v1/kb/search/context         获取格式化上下文
```

**认证**: 所有请求需要 Bearer token
```
Authorization: Bearer {access_token}
```

---

## 📋 测试清单

### 后端验证
- [x] 7/7 组件导入成功
- [x] 5 个 API 路由已注册
- [x] 数据库模型定义完整
- [x] Pydantic 验证模式工作
- [ ] 实际文件上传测试 (待做)
- [ ] 搜索端到端流程 (待做)

### 前端功能
- [x] 知识库管理页面
- [x] 文件上传组件
- [x] 搜索结果显示
- [x] 文档详情展示
- [x] RAG 节点配置
- [ ] API 集成测试 (待做)
- [ ] UI 交互测试 (待做)

---

## 🚀 接下来要做什么

### 今天/明天 (Day 4-5)

**优先级: 高** - 必须完成

1. **工作流执行集成**
   - 在 workflow engine 中检查 RAG 配置
   - 如启用，执行 `rag_service.search_chunks()`
   - 将结果注入到 LLM prompt 中

2. **端到端 API 测试**
   ```bash
   # 测试上传 → 搜索 → 获取上下文 完整流程
   ```

3. **错误处理完善**
   - 文件大小验证
   - API 错误响应
   - 用户友好的提示

### 本周末 (Day 6-7)

**优先级: 中** - 推荐实现

4. **后台任务队列** (Celery + Redis)
   - 异步向量化处理
   - 长文件处理

5. **缓存层优化**
   - Redis 搜索结果缓存
   - 热门查询加速

### 下周+ (Week 3+)

**优先级: 低** - 进一步改进

6. **测试覆盖**
   - 单元测试 (pytest)
   - 集成测试
   - E2E 测试 (Playwright)

7. **前端优化**
   - 响应式设计
   - 深色模式
   - 无障碍支持

---

## 🔧 关键配置

### 环境变量 (backend/.env)
```bash
# 数据库
DATABASE_URL=postgresql+asyncpg://postgres:password@host.docker.internal:5432/tenmuses

# LLM API (可选 - 用于真实向量化)
OPENAI_API_KEY=sk-xxx...
ANTHROPIC_API_KEY=sk-xxx...

# JWT
JWT_SECRET_KEY=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256
```

### 依赖包
```bash
# 后端依赖 (已安装)
pip install fastapi sqlalchemy asyncpg pydantic
pip install pypdf python-docx tiktoken
pip install openai anthropic

# 前端依赖 (已安装)
npm install next react react-dom
npm install @/components/ui lucide-react
```

---

## 💾 数据库

### 表结构

**KBDocument** (16 列)
- id (UUID)
- user_id (UUID) - FK to users
- filename (VARCHAR)
- file_size (INTEGER)
- source_type (VARCHAR) - file | url | text
- embedding (VECTOR(1536)) - pgvector
- status (VARCHAR) - pending | processing | completed | failed
- chunk_count (INTEGER)
- created_at, updated_at (TIMESTAMP)
- ...等

**KBChunk** (8 列)
- id (UUID)
- document_id (UUID) - FK to kb_documents
- chunk_index (INTEGER)
- content (TEXT)
- token_count (INTEGER)
- embedding (VECTOR(1536))
- metadata (JSONB)
- created_at (TIMESTAMP)

### 索引
- B-Tree: document_id, user_id, status
- HNSW (向量): embedding (支持快速相似搜索)

---

## 📚 文档参考

| 文档 | 内容 |
|------|------|
| [PHASE_2_3_FRONTEND_GUIDE.md](../PHASE_2_3_FRONTEND_GUIDE.md) | 前端实现详细指南 |
| [PHASE_2_3_E2E_VERIFICATION_COMPLETE.md](../PHASE_2_3_E2E_VERIFICATION_COMPLETE.md) | 验证完成报告 |
| [PHASE_2_3_RAG_IMPLEMENTATION_STATUS.md](../PHASE_2_3_RAG_IMPLEMENTATION_STATUS.md) | 实现状态 |
| [docs/design.md](../docs/design.md) | 系统设计文档 |
| [PHASE_2_RAG_QUICKSTART.md](../PHASE_2_RAG_QUICKSTART.md) | 快速启动指南 |

---

## 🎓 代码示例

### 后端：搜索文档
```python
from app.services.rag_service import RAGService

service = RAGService(db=session, embedding_service=emb_svc)
results = await service.search_chunks(
    query="AI 工作流",
    user_id=user_id,
    top_k=5,
    min_score=0.5
)
context = service.format_context(results)
```

### 前端：上传文件
```typescript
const formData = new FormData()
formData.append('file', file)

const response = await fetch('/api/v1/kb/documents', {
  method: 'POST',
  headers: { Authorization: `Bearer ${token}` },
  body: formData
})
```

### 前端：搜索
```typescript
const response = await fetch('/api/v1/kb/search', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`
  },
  body: JSON.stringify({
    query: '搜索词',
    top_k: 5,
    search_chunks: true
  })
})
```

---

## 🐛 常见问题

### Q: 后端验证失败
**A**: 检查：
1. PostgreSQL 是否运行: `docker ps | grep postgres`
2. Python 虚拟环境是否激活
3. 依赖是否安装: `pip list | grep pydantic`

### Q: API 返回 401
**A**: 检查：
1. Token 是否有效
2. 前端是否正确设置 `Authorization` header
3. `.env` 中 `JWT_SECRET_KEY` 是否与后端一致

### Q: 搜索返回空结果
**A**: 可能原因：
1. 文档还在处理中 (status = pending/processing)
2. 相关性阈值 (min_score) 设置太高
3. 向量化失败 (检查 OPENAI_API_KEY)

### Q: 前端组件未显示
**A**: 检查：
1. API 错误响应（浏览器 F12 → Network）
2. 认证 token 是否正确
3. 后端服务是否在运行

---

## 📞 调试技巧

### 查看后端日志
```bash
cd backend && python -m app.main 2>&1 | grep -i "error\|warn"
```

### 测试 API 端点
```bash
# 使用 curl
curl -X GET http://localhost:8000/api/v1/kb/documents \
  -H "Authorization: Bearer YOUR_TOKEN"

# 使用 API 文档
http://localhost:8000/docs
```

### 前端调试
```javascript
// 在浏览器控制台
localStorage.getItem('accessToken')  // 检查 token
fetch('/api/v1/kb/documents').then(r => r.json())  // 测试 API
```

---

## ✅ 完成检查表

项目完成时：
- [ ] 所有后端测试通过 (7/7)
- [ ] 前端知识库页面可访问
- [ ] 文件上传功能工作
- [ ] 搜索功能工作
- [ ] 工作流 RAG 节点可配置
- [ ] 工作流执行集成完成
- [ ] API 端到端测试通过
- [ ] 文档完成和更新

---

## 🎯 下一里程碑

**Phase 2.3 Week 3**: 优化与测试
- [ ] 后台任务队列实现
- [ ] 缓存层部署
- [ ] 单元测试编写
- [ ] 性能优化

**Phase 2.4**: Copilot 集成
- [ ] CopilotKit 前端集成
- [ ] 自然语言工作流生成
- [ ] 画布编辑建议

---

**更新时间**: 2026-01-01  
**维护者**: AI Assistant  
**状态**: 🟢 Ready for continuation

