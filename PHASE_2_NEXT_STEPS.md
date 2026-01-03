# Phase 2 下一阶段实施计划

**当前进度**: Phase 2 Enhanced MVP (60% 完成)  
**已完成**: 动态图构建 + HITL + P0/P1 修复  
**待完成**: RAG 知识库 + Copilot 集成

---

## 📊 当前状态评估

### ✅ 已完成功能

| 功能模块 | 完成度 | 状态 |
|---------|--------|------|
| 动态图构建工厂 | 100% | ✅ 验证通过 |
| HITL 中断机制 | 100% | ✅ 验证通过 |
| P0 安全修复 | 100% | ✅ 3/3 通过 |
| P1 功能改进 | 100% | ✅ 2/2 通过 |
| 前后端服务 | 100% | ✅ 运行正常 |

### 🚧 待实施功能

| 功能模块 | 优先级 | 预计工期 | 状态 |
|---------|--------|---------|------|
| **RAG 知识库** | P0 | 2-3 周 | 📋 待开始 |
| **Copilot 集成** | P1 | 2-3 周 | 📋 待开始 |
| 模板市场 | P1 | 4-6 周 | 📅 Phase 2.5 |

---

## 🎯 Phase 2 剩余任务：RAG 知识库集成

### 目标

实现文档上传、向量化存储、语义检索，并集成到工作流节点中，提升 LLM 输出质量。

### 架构设计

```
用户上传文档 → 文本提取 → 分片 → 向量化 → pgvector 存储
                                                    ↓
                                     工作流执行 ← 语义检索 ← LLM 节点配置
```

### 技术选型

**向量数据库**: `pgvector` (PostgreSQL 扩展)
- 优势: 与现有 PostgreSQL 集成，无需额外维护
- 向量维度: 1536 (OpenAI text-embedding-3-small)

**嵌入模型**: OpenAI `text-embedding-3-small`
- 成本: $0.02 / 1M tokens
- 性能: 适中，满足 MVP 需求

**文档处理**: `unstructured` + `pypdf`
- 支持: PDF, DOCX, TXT, HTML, Markdown

### 数据库设计

```sql
-- 知识库文档表
CREATE TABLE kb_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    workspace_id UUID,  -- 可选：团队/空间隔离
    
    -- 来源信息
    source_type VARCHAR(50) NOT NULL,  -- 'file', 'url', 'text'
    source_url TEXT,
    filename VARCHAR(500),
    file_size INTEGER,
    
    -- 内容
    content TEXT NOT NULL,
    content_hash VARCHAR(64),  -- SHA256，用于去重
    
    -- 向量
    embedding VECTOR(1536),
    
    -- 元数据
    metadata JSONB DEFAULT '{}',
    chunk_count INTEGER DEFAULT 1,
    
    -- 状态
    status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed
    
    -- 时间
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    processed_at TIMESTAMP
);

-- 文档分片表 (大文档需要分片)
CREATE TABLE kb_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES kb_documents(id) ON DELETE CASCADE,
    
    -- 分片内容
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER,
    
    -- 向量
    embedding VECTOR(1536),
    
    -- 元数据
    metadata JSONB DEFAULT '{}',
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- 向量相似度索引 (HNSW 算法)
CREATE INDEX ON kb_documents USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON kb_chunks USING hnsw (embedding vector_cosine_ops);

-- 用户文档索引
CREATE INDEX idx_kb_documents_user ON kb_documents(user_id, created_at DESC);
CREATE INDEX idx_kb_chunks_document ON kb_chunks(document_id, chunk_index);
```

### 详细任务清单

#### 1️⃣ 后端 RAG 基础设施 (第1周)

**数据库与模型**
- [ ] 安装 pgvector 扩展
  ```sql
  CREATE EXTENSION IF NOT EXISTS vector;
  ```
- [ ] 创建 `kb_documents` 和 `kb_chunks` 表
- [ ] 创建 SQLAlchemy 模型 (`backend/app/models/knowledge.py`)
- [ ] 创建 Pydantic schemas (`backend/app/schemas/knowledge.py`)

**文档处理服务**
- [ ] 创建 `backend/app/services/document_processor.py`
  - [ ] `extract_text(file_path, mime_type)` - 文本提取
  - [ ] `chunk_text(text, max_tokens=500)` - 文本分片
  - [ ] `compute_hash(content)` - 内容哈希（去重）

**向量化服务**
- [ ] 创建 `backend/app/services/embedding_service.py`
  - [ ] `embed_text(text: str) -> List[float]` - 单个文本向量化
  - [ ] `embed_batch(texts: List[str])` - 批量向量化
  - [ ] 配置 OpenAI embedding API

**RAG 检索服务**
- [ ] 创建 `backend/app/services/rag_service.py`
  - [ ] `search_documents(query, user_id, top_k=5)` - 相似度检索
  - [ ] `search_chunks(query, user_id, top_k=10)` - 分片级检索
  - [ ] `format_context(chunks)` - 格式化为 LLM 上下文

#### 2️⃣ 知识库 API 端点 (第1-2周)

**CRUD 接口** (`backend/app/api/v1/knowledge.py`)

```python
# 文档上传
POST /api/v1/kb/documents
Content-Type: multipart/form-data
- file: File
- source_type: 'file' | 'url' | 'text'
- metadata: JSON (可选)

Response:
{
  "id": "doc-uuid",
  "filename": "report.pdf",
  "status": "processing",
  "chunkCount": 0
}

# 文档列表
GET /api/v1/kb/documents?page=1&page_size=20&status=completed

# 文档详情
GET /api/v1/kb/documents/{id}

# 删除文档
DELETE /api/v1/kb/documents/{id}

# 语义搜索
POST /api/v1/kb/search
{
  "query": "什么是 LangGraph?",
  "topK": 5,
  "filters": {
    "documentIds": ["doc-1", "doc-2"],  // 可选
    "minScore": 0.7  // 相似度阈值
  }
}

Response:
{
  "results": [
    {
      "documentId": "doc-1",
      "chunkId": "chunk-1",
      "content": "LangGraph 是...",
      "score": 0.92,
      "metadata": {...}
    }
  ],
  "total": 5
}
```

**任务列表**
- [ ] 实现文档上传端点（支持 PDF/DOCX/TXT）
- [ ] 实现 URL 爬取端点（基于 `requests` + `beautifulsoup4`）
- [ ] 实现文本直接输入端点
- [ ] 实现文档列表/详情/删除端点
- [ ] 实现语义搜索端点
- [ ] 添加后台任务处理（Celery 或 FastAPI BackgroundTasks）

#### 3️⃣ 工作流节点 RAG 集成 (第2周)

**节点配置扩展**

在 `NodeData` 中增加 RAG 配置：

```python
# backend/app/schemas/node.py
class LLMConfig(BaseModel):
    # ... 现有字段
    
    # RAG 配置
    enable_rag: bool = False
    rag_config: Optional[Dict[str, Any]] = None
    # {
    #   "documentIds": ["doc-1", "doc-2"],  // 指定文档
    #   "topK": 5,
    #   "minScore": 0.7,
    #   "contextTemplate": "参考资料:\n{context}\n\n问题: {query}"
    # }
```

**执行器增强**

```python
# backend/app/services/dynamic_graph_factory.py
class LLMNodeExecutor(NodeExecutor):
    @retry(...)
    async def _invoke_llm(self, config, prompt: str, state: WorkflowState):
        # 1. RAG 检索
        if config.enable_rag and config.rag_config:
            context = await self._retrieve_context(
                query=prompt,
                rag_config=config.rag_config,
                user_id=state.metadata.get("user_id")
            )
            
            # 2. 注入上下文
            template = config.rag_config.get(
                "contextTemplate",
                "参考资料:\n{context}\n\n问题: {query}"
            )
            prompt = template.format(context=context, query=prompt)
        
        # 3. 调用 LLM
        result = await llm_client.invoke(...)
        return result
    
    async def _retrieve_context(self, query, rag_config, user_id):
        from app.services.rag_service import RAGService
        
        rag_service = RAGService()
        results = await rag_service.search_documents(
            query=query,
            user_id=user_id,
            top_k=rag_config.get("topK", 5),
            document_ids=rag_config.get("documentIds"),
            min_score=rag_config.get("minScore", 0.7)
        )
        
        # 格式化上下文
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[{i}] {result['content']}\n来源: {result['metadata'].get('filename', 'Unknown')}"
            )
        
        return "\n\n".join(context_parts)
```

**任务列表**
- [ ] 扩展 `LLMConfig` schema 支持 RAG
- [ ] 在 `LLMNodeExecutor` 中实现 `_retrieve_context`
- [ ] 添加 RAG 上下文格式化逻辑
- [ ] 测试带 RAG 的工作流执行

#### 4️⃣ 前端知识库 UI (第2-3周)

**知识库管理页面** (`frontend/src/app/knowledge/page.tsx`)

```tsx
// 功能需求：
- 文档列表（表格视图）
- 上传按钮（拖拽上传 + 文件选择）
- 搜索框（测试语义检索）
- 删除/查看详情
- 处理状态展示（pending/processing/completed/failed）
```

**工作流节点配置面板**

在节点属性面板中增加 RAG 配置：

```tsx
// frontend/src/components/workflow/NodeConfigPanel.tsx

{nodeType === 'llm' && (
  <div className="space-y-4">
    {/* 现有配置... */}
    
    {/* RAG 配置 */}
    <div className="border-t pt-4">
      <label className="flex items-center space-x-2">
        <input
          type="checkbox"
          checked={config.enableRag}
          onChange={(e) => updateConfig('enableRag', e.target.checked)}
        />
        <span>启用知识库检索 (RAG)</span>
      </label>
      
      {config.enableRag && (
        <div className="mt-4 space-y-3">
          {/* 文档选择 */}
          <DocumentSelector
            selectedDocs={config.ragConfig?.documentIds || []}
            onChange={(ids) => updateRagConfig('documentIds', ids)}
          />
          
          {/* 检索参数 */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label>相似度阈值</label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={config.ragConfig?.minScore || 0.7}
                onChange={(e) => updateRagConfig('minScore', parseFloat(e.target.value))}
              />
            </div>
            <div>
              <label>检索数量</label>
              <input
                type="number"
                min="1"
                max="20"
                value={config.ragConfig?.topK || 5}
                onChange={(e) => updateRagConfig('topK', parseInt(e.target.value))}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  </div>
)}
```

**任务列表**
- [ ] 创建知识库管理页面路由
- [ ] 实现文档上传组件（react-dropzone）
- [ ] 实现文档列表组件（表格 + 分页）
- [ ] 实现语义搜索测试界面
- [ ] 在节点配置面板中增加 RAG 开关
- [ ] 实现文档选择器组件
- [ ] 实现 RAG 参数配置 UI

#### 5️⃣ RAG 集成测试 (第3周)

**测试场景**

1. **文档上传与处理**
   - 上传 5 种类型文档（PDF/DOCX/TXT/MD/HTML）
   - 验证向量化成功
   - 验证分片逻辑

2. **语义检索准确性**
   - 上传技术文档（如 LangGraph 官方文档）
   - 搜索 "如何实现人在回路"
   - 验证检索结果相关性

3. **工作流 RAG 增强**
   - 创建报告生成工作流
   - 启用 RAG，指定参考文档
   - 对比启用/未启用 RAG 的输出质量

**验收标准**
- [ ] 文档上传成功率 > 95%
- [ ] 语义检索平均相似度 > 0.75
- [ ] RAG 增强后输出质量主观提升明显

---

## 🤖 Phase 2 剩余任务：Copilot 集成

### 目标

集成 CopilotKit，实现自然语言驱动工作流编辑（添加节点、连线、重命名等）。

### 技术选型

**前端**: `@copilotkit/react-core` + `@copilotkit/react-ui`
**后端**: CopilotKit 需要 LangChain/LangGraph 桥接

### 架构设计

```
用户语音/文本 → Copilot Chat
                    ↓
         解析意图 (LLM)
                    ↓
    调用 useCopilotAction 注册的函数
                    ↓
         更新 React Flow 状态
                    ↓
              画布更新
```

### 详细任务清单

#### 1️⃣ 前端 CopilotKit 集成 (第1周)

**安装依赖**
```bash
cd frontend
npm install @copilotkit/react-core @copilotkit/react-ui
```

**配置 Copilot 提供商**

```tsx
// frontend/src/app/layout.tsx
import { CopilotKit } from "@copilotkit/react-core";

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <CopilotKit
          runtimeUrl="/api/copilot"  // 后端 Copilot 端点
        >
          {children}
        </CopilotKit>
      </body>
    </html>
  );
}
```

**暴露画布状态**

```tsx
// frontend/src/app/workflows/[id]/page.tsx
import { useCopilotReadable } from "@copilotkit/react-core";

export default function WorkflowEditor() {
  const { nodes, edges } = useWorkflowStore();
  
  // 暴露给 Copilot
  useCopilotReadable({
    description: "当前工作流画布状态",
    value: {
      nodeCount: nodes.length,
      edgeCount: edges.length,
      nodes: nodes.map(n => ({
        id: n.id,
        type: n.data.type,
        label: n.data.label,
        position: n.position
      })),
      edges: edges.map(e => ({
        source: e.source,
        target: e.target
      }))
    }
  });
  
  return <ReactFlow ... />;
}
```

**注册 Copilot Actions**

```tsx
// frontend/src/hooks/useCopilotActions.ts
import { useCopilotAction } from "@copilotkit/react-core";
import { useWorkflowStore } from "@/stores/workflow-store";

export function useCopilotWorkflowActions() {
  const { addNode, addEdge, updateNode, deleteNode } = useWorkflowStore();
  
  // 添加节点
  useCopilotAction({
    name: "addNode",
    description: "在工作流中添加新节点",
    parameters: [
      {
        name: "type",
        type: "string",
        description: "节点类型: llm, tool, router, map",
        required: true
      },
      {
        name: "label",
        type: "string",
        description: "节点显示名称",
        required: true
      },
      {
        name: "position",
        type: "object",
        description: "节点位置 {x, y}",
        required: false
      }
    ],
    handler: async ({ type, label, position }) => {
      const newNode = {
        id: `node-${Date.now()}`,
        type: "agentNode",
        data: {
          label,
          type,
          status: "idle"
        },
        position: position || { x: 100, y: 100 }
      };
      
      addNode(newNode);
      return `已添加 ${type} 节点: ${label}`;
    }
  });
  
  // 连接节点
  useCopilotAction({
    name: "connectNodes",
    description: "连接两个节点",
    parameters: [
      {
        name: "sourceLabel",
        type: "string",
        description: "起始节点名称",
        required: true
      },
      {
        name: "targetLabel",
        type: "string",
        description: "目标节点名称",
        required: true
      }
    ],
    handler: async ({ sourceLabel, targetLabel }) => {
      const sourceNode = nodes.find(n => n.data.label === sourceLabel);
      const targetNode = nodes.find(n => n.data.label === targetLabel);
      
      if (!sourceNode || !targetNode) {
        return "未找到指定节点";
      }
      
      addEdge({
        id: `edge-${Date.now()}`,
        source: sourceNode.id,
        target: targetNode.id
      });
      
      return `已连接 ${sourceLabel} → ${targetLabel}`;
    }
  });
  
  // 重命名节点
  useCopilotAction({
    name: "renameNode",
    description: "重命名节点",
    parameters: [
      {
        name: "oldLabel",
        type: "string",
        required: true
      },
      {
        name: "newLabel",
        type: "string",
        required: true
      }
    ],
    handler: async ({ oldLabel, newLabel }) => {
      const node = nodes.find(n => n.data.label === oldLabel);
      if (!node) return "未找到节点";
      
      updateNode(node.id, { label: newLabel });
      return `已重命名: ${oldLabel} → ${newLabel}`;
    }
  });
  
  // 自动布局
  useCopilotAction({
    name: "autoLayout",
    description: "自动整理画布布局",
    handler: async () => {
      // 调用 dagre 或其他布局算法
      const layoutedNodes = computeLayout(nodes, edges);
      layoutedNodes.forEach(n => updateNode(n.id, { position: n.position }));
      return "布局已优化";
    }
  });
}
```

**Copilot Chat UI**

```tsx
// frontend/src/components/CopilotPanel.tsx
import { CopilotSidebar } from "@copilotkit/react-ui";

export function CopilotPanel() {
  return (
    <CopilotSidebar
      labels={{
        title: "Workflow Copilot",
        initial: "我可以帮你编辑工作流，试试：\n- 添加一个研究节点\n- 连接节点A到节点B\n- 优化画布布局"
      }}
    />
  );
}
```

**任务列表**
- [ ] 安装 CopilotKit 依赖
- [ ] 配置 CopilotKit Provider
- [ ] 实现 `useCopilotReadable`（暴露画布状态）
- [ ] 实现 5 个核心 Actions（添加/连接/重命名/删除/布局）
- [ ] 集成 Copilot Chat UI
- [ ] 测试自然语言指令

#### 2️⃣ 后端 Copilot Runtime (第1-2周)

**Copilot 端点**

```python
# backend/app/api/v1/copilot.py
from fastapi import APIRouter, Request
from app.services.copilot_service import CopilotService

router = APIRouter(prefix="/copilot", tags=["copilot"])

@router.post("/")
async def copilot_runtime(request: Request):
    """
    CopilotKit runtime endpoint
    处理 Copilot 请求并返回响应
    """
    body = await request.json()
    
    service = CopilotService()
    response = await service.handle_request(body)
    
    return response
```

**Copilot 服务**

```python
# backend/app/services/copilot_service.py
from typing import Dict, Any
from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentExecutor

class CopilotService:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4-turbo-preview")
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理 CopilotKit 请求
        """
        message_type = request.get("type")
        
        if message_type == "chat":
            return await self._handle_chat(request)
        elif message_type == "action":
            return await self._handle_action(request)
        else:
            return {"error": "Unknown request type"}
    
    async def _handle_chat(self, request: Dict[str, Any]):
        """处理聊天消息"""
        messages = request.get("messages", [])
        context = request.get("context", {})
        
        # 构建 prompt（包含画布上下文）
        system_prompt = f"""
        你是一个工作流编辑助手。当前画布状态:
        - 节点数: {context.get('nodeCount', 0)}
        - 边数: {context.get('edgeCount', 0)}
        
        用户可以请求你:
        1. 添加节点
        2. 连接节点
        3. 重命名节点
        4. 优化布局
        
        请根据用户意图调用相应的 action。
        """
        
        # 调用 LLM
        response = await self.llm.ainvoke([
            {"role": "system", "content": system_prompt},
            *messages
        ])
        
        return {
            "message": response.content,
            "actions": self._extract_actions(response.content)
        }
    
    def _extract_actions(self, text: str) -> list:
        """从 LLM 响应中提取需要执行的 actions"""
        # 简单实现：寻找特定关键词
        actions = []
        
        if "添加" in text and "节点" in text:
            actions.append({
                "name": "addNode",
                "arguments": {...}  # 从文本中提取参数
            })
        
        return actions
```

**任务列表**
- [ ] 创建 `/api/copilot` 端点
- [ ] 实现 `CopilotService.handle_request`
- [ ] 实现聊天消息处理
- [ ] 实现 action 提取逻辑
- [ ] 测试前后端 Copilot 通信

#### 3️⃣ Copilot 增强功能 (第2周)

**一句话生成工作流**

```tsx
// 示例对话：
用户: "创建一个 AI 趋势报告生成器"

Copilot:
1. 添加研究节点 (搜索最新 AI 新闻)
2. 添加大纲节点 (生成报告大纲)
3. 添加撰写节点 (撰写报告正文)
4. 连接: 研究 → 大纲 → 撰写
5. 自动布局

// 实现：
useCopilotAction({
  name: "createWorkflowFromDescription",
  description: "根据描述生成完整工作流",
  parameters: [
    {
      name: "description",
      type: "string",
      required: true
    }
  ],
  handler: async ({ description }) => {
    // 调用后端 LLM 分析描述
    const response = await fetch("/api/v1/copilot/generate-workflow", {
      method: "POST",
      body: JSON.stringify({ description })
    });
    
    const { nodes, edges } = await response.json();
    
    // 批量添加到画布
    nodes.forEach(addNode);
    edges.forEach(addEdge);
    
    return `已创建工作流: ${nodes.length} 个节点`;
  }
});
```

**任务列表**
- [ ] 实现一句话生成工作流功能
- [ ] 添加工作流描述解析逻辑
- [ ] 实现节点类型推断（根据描述）
- [ ] 测试复杂工作流生成

#### 4️⃣ Copilot 集成测试 (第2-3周)

**测试场景**

1. **基础指令**
   - "添加一个 LLM 节点叫研究员"
   - "连接研究员到写作者"
   - "重命名研究员为数据分析师"

2. **复杂操作**
   - "创建一个包含3个并行任务的工作流"
   - "优化当前画布布局"
   - "删除所有未连接的节点"

3. **一句话生成**
   - "创建竞品分析工作流"
   - "创建代码审查工作流"

**验收标准**
- [ ] 基础指令准确率 > 90%
- [ ] 复杂操作成功率 > 80%
- [ ] 一句话生成的工作流可用性 > 70%

---

## 📅 时间规划

### 第 1-2 周：RAG 后端基础

- 数据库设计与实现
- 文档处理与向量化
- RAG 检索服务
- API 端点开发

### 第 2-3 周：RAG 前端与集成

- 知识库管理 UI
- 节点 RAG 配置
- 工作流集成测试

### 第 3-4 周：Copilot 前端集成

- CopilotKit 配置
- Actions 实现
- Chat UI 集成

### 第 4-5 周：Copilot 后端与增强

- Copilot Runtime
- 一句话生成工作流
- 集成测试

### 第 5-6 周：联调与优化

- 端到端测试
- 性能优化
- 文档完善

---

## ✅ 验收标准

### RAG 模块

- [ ] 支持 5 种文档类型上传
- [ ] 向量检索准确率 > 80%
- [ ] 工作流 RAG 增强效果明显

### Copilot 模块

- [ ] 自然语言指令准确率 > 85%
- [ ] 支持 10+ 常用操作
- [ ] 一句话生成工作流成功率 > 70%

### 整体

- [ ] 所有单元测试通过
- [ ] API 响应时间 < 500ms (P95)
- [ ] 文档完整且可执行

---

## 🚀 启动命令

### 开发环境

```bash
# 后端
cd backend
source ../.venv/bin/activate
python -m app.main

# 前端
cd frontend
npm run dev
```

### 安装新依赖

```bash
# 后端 RAG
pip install pgvector unstructured pypdf sentence-transformers

# 前端 Copilot
npm install @copilotkit/react-core @copilotkit/react-ui
```

---

## 📚 参考资料

- [pgvector 文档](https://github.com/pgvector/pgvector)
- [CopilotKit 文档](https://docs.copilotkit.ai/)
- [LangChain RAG 教程](https://python.langchain.com/docs/use_cases/question_answering/)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)

---

**下一步**: 开始实施 RAG 知识库集成 (第1周任务)
