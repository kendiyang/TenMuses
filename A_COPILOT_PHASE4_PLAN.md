# Task A Phase 4: 高级功能实现计划

**阶段**: Phase 4 高级功能  
**目标**: 实现流式响应、建议历史、提示编辑等高级功能  
**预计时长**: 6 小时  
**开始日期**: 2026-01-02  
**目标完成日期**: 2026-01-03

---

## 概述

Phase 4 将在 Phase 3 组件提取的基础上，添加以下高级功能：

1. **流式响应支持** (1.5 小时)
   - 实现 SSE (Server-Sent Events) 支持
   - 逐字显示建议内容
   - 添加取消机制

2. **建议历史和收藏** (1.5 小时)
   - 本地存储历史建议
   - 收藏常用建议
   - 快速访问收藏夹

3. **提示模板编辑增强** (1.5 小时)
   - 实时语法高亮
   - 模板变量预览
   - 更好的令牌估计

4. **上下文控制和优化** (1.5 小时)
   - 细粒度上下文选择
   - 上下文优化建议
   - 性能监控

---

## Step 1: 流式响应支持 (1.5 小时)

### 目标
实现服务器推送事件流，使建议和诊断结果能够逐步显示。

### 子任务

#### 1.1 后端 SSE 端点 (0.5 小时)
**文件**: `backend/app/api/v1/copilot.py`

```python
@router.get("/chat/stream/{thread_id}")
async def chat_stream(
    thread_id: str,
    message: str,
    current_user: User = Depends(get_current_user)
):
    """流式 Copilot 响应"""
    async def generate():
        # 初始化
        yield f"data: {json.dumps({'type': 'started', 'threadId': thread_id})}\n\n"
        
        # 获取上下文
        context = await get_workflow_context(thread_id, current_user.id)
        
        # 调用 LLM 流式
        async for chunk in copilot_service.stream_chat(message, context):
            yield f"data: {json.dumps(chunk)}\n\n"
        
        # 结束
        yield f"data: {json.dumps({'type': 'completed'})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

**实现细节**:
- 使用 FastAPI StreamingResponse
- 按行发送 JSON 数据
- 包含进度信息

#### 1.2 前端流式客户端 (0.5 小时)
**文件**: `frontend/src/lib/copilot-stream-client.ts`

```typescript
export class CopilotStreamClient {
  async *streamChat(
    threadId: string,
    message: string
  ): AsyncGenerator<ChatStreamEvent> {
    const response = await fetch(`/api/v1/copilot/chat/stream/${threadId}?message=${encodeURIComponent(message)}`, {
      headers: {
        'Authorization': `Bearer ${getAccessToken()}`
      }
    })
    
    const reader = response.body?.getReader()
    const decoder = new TextDecoder()
    
    while (true) {
      const { done, value } = await reader!.read()
      if (done) break
      
      const text = decoder.decode(value)
      const lines = text.split('\n')
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const json = JSON.parse(line.slice(6))
          yield json
        }
      }
    }
  }
}
```

**实现细节**:
- 异步生成器处理流
- 逐行解析 SSE 数据
- 错误处理

#### 1.3 UI 集成 (0.5 小时)
**文件**: `frontend/src/hooks/useCopilotStream.ts`

```typescript
export function useCopilotStream() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [currentMessage, setCurrentMessage] = useState('')
  
  const streamChat = async (input: string, context: WorkflowContext) => {
    setIsLoading(true)
    const client = new CopilotStreamClient()
    
    try {
      for await (const event of client.streamChat(context.workflowId, input)) {
        switch (event.type) {
          case 'token':
            setCurrentMessage(prev => prev + event.content)
            break
          case 'completed':
            // 消息完成
            break
        }
      }
    } finally {
      setIsLoading(false)
    }
  }
  
  return { messages, isLoading, streamChat }
}
```

**实现细节**:
- Hook 管理流状态
- 逐字显示消息
- 错误处理

### 验证清单
- [ ] 后端 SSE 端点测试
- [ ] 前端流式客户端测试
- [ ] UI 集成测试
- [ ] 性能测试 (100+ token 消息)

---

## Step 2: 建议历史和收藏 (1.5 小时)

### 目标
保存用户的建议历史，支持收藏和快速访问。

### 子任务

#### 2.1 本地存储结构 (0.5 小时)
**文件**: `frontend/src/lib/suggestion-storage.ts`

```typescript
interface StoredSuggestion {
  id: string
  timestamp: number
  type: 'workflow' | 'node'
  content: any
  isFavorite: boolean
  context?: {
    workflowId: string
    nodeCount?: number
  }
}

export class SuggestionStorage {
  private static readonly STORAGE_KEY = 'copilot_suggestions'
  private static readonly MAX_ITEMS = 100
  
  static saveSuggestion(suggestion: StoredSuggestion) {
    const all = this.getAll()
    all.unshift(suggestion)
    
    // 保持最多 100 条
    if (all.length > this.MAX_ITEMS) {
      all.pop()
    }
    
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(all))
  }
  
  static getFavorites(): StoredSuggestion[] {
    return this.getAll().filter(s => s.isFavorite)
  }
  
  static toggleFavorite(id: string) {
    const all = this.getAll()
    const item = all.find(s => s.id === id)
    if (item) {
      item.isFavorite = !item.isFavorite
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(all))
    }
  }
  
  static getAll(): StoredSuggestion[] {
    const stored = localStorage.getItem(this.STORAGE_KEY)
    return stored ? JSON.parse(stored) : []
  }
}
```

**实现细节**:
- IndexedDB 备选 (大数据)
- 过期清理机制
- 快速搜索

#### 2.2 历史面板组件 (0.5 小时)
**文件**: `frontend/src/components/workflow/CopilotHistory.tsx`

```typescript
export function CopilotHistory() {
  const [suggestions, setSuggestions] = useState<StoredSuggestion[]>([])
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false)
  
  useEffect(() => {
    const all = SuggestionStorage.getAll()
    setSuggestions(
      showFavoritesOnly 
        ? all.filter(s => s.isFavorite)
        : all
    )
  }, [showFavoritesOnly])
  
  return (
    <div className="space-y-2 p-3">
      <div className="flex items-center gap-2">
        <button onClick={() => setShowFavoritesOnly(!showFavoritesOnly)}>
          {showFavoritesOnly ? '⭐ 收藏' : '📋 历史'}
        </button>
        <span className="text-xs text-gray-500">{suggestions.length} 项</span>
      </div>
      
      <div className="space-y-1 max-h-60 overflow-y-auto">
        {suggestions.map(s => (
          <div key={s.id} className="p-2 bg-gray-50 rounded flex items-start gap-2">
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold truncate">{s.type}</p>
              <p className="text-xs text-gray-600 line-clamp-2">{s.content?.name || s.content?.label}</p>
            </div>
            <button
              onClick={() => SuggestionStorage.toggleFavorite(s.id)}
              className="text-lg"
            >
              {s.isFavorite ? '⭐' : '☆'}
            </button>
          </div>
        ))}
      </div>
    </div>
  )
}
```

**实现细节**:
- 无限滚动
- 快速过滤
- 星标标记

#### 2.3 CopilotPanel 集成 (0.5 小时)
**修改**: `frontend/src/components/workflow/CopilotPanel.tsx`

- 添加标签页: 历史 / 收藏
- 导入 CopilotHistory 组件
- 自动保存建议到历史

### 验证清单
- [ ] 本地存储功能测试
- [ ] 历史面板 UI 测试
- [ ] 收藏/取消收藏功能
- [ ] 数据持久化测试

---

## Step 3: 提示模板编辑增强 (1.5 小时)

### 目标
增强提示模板的编辑和预览功能。

### 子任务

#### 3.1 语法高亮编辑器 (0.5 小时)
**依赖**: `npm install highlight.js prismjs`

**文件**: `frontend/src/components/ui/code-editor.tsx`

```typescript
import { highlight, languages } from 'prismjs'

export function CodeEditor({ 
  value, 
  onChange,
  language = 'text'
}: CodeEditorProps) {
  const [isFocused, setIsFocused] = useState(false)
  
  const highlightedCode = useMemo(() => {
    try {
      return highlight(value, languages[language], language)
    } catch {
      return escapeHtml(value)
    }
  }, [value, language])
  
  return (
    <div className="relative">
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        className="absolute inset-0 bg-transparent text-transparent caret-white font-mono resize-none"
      />
      <pre className="bg-gray-900 text-white p-3 rounded-lg font-mono text-sm overflow-auto pointer-events-none">
        <code 
          dangerouslySetInnerHTML={{ __html: highlightedCode }}
          className={`language-${language}`}
        />
      </pre>
    </div>
  )
}
```

**实现细节**:
- 透明 textarea 叠加
- Prism.js 高亮
- 同步滚动

#### 3.2 模板变量系统 (0.5 小时)
**文件**: `frontend/src/lib/template-variables.ts`

```typescript
export const TEMPLATE_VARIABLES = {
  workflow: {
    nodeCount: '工作流中的节点数',
    edgeCount: '工作流中的连接数',
    complexity: '工作流复杂度 (simple/medium/advanced)',
    description: '工作流描述'
  },
  node: {
    type: '节点类型',
    label: '节点标签',
    index: '节点在工作流中的位置'
  },
  user: {
    name: '用户名',
    id: '用户 ID'
  }
}

export function previewTemplate(
  template: string,
  variables: Record<string, string | number>
): string {
  let result = template
  
  for (const [key, value] of Object.entries(variables)) {
    result = result.replace(new RegExp(`{{${key}}}`, 'g'), String(value))
  }
  
  return result
}
```

**实现细节**:
- 变量提示
- 实时预览
- 变量验证

#### 3.3 增强的 CopilotPromptTemplate (0.5 小时)
**修改**: `frontend/src/components/workflow/CopilotPromptTemplate.tsx`

```typescript
export function CopilotPromptTemplate({
  template,
  onApply,
  onApplyToNode,
  loading = false,
  className,
}: CopilotPromptTemplateProps) {
  const [editedContent, setEditedContent] = useState(template?.content || '')
  const [showPreview, setShowPreview] = useState(false)
  const [variables, setVariables] = useState<Record<string, string>>({})
  
  const preview = useMemo(() => {
    return previewTemplate(editedContent, variables)
  }, [editedContent, variables])
  
  const tokenCount = useMemo(() => {
    return Math.ceil(preview.length / 4)
  }, [preview])
  
  return (
    <div className="space-y-3 p-3">
      {/* 编辑器 */}
      <CodeEditor
        value={editedContent}
        onChange={setEditedContent}
        language="text"
      />
      
      {/* 变量插入 */}
      <div className="flex flex-wrap gap-1">
        {Object.entries(TEMPLATE_VARIABLES.workflow).map(([key, desc]) => (
          <button
            key={key}
            onClick={() => {
              setEditedContent(prev => prev + ` {{${key}}}`)
            }}
            className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
            title={desc}
          >
            +{key}
          </button>
        ))}
      </div>
      
      {/* 预览 */}
      {showPreview && (
        <div className="bg-gray-100 p-2 rounded text-xs whitespace-pre-wrap font-mono">
          {preview}
        </div>
      )}
      
      {/* 令牌计数 */}
      <div className="text-xs text-gray-600">
        估计令牌: {tokenCount}
      </div>
    </div>
  )
}
```

### 验证清单
- [ ] 语法高亮功能
- [ ] 变量插入功能
- [ ] 预览显示
- [ ] 令牌计算准确性

---

## Step 4: 上下文控制和优化 (1.5 小时)

### 目标
给用户细粒度控制，优化 Copilot 的性能。

### 子任务

#### 4.1 上下文配置组件 (0.5 小时)
**文件**: `frontend/src/components/workflow/CopilotContextConfig.tsx`

```typescript
export interface ContextConfig {
  includeNodes: boolean
  includeEdges: boolean
  includeMetadata: boolean
  maxNodeCount?: number
  maxContextSize?: number // KB
}

export function CopilotContextConfig({
  config,
  onChange,
  estimatedSize
}: CopilotContextConfigProps) {
  return (
    <div className="space-y-2 p-3 border-t">
      <h4 className="text-xs font-semibold">上下文设置</h4>
      
      <label className="flex items-center gap-2 text-xs">
        <input
          type="checkbox"
          checked={config.includeNodes}
          onChange={(e) => onChange({ ...config, includeNodes: e.target.checked })}
        />
        包含节点信息
      </label>
      
      <label className="flex items-center gap-2 text-xs">
        <input
          type="checkbox"
          checked={config.includeEdges}
          onChange={(e) => onChange({ ...config, includeEdges: e.target.checked })}
        />
        包含连接信息
      </label>
      
      <label className="flex items-center gap-2 text-xs">
        <input
          type="checkbox"
          checked={config.includeMetadata}
          onChange={(e) => onChange({ ...config, includeMetadata: e.target.checked })}
        />
        包含元数据
      </label>
      
      <div className="text-xs text-gray-600">
        估计大小: {(estimatedSize / 1024).toFixed(2)} KB
      </div>
    </div>
  )
}
```

**实现细节**:
- 复选框控制
- 实时大小估计
- 性能优化建议

#### 4.2 上下文优化建议 (0.5 小时)
**文件**: `frontend/src/lib/context-optimizer.ts`

```typescript
export function analyzeContext(context: WorkflowContext): ContextSuggestion[] {
  const suggestions: ContextSuggestion[] = []
  
  // 检查节点过多
  if (context.nodeCount > 50) {
    suggestions.push({
      type: 'warning',
      message: `工作流有 ${context.nodeCount} 个节点，建议使用摘要模式`,
      action: 'enable_summary'
    })
  }
  
  // 检查边过多
  if (context.edgeCount > 100) {
    suggestions.push({
      type: 'warning',
      message: '连接过多，建议简化展示',
      action: 'exclude_edges'
    })
  }
  
  return suggestions
}
```

**实现细节**:
- 启发式分析
- 性能预估
- 优化建议

#### 4.3 性能监控 (0.5 小时)
**文件**: `frontend/src/lib/copilot-metrics.ts`

```typescript
export class CopilotMetrics {
  static recordRequest(
    type: 'chat' | 'suggest' | 'diagnose',
    duration: number,
    contextSize: number,
    success: boolean
  ) {
    // 上报指标
    analytics.track('copilot_request', {
      type,
      duration,
      contextSize,
      success,
      timestamp: Date.now()
    })
  }
  
  static getAverageLatency(type: string): number {
    // 计算平均延迟
    return 0
  }
}
```

**实现细节**:
- 请求计时
- 大小跟踪
- 成功率监控

### 验证清单
- [ ] 上下文配置 UI
- [ ] 大小估计准确
- [ ] 优化建议有效
- [ ] 性能数据收集

---

## 总体进度跟踪

| Step | 名称 | 预计 | 进度 | 状态 |
|------|------|------|------|------|
| 1 | 流式响应 | 1.5h | 0% | 📋 |
| 2 | 历史收藏 | 1.5h | 0% | 📋 |
| 3 | 模板编辑 | 1.5h | 0% | 📋 |
| 4 | 上下文优化 | 1.5h | 0% | 📋 |
| **总计** | **Phase 4** | **6h** | **0%** | **📋** |

---

## 依赖和前置条件

✅ **已完成**:
- Phase 3 组件提取
- CopilotPanel 集成
- 基础类型定义

📋 **新增依赖**:
- `prismjs`: 代码高亮
- `highlight.js`: 语法高亮 (可选)

---

## 测试计划

### 单元测试
- 流式响应处理测试
- 本地存储测试
- 模板变量替换测试
- 上下文分析测试

### 集成测试
- SSE 连接测试
- UI 流式显示测试
- 历史持久化测试
- 性能监控测试

### E2E 测试
- 完整流式对话流程
- 建议收藏流程
- 模板编辑应用流程
- 性能基准测试

---

## 成功标准

✅ **功能完整**
- [ ] 流式响应完整显示
- [ ] 建议历史正确保存
- [ ] 模板编辑功能完整
- [ ] 上下文配置有效

✅ **代码质量**
- [ ] TypeScript 类型完整
- [ ] 单元测试覆盖 >80%
- [ ] 文档注释完整
- [ ] 零编译错误

✅ **性能指标**
- [ ] 流式响应延迟 <100ms
- [ ] 历史查询 <50ms
- [ ] 模板渲染 <200ms
- [ ] 上下文分析 <500ms

✅ **用户体验**
- [ ] UI 流畅无卡顿
- [ ] 反馈及时清晰
- [ ] 错误处理优雅
- [ ] 文档清晰完整

---

## 风险和缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| SSE 浏览器兼容性 | 低 | 中 | polyfill + fallback |
| localStorage 容量限制 | 低 | 中 | IndexedDB 备选 |
| 性能开销 | 中 | 中 | 增量更新 + 缓存 |
| 复杂度增加 | 中 | 中 | 模块化 + 测试 |

---

## 相关文档

- [A_COPILOT_PHASE3_COMPLETION.md](./A_COPILOT_PHASE3_COMPLETION.md) - Phase 3 完成报告
- [A_COPILOT_PHASE3_PLAN.md](./A_COPILOT_PHASE3_PLAN.md) - Phase 3 计划
- [.github/copilot-instructions.md](./.github/copilot-instructions.md) - 项目指南

---

**计划版本**: 1.0  
**创建日期**: 2026-01-02  
**状态**: 就绪 📋

开始 Phase 4 实现时，将此文档作为参考。每完成一个 Step，更新进度状态。
