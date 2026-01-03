# WebSocket RAG 事件集成指南

## 概述

本文档说明如何在工作流执行中集成 RAG 搜索的实时事件流。系统通过 WebSocket 连接流式传输 RAG 搜索结果，允许前端实时显示搜索进度和结果。

## 架构

```
┌─────────────────────┐
│   前端工作流执行     │
└──────────┬──────────┘
           │ WebSocket
           ▼
┌─────────────────────┐
│   RAG Node Handler  │ (后端)
│  - 搜索初始化        │
│  - 流式结果          │
│  - 错误处理          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  RAGService + DB    │
│  - 向量搜索          │
│  - 结果聚合          │
└─────────────────────┘
```

## 事件类型

### 1. RAG 搜索开始

**事件类型**: `rag_search_started`

```typescript
{
  type: 'rag_search_started',
  threadId: 'xyz123',
  nodeId: 'rag_node_1',
  payload: {
    query: "什么是 LangGraph?",
    topK: 5,
    minScore: 0.5,
    ragMode: 'chunk',
    documentsCount: 3
  }
}
```

### 2. RAG 搜索结果

**事件类型**: `rag_result`

```typescript
{
  type: 'rag_result',
  threadId: 'xyz123',
  nodeId: 'rag_node_1',
  payload: {
    results: [
      {
        id: 'doc_chunk_1',
        title: 'LangGraph 指南',
        content: '...',
        score: 0.95,
        metadata: { source: 'doc1.pdf', page: 1 },
        chunkIndex: 0
      },
      // ... 更多结果
    ],
    query: "什么是 LangGraph?",
    totalCount: 3,
    durationMs: 245
  }
}
```

### 3. RAG 搜索错误

**事件类型**: `rag_error`

```typescript
{
  type: 'rag_error',
  threadId: 'xyz123',
  nodeId: 'rag_node_1',
  payload: {
    message: '搜索超时',
    code: 'SEARCH_TIMEOUT',
    nodeId: 'rag_node_1'
  }
}
```

### 4. RAG 搜索完成

**事件类型**: `rag_complete`

```typescript
{
  type: 'rag_complete',
  threadId: 'xyz123',
  nodeId: 'rag_node_1',
  payload: {
    status: 'success',
    totalResults: 3,
    durationMs: 245
  }
}
```

## 前端集成

### 步骤 1: 使用 Hook

```typescript
import { useRagWebSocket } from '@/hooks/useRagWebSocket'

export function MyWorkflowComponent() {
  const { state, wsClient } = useRagWebSocket({
    threadId: 'xyz123',
    enabled: true,
    onSearchStarted: (payload) => {
      console.log('搜索开始:', payload.query)
    },
    onResultsReceived: (payload) => {
      console.log('收到结果:', payload.results.length)
    },
    onSearchError: (payload) => {
      console.error('搜索错误:', payload.message)
    },
    onSearchComplete: (payload) => {
      console.log('搜索完成，耗时:', payload.durationMs)
    }
  })

  return (
    <RagSearchDisplay 
      state={state}
      onResultClick={(result) => console.log(result)}
    />
  )
}
```

### 步骤 2: 集成到工作流执行面板

```typescript
import ExecutionPanelRagIntegration from '@/components/workflow/ExecutionPanelRagIntegration'

export function WorkflowExecutionPage() {
  const [threadId, setThreadId] = useState<string | null>(null)
  const [isExecuting, setIsExecuting] = useState(false)

  return (
    <div className="flex gap-4">
      <div className="flex-1">
        {/* 工作流画布 */}
      </div>
      <div className="w-80">
        <ExecutionPanelRagIntegration
          threadId={threadId}
          isExecuting={isExecuting}
        />
      </div>
    </div>
  )
}
```

## 后端实现要求

### RAG Node Handler

```python
# backend/app/api/v1/websocket.py

async def handle_rag_node(
    node_config: RagConfig,
    input_text: str,
    send_event: Callable,
) -> str:
    """处理 RAG 节点的工作流执行"""
    
    # 发送搜索开始事件
    await send_event({
        'type': 'rag_search_started',
        'nodeId': node_config.node_id,
        'payload': {
            'query': input_text,
            'topK': node_config.topK,
            'minScore': node_config.minScore,
            'ragMode': node_config.ragMode,
            'documentsCount': len(node_config.knowledge_documents)
        }
    })
    
    try:
        # 执行搜索
        start_time = time.time()
        results = await rag_service.search_chunks(
            query=input_text,
            top_k=node_config.topK,
            min_score=node_config.minScore,
            document_ids=node_config.knowledge_documents
        )
        duration_ms = int((time.time() - start_time) * 1000)
        
        # 发送结果事件
        await send_event({
            'type': 'rag_result',
            'nodeId': node_config.node_id,
            'payload': {
                'results': results,
                'query': input_text,
                'totalCount': len(results),
                'durationMs': duration_ms
            }
        })
        
        # 发送完成事件
        await send_event({
            'type': 'rag_complete',
            'nodeId': node_config.node_id,
            'payload': {
                'status': 'success',
                'totalResults': len(results),
                'durationMs': duration_ms
            }
        })
        
        # 格式化上下文供后续 LLM 使用
        context = await rag_service.format_context(results)
        return context
        
    except Exception as e:
        # 发送错误事件
        await send_event({
            'type': 'rag_error',
            'nodeId': node_config.node_id,
            'payload': {
                'message': str(e),
                'code': 'RAG_SEARCH_ERROR'
            }
        })
        raise
```

## 状态管理

### RagSearchState

```typescript
interface RagSearchState {
  isSearching: boolean           // 搜索进行中
  results: RagResultPayload | null  // 搜索结果
  error: RagErrorPayload | null     // 错误信息
  query: string                  // 查询字符串
  startTime: number | null       // 开始时间戳
}
```

## UI 组件

### RagSearchDisplay

显示 RAG 搜索的实时结果

**Props**:
- `state: RagSearchState` - 搜索状态
- `onResultClick?: (result: RagResult) => void` - 结果点击处理
- `highlightQuery?: boolean` - 是否高亮查询词

**特性**:
- 实时加载状态显示
- 错误处理和展示
- 结果卡片显示，包括：
  - 相关性评分
  - 文档标题
  - 内容预览
  - 元数据
  - 分片索引

## 最佳实践

### 1. 错误处理

```typescript
const { state } = useRagWebSocket({
  onSearchError: (payload) => {
    // 记录错误
    logger.error('RAG Search Error', {
      code: payload.code,
      message: payload.message,
      nodeId: payload.nodeId
    })
    
    // 显示用户友好的错误消息
    toast.error('搜索失败，请重试')
  }
})
```

### 2. 性能优化

```typescript
// 避免频繁的 re-render
const memoizedResults = useMemo(() => 
  state.results?.results || []
, [state.results])

// 使用防抖处理快速事件
const debouncedSearch = useDebouncedCallback(
  (query: string) => performSearch(query),
  500
)
```

### 3. 用户反馈

```typescript
// 显示进度指示
<div className="flex items-center gap-2">
  {state.isSearching && <Loader2 className="animate-spin" />}
  <span>
    {state.isSearching ? '搜索中...' : `找到 ${state.results?.totalCount} 个结果`}
  </span>
</div>
```

## 调试技巧

### 1. 监听所有 WebSocket 事件

```typescript
const { wsClient } = useRagWebSocket({ threadId })

useEffect(() => {
  wsClient.on('*', (event) => {
    console.log('[WebSocket Event]', event)
  })
}, [wsClient])
```

### 2. 检查连接状态

```typescript
console.log('WebSocket 已连接:', wsClient.isConnected())
```

### 3. 手动发送测试消息

```typescript
// 在浏览器控制台中
ws = new WebSocket('ws://localhost:8000/ws/run/test-thread')
ws.send(JSON.stringify({
  action: 'start',
  input: 'test query'
}))
```

## 部署检查清单

- [ ] 后端 RAG Node Handler 已实现
- [ ] WebSocket 事件发送逻辑正确
- [ ] 前端 WebSocket 客户端已连接
- [ ] 事件类型定义完整
- [ ] useRagWebSocket Hook 正确配置
- [ ] RagSearchDisplay 组件已集成
- [ ] 错误处理已覆盖所有场景
- [ ] 性能测试通过（大量结果）
- [ ] 用户反馈机制已实现

## 常见问题

### Q: 搜索结果不显示怎么办？
**A**: 检查以下几点：
1. WebSocket 连接是否成功 (`wsClient.isConnected()`)
2. 后端是否正确发送了 `rag_result` 事件
3. 浏览器控制台是否有错误消息
4. ThreadId 是否正确传递

### Q: 如何处理大量搜索结果？
**A**:
1. 使用虚拟滚动 (react-window)
2. 分页加载结果
3. 在服务器端限制 topK 值
4. 使用客户端过滤

### Q: 如何自定义搜索结果的显示？
**A**: 继承或复制 `RagSearchDisplay` 组件，根据需要修改 JSX 和样式。

---

**相关文件**:
- `frontend/src/types/websocket.ts` - 事件类型定义
- `frontend/src/hooks/useRagWebSocket.ts` - WebSocket Hook
- `frontend/src/components/workflow/RagSearchDisplay.tsx` - 搜索结果显示
- `frontend/src/components/workflow/ExecutionPanelRagIntegration.tsx` - 执行面板集成示例
