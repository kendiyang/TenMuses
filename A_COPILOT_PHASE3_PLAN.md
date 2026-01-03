# Task A - Phase 3 实现计划

**阶段**: Phase 3: 建议卡片和诊断组件优化  
**预计时间**: 4 小时  
**预计完成**: 2026-01-03 (Day 3)  
**优先级**: P1 (关键)  
**状态**: 📋 计划中  

---

## 📋 Phase 3 目标

将 CopilotPanel 中的建议卡片和诊断显示提取为独立、可复用的组件，提高代码的可维护性和功能丰富性。

---

## 🎯 分阶段任务

### Step 1: 提取 CopilotSuggestions 组件 (1h) ⏳

**目标**: 创建独立的建议卡片展示组件

**文件**: `frontend/src/components/workflow/CopilotSuggestions.tsx`

**功能**:
- 显示工作流建议列表
- 显示节点建议列表
- 处理应用操作
- 显示加载状态

**API**:
```typescript
interface CopilotSuggestionsProps {
  suggestions?: {
    workflows?: WorkflowSuggestion[]
    nodes?: NodeSuggestion[]
  }
  onApply?: (item: any, type: 'workflow' | 'node') => void
  loading?: boolean
}

export function CopilotSuggestions(props: CopilotSuggestionsProps)
```

**代码框架**:
```tsx
export function CopilotSuggestions({
  suggestions,
  onApply,
  loading,
}: CopilotSuggestionsProps) {
  const [appliedId, setAppliedId] = useState<string | null>(null)

  if (!suggestions) return null

  return (
    <div className="space-y-3 p-3 border-t bg-blue-50">
      {/* 工作流建议 */}
      {suggestions.workflows?.map((wf, idx) => (
        <Card key={idx} className="p-2">
          <h5>{wf.name}</h5>
          <p>{wf.description}</p>
          <Button onClick={() => onApply?.(wf, 'workflow')}>应用</Button>
        </Card>
      ))}

      {/* 节点建议 */}
      {suggestions.nodes?.map((node, idx) => (
        <Card key={idx} className="p-2">
          <h5>{node.label || node.type}</h5>
          <p>{node.explanation}</p>
          <Button onClick={() => onApply?.(node, 'node')}>+</Button>
        </Card>
      ))}
    </div>
  )
}
```

**测试**: 5 个单元测试
- 渲染空建议
- 渲染工作流建议
- 渲染节点建议
- 处理应用事件
- 显示加载状态

---

### Step 2: 提取 CopilotDiagnostics 组件 (1h) ⏳

**目标**: 创建独立的诊断结果展示组件

**文件**: `frontend/src/components/workflow/CopilotDiagnostics.tsx`

**功能**:
- 显示工作流评分
- 显示诊断项目列表
- 支持问题高亮定位
- 展示修复建议

**API**:
```typescript
interface CopilotDiagnosticsProps {
  result?: WorkflowDiagnosis
  onHighlightNode?: (nodeId: string) => void
}

export function CopilotDiagnostics(props: CopilotDiagnosticsProps)
```

**代码框架**:
```tsx
export function CopilotDiagnostics({
  result,
  onHighlightNode,
}: CopilotDiagnosticsProps) {
  if (!result) return null

  const getIcon = (level: string) => {
    switch (level) {
      case 'error': return <AlertCircle className="text-red-600" />
      case 'warning': return <AlertTriangle className="text-yellow-600" />
      default: return <Info className="text-blue-600" />
    }
  }

  return (
    <div className="p-3 border-t space-y-3">
      {/* 评分进度条 */}
      <div className="flex items-center justify-between">
        <span>工作流评分</span>
        <div className="w-24 h-2 bg-gray-200 rounded-full">
          <div
            className={`h-full ${result.score >= 80 ? 'bg-green-500' : 'bg-yellow-500'}`}
            style={{ width: `${result.score}%` }}
          />
        </div>
        <span className="font-bold">{result.score}/100</span>
      </div>

      {/* 摘要 */}
      <p className="text-sm text-gray-700">{result.summary}</p>

      {/* 诊断项目 */}
      {result.diagnostics.map((d, idx) => (
        <div key={idx} className="p-2 border rounded-lg">
          <div className="flex gap-2">
            {getIcon(d.level)}
            <div>
              <h5 className="font-semibold">{d.description}</h5>
              <p className="text-sm">💡 {d.suggestion}</p>
              {d.location?.node_id && (
                <button onClick={() => onHighlightNode?.(d.location!.node_id)}>
                  查看节点 →
                </button>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
```

**测试**: 5 个单元测试
- 渲染空诊断
- 显示评分和摘要
- 渲染诊断项目
- 处理节点高亮
- 显示不同级别的问题

---

### Step 3: 提取 CopilotPromptTemplate 组件 (1h) ⏳

**目标**: 创建 LLM 提示词模板展示和编辑组件

**文件**: `frontend/src/components/workflow/CopilotPromptTemplate.tsx`

**功能**:
- 显示生成的提示词
- 支持编辑提示词
- 显示令牌估计
- 支持不同的样式（结构化/详细/简洁）

**API**:
```typescript
interface CopilotPromptTemplateProps {
  template?: PromptTemplate
  onEdit?: (prompt: string) => void
  onApply?: (prompt: string) => void
  loading?: boolean
}

export function CopilotPromptTemplate(props: CopilotPromptTemplateProps)
```

**代码框架**:
```tsx
export function CopilotPromptTemplate({
  template,
  onEdit,
  onApply,
  loading,
}: CopilotPromptTemplateProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editedPrompt, setEditedPrompt] = useState(template?.prompt || '')

  if (!template) return null

  return (
    <div className="p-3 border-t space-y-3 bg-blue-50">
      {/* 标题 */}
      <div className="flex items-center justify-between">
        <h4 className="font-semibold">生成的提示词</h4>
        <Badge variant="outline">{template.style}</Badge>
      </div>

      {/* 提示词内容 */}
      {!isEditing ? (
        <div className="p-3 bg-white border rounded-lg max-h-48 overflow-y-auto">
          <p className="text-sm whitespace-pre-wrap font-mono">{template.prompt}</p>
        </div>
      ) : (
        <textarea
          value={editedPrompt}
          onChange={(e) => setEditedPrompt(e.target.value)}
          className="w-full p-3 border rounded-lg font-mono text-sm resize-none"
          rows={6}
        />
      )}

      {/* 令牌估计 */}
      <div className="text-xs text-gray-600 flex justify-between">
        <span>预计令牌: {template.estimated_tokens}</span>
        <span>风格: {template.style}</span>
      </div>

      {/* 操作按钮 */}
      <div className="flex gap-2">
        <Button
          size="sm"
          variant={isEditing ? 'default' : 'outline'}
          onClick={() => {
            if (isEditing) {
              onEdit?.(editedPrompt)
              setIsEditing(false)
            } else {
              setIsEditing(true)
            }
          }}
        >
          {isEditing ? '保存' : '编辑'}
        </Button>
        <Button
          size="sm"
          onClick={() => onApply?.(editedPrompt)}
          disabled={loading}
        >
          应用到节点
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => navigator.clipboard.writeText(editedPrompt)}
        >
          <Copy className="h-3 w-3" />
        </Button>
      </div>
    </div>
  )
}
```

**测试**: 5 个单元测试
- 渲染空模板
- 显示提示词内容
- 编辑模式切换
- 应用到节点
- 复制到剪贴板

---

### Step 4: 更新 CopilotPanel 使用新组件 (0.5h) ⏳

**目标**: 重构 CopilotPanel 使用新的独立组件

**文件**: `frontend/src/components/workflow/CopilotPanel.tsx`

**修改内容**:
```tsx
import { CopilotSuggestions } from './CopilotSuggestions'
import { CopilotDiagnostics } from './CopilotDiagnostics'
import { CopilotPromptTemplate } from './CopilotPromptTemplate'

// 在消息渲染中替换为新组件
{msg.suggestions && (
  <CopilotSuggestions
    suggestions={msg.suggestions}
    onApply={handleSuggestionApply}
  />
)}

{msg.diagnostics && (
  <CopilotDiagnostics
    result={msg.diagnostics}
    onHighlightNode={handleHighlightNode}
  />
)}

{msg.promptTemplate && (
  <CopilotPromptTemplate
    template={msg.promptTemplate}
    onApply={handleApplyPrompt}
  />
)}
```

**移除**:
- 重复的建议卡片代码
- 重复的诊断显示代码
- 直接的提示词渲染

---

### Step 5: 集成测试 (0.5h) ⏳

**目标**: 测试新组件的集成和交互

**文件**: `frontend/__tests__/integration/copilot-components.test.tsx`

**测试场景**:
1. CopilotSuggestions 应用工作流
2. CopilotDiagnostics 高亮节点
3. CopilotPromptTemplate 编辑和应用
4. 完整的 CopilotPanel 组件集成

---

## 🔧 技术细节

### 组件关系图

```
CopilotPanel
├─ CopilotSuggestions (工作流和节点建议)
├─ CopilotDiagnostics (诊断结果)
├─ CopilotPromptTemplate (提示词模板)
└─ Message Display (基础消息显示)
```

### Props 传递链

```
WorkflowPage
  └─ CopilotPanel (workflowId, callbacks)
     ├─ useCopilotChat (messages, sendMessage)
     ├─ useWorkflowContext (getContext)
     ├─ CopilotSuggestions (onApply)
     ├─ CopilotDiagnostics (onHighlightNode)
     └─ CopilotPromptTemplate (onApply)
```

---

## 📊 时间分配

| 任务 | 预计 | 说明 |
|------|------|------|
| Step 1: Suggestions 组件 | 1h | UI + 状态管理 |
| Step 2: Diagnostics 组件 | 1h | 评分展示 + 问题列表 |
| Step 3: Prompt 组件 | 1h | 编辑 + 预览 |
| Step 4: 更新 CopilotPanel | 0.5h | 集成新组件 |
| Step 5: 集成测试 | 0.5h | 验证功能 |
| **总计** | **4h** | **Day 3 完成** |

---

## ✅ 验收标准

### 功能验收
- [ ] CopilotSuggestions 正确显示建议
- [ ] CopilotDiagnostics 正确显示诊断
- [ ] CopilotPromptTemplate 支持编辑
- [ ] 三个组件都可独立使用
- [ ] CopilotPanel 使用新组件后功能完整

### UI/UX 验收
- [ ] 组件布局美观一致
- [ ] 交互响应及时
- [ ] 错误消息清晰
- [ ] 加载状态明显
- [ ] 无视觉重复

### 测试验收
- [ ] 所有新组件测试通过
- [ ] 集成测试通过
- [ ] 没有控制台错误
- [ ] 没有未处理的异常
- [ ] 性能无明显下降

---

## 🚀 后续工作 (Phase 4-5)

### Phase 4: 高级特性 (6 小时)
- [ ] 流式响应支持（SSE）
- [ ] 建议历史记录
- [ ] 建议收藏功能
- [ ] 提示词编辑功能
- [ ] 工作流对比功能

### Phase 5: 完整测试和优化 (6 小时)
- [ ] 前端单元测试 (Jest)
- [ ] E2E 集成测试 (Cypress)
- [ ] 性能优化
- [ ] 可访问性改进
- [ ] 生产部署准备

---

## 📝 关键决策点

### 1. 组件独立性
- **选项 A**: 完全独立的组件，无内部状态
- **选项 B**: 带内部状态管理的完整组件
- **推荐**: 选项 A (灵活性更高)

### 2. 编辑模式
- **选项 A**: 内联编辑
- **选项 B**: 弹出对话框
- **推荐**: 选项 A (用户体验更好)

### 3. 提示词样式
- **选项 A**: 下拉菜单选择
- **选项 B**: 按钮组切换
- **推荐**: 选项 B (更直观)

---

**版本**: 1.0  
**状态**: 📋 Ready to Plan  
**下一步**: 开始 Phase 3 实现
