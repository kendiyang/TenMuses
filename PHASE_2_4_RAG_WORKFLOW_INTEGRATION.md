# Phase 2.4: 工作流执行 RAG 集成（Day 4-5）

> **版本**: 1.0  
> **日期**: 2026-01-01  
> **状态**: 🟢 实施指南  
> **进度**: 50% → 55% (预期)

---

## 📋 概述

### 目标

在工作流执行时集成 RAG（检索增强生成），使得 LLM 节点可以自动从知识库检索相关文档并注入到 prompt 中，显著提升生成质量。

### 核心功能

- ✅ LLM 节点支持 RAG 配置
- ✅ 自动检索和上下文注入
- ✅ WebSocket 事件实时显示检索进度
- ✅ 执行面板展示 RAG 结果
- ✅ 端到端工作流验证

### 工作流图解

```
用户输入
    ↓
[工作流开始]
    ↓
[LLM节点-启用RAG]
    ├─→ 提取 Query
    ├─→ 执行 RAG 检索 ✨ (新增)
    │   └─→ 调用 RAGService.search_chunks()
    │   └─→ 发送 "rag_search" 事件
    ├─→ 格式化上下文 (新增)
    ├─→ 注入 RAG 上下文到 Prompt (新增)
    ├─→ 调用 LLM 生成响应
    └─→ 流式返回 Token
    ↓
[后续节点或完成]
    ↓
用户查看结果
```

---

## 🔧 技术实现

### 1. LLMConfig 扩展

#### 文件: `backend/app/schemas/node.py`

```python
class LLMConfig(BaseModel):
    """LLM节点配置 - 扩展了RAG支持"""
    
    # 基础配置
    provider: Literal["openai", "anthropic"] = "openai"
    model: str = "gpt-4-turbo-preview"
    temperature: float = Field(default=0.7, ge=0, le=1)
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    
    # ✨ RAG 配置 - 新增字段
    enable_rag: bool = Field(
        default=False, 
        description="是否启用知识库检索"
    )
    knowledge_documents: List[str] = Field(
        default_factory=list, 
        description="知识库文档ID列表"
    )
    rag_mode: Literal["document", "chunk"] = Field(
        default="chunk", 
        description="检索模式: 文档级或分片级"
    )
    rag_top_k: int = Field(
        default=5, 
        ge=1, le=20,
        description="检索结果数量"
    )
    rag_min_score: float = Field(
        default=0.5, 
        ge=0.0, le=1.0,
        description="最小相关性阈值"
    )
```

**改动说明:**
- ✅ 已实现 (见 [node.py 第 45-60 行](../backend/app/schemas/node.py#L45-L60))
- 向后兼容: 所有新字段均有默认值
- 不会影响现有工作流

### 2. StreamingLLMNodeExecutor 增强

#### 文件: `backend/app/services/executor_library.py`

新增三个关键方法：

```python
class StreamingLLMNodeExecutor(LLMNodeExecutor):
    """支持RAG的流式LLM执行器"""
    
    def __init__(self, node, stream_callback=None, 
                 user_id: Optional[str] = None, 
                 db_session=None):
        super().__init__(node)
        self.stream_callback = stream_callback
        self.user_id = user_id
        self.db_session = db_session
    
    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        """执行LLM节点，支持RAG检索"""
        config = self.node.data.llm_config
        
        # ... 准备输入 ...
        
        # ✨ 第一步：RAG检索（如果启用）
        rag_context = ""
        if config.enable_rag and config.knowledge_documents:
            rag_context = await self._retrieve_rag_context_with_query(
                query=prompt,
                config=config
            )
            
            # 发送RAG搜索事件到WebSocket
            if self.stream_callback:
                await self.stream_callback({
                    "type": "rag_search",
                    "nodeId": self.node.id,
                    "payload": {
                        "query": prompt,
                        "context": rag_context,
                        "documentCount": len(config.knowledge_documents),
                        "topK": config.rag_top_k,
                        "mode": config.rag_mode
                    }
                })
        
        # ✨ 第二步：注入RAG上下文
        enhanced_prompt = self._inject_rag_context(prompt, rag_context)
        
        # ... 调用LLM ...
```

**关键方法:**

1. `_retrieve_rag_context_with_query(query, config)`
   - 调用 `RAGService.search_chunks()` 或 `search_documents()`
   - 返回格式化的知识库上下文

2. `_inject_rag_context(prompt, rag_context)`
   - 将知识库内容注入到 prompt 前面
   - 返回增强后的 prompt

3. `execute(state)`
   - 协调 RAG 检索和 LLM 调用

**改动说明:**
- ✅ 已实现 (见 [executor_library.py 第 39-220 行](../backend/app/services/executor_library.py#L39-L220))
- 完全向后兼容
- RAG 检索为可选功能

### 3. WebSocket 事件扩展

#### 新事件类型: `rag_search`

```json
{
  "type": "rag_search",
  "nodeId": "research-with-rag",
  "threadId": "thread-001",
  "payload": {
    "query": "用户原始查询",
    "context": "【知识库检索结果】\n...",
    "documentCount": 3,
    "topK": 5,
    "mode": "chunk",
    "resultsCount": 3
  }
}
```

**事件流序列:**

```
1. run_started
2. node_started ("research-with-rag")
3. node_status (status: "executing")
4. rag_search ✨ (新增 - 仅当启用RAG时)
5. token (流式Token多个)
6. node_status (status: "completed")
7. run_completed
```

---

## 📐 架构图

### 数据流

```
┌─────────────────────────────────────────────────────────────┐
│                    WebSocket 连接建立                        │
└─────────────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────────┐
│              工作流执行 (DynamicGraphFactory)               │
└─────────────────────────────────────────────────────────────┘
           ↓
    ┌─────────────────────┐
    │  LLM 节点开始       │
    │ (research-with-rag) │
    └─────────────────────┘
           ↓
    检查: enable_rag?
    ├─ YES ✨
    │   └─→ StreamingLLMNodeExecutor._retrieve_rag_context()
    │       ├─→ RAGService.search_chunks(query, user_id, top_k, min_score)
    │       └─→ RAGService.format_context(results)
    │           └─→ 推送 rag_search 事件
    │
    └─ NO
        └─→ 直接调用 LLM
           ↓
    StreamingLLMNodeExecutor._inject_rag_context()
    └─→ 增强的 Prompt: 知识库上下文 + 原始 Query
           ↓
    llm_client.stream()
    └─→ 推送 token 事件（流式）
           ↓
    保存结果到 state.context
```

### 模块依赖

```
StreamingLLMNodeExecutor
  ├─ RAGService (延迟导入，避免循环)
  ├─ llm_client (调用LLM)
  └─ stream_callback (WebSocket事件)

RAGService
  ├─ KBDocument (数据模型)
  ├─ KBChunk (数据模型)
  ├─ EmbeddingService (向量化)
  └─ AsyncSession (数据库)
```

---

## ✅ 实施清单

### Day 4 上午 ✓ 完成

- [x] 扩展 LLMConfig 数据模型
- [x] 实现 StreamingLLMNodeExecutor RAG 方法
- [x] 定义 WebSocket rag_search 事件
- [x] 创建演示脚本和文档

### Day 4 下午 (待做)

- [ ] 更新 DynamicGraphFactory 传递用户ID和DB会话
- [ ] 集成到工作流执行管道
- [ ] 修改 WebSocket 事件推送

### Day 5 上午 (待做)

- [ ] 前端接收 rag_search 事件
- [ ] 在执行面板显示 RAG 结果
- [ ] 显示检索的文档列表

### Day 5 下午 (待做)

- [ ] 端到端集成测试
- [ ] 错误处理和边界情况
- [ ] 文档和使用指南

---

## 🚀 使用指南

### 创建启用RAG的工作流

#### 1. 创建工作流 JSON

```json
{
  "nodes": [
    {
      "id": "research",
      "type": "llm",
      "data": {
        "label": "Research with Knowledge Base",
        "llm_config": {
          "provider": "openai",
          "model": "gpt-4-turbo-preview",
          "temperature": 0.7,
          "max_tokens": 2000,
          
          "enable_rag": true,
          "knowledge_documents": ["doc-1", "doc-2", "doc-3"],
          "rag_mode": "chunk",
          "rag_top_k": 5,
          "rag_min_score": 0.5
        }
      }
    }
  ]
}
```

#### 2. 上传知识库文档

```bash
curl -X POST http://localhost:8000/api/v1/kb/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@ai_trends.pdf" \
  -F "source_type=file"
```

获取返回的 `document_id`，添加到工作流的 `knowledge_documents` 列表。

#### 3. 执行工作流

```bash
curl -X POST http://localhost:8000/api/v1/workflows/{workflow_id}/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": "请分析2024年的AI趋势"
  }'
```

返回:
```json
{
  "runId": "run-123",
  "threadId": "thread-456",
  "wsUrl": "ws://localhost:8000/ws/run/thread-456"
}
```

#### 4. 连接 WebSocket 并接收事件

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/run/thread-456");

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.type === "rag_search") {
    // 显示RAG搜索结果
    console.log("检索到文档:", message.payload.resultsCount);
    console.log("上下文:", message.payload.context);
  } else if (message.type === "token") {
    // 逐字显示Token
    console.log(message.payload.content);
  }
};
```

---

## 🔌 API 集成点

### 现有API（保持不变）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/kb/documents` | POST | 上传知识库文档 |
| `/api/v1/kb/documents` | GET | 列表文档 |
| `/api/v1/kb/search` | POST | 手动搜索 |

### 工作流执行API（已有）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/workflows` | GET | 列表工作流 |
| `/api/v1/workflows` | POST | 创建工作流 |
| `/api/v1/workflows/{id}` | GET | 获取工作流 |
| `/api/v1/workflows/{id}` | PUT | 更新工作流 |
| `/api/v1/workflows/{id}/run` | POST | 执行工作流 |
| `/ws/run/{thread_id}` | WS | WebSocket执行流 |

### 新增事件（WebSocket）

| 事件类型 | 触发条件 | 说明 |
|---------|--------|------|
| `rag_search` | LLM节点启用RAG | RAG搜索完成时推送 |

---

## 🧪 测试方案

### 单元测试

```python
# test_rag_execution.py

async def test_rag_retrieval():
    """测试RAG检索"""
    executor = StreamingLLMNodeExecutor(
        node=create_llm_node_with_rag(),
        user_id="user-1",
        db_session=db
    )
    
    context = await executor._retrieve_rag_context_with_query(
        query="AI trends",
        config=llm_config
    )
    
    assert len(context) > 0
    assert "【知识库检索结果】" in context

async def test_rag_context_injection():
    """测试上下文注入"""
    executor = StreamingLLMNodeExecutor(...)
    
    original = "What is RAG?"
    context = "RAG is..."
    
    enhanced = executor._inject_rag_context(original, context)
    
    assert context in enhanced
    assert original in enhanced
```

### 集成测试

```python
# test_rag_workflow_e2e.py

async def test_full_workflow_with_rag():
    """测试完整工作流"""
    # 1. 上传文档
    doc_id = await upload_document("ai_trends.pdf")
    
    # 2. 创建工作流
    workflow = create_workflow_with_rag([doc_id])
    
    # 3. 执行工作流
    events = []
    async for event in execute_workflow_streaming(workflow):
        events.append(event)
    
    # 4. 验证事件
    rag_events = [e for e in events if e["type"] == "rag_search"]
    assert len(rag_events) > 0
    
    token_events = [e for e in events if e["type"] == "token"]
    assert len(token_events) > 0
```

### 手动测试

见 `demo_rag_workflow_integration.py`，运行：

```bash
python backend/demo_rag_workflow_integration.py
```

---

## 📊 性能指标

### 预期性能

| 指标 | 目标 | 说明 |
|------|------|------|
| RAG检索延迟 | < 500ms | 向量搜索延迟 |
| Token生成速度 | > 30 tokens/s | 流式生成速度 |
| 内存占用 | < 500MB | 单个执行 |
| 并发数 | >= 10 | 同时执行数 |

### 监控指标

```python
# 在WebSocket中添加时间戳
{
  "type": "rag_search",
  "payload": {
    "startTime": 1234567890,
    "endTime": 1234567891,
    "durationMs": 1050,  # RAG检索耗时
    ...
  }
}
```

---

## 🐛 错误处理

### RAG检索失败

```python
async def _retrieve_rag_context_with_query(self, query, config):
    try:
        results = await rag_service.search_chunks(...)
        return rag_service.format_context(results)
    except Exception as e:
        # RAG失败不应阻止LLM执行
        logger.warning(f"RAG检索失败: {e}")
        return ""  # 返回空，继续执行
```

### 知识库文档不存在

```python
if config.knowledge_documents:
    # 验证文档ID是否有效
    valid_docs = await db.execute(
        select(KBDocument).filter(
            KBDocument.id.in_(config.knowledge_documents)
        )
    )
    
    if not valid_docs:
        logger.warning("指定的知识库文档不存在")
        rag_context = ""
```

---

## 📚 参考资源

### 相关文件

- [LLMConfig 定义](../backend/app/schemas/node.py#L45)
- [StreamingLLMNodeExecutor](../backend/app/services/executor_library.py#L39)
- [RAGService](../backend/app/services/rag_service.py)
- [演示脚本](../backend/demo_rag_workflow_integration.py)

### 文档

- [Phase 2.3 RAG 实现状态](PHASE_2_3_RAG_IMPLEMENTATION_STATUS.md)
- [系统设计](docs/design.md)
- [RAG 快速开始](PHASE_2_RAG_QUICKSTART.md)

---

## 📅 下一步

### Week 2 (Day 6-7)

- [ ] 前端工作流编辑器RAG配置UI
- [ ] 执行面板RAG结果展示
- [ ] 历史记录和重放

### Week 3+

- [ ] Celery异步任务队列
- [ ] Redis缓存层
- [ ] HITL中断机制
- [ ] 性能优化

---

## ✨ 快速参考

### 启用RAG的最小配置

```json
{
  "enable_rag": true,
  "knowledge_documents": ["doc-1"],
  "rag_mode": "chunk",
  "rag_top_k": 5,
  "rag_min_score": 0.5
}
```

### WebSocket事件监听

```javascript
const ws = new WebSocket(wsUrl);

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  
  switch(msg.type) {
    case "rag_search":
      displayRagResults(msg.payload);
      break;
    case "token":
      displayToken(msg.payload.content);
      break;
  }
};
```

### 调试命令

```bash
# 查看后端日志
tail -f /tmp/backend.log | grep -i "rag\|search"

# 测试RAG端点
curl http://localhost:8000/api/v1/kb/search \
  -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"AI trends","top_k":5}'
```

---

**更新时间**: 2026-01-01  
**维护者**: AI Assistant  
**版本**: 1.0
