# A. Copilot 集成 - 完整技术设计与实现

**预计工期**: 40-50 小时  
**优先级**: P1 (关键功能)  
**状态**: 🟡 开始实现

---

## 1. 功能概述

### 核心功能
1. **Copilot Chat**: 工作流编辑时的 AI 对话助手
2. **工作流建议**: AI 自动生成工作流建议
3. **节点补全**: 智能建议和补全工作流节点
4. **错误诊断**: 识别工作流配置错误并给出修复建议
5. **代码生成**: 为 LLM 节点生成提示词模板

### 用户交互流程

```
用户编辑工作流
    ↓
打开 Copilot 面板
    ↓
描述需求 (e.g., "我需要一个分类工作流")
    ↓
Copilot Chat 响应 + 建议
    ↓
点击建议 → 自动生成工作流节点
    ↓
优化和调整
    ↓
保存工作流
```

---

## 2. 技术架构

### 2.1 后端架构

```python
backend/app/
├── services/
│   └── copilot_service.py (新建 - 300 行)
│       ├── CopilotService 类
│       │   ├── chat(message, context) → str
│       │   ├── suggest_workflow(description) → List[WorkflowTemplate]
│       │   ├── suggest_node(node_type, context) → NodeSuggestion
│       │   ├── diagnose_workflow(workflow) → List[Diagnostic]
│       │   └── generate_prompt_template(task_desc) → str
│       └── PromptTemplate 辅助类
├── api/v1/
│   └── copilot.py (新建 - 200 行)
│       ├── POST /api/v1/copilot/chat
│       ├── POST /api/v1/copilot/suggest/workflow
│       ├── POST /api/v1/copilot/suggest/node
│       ├── POST /api/v1/copilot/diagnose
│       └── POST /api/v1/copilot/generate-prompt
└── schemas/
    └── copilot.py (新建 - 150 行)
        ├── ChatRequest
        ├── ChatResponse
        ├── WorkflowSuggestion
        ├── NodeSuggestion
        └── Diagnostic
```

### 2.2 前端架构

```typescript
frontend/src/
├── components/
│   └── workflow/
│       ├── CopilotPanel.tsx (新建 - 300 行)
│       │   ├── Chat 窗口
│       │   ├── 消息历史
│       │   ├── 输入框 + 快速按钮
│       │   └── 加载状态
│       ├── CopilotSuggestions.tsx (新建 - 150 行)
│       │   ├── 工作流建议卡片
│       │   ├── 节点建议卡片
│       │   └── 应用按钮
│       └── CopilotDiagnostics.tsx (新建 - 100 行)
│           └── 诊断结果展示
├── hooks/
│   └── useCopilotChat.ts (新建 - 200 行)
│       ├── useChat() Hook
│       ├── 消息管理
│       ├── 加载/错误状态
│       └── API 调用
├── services/
│   └── copilot-client.ts (新建 - 150 行)
│       ├── CopilotClient 类
│       └── API 方法封装
└── types/
    └── copilot.ts (新建 - 100 行)
        ├── ChatMessage
        ├── WorkflowSuggestion
        └── Diagnostic
```

---

## 3. 详细设计

### 3.1 后端 API 设计

#### 1. Chat API
```python
POST /api/v1/copilot/chat
Request:
{
  "message": "如何创建一个数据处理工作流?",
  "context": {
    "workflow_id": "xxx",
    "current_nodes": [...],
    "user_id": "xxx"
  },
  "chat_history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}

Response:
{
  "message": "你可以创建这样的工作流...",
  "suggestions": {
    "workflows": [...],
    "nodes": [...],
    "prompt_templates": [...]
  },
  "thinking": "用户想要...所以建议..."
}
```

#### 2. Workflow 建议 API
```python
POST /api/v1/copilot/suggest/workflow
Request:
{
  "description": "创建一个新闻分类工作流",
  "category": "data_processing|nlp|web_scraping|...",
  "complexity": "simple|medium|advanced"
}

Response:
{
  "workflows": [
    {
      "id": "template_001",
      "name": "新闻分类工作流",
      "description": "...",
      "nodes": [...],
      "edges": [...],
      "explanation": "这个工作流包含..."
    }
  ],
  "metadata": {
    "total": 3,
    "categories": ["nlp", "classification"]
  }
}
```

#### 3. Node 建议 API
```python
POST /api/v1/copilot/suggest/node
Request:
{
  "current_node_type": "LLM",
  "next_action": "继续分类结果",
  "context": {
    "workflow_description": "...",
    "previous_outputs": {...}
  }
}

Response:
{
  "suggestions": [
    {
      "type": "Router",
      "config": {
        "condition": "classification_result == 'news'",
        "next_node": "process_news"
      },
      "explanation": "用于根据分类结果路由"
    },
    {
      "type": "Tool",
      "config": {...},
      "explanation": "..."
    }
  ]
}
```

#### 4. 诊断 API
```python
POST /api/v1/copilot/diagnose
Request:
{
  "workflow": {
    "nodes": [...],
    "edges": [...]
  }
}

Response:
{
  "diagnostics": [
    {
      "level": "error|warning|info",
      "type": "disconnected_node|missing_required_input|infinite_loop|...",
      "description": "节点 X 没有输入连接",
      "location": {"node_id": "xxx"},
      "suggestion": "添加从 Y 节点的连接"
    }
  ],
  "score": 75  // 工作流质量评分 (0-100)
}
```

#### 5. 提示词生成 API
```python
POST /api/v1/copilot/generate-prompt
Request:
{
  "task": "新闻标题分类为：政治、体育、娱乐、其他",
  "input_format": "单行新闻标题",
  "output_format": "json with {title, category, confidence}",
  "examples": [
    {"input": "习近平视察...", "output": "category: 政治"}
  ]
}

Response:
{
  "prompt": """你是一个新闻分类专家。
  
任务: 将输入的新闻标题分类到以下类别之一: 政治、体育、娱乐、其他

输入格式: 单行新闻标题
输出格式: {"title": "原始标题", "category": "...", "confidence": 0.0-1.0}

示例:
输入: "习近平视察..."
输出: {"title": "习近平视察...", "category": "政治", "confidence": 0.95}

现在请对以下新闻进行分类:
{{INPUT}}""",
  "style": "structured|detailed|concise",
  "estimated_tokens": 250
}
```

### 3.2 前端组件设计

#### CopilotPanel.tsx
```typescript
interface CopilotPanelProps {
  workflowId?: string
  onNodeSuggestionClick?: (node: NodeSuggestion) => void
  onWorkflowSuggestionClick?: (workflow: WorkflowSuggestion) => void
}

export function CopilotPanel({ 
  workflowId, 
  onNodeSuggestionClick,
  onWorkflowSuggestionClick 
}: CopilotPanelProps) {
  const { messages, isLoading, error, sendMessage, clearHistory } = useCopilotChat()
  const [inputValue, setInputValue] = useState('')

  const handleSend = async () => {
    await sendMessage(inputValue, {
      workflow_id: workflowId,
      context_type: 'workflow_editor'
    })
    setInputValue('')
  }

  return (
    <Panel title="Copilot" icon={<Sparkles />}>
      <div className="flex flex-col h-full">
        {/* 消息列表 */}
        <div className="flex-1 overflow-auto space-y-3 p-3">
          {messages.map((msg, idx) => (
            <ChatMessage 
              key={idx} 
              role={msg.role} 
              content={msg.content}
            />
          ))}
          {isLoading && <LoadingMessage />}
        </div>

        {/* 建议卡片 */}
        {message.suggestions && (
          <CopilotSuggestions 
            suggestions={message.suggestions}
            onApply={...}
          />
        )}

        {/* 诊断结果 */}
        {message.diagnostics && (
          <CopilotDiagnostics 
            diagnostics={message.diagnostics}
          />
        )}

        {/* 输入框 */}
        <div className="border-t p-3 space-y-2">
          <Input
            placeholder="问我关于工作流的任何问题..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          />
          <div className="flex gap-2">
            <Button onClick={handleSend} disabled={!inputValue || isLoading}>
              发送
            </Button>
            <Button variant="outline" onClick={clearHistory}>
              清除历史
            </Button>
          </div>
          
          {/* 快速按钮 */}
          <div className="text-xs space-y-1">
            <Button variant="ghost" size="sm" 
              onClick={() => setInputValue('建议我一个工作流')}>
              💡 建议工作流
            </Button>
            <Button variant="ghost" size="sm"
              onClick={() => setInputValue('检查工作流是否正确')}>
              🔍 诊断工作流
            </Button>
          </div>
        </div>
      </div>
    </Panel>
  )
}
```

#### useCopilotChat.ts
```typescript
interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  suggestions?: any
  diagnostics?: any
}

export function useCopilotChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendMessage = async (content: string, context?: any) => {
    // 添加用户消息
    setMessages(prev => [...prev, { 
      role: 'user', 
      content,
      timestamp: Date.now()
    }])

    setIsLoading(true)
    try {
      const response = await copilotClient.chat({
        message: content,
        context,
        chat_history: messages
      })

      // 添加助手响应
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.message,
        suggestions: response.suggestions,
        diagnostics: response.diagnostics,
        timestamp: Date.now()
      }])
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setIsLoading(false)
    }
  }

  const clearHistory = () => {
    setMessages([])
    setError(null)
  }

  return { messages, isLoading, error, sendMessage, clearHistory }
}
```

---

## 4. 实现细节

### 4.1 后端实现步骤

#### Step 1: 创建 CopilotService (Day 1)
```python
# backend/app/services/copilot_service.py

from typing import List, Optional, Dict, Any
from openai import OpenAI, AsyncOpenAI
from pydantic import BaseModel
import json

class CopilotService:
    def __init__(self, openai_api_key: str, model: str = "gpt-4"):
        self.client = AsyncOpenAI(api_key=openai_api_key)
        self.model = model
        self.system_prompt = """你是 TenMuses 工作流编辑助手。
你的职责是:
1. 回答关于工作流设计的问题
2. 根据用户需求建议工作流
3. 提供节点配置建议
4. 诊断工作流问题
5. 生成 LLM 提示词

保持回复简洁、有用、专业。"""

    async def chat(self, message: str, context: Dict[str, Any]) -> str:
        """处理聊天消息"""
        # 构造上下文
        system_msg = self.system_prompt
        if context.get('workflow_description'):
            system_msg += f"\n\n当前工作流描述: {context['workflow_description']}"
        
        # 调用 OpenAI
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_msg},
                *context.get('chat_history', []),
                {"role": "user", "content": message}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content

    async def suggest_workflow(self, description: str) -> List[Dict]:
        """建议工作流模板"""
        prompt = f"""根据以下需求,建议 3 个工作流模板:

需求: {description}

返回 JSON 格式:
{{
  "workflows": [
    {{
      "name": "工作流名称",
      "description": "描述",
      "nodes": [
        {{"type": "LLM", "config": {{...}}}},
        ...
      ],
      "edges": [
        {{"from": "node_1", "to": "node_2"}},
        ...
      ],
      "explanation": "为什么推荐这个工作流"
    }},
    ...
  ]
}}"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是工作流设计专家,返回有效的 JSON"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        # 解析并验证 JSON
        content = response.choices[0].message.content
        # 提取 JSON (可能包含在 markdown 代码块中)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        return json.loads(content.strip())
```

#### Step 2: 创建 API 端点 (Day 2)
```python
# backend/app/api/v1/copilot.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import get_current_user
from app.services.copilot_service import CopilotService
from app.schemas.copilot import (
    ChatRequest, ChatResponse,
    WorkflowSuggestionRequest, WorkflowSuggestionResponse
)

router = APIRouter(prefix="/copilot", tags=["copilot"])

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Copilot 聊天端点"""
    copilot = CopilotService(api_key=get_openai_key())
    
    try:
        response = await copilot.chat(
            message=request.message,
            context={
                **request.context.dict() if request.context else {},
                "chat_history": request.chat_history,
                "user_id": current_user.id
            }
        )
        
        return ChatResponse(
            message=response,
            suggestions=None,  # 可以在需要时添加建议提取逻辑
            diagnostics=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suggest/workflow", response_model=WorkflowSuggestionResponse)
async def suggest_workflow(
    request: WorkflowSuggestionRequest,
    current_user = Depends(get_current_user)
):
    """工作流建议端点"""
    copilot = CopilotService(api_key=get_openai_key())
    
    try:
        workflows = await copilot.suggest_workflow(
            description=request.description
        )
        return WorkflowSuggestionResponse(workflows=workflows['workflows'])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 4.2 前端实现步骤

#### Step 1: 创建 Hook (Day 2)
```typescript
// frontend/src/hooks/useCopilotChat.ts

import { useState, useCallback } from 'react'
import { copilotClient } from '@/services/copilot-client'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: number
  suggestions?: any
}

export function useCopilotChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendMessage = useCallback(async (content: string, context?: any) => {
    setMessages(prev => [...prev, {
      role: 'user',
      content,
      timestamp: Date.now()
    }])

    setIsLoading(true)
    try {
      const response = await copilotClient.chat({
        message: content,
        context: context || {},
        chat_history: messages.map(m => ({
          role: m.role,
          content: m.content
        }))
      })

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: response.message,
        suggestions: response.suggestions,
        timestamp: Date.now()
      }])
      setError(null)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setIsLoading(false)
    }
  }, [messages])

  const clearHistory = useCallback(() => {
    setMessages([])
    setError(null)
  }, [])

  return { messages, isLoading, error, sendMessage, clearHistory }
}
```

#### Step 2: 创建组件 (Day 3)
```typescript
// frontend/src/components/workflow/CopilotPanel.tsx

import { useState } from 'react'
import { useCopilotChat } from '@/hooks/useCopilotChat'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Sparkles, Send, RefreshCw } from 'lucide-react'

interface CopilotPanelProps {
  workflowId?: string
  onNodeApply?: (node: any) => void
  onWorkflowApply?: (workflow: any) => void
}

export function CopilotPanel({
  workflowId,
  onNodeApply,
  onWorkflowApply
}: CopilotPanelProps) {
  const { messages, isLoading, error, sendMessage, clearHistory } = useCopilotChat()
  const [inputValue, setInputValue] = useState('')

  const handleSend = async () => {
    if (!inputValue.trim()) return
    
    await sendMessage(inputValue, {
      workflow_id: workflowId,
      context_type: 'workflow_editor'
    })
    setInputValue('')
  }

  const handleQuickButton = (text: string) => {
    setInputValue(text)
  }

  return (
    <Card className="flex flex-col h-[600px] bg-gradient-to-br from-blue-50 to-purple-50 border border-purple-200">
      {/* 标题 */}
      <div className="flex items-center gap-2 p-4 border-b bg-white rounded-t-lg">
        <Sparkles className="h-5 w-5 text-purple-600" />
        <h3 className="font-semibold text-gray-900">Copilot 助手</h3>
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-auto space-y-3 p-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <Sparkles className="h-12 w-12 mx-auto text-gray-300 mb-2" />
            <p>开始对话以获得工作流建议</p>
          </div>
        )}
        
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs px-3 py-2 rounded-lg ${
                msg.role === 'user'
                  ? 'bg-purple-600 text-white'
                  : 'bg-white text-gray-900 border border-gray-200'
              }`}
            >
              <p className="text-sm">{msg.content}</p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white px-3 py-2 rounded-lg border border-gray-200">
              <div className="flex gap-1">
                <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" />
                <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce delay-100" />
                <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 快速按钮 */}
      <div className="border-t p-3 space-y-2 bg-white">
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start text-xs text-left"
          onClick={() => handleQuickButton('建议一个完整的工作流')}
        >
          💡 建议工作流
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start text-xs text-left"
          onClick={() => handleQuickButton('检查这个工作流是否正确')}
        >
          🔍 诊断工作流
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-start text-xs text-left"
          onClick={() => handleQuickButton('帮我生成一个 LLM 提示词')}
        >
          ✍️ 生成提示词
        </Button>
      </div>

      {/* 输入框 */}
      <div className="border-t p-3 bg-white space-y-2 rounded-b-lg">
        {error && (
          <div className="text-xs text-red-600 bg-red-50 p-2 rounded">
            {error}
          </div>
        )}
        <div className="flex gap-2">
          <Input
            placeholder="问我任何关于工作流的问题..."
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSend()
              }
            }}
            disabled={isLoading}
            className="text-sm"
          />
          <Button
            onClick={handleSend}
            disabled={!inputValue.trim() || isLoading}
            size="sm"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="w-full"
          onClick={clearHistory}
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          清除历史
        </Button>
      </div>
    </Card>
  )
}
```

---

## 5. 测试计划

### 5.1 单元测试

```python
# backend/test_copilot.py

@pytest.mark.asyncio
async def test_copilot_chat():
    """测试 Copilot Chat"""
    copilot = CopilotService(api_key="test-key")
    response = await copilot.chat(
        message="如何创建工作流?",
        context={}
    )
    assert isinstance(response, str)
    assert len(response) > 0

@pytest.mark.asyncio
async def test_suggest_workflow():
    """测试工作流建议"""
    copilot = CopilotService(api_key="test-key")
    result = await copilot.suggest_workflow(
        description="创建数据分析工作流"
    )
    assert "workflows" in result
    assert len(result["workflows"]) > 0
```

### 5.2 集成测试

```python
# backend/test_copilot_integration.py

@pytest.mark.asyncio
async def test_copilot_api_chat(client: AsyncClient):
    """测试 Chat API"""
    response = await client.post(
        "/api/v1/copilot/chat",
        json={
            "message": "建议一个工作流",
            "chat_history": []
        },
        headers={"Authorization": f"Bearer {test_token}"}
    )
    assert response.status_code == 200
    assert "message" in response.json()
```

---

## 6. 集成到工作流编辑器

### 6.1 在 WorkflowCanvas 中集成

```typescript
// frontend/src/components/workflow/WorkflowCanvas.tsx

import { CopilotPanel } from './CopilotPanel'

export function WorkflowCanvas() {
  // ... existing code ...

  return (
    <div className="flex gap-4 h-screen">
      {/* 左侧: 工具栏 */}
      <NodeToolbar />

      {/* 中央: 画布 */}
      <div className="flex-1">
        <ReactFlow>
          {/* nodes and edges */}
        </ReactFlow>
      </div>

      {/* 右侧上: 属性面板 */}
      <div className="w-80 space-y-4">
        <PropertiesPanel />

        {/* 右侧下: Copilot */}
        <CopilotPanel
          workflowId={workflow.id}
          onNodeApply={(node) => {
            // 添加节点到画布
            addNode(node)
          }}
          onWorkflowApply={(workflow) => {
            // 应用整个工作流
            loadWorkflow(workflow)
          }}
        />
      </div>
    </div>
  )
}
```

---

## 7. 部署要求

### 环境变量
```bash
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4  # 或 gpt-4-turbo-preview
COPILOT_MAX_TOKENS=2000
COPILOT_TEMPERATURE=0.7
```

### 依赖
```txt
openai>=1.0.0
python-dotenv
pydantic
```

---

## 8. 开发时间表

| 任务 | 时间 | 状态 |
|------|------|------|
| Step 1: CopilotService + 基础方法 | 6h | ⏳ |
| Step 2: API 端点设计和实现 | 6h | ⏳ |
| Step 3: 前端 Hook 和 Service | 4h | ⏳ |
| Step 4: CopilotPanel 组件 | 8h | ⏳ |
| Step 5: 建议卡片组件 | 4h | ⏳ |
| Step 6: 单元测试 | 6h | ⏳ |
| Step 7: 集成测试 | 4h | ⏳ |
| Step 8: UI 优化和文档 | 6h | ⏳ |
| **总计** | **44h** | **⏳** |

---

## 9. 成功标准

- ✅ Chat API 返回相关回复
- ✅ 工作流建议 API 生成有效的节点配置
- ✅ 前端可以显示和应用建议
- ✅ 错误处理覆盖主要场景
- ✅ 单元测试覆盖 80%+ 代码
- ✅ 响应时间 < 3 秒 (不含 OpenAI API 延迟)
- ✅ 用户满意度 > 4/5

---

现在开始实现! 让我们从 **Step 1: CopilotService** 开始。
