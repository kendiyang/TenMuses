# Phase 2.4 前端集成指南 - RAG 工作流配置与执行

## 📋 概述

本文档描述 TenMuses 前端如何集成 RAG（检索增强生成）功能，使用户能够在工作流编辑器中为 LLM 节点配置知识库，并在执行时实时查看 RAG 检索结果。

**完成日期**: 2026-01-01  
**前端框架**: Next.js 14 + React + TypeScript + Tailwind CSS  
**状态管理**: Zustand  
**画布库**: React Flow  

---

## 🎯 功能目标

### Day 5 已完成功能

1. **节点属性面板 RAG 配置** ✅
   - 为 LLM 节点添加知识库配置区域
   - 支持启用/禁用 RAG
   - 支持选择多个知识库文档
   - 配置检索模式（chunk/document）
   - 配置检索参数（Top K、最小相关度分数）

2. **知识库文档选择器组件** ✅
   - 从后端 API 加载可用文档
   - 支持搜索和多选
   - 显示已选文档列表
   - 实时更新

3. **执行面板 RAG 结果展示** ✅
   - WebSocket 接收 `rag_search` 事件
   - 显示检索到的文档标题和相关度分数
   - 显示文档片段（如果有）
   - 与流式输出整合展示

---

## 🏗️ 架构设计

### 数据流

```
用户操作（属性面板） 
  → Zustand Store (节点状态更新)
    → React Flow 画布同步
      → 保存到后端 workflow.canvas_json
        
工作流执行
  → WebSocket 连接 ws://localhost:8000/ws/run/{thread_id}
    → 接收 rag_search 事件
      → 更新节点 ragSearchResults
        → 执行面板实时显示
```

### 文件结构

```
frontend/src/
├── types/
│   └── workflow.ts              # AgentNodeData 类型定义（包含 RAG 字段）
├── stores/
│   └── workflow-store.ts        # Zustand 状态管理
├── components/
│   └── workflow/
│       ├── PropertiesPanel.tsx           # ✨ RAG 配置 UI
│       ├── KnowledgeDocumentSelector.tsx # ✨ 文档选择器
│       └── ExecutionPanel.tsx            # ✨ RAG 结果展示
├── hooks/
│   └── useWorkflowExecution.ts  # ✨ 处理 rag_search 事件
└── app/
    └── workflows/[id]/page.tsx  # 工作流编辑器页面
```

---

## 📝 核心实现

### 1. 数据模型扩展

#### `types/workflow.ts` - AgentNodeData 类型

```typescript
export interface AgentNodeData {
  label: string
  type: 'llm' | 'tool' | 'router' | 'map' | 'research' | 'writer' | 'reviewer'
  status: NodeStatus
  modelConfig?: {
    provider: 'openai' | 'anthropic'
    model: string
    temperature?: number
    maxTokens?: number
    
    // ✨ RAG 配置字段
    enableRag?: boolean                    // 启用 RAG
    knowledgeDocuments?: string[]          // 选中的文档 ID 列表
    ragMode?: 'document' | 'chunk'         // 检索模式
    ragTopK?: number                       // Top K 结果数量 (1-20)
    ragMinScore?: number                   // 最小相关度分数 (0.0-1.0)
  }
  prompt?: string
  streamingContent?: string
  error?: string
  
  // ✨ RAG 搜索结果（从 WebSocket 接收）
  ragSearchResults?: Array<{
    documentId: string
    title: string
    score: number
    snippet?: string
  }>
}
```

**关键设计决策**:
- `enableRag` 默认 `false`，保持向后兼容
- `ragMode` 默认 `'chunk'`（细粒度检索）
- `ragTopK` 默认 `5`，范围 1-20
- `ragMinScore` 默认 `0.5`，范围 0.0-1.0

---

### 2. 知识库文档选择器组件

#### `KnowledgeDocumentSelector.tsx`

```typescript
interface KnowledgeDocumentSelectorProps {
  selectedDocumentIds: string[]
  onChange: (documentIds: string[]) => void
}
```

**功能特性**:
- ✅ 调用 `GET /api/v1/kb/documents` 加载文档列表
- ✅ 支持搜索过滤（按标题）
- ✅ 复选框多选
- ✅ 已选文档显示（带删除按钮）
- ✅ 加载和错误状态处理
- ✅ 响应式设计

**UI 布局**:
```
┌─────────────────────────────────────────┐
│ Selected Documents (3)                  │
│ [doc-1 ×] [doc-2 ×] [doc-3 ×]          │
├─────────────────────────────────────────┤
│ 🔍 Search documents...                  │
├─────────────────────────────────────────┤
│ ☑ AI Trends Report 2024                │
│   file • 2026-01-01                     │
│ ☐ LangGraph Documentation              │
│   url • 2025-12-15                      │
│ ☐ Research Notes                        │
│   text • 2025-12-20                     │
└─────────────────────────────────────────┘
```

---

### 3. 属性面板 RAG 配置 UI

#### `PropertiesPanel.tsx`

**新增配置区域**（仅 LLM 节点显示）:

```tsx
{isLLMNode && (
  <div className="border-t border-border pt-4 mt-4">
    <div className="flex items-center justify-between mb-3">
      <div className="flex items-center gap-2">
        <Database className="w-4 h-4" />
        <label>Knowledge Base (RAG)</label>
      </div>
      <ToggleSwitch 
        checked={node.data.modelConfig?.enableRag || false}
        onChange={handleEnableRagChange}
      />
    </div>

    {node.data.modelConfig?.enableRag && (
      <div className="space-y-3 pl-6 border-l-2 border-blue-200">
        {/* 文档选择器 */}
        <KnowledgeDocumentSelector
          selectedDocumentIds={node.data.modelConfig?.knowledgeDocuments || []}
          onChange={handleKnowledgeDocumentsChange}
        />

        {/* 检索模式 */}
        <Select value={ragMode} onChange={handleRagModeChange}>
          <option value="chunk">Chunk (Fine-grained)</option>
          <option value="document">Document (Whole file)</option>
        </Select>

        {/* Top K 滑块 */}
        <RangeSlider 
          label="Top K Results"
          min={1} max={20} step={1}
          value={ragTopK}
          onChange={handleRagTopKChange}
        />

        {/* 最小分数滑块 */}
        <RangeSlider 
          label="Min Relevance Score"
          min={0} max={1} step={0.05}
          value={ragMinScore}
          onChange={handleRagMinScoreChange}
        />
      </div>
    )}
  </div>
)}
```

**状态更新函数**:

```typescript
const handleEnableRagChange = (enableRag: boolean) => {
  updateNode(nodeId, {
    modelConfig: { 
      ...node.data.modelConfig!, 
      enableRag,
      knowledgeDocuments: enableRag 
        ? (node.data.modelConfig?.knowledgeDocuments || []) 
        : [],
    },
  })
  if (enableRag) setShowRagConfig(true)
}
```

---

### 4. WebSocket 事件处理

#### `hooks/useWorkflowExecution.ts`

**新增 `rag_search` 事件处理**:

```typescript
const handleEvent = useCallback((event: WSEvent) => {
  switch (event.type) {
    // ... 其他事件处理

    case 'rag_search':
      if (event.nodeId) {
        addLog(`RAG: Retrieved ${event.payload.documentCount} documents`)
        
        // 更新节点 RAG 搜索结果
        updateNode(event.nodeId, {
          ragSearchResults: event.payload.results || [],
        })
      }
      break
  }
}, [addLog, updateNode])
```

**WebSocket 事件格式**（后端发送）:

```json
{
  "type": "rag_search",
  "runId": "run-123",
  "threadId": "thread-abc",
  "nodeId": "node-research",
  "payload": {
    "query": "AI trends 2024",
    "documentCount": 3,
    "topK": 5,
    "mode": "chunk",
    "results": [
      {
        "documentId": "doc-1",
        "title": "AI Trends Report",
        "score": 0.94,
        "snippet": "Recent developments in AI..."
      },
      {
        "documentId": "doc-2",
        "title": "LangGraph Guide",
        "score": 0.87,
        "snippet": "LangGraph enables..."
      }
    ]
  }
}
```

---

### 5. 执行面板 RAG 结果展示

#### `ExecutionPanel.tsx`

**RAG 结果卡片**（在流式输出之前显示）:

```tsx
{streamingOutputs.map((s) => {
  const node = nodes.find((n) => n.id === s.id)
  const hasRagResults = node?.data.ragSearchResults?.length > 0

  return (
    <div key={s.id} className="space-y-2">
      <div className="text-xs font-medium">{s.label}</div>
      
      {/* ✨ RAG 搜索结果卡片 */}
      {hasRagResults && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <div className="flex items-center gap-2 text-xs font-medium text-blue-700">
            <Database className="w-3 h-3" />
            <span>Knowledge Base Results ({node.data.ragSearchResults!.length})</span>
          </div>
          <div className="space-y-1.5 mt-2">
            {node.data.ragSearchResults!.map((result, idx) => (
              <div key={idx} className="flex items-start gap-2 text-xs">
                <FileText className="w-3 h-3 text-blue-600 mt-0.5" />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-blue-900">
                      {result.title}
                    </span>
                    <span className="text-blue-600 font-mono">
                      {(result.score * 100).toFixed(0)}%
                    </span>
                  </div>
                  {result.snippet && (
                    <div className="text-blue-700 text-xs mt-0.5 line-clamp-2">
                      {result.snippet}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 流式输出 */}
      <div className="whitespace-pre-wrap text-sm">
        {s.content || <em>No output yet</em>}
      </div>
    </div>
  )
})}
```

**视觉效果**:
```
┌─────────────────────────────────────────────┐
│ Research Node                               │
│                                             │
│ ┌─ Knowledge Base Results (3) ────────────┐│
│ │ 📄 AI Trends Report           94%       ││
│ │    Recent developments in AI...         ││
│ │ 📄 LangGraph Documentation    87%       ││
│ │    LangGraph enables...                 ││
│ │ 📄 Workflow Design Patterns   72%       ││
│ └─────────────────────────────────────────┘│
│                                             │
│ Based on the retrieved knowledge,          │
│ AI trends in 2024 include...               │
│ [streaming output...]                      │
└─────────────────────────────────────────────┘
```

---

## 🔌 后端集成点

### API 端点

#### 1. 获取知识库文档列表

```http
GET /api/v1/kb/documents
Authorization: Bearer {token}

Response 200:
{
  "documents": [
    {
      "id": "doc-uuid-1",
      "title": "AI Trends Report 2024",
      "sourceType": "file",
      "createdAt": "2026-01-01T00:00:00Z"
    },
    {
      "id": "doc-uuid-2",
      "title": "LangGraph Documentation",
      "sourceType": "url",
      "createdAt": "2025-12-15T00:00:00Z"
    }
  ]
}
```

#### 2. 工作流保存（canvas_json 包含 RAG 配置）

```http
PUT /api/v1/workflows/{workflow_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "canvas_json": {
    "nodes": [
      {
        "id": "node-1",
        "type": "default",
        "data": {
          "label": "Research",
          "type": "llm",
          "status": "idle",
          "modelConfig": {
            "provider": "openai",
            "model": "gpt-4-turbo-preview",
            "temperature": 0.7,
            "enableRag": true,
            "knowledgeDocuments": ["doc-uuid-1", "doc-uuid-2"],
            "ragMode": "chunk",
            "ragTopK": 5,
            "ragMinScore": 0.5
          }
        }
      }
    ],
    "edges": []
  }
}
```

#### 3. WebSocket 执行流

```
连接: ws://localhost:8000/ws/run/{thread_id}
认证: 通过 URL 参数或首条消息

事件流:
1. { "type": "connected" }
2. { "type": "run_started", "payload": {...} }
3. { "type": "node_started", "nodeId": "node-1", "payload": {...} }
4. { "type": "rag_search", "nodeId": "node-1", "payload": {
     "query": "...",
     "documentCount": 3,
     "topK": 5,
     "mode": "chunk",
     "results": [...]
   }}
5. { "type": "token", "nodeId": "node-1", "payload": { "content": "..." } }
6. ...
7. { "type": "run_completed" }
```

---

## 📱 用户交互流程

### 场景 1: 配置 RAG 节点

1. 用户在画布上选中一个 LLM 节点（如 "Research"）
2. 右侧属性面板打开
3. 用户滚动到 "Knowledge Base (RAG)" 区域
4. 用户打开 RAG 开关 ✅
5. RAG 配置区域展开
6. 用户点击文档选择器，搜索并勾选 3 个文档
7. 用户调整 "Top K" 滑块到 10
8. 用户调整 "Min Score" 滑块到 0.7
9. 用户点击顶部 "Save" 按钮保存工作流

**结果**: 
- 节点 `modelConfig` 更新
- 画布 JSON 同步
- 后端 API 保存成功

---

### 场景 2: 执行启用 RAG 的工作流

1. 用户点击顶部 "Run" 按钮
2. 前端调用 `POST /api/v1/workflows/{id}/run`
3. 后端返回 `{ thread_id: "..." }`
4. 前端建立 WebSocket 连接
5. 执行面板显示 "Connected" ✅
6. 后端开始执行工作流
7. **RAG 节点执行**:
   - 前端收到 `node_started` 事件 → 节点变为 "Executing" 状态
   - 前端收到 `rag_search` 事件 → 执行面板显示蓝色 RAG 结果卡片
   - 前端收到 `token` 事件流 → 流式输出开始
8. 执行完成，前端收到 `run_completed` 事件

**用户可见**:
- ✅ 实时执行日志
- ✅ RAG 检索结果（文档标题 + 相关度）
- ✅ LLM 流式输出
- ✅ 节点状态变化（idle → executing → completed）

---

## 🎨 UI 设计规范

### 颜色方案

- **RAG 配置区域**: 蓝色主题
  - 边框: `border-blue-200`
  - 背景: `bg-blue-50`
  - 文字: `text-blue-700`, `text-blue-900`
  
- **已选文档标签**: 
  - 背景: `bg-blue-50`
  - 文字: `text-blue-700`
  - 删除按钮 hover: `bg-blue-100`

- **RAG 结果卡片**:
  - 边框: `border-blue-200`
  - 背景: `bg-blue-50`
  - 图标: `text-blue-600`

### 图标使用

- 📚 `Database` - RAG 配置标题
- 🔍 `Search` - 文档搜索输入框
- 📄 `FileText` - 单个文档项
- ❌ `X` - 删除已选文档

### 响应式布局

- 文档选择器列表: 最大高度 `max-h-48` (约 6-7 项)
- RAG 结果卡片: 自适应高度
- 所有输入组件: `w-full`

---

## 🧪 测试清单

### 单元测试

- [ ] KnowledgeDocumentSelector 正确加载文档列表
- [ ] 搜索功能正确过滤文档
- [ ] 多选/取消选择功能正常
- [ ] PropertiesPanel RAG 开关正确更新 modelConfig
- [ ] 滑块组件正确更新数值
- [ ] ExecutionPanel 正确显示 RAG 结果

### 集成测试

- [ ] 保存包含 RAG 配置的工作流到后端
- [ ] 从后端加载工作流，RAG 配置正确恢复
- [ ] WebSocket 接收 rag_search 事件，UI 正确更新
- [ ] 多个节点启用 RAG，各自独立显示结果

### 端到端测试（下一步）

- [ ] 完整流程: 上传文档 → 配置 RAG → 执行 → 查看结果
- [ ] 边界情况: 无文档、搜索无结果、RAG 检索失败

---

## 🚀 部署清单

### 前端部署

1. 确保所有依赖已安装:
   ```bash
   cd frontend
   npm install
   ```

2. 环境变量配置 (`.env.local`):
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_WS_URL=ws://localhost:8000
   ```

3. 构建生产版本:
   ```bash
   npm run build
   npm run start
   ```

### 后端要求

- ✅ `GET /api/v1/kb/documents` 端点已实现
- ✅ WebSocket `/ws/run/{thread_id}` 支持 `rag_search` 事件
- ✅ `StreamingLLMNodeExecutor` 已集成 RAG 检索逻辑
- ✅ `LLMConfig` schema 包含 RAG 字段

---

## 📊 性能考量

### 前端性能

- **文档列表加载**: 首次加载约 100-500ms（取决于文档数量）
- **搜索过滤**: 客户端过滤，实时响应
- **WebSocket 事件处理**: 每个事件 < 10ms
- **UI 更新**: React 组件重渲染优化（useMemo, useCallback）

### 用户体验优化

- 文档选择器: 虚拟滚动（如文档数 > 100）
- RAG 结果: 折叠/展开（如结果 > 5 条）
- 加载状态: 骨架屏或 Spinner

---

## 🐛 已知问题与限制

### 当前限制

1. **文档选择器**: 
   - 仅支持按标题搜索（未来可支持按内容搜索）
   - 未实现虚拟滚动（大量文档时可能卡顿）

2. **RAG 结果显示**:
   - 仅显示前 N 条结果（不可分页）
   - snippet 截断到 2 行（未来可点击展开）

3. **配置验证**:
   - 前端未验证 knowledgeDocuments 是否存在（依赖后端验证）

### 计划改进

- [ ] 支持 RAG 结果分页
- [ ] 文档选择器支持按标签筛选
- [ ] RAG 配置预设（常用配置快速应用）
- [ ] 导出/导入工作流时保留 RAG 配置

---

## 📚 参考资源

### 代码文件

- [workflow.ts](/Users/mg/Workspace/TenMuses/frontend/src/types/workflow.ts) - 类型定义
- [PropertiesPanel.tsx](/Users/mg/Workspace/TenMuses/frontend/src/components/workflow/PropertiesPanel.tsx) - RAG 配置 UI
- [KnowledgeDocumentSelector.tsx](/Users/mg/Workspace/TenMuses/frontend/src/components/workflow/KnowledgeDocumentSelector.tsx) - 文档选择器
- [ExecutionPanel.tsx](/Users/mg/Workspace/TenMuses/frontend/src/components/workflow/ExecutionPanel.tsx) - RAG 结果展示
- [useWorkflowExecution.ts](/Users/mg/Workspace/TenMuses/frontend/src/hooks/useWorkflowExecution.ts) - WebSocket 事件处理

### 后端相关

- [PHASE_2_4_RAG_WORKFLOW_INTEGRATION.md](/Users/mg/Workspace/TenMuses/PHASE_2_4_RAG_WORKFLOW_INTEGRATION.md) - 后端实现指南
- [node.py](/Users/mg/Workspace/TenMuses/backend/app/schemas/node.py) - LLMConfig schema
- [executor_library.py](/Users/mg/Workspace/TenMuses/backend/app/services/executor_library.py) - RAG 集成逻辑

### 设计文档

- [design.md](/Users/mg/Workspace/TenMuses/docs/design.md) - 系统设计文档（Phase 2.4 部分）

---

## ✅ 快速上手

### 1. 启动开发环境

```bash
# 启动后端（确保 RAG 功能已实现）
cd backend
source venv/bin/activate
python -m app.main

# 启动前端
cd frontend
npm run dev
```

### 2. 测试 RAG 配置

1. 访问 `http://localhost:3000/workflows/{workflow_id}`
2. 选中一个 LLM 节点
3. 在属性面板启用 RAG 开关
4. 选择文档并调整参数
5. 点击 "Save" 保存

### 3. 执行工作流

1. 点击 "Run" 按钮
2. 观察执行面板：
   - 执行日志显示 RAG 检索
   - 蓝色卡片显示检索结果
   - 流式输出显示 LLM 响应

---

## 📞 支持与反馈

如遇到问题或有改进建议，请：
1. 检查浏览器控制台错误日志
2. 检查后端日志（`tail -f backend.log`）
3. 验证 WebSocket 连接状态
4. 检查 API 端点是否正常响应

---

**文档版本**: v1.0  
**最后更新**: 2026-01-01  
**状态**: ✅ Day 5 前端集成完成
