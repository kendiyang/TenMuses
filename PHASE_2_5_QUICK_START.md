# RAG 系统快速启动指南

## 5 分钟快速开始

### 前置条件
```bash
# 检查 Python 版本 (3.10+)
python --version

# 检查 Node 版本 (18+)
node --version

# 检查 PostgreSQL 已安装
psql --version
```

### 第 1 步: 创建数据库

```bash
# 创建数据库
createdb tenmuses

# 验证
psql tenmuses -c "SELECT 1" 
# 输出应为: 1
```

### 第 2 步: 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
.\venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 创建 .env 文件
cat > .env << EOF
DATABASE_URL=postgresql://user:password@localhost/tenmuses
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-your-key-here
JWT_SECRET_KEY=your-secret-key
EOF

# 运行迁移脚本
python -m app.scripts.migrate_003_knowledge_base

# 启动服务器
uvicorn app.main:app --reload

# 检查 API 文档
open http://localhost:8000/docs
```

### 第 3 步: 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 创建 .env.local 文件
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
EOF

# 启动开发服务器
npm run dev

# 打开浏览器
open http://localhost:3000
```

## 功能演示 (3 步)

### 步骤 1: 上传文档

访问 http://localhost:3000/knowledge-base

1. 点击 "上传文档" 区域
2. 拖放一个 PDF/DOCX 文件
3. 等待处理完成 (显示 "已完成" 状态)

### 步骤 2: 配置工作流 RAG 节点

1. 访问 http://localhost:3000/workflows
2. 创建或打开工作流
3. 添加 "RAG 节点"
4. 在节点配置中:
   - ✅ 启用 RAG
   - 选择已上传的文档
   - 调整 topK (默认 5)
   - 调整 minScore (默认 0.5)

### 步骤 3: 执行工作流并查看搜索结果

1. 点击 "执行" 按钮
2. 输入查询文本 (例如: "什么是 RAG?")
3. 观看实时搜索结果
   - "RAG 搜索结果" 标签页
   - 显示相关文档片段
   - 显示相关性评分

## API 快速参考

### 上传文档

```bash
curl -X POST http://localhost:8000/api/v1/kb/upload \
  -H "Authorization: Bearer {token}" \
  -F "file=@document.pdf" \
  -F "title=My Document"
```

### 搜索文档

```bash
curl -X POST http://localhost:8000/api/v1/kb/search \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is RAG?",
    "top_k": 5,
    "min_score": 0.5,
    "search_chunks": true
  }'
```

### 列出文档

```bash
curl -X GET "http://localhost:8000/api/v1/kb/documents?status=completed" \
  -H "Authorization: Bearer {token}"
```

### 获取搜索上下文

```bash
curl -X GET "http://localhost:8000/api/v1/kb/search/context" \
  -H "Authorization: Bearer {token}" \
  -d '{
    "document_ids": ["doc1", "doc2"],
    "top_k": 3
  }'
```

## 配置调整

### RAG 参数

| 参数 | 范围 | 默认值 | 说明 |
|------|------|--------|------|
| topK | 1-20 | 5 | 返回最相关的 N 个结果 |
| minScore | 0.0-1.0 | 0.5 | 最小相关性分数 |
| ragMode | document/chunk | chunk | 搜索级别 |

### 性能优化

```python
# backend/app/services/rag_service.py

# 调整 HNSW 索引参数
CREATE INDEX kb_chunks_embedding_hnsw USING hnsw (embedding vector_cosine_ops)
  WITH (
    m=16,                    # 图的最大邻居数 (增加 = 更准确但更慢)
    ef_construction=200      # 构建参数 (增加 = 更准确)
  )

# 调整搜索参数
SET hnsw.ef_search = 100    # 查询参数 (增加 = 更准确但更慢)
```

## 故障排除

### 问题: "连接被拒绝" 错误

```bash
# 检查后端是否运行
curl http://localhost:8000/docs

# 检查数据库连接
psql -U postgres -d tenmuses -c "SELECT 1"

# 检查环境变量
echo $DATABASE_URL
echo $OPENAI_API_KEY
```

### 问题: WebSocket 连接失败

```typescript
// 在浏览器控制台检查
// 应该显示已连接
const ws = new WebSocket('ws://localhost:8000/ws/run/test')
ws.addEventListener('open', () => console.log('Connected!'))
```

### 问题: 搜索结果为空

```bash
# 检查文档是否已处理
curl -X GET "http://localhost:8000/api/v1/kb/documents" \
  -H "Authorization: Bearer {token}" | jq

# 验证嵌入服务
curl -X GET http://localhost:8000/api/v1/health

# 检查数据库中的分片
psql tenmuses -c "SELECT COUNT(*) FROM kb_chunks;"
```

## 开发快速命令

```bash
# 运行后端测试
cd backend
pytest test_rag_unit.py -v

# 运行前端构建
cd frontend
npm run build

# 类型检查
npm run type-check

# 代码格式化
npm run format

# 清空数据库并重新初始化
psql -U postgres -d tenmuses -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
python -m app.scripts.migrate_003_knowledge_base
```

## 集成到现有工作流

### 1. 添加 RAG 节点到工作流

```typescript
// frontend/src/components/workflow/WorkflowCanvas.tsx

import RagNodeConfig from '@/components/canvas/RagNodeConfig'

// 在节点类型处理中添加
if (selectedNode.type === 'rag') {
  return (
    <RagNodeConfig
      value={selectedNode.config}
      onChange={(newConfig) => updateNodeConfig(selectedNode.id, newConfig)}
    />
  )
}
```

### 2. 处理后端 RAG 执行

```python
# backend/app/api/v1/websocket.py

async def handle_rag_node(config, input_text, send_event):
    await send_event({
        'type': 'rag_search_started',
        'payload': { 'query': input_text, 'topK': config.topK }
    })
    
    results = await rag_service.search_chunks(
        query=input_text,
        top_k=config.topK,
        min_score=config.minScore,
        document_ids=config.knowledge_documents
    )
    
    await send_event({
        'type': 'rag_result',
        'payload': { 'results': results }
    })
    
    context = await rag_service.format_context(results)
    return context  # 用于后续节点
```

### 3. 在前端显示结果

```typescript
// 使用 ExecutionPanelRagIntegration 或自定义实现
import { useRagWebSocket } from '@/hooks/useRagWebSocket'
import RagSearchDisplay from '@/components/workflow/RagSearchDisplay'

export function WorkflowExecutionPanel() {
  const { state } = useRagWebSocket({ threadId, enabled: true })
  
  return <RagSearchDisplay state={state} />
}
```

## 监控和日志

### 后端日志

```bash
# 启用详细日志
LOG_LEVEL=DEBUG uvicorn app.main:app --reload

# 查看特定模块日志
grep "RAGService" app.log
```

### 前端日志

```typescript
// 启用 WebSocket 日志
localStorage.setItem('debug', 'websocket-client:*')

// 查看所有事件
wsClient.on('*', (event) => console.log('[Event]', event))
```

### 数据库日志

```sql
-- 启用查询日志
ALTER SYSTEM SET log_min_duration_statement = 100;
SELECT pg_reload_conf();

-- 查看慢查询
SELECT query, calls, mean_exec_time 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC;
```

## 生产部署

### 环境变量清单

```bash
# 后端
DATABASE_URL=postgresql://user:pass@prod-db/tenmuses
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...
JWT_SECRET_KEY=long-random-secret
ENVIRONMENT=production
LOG_LEVEL=INFO

# 前端
NEXT_PUBLIC_API_URL=https://api.example.com
NEXT_PUBLIC_WS_URL=wss://api.example.com
```

### Docker 部署

```dockerfile
# Dockerfile.backend
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app ./app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]

# Dockerfile.frontend
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
```

### 数据库备份

```bash
# 备份
pg_dump tenmuses > backup.sql

# 恢复
psql tenmuses < backup.sql

# 远程备份到 S3
pg_dump tenmuses | gzip | aws s3 cp - s3://bucket/backup.sql.gz
```

## 性能测试

```bash
# 加载测试 (需要 Apache Bench)
ab -n 1000 -c 10 http://localhost:8000/api/v1/health

# 压力测试 WebSocket
wscat -c ws://localhost:8000/ws/run/test --execute '{"action":"start","input":"test query"}'

# 数据库性能测试
pgbench -i -s 100 tenmuses
pgbench -c 10 -j 2 -t 1000 tenmuses
```

## 进一步的资源

- 📚 [RAG 完整实现总结](./PHASE_2_5_RAG_IMPLEMENTATION_FINAL_SUMMARY.md)
- 📡 [WebSocket 集成指南](./PHASE_2_5_WEBSOCKET_RAG_INTEGRATION_GUIDE.md)
- 🔧 [后端完成总结](./PHASE_2_5_RAG_BACKEND_COMPLETION.md)
- 🎨 [前端集成指南](./PHASE_2_5_FRONTEND_RAG_INTEGRATION_COMPLETE.md)
- ⚡ [快速参考](./PHASE_2_5_QUICK_REFERENCE.md)

---

**现在您已准备好运行完整的 RAG 系统了!** 🚀

有问题? 参考文档或查看源代码中的详细注释。
