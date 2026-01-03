# Task A: Copilot 集成 - Phase 2 实现计划

**阶段**: Phase 2: 组件集成  
**预计时间**: 8 小时  
**预计完成**: 2026-01-03 (Day 3)  
**优先级**: P1 (关键)  
**状态**: 🟡 计划中

---

## 📋 Phase 2 目标

将完整的 Copilot AI 助手集成到工作流编辑器中，使用户能够：
1. ✅ 在编辑工作流时使用 AI 聊天
2. ✅ 直接应用 AI 建议的工作流和节点
3. ✅ 获得工作流问题诊断
4. ✅ 生成 LLM 节点的提示词

---

## 🎯 分阶段任务

### Step 1: 集成 CopilotPanel 到 WorkflowCanvas (3h) ⏳

**目标**: 在工作流编辑器中显示 Copilot 面板

#### 1.1 定位和布局分析

```bash
# 查找 WorkflowCanvas 组件
find frontend/src -name "*WorkflowCanvas*" -o -name "*workflow*canvas*"

# 查看现有布局
cat frontend/src/components/workflow/WorkflowCanvas.tsx | head -100
```

**期望文件位置**: 
- `frontend/src/components/workflow/WorkflowCanvas.tsx`
- `frontend/src/app/workflows/[id]/page.tsx` 或类似

#### 1.2 修改 WorkflowCanvas

**文件**: `frontend/src/components/workflow/WorkflowCanvas.tsx`

**修改内容**:
```typescript
// 1. 导入 CopilotPanel
import { CopilotPanel } from './CopilotPanel'

// 2. 在组件中添加 CopilotPanel
export function WorkflowCanvas({ workflowId, workflow, onSave }: WorkflowCanvasProps) {
  return (
    <div className="flex gap-4 h-screen">
      {/* 左侧: 工具栏 */}
      <NodeToolbar />

      {/* 中央: 画布 */}
      <div className="flex-1 overflow-auto">
        <ReactFlow {/* ... */} />
      </div>

      {/* 右侧: 属性和 Copilot */}
      <div className="w-80 space-y-4 overflow-auto">
        <PropertiesPanel />
        <CopilotPanel 
          workflowId={workflowId}
          onNodeApply={handleNodeApply}
          onWorkflowApply={handleWorkflowApply}
        />
      </div>
    </div>
  )
}
```

#### 1.3 实现回调处理

**文件**: `frontend/src/components/workflow/WorkflowCanvas.tsx`

**实现**:
```typescript
// 处理节点建议应用
const handleNodeApply = (node: any) => {
  // 1. 生成唯一 ID
  const nodeId = `node_${Date.now()}`
  
  // 2. 创建节点对象
  const newNode = {
    id: nodeId,
    data: { label: node.label || node.type },
    position: { x: 250, y: 250 }, // 默认位置
    type: node.type.toLowerCase(),
  }

  // 3. 添加到画布
  addNode(newNode)
  
  // 4. 显示成功提示
  showToast('节点已添加', 'success')
}

// 处理工作流建议应用
const handleWorkflowApply = (workflow: any) => {
  // 1. 清空当前工作流（或添加确认）
  if (!confirm('要替换当前工作流吗?')) return
  
  // 2. 加载工作流
  loadWorkflow(workflow)
  
  // 3. 自动布局
  autoLayout()
  
  // 4. 保存变更
  onSave?.(workflow)
}
```

**预计代码行数**: 80-100 行

---

### Step 2: 实现建议卡片组件 (3h) ⏳

**目标**: 美观显示 AI 建议，支持一键应用

#### 2.1 创建建议卡片组件

**文件**: `frontend/src/components/workflow/CopilotSuggestions.tsx`

**代码框架**:
```typescript
import React from 'react'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Zap, Copy, Check } from 'lucide-react'
import { WorkflowSuggestion, NodeSuggestion } from '@/types/copilot'

interface CopilotSuggestionsProps {
  suggestions?: {
    workflows?: WorkflowSuggestion[]
    nodes?: NodeSuggestion[]
  }
  onApply?: (item: any, type: 'workflow' | 'node') => void
  loading?: boolean
}

export function CopilotSuggestions({
  suggestions,
  onApply,
  loading,
}: CopilotSuggestionsProps) {
  const [appliedId, setAppliedId] = React.useState<string | null>(null)

  if (!suggestions) return null

  return (
    <div className="space-y-3 p-3 border-t bg-blue-50">
      {/* 工作流建议 */}
      {suggestions.workflows && suggestions.workflows.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-gray-700">工作流建议</h4>
          {suggestions.workflows.map((wf, idx) => (
            <Card key={idx} className="p-2 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <h5 className="text-xs font-semibold text-gray-900 truncate">
                    {wf.name}
                  </h5>
                  <p className="text-xs text-gray-600 line-clamp-2">
                    {wf.description}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    {wf.nodes.length} 节点 • {wf.edges.length} 连接
                  </p>
                </div>
                <Button
                  size="sm"
                  variant={appliedId === `wf_${idx}` ? 'default' : 'outline'}
                  onClick={() => {
                    onApply?.(wf, 'workflow')
                    setAppliedId(`wf_${idx}`)
                  }}
                  disabled={loading}
                >
                  {appliedId === `wf_${idx}` ? <Check className="h-3 w-3" /> : '应用'}
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* 节点建议 */}
      {suggestions.nodes && suggestions.nodes.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-gray-700">节点建议</h4>
          {suggestions.nodes.map((node, idx) => (
            <Card key={idx} className="p-2 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="text-xs">
                      {node.type}
                    </Badge>
                    {node.label && (
                      <span className="text-xs font-semibold text-gray-900 truncate">
                        {node.label}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                    {node.explanation}
                  </p>
                </div>
                <Button
                  size="sm"
                  variant={appliedId === `node_${idx}` ? 'default' : 'outline'}
                  onClick={() => {
                    onApply?.(node, 'node')
                    setAppliedId(`node_${idx}`)
                  }}
                  disabled={loading}
                >
                  {appliedId === `node_${idx}` ? <Check className="h-3 w-3" /> : '加'}
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
```

**预计代码行数**: 150-180 行

#### 2.2 修改 CopilotPanel 集成建议卡片

**文件**: `frontend/src/components/workflow/CopilotPanel.tsx`

**修改**: 在消息显示区域下方添加建议卡片

```typescript
// 在消息渲染后添加:
{message.suggestions && (
  <CopilotSuggestions
    suggestions={message.suggestions}
    onApply={handleSuggestionApply}
  />
)}
```

---

### Step 3: 实现诊断结果显示 (2h) ⏳

**目标**: 清晰展示工作流问题和修复建议

#### 3.1 创建诊断组件

**文件**: `frontend/src/components/workflow/CopilotDiagnostics.tsx`

**代码框架**:
```typescript
import React from 'react'
import { AlertCircle, AlertTriangle, Info, CheckCircle } from 'lucide-react'
import { WorkflowDiagnosis, Diagnostic } from '@/types/copilot'

interface CopilotDiagnosticsProps {
  result?: WorkflowDiagnosis
  onHighlightNode?: (nodeId: string) => void
}

export function CopilotDiagnostics({
  result,
  onHighlightNode,
}: CopilotDiagnosticsProps) {
  if (!result) return null

  const getIcon = (level: string) => {
    switch (level) {
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-600" />
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-600" />
      default:
        return <Info className="h-4 w-4 text-blue-600" />
    }
  }

  const getColor = (level: string) => {
    switch (level) {
      case 'error':
        return 'bg-red-50 border-red-200'
      case 'warning':
        return 'bg-yellow-50 border-yellow-200'
      default:
        return 'bg-blue-50 border-blue-200'
    }
  }

  return (
    <div className="p-3 border-t space-y-3">
      {/* 诊断评分 */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-gray-700">工作流评分</span>
        <div className="flex items-center gap-2">
          <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all ${
                result.score >= 80
                  ? 'bg-green-500'
                  : result.score >= 60
                  ? 'bg-yellow-500'
                  : 'bg-red-500'
              }`}
              style={{ width: `${result.score}%` }}
            />
          </div>
          <span className="text-sm font-bold text-gray-900 w-8">
            {result.score}/100
          </span>
        </div>
      </div>

      {/* 摘要 */}
      <p className="text-xs text-gray-700 line-clamp-2">{result.summary}</p>

      {/* 诊断项目 */}
      {result.diagnostics.length > 0 && (
        <div className="space-y-2">
          {result.diagnostics.map((diag, idx) => (
            <div
              key={idx}
              className={`p-2 rounded border ${getColor(diag.level)}`}
            >
              <div className="flex gap-2">
                {getIcon(diag.level)}
                <div className="flex-1">
                  <h5 className="text-xs font-semibold text-gray-900">
                    {diag.description}
                  </h5>
                  <p className="text-xs text-gray-600 mt-0.5">
                    💡 {diag.suggestion}
                  </p>
                  {diag.location?.node_id && (
                    <button
                      onClick={() => onHighlightNode?.(diag.location!.node_id)}
                      className="text-xs text-blue-600 hover:underline mt-1"
                    >
                      查看节点 →
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 如果没有问题 */}
      {result.diagnostics.length === 0 && (
        <div className="flex items-center gap-2 p-2 bg-green-50 rounded border border-green-200">
          <CheckCircle className="h-4 w-4 text-green-600 flex-shrink-0" />
          <span className="text-xs text-green-700 font-semibold">
            工作流没有明显问题! ✨
          </span>
        </div>
      )}
    </div>
  )
}
```

**预计代码行数**: 120-150 行

#### 3.2 在 CopilotPanel 中集成诊断

```typescript
// 在 CopilotPanel 中添加:
{message.diagnostics && (
  <CopilotDiagnostics
    result={message.diagnostics}
    onHighlightNode={handleHighlightNode}
  />
)}
```

---

### Step 4: 工作流上下文管理 (1h) ⏳

**目标**: 动态获取和传递工作流上下文

#### 4.1 创建 hook: useWorkflowContext

**文件**: `frontend/src/hooks/useWorkflowContext.ts`

**代码框架**:
```typescript
import { useCallback } from 'react'

interface WorkflowContextType {
  nodes: any[]
  edges: any[]
  description?: string
}

/**
 * 获取当前工作流的上下文信息
 */
export function useWorkflowContext() {
  const getContext = useCallback((): WorkflowContextType => {
    // 从 Zustand store 或 React Context 获取
    // 这里假设使用 Zustand (根据项目实际情况调整)
    
    // 方式1: 直接从 store
    const { nodes, edges, description } = useWorkflowStore()
    
    return {
      nodes: nodes.map(n => ({
        id: n.id,
        type: n.type,
        label: n.data?.label,
        config: n.data?.config,
      })),
      edges: edges.map(e => ({
        from: e.source,
        to: e.target,
      })),
      description,
    }
  }, [])

  return { getContext }
}
```

**预计代码行数**: 30-40 行

#### 4.2 修改 useCopilotChat 传递上下文

**文件**: `frontend/src/hooks/useCopilotChat.ts`

**修改**:
```typescript
// 在 sendMessage 中添加上下文参数
const sendMessage = useCallback(
  async (content: string, context?: Record<string, any>) => {
    // ...现有代码...
    
    // 合并工作流上下文
    const fullContext = {
      ...context,
      timestamp: new Date().toISOString(),
      userAgent: typeof window !== 'undefined' ? navigator.userAgent : '',
    }
  },
  []
)
```

---

### Step 5: 集成测试 (1h) ⏳

**目标**: 验证集成功能正常工作

#### 5.1 创建集成测试

**文件**: `frontend/__tests__/integration/copilot-workflow-integration.test.tsx`

**测试框架**:
```typescript
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { WorkflowCanvas } from '@/components/workflow/WorkflowCanvas'
import { CopilotPanel } from '@/components/workflow/CopilotPanel'

describe('Copilot Workflow Integration', () => {
  it('应该将工作流建议应用到画布', async () => {
    // 1. 渲染
    const { container } = render(
      <WorkflowCanvas workflowId="test-123" />
    )

    // 2. 找到 Copilot 面板
    const copilotPanel = screen.getByText('Copilot 助手')
    expect(copilotPanel).toBeInTheDocument()

    // 3. 模拟用户输入
    const input = screen.getByPlaceholderText(/问我任何关于工作流的问题/)
    await userEvent.type(input, '建议一个数据处理工作流')
    
    // 4. 点击发送
    const sendButton = screen.getByRole('button', { name: /发送/ })
    await userEvent.click(sendButton)

    // 5. 等待建议出现
    await waitFor(() => {
      expect(screen.getByText(/数据处理工作流/)).toBeInTheDocument()
    })

    // 6. 应用建议
    const applyButton = screen.getByRole('button', { name: /应用/ })
    await userEvent.click(applyButton)

    // 7. 验证节点已添加
    expect(screen.getByText(/节点已添加/)).toBeInTheDocument()
  })

  it('应该诊断工作流问题', async () => {
    // ...测试诊断功能...
  })

  it('应该生成提示词模板', async () => {
    // ...测试提示词生成...
  })
})
```

**预计代码行数**: 100-120 行

---

## 🔧 技术细节

### 数据流向

```
用户输入消息
    ↓
CopilotPanel 调用 useCopilotChat.sendMessage()
    ↓
sendMessage 获取工作流上下文 (useWorkflowContext)
    ↓
发送到后端 /api/v1/copilot/chat
    ↓
后端返回消息 + 建议 + 诊断
    ↓
CopilotPanel 显示消息
    ↓
CopilotSuggestions 显示建议卡片
    ↓
用户点击 "应用"
    ↓
WorkflowCanvas 调用 onNodeApply / onWorkflowApply
    ↓
更新工作流状态 (Zustand store)
    ↓
画布自动重新渲染
```

### 关键 Props 传递

```
WorkflowCanvas
├─ CopilotPanel (workflowId, onNodeApply, onWorkflowApply)
│  ├─ useCopilotChat (Hook)
│  │  ├─ useWorkflowContext (获取上下文)
│  │  └─ copilotClient (API 调用)
│  └─ CopilotSuggestions (建议卡片)
│     └─ CopilotDiagnostics (诊断结果)
└─ ReactFlow (画布)
```

---

## 📊 时间分配

| 任务 | 预计 | 说明 |
|------|------|------|
| Step 1: 集成到 Canvas | 3h | 最复杂的部分 |
| Step 2: 建议卡片 | 3h | UI 组件编写 |
| Step 3: 诊断显示 | 2h | 相对简单 |
| Step 4: 上下文管理 | 1h | Hook 编写 |
| Step 5: 集成测试 | 1h | 验证功能 |
| **总计** | **8h** | **预计 Day 3 完成** |

---

## ✅ 验收标准

### 功能验收
- [ ] CopilotPanel 正确显示在 WorkflowCanvas 右侧
- [ ] 建议卡片美观显示工作流和节点建议
- [ ] 点击 "应用" 按钮成功添加节点到画布
- [ ] 诊断结果正确显示错误/警告/信息
- [ ] 工作流上下文正确传递到后端

### UI/UX 验收
- [ ] 面板布局整洁，无重叠
- [ ] 按钮和交互响应及时
- [ ] 错误消息清晰易懂
- [ ] 加载状态明确显示
- [ ] 移动端响应式 (可选)

### 测试验收
- [ ] 集成测试 100% 通过
- [ ] 没有控制台错误
- [ ] 没有未处理的异常
- [ ] 性能无明显下降

---

## 🚀 开始实现

### Step-by-Step 检查清单

```bash
# 1. 查看现有 WorkflowCanvas 结构
cat frontend/src/components/workflow/WorkflowCanvas.tsx

# 2. 确认 CopilotPanel 文件存在
test -f frontend/src/components/workflow/CopilotPanel.tsx && echo "✅ CopilotPanel 存在"

# 3. 查看 Zustand store 结构 (工作流状态)
find frontend/src -name "*store*" -o -name "*context*" | grep -i workflow

# 4. 检查现有的 node/edge 类型定义
grep -r "interface.*Node\|interface.*Edge" frontend/src/types/

# 5. 开始实现 Step 1
```

---

## 📌 关键决策点

### 1. 工作流状态管理
- **选项 A**: 使用现有的 Zustand store
- **选项 B**: 使用 React Context
- **推荐**: 检查现有项目使用的方式，保持一致

### 2. 建议应用逻辑
- **选项 A**: 替换整个工作流
- **选项 B**: 只添加建议的节点
- **推荐**: 选项 B (更安全，用户体验好)

### 3. 节点位置计算
- **选项 A**: 固定位置 (250, 250)
- **选项 B**: 自动布局算法
- **推荐**: 选项 A (快速实现，用户可以调整)

---

## 📚 参考资源

- [CopilotPanel 组件](../frontend/src/components/workflow/CopilotPanel.tsx)
- [useCopilotChat Hook](../frontend/src/hooks/useCopilotChat.ts)
- [copilot-client 服务](../frontend/src/services/copilot-client.ts)
- [Copilot 类型定义](../frontend/src/types/copilot.ts)

---

**版本**: 1.0  
**状态**: 📋 Ready to Implement  
**下一步**: 开始 Step 1 - 集成 CopilotPanel
