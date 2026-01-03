# TenMuses PHASE 2.4+ 详细实施计划与代码缺口清单

> **生成时间**: 2026-01-01  
> **覆盖范围**: RAG 完整实现、Copilot 集成、模板市场规划  
> **目标受众**: 开发团队、项目经理

---

## 📊 当前代码缺口完整清单

### 后端缺口详细分析

#### 1. 向量化与嵌入服务 (HIGH PRIORITY)

**文件**: `backend/app/services/embedding_service.py`

```python
# ❌ 缺失实现
class EmbeddingService:
    """向量化服务 - 将文本转换为向量表示"""
    
    # 缺失:
    async def embed_text(self, text: str) -> List[float]:
        """单个文本向量化"""
        # 应该调用 OpenAI API 或本地模型
        pass
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """批量向量化（有 token 限制）"""
        # 应该分批处理，避免超过 API 限制
        pass
    
    async def embed_with_retry(self, text: str, max_retries=3) -> List[float]:
        """带重试的向量化"""
        pass
```

**完成标准**:
- [ ] 实现 `embed_text()` - 调用 OpenAI embedding 或 Ollama
- [ ] 实现 `embed_batch()` - 支持批量，处理 token limits
- [ ] 添加重试机制 (tenacity)
- [ ] 添加缓存支持 (Redis, optional)
- [ ] 添加错误处理和降级策略
- [ ] 单元测试 (2-3 个 test cases)

**估计工期**: 4-6 小时

---

#### 2. 文档处理服务 (HIGH PRIORITY)

**文件**: `backend/app/services/document_processor.py`

```python
# ❌ 缺失实现
class DocumentProcessor:
    """文档处理服务 - 提取、分片、哈希"""
    
    # 缺失:
    async def extract_text(
        self, 
        file_path: str, 
        mime_type: str
    ) -> str:
        """从各种格式文件中提取文本"""
        # 支持: PDF, DOCX, TXT, HTML, Markdown
        pass
    
    async def chunk_text(
        self,
        text: str,
        chunk_size: int = 500,
        overlap: int = 100
    ) -> List[str]:
        """分片文本 - 按 token 数或字符数"""
        pass
    
    def compute_hash(self, content: str) -> str:
        """计算内容 SHA256 哈希 - 用于去重"""
        pass
    
    async def process_file(
        self,
        file_path: str,
        mime_type: str
    ) -> Tuple[List[str], int]:
        """完整处理流程: 提取 → 分片"""
        pass
```

**完成标准**:
- [ ] 实现 `extract_text()` - 支持 5+ 种格式
- [ ] 实现 `chunk_text()` - 智能分片（考虑段落边界）
- [ ] 实现 `compute_hash()` - SHA256
- [ ] 实现 `process_file()` - 完整流程
- [ ] 添加错误处理（文件损坏、格式不支持等）
- [ ] 单元测试 (test files included)
- [ ] 依赖安装: `pypdf`, `python-docx`, `beautifulsoup4`

**估计工期**: 6-8 小时

---

#### 3. RAG 服务完善 (HIGH PRIORITY)

**文件**: `backend/app/services/rag_service.py`

**现状**: 框架级实现已有，缺少：

```python
# ❌ 缺失的关键方法
async def search_documents(
    self,
    query: str,
    user_id: UUID,
    top_k: int = 5,
    document_ids: Optional[List[UUID]] = None,
    min_score: float = 0.7
) -> List[KBSearchResultItem]:
    """
    搜索文档 - 使用余弦相似度
    
    缺失:
    - 向量化查询
    - 调用 pgvector 进行相似度搜索
    - 结果格式化
    - 相似度阈值过滤
    """
    pass

async def search_chunks(
    self,
    query: str,
    user_id: UUID,
    top_k: int = 10,
    min_score: float = 0.5
) -> List[ChunkSearchResultItem]:
    """搜索分片 - 比文档级更细粒度"""
    pass

async def format_context(
    self,
    chunks: List[ChunkSearchResultItem],
    max_chars: int = 2000
) -> str:
    """格式化为 LLM 上下文"""
    pass
```

**完成标准**:
- [ ] 实现向量数据库查询逻辑
- [ ] 集成 pgvector cosine distance
- [ ] 实现结果格式化
- [ ] 添加元数据处理（来源、日期等）
- [ ] 单元测试

**估计工期**: 4-5 小时

---

#### 4. 知识库 API 端点 (HIGH PRIORITY)

**文件**: `backend/app/api/v1/knowledge.py`

**现状**: 文件存在，缺少完整实现

```python
# ❌ 缺失端点实现

@router.post("/documents")
async def upload_document(
    file: UploadFile,
    source_type: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> DocumentUploadResponse:
    """
    缺失:
    1. 文件验证 (大小、类型、病毒扫描)
    2. 文本提取 (DocumentProcessor.extract_text)
    3. 分片处理 (DocumentProcessor.chunk_text)
    4. 向量化 (EmbeddingService.embed_batch)
    5. 数据库存储 (批量插入 kb_documents + kb_chunks)
    6. 后台任务管理 (异步处理大文件)
    7. 错误回滚
    """
    pass

@router.post("/search")
async def search_knowledge(
    query: SearchQuery,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SearchResponse:
    """
    缺失:
    1. 请求验证
    2. 调用 RAGService.search_chunks()
    3. 结果格式化
    4. 分页支持
    """
    pass

@router.get("/documents/{doc_id}/chunks")
async def get_document_chunks(doc_id: UUID):
    """获取文档的所有分片"""
    pass

@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: UUID):
    """删除文档及其分片"""
    pass
```

**完成标准**:
- [ ] POST `/documents` - 上传、处理、存储
- [ ] POST `/search` - 语义搜索
- [ ] GET `/documents` - 分页列表
- [ ] GET `/documents/{id}` - 详情
- [ ] GET `/documents/{id}/chunks` - 分片列表
- [ ] DELETE `/documents/{id}` - 删除
- [ ] 错误处理 (4xx, 5xx)
- [ ] 集成测试

**估计工期**: 8-10 小时

---

#### 5. 数据库模型 (HIGH PRIORITY)

**文件**: `backend/app/models/knowledge.py`

**现状**: 完全缺失

```python
# ❌ 需要完整实现
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, VECTOR, JSONB

class KBDocument(Base):
    __tablename__ = "kb_documents"
    
    # 缺失所有字段
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey("users.id"))
    # ... 其他字段

class KBChunk(Base):
    __tablename__ = "kb_chunks"
    
    # 缺失所有字段
    id = Column(UUID, primary_key=True)
    document_id = Column(UUID, ForeignKey("kb_documents.id"))
    # ... 其他字段
```

**完成标准**:
- [ ] 完整的 KBDocument 模型
- [ ] 完整的 KBChunk 模型
- [ ] 关系定义
- [ ] 索引定义
- [ ] 时间戳自动管理

**估计工期**: 2-3 小时

---

#### 6. Pydantic Schemas (HIGH PRIORITY)

**文件**: `backend/app/schemas/knowledge.py`

```python
# ❌ 需要完整实现
class KBDocumentCreate(BaseModel):
    filename: str
    source_type: str  # 'file', 'url', 'text'
    # ... 其他字段

class KBDocumentResponse(BaseModel):
    id: UUID
    filename: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    chunk_count: int
    # ... 其他字段
    
    class Config:
        from_attributes = True

class KBSearchResultItem(BaseModel):
    document_id: UUID
    chunk_id: UUID
    content: str
    score: float
    # ... 其他字段

# ... 更多 schemas
```

**完成标准**:
- [ ] KBDocumentCreate, Response, Update
- [ ] KBChunkResponse
- [ ] KBSearchResultItem, ChunkSearchResultItem
- [ ] SearchQuery, SearchResponse
- [ ] 所有 Pydantic validators

**估计工期**: 3-4 小时

---

#### 7. 数据库迁移脚本 (HIGH PRIORITY)

**文件**: `backend/alembic/versions/*.py` 或手动 SQL

```sql
-- ❌ 需要执行的 SQL 脚本

-- 1. 启用 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. 创建 kb_documents 表
CREATE TABLE kb_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_type VARCHAR(50) NOT NULL,
    filename VARCHAR(500),
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 3. 创建 kb_chunks 表
CREATE TABLE kb_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES kb_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 4. 创建索引
CREATE INDEX idx_kb_documents_user ON kb_documents(user_id);
CREATE INDEX idx_kb_documents_status ON kb_documents(status);
CREATE INDEX idx_kb_chunks_document ON kb_chunks(document_id);
CREATE INDEX idx_kb_documents_embedding ON kb_documents USING hnsw (embedding vector_cosine_ops);
CREATE INDEX idx_kb_chunks_embedding ON kb_chunks USING hnsw (embedding vector_cosine_ops);
```

**完成标准**:
- [ ] pgvector 扩展安装
- [ ] 所有表创建
- [ ] 所有索引创建
- [ ] 迁移脚本可重复运行

**估计工期**: 1-2 小时

---

#### 8. WebSocket RAG 事件推送 (MEDIUM PRIORITY)

**文件**: `backend/app/services/dynamic_graph_factory.py`

**缺口**: 在执行器中推送 `rag_search` 事件

```python
# ❌ 需要修改 DynamicGraphFactory

class DynamicGraphFactory:
    def compile_graph(self, canvas_json, stream_callback=None):
        """
        缺失:
        - 将 stream_callback 传递给执行器
        - 执行器在执行时调用 stream_callback
        """
        pass

class StreamingLLMNodeExecutor(LLMNodeExecutor):
    async def execute(self, state: WorkflowState) -> Dict[str, Any]:
        # ... 现有代码 ...
        
        # ✅ 这部分已经有框架，需要完整实现
        if config.enable_rag:
            rag_context = await self._retrieve_rag_context(...)
            if self.stream_callback:
                await self.stream_callback({
                    "type": "rag_search",
                    "nodeId": self.node.id,
                    "payload": {
                        "query": prompt,
                        "context": rag_context,
                        # ... 更多字段
                    }
                })
```

**完成标准**:
- [ ] DynamicGraphFactory 接受 stream_callback 参数
- [ ] 将 callback 传递给所有执行器
- [ ] 执行器在关键点调用 callback
- [ ] 测试事件推送

**估计工期**: 2-3 小时

---

### 前端缺口详细分析

#### 1. 知识库管理页面 (HIGH PRIORITY)

**文件**: `frontend/src/app/knowledge/page.tsx`

```typescript
// ❌ 完全缺失

export default function KnowledgePage() {
  // 需要实现:
  // 1. 文档列表 (表格)
  // 2. 上传区域 (拖拽 + 文件选择)
  // 3. 搜索和过滤
  // 4. 删除和查看详情
  // 5. 处理状态显示 (processing, completed, failed)
  // 6. 分页
  
  return (
    <div className="space-y-6">
      {/* 上传区域 */}
      {/* 搜索栏 */}
      {/* 文档表格 */}
    </div>
  )
}
```

**完成标准**:
- [ ] 页面框架和布局
- [ ] 文档列表表格
- [ ] 上传区域（拖拽 + 文件选择）
- [ ] 删除功能
- [ ] 详情视图
- [ ] 分页支持
- [ ] 加载和错误状态
- [ ] 响应式设计

**估计工期**: 6-8 小时

---

#### 2. 文档选择器组件 (HIGH PRIORITY)

**文件**: `frontend/src/components/workflow/KnowledgeDocumentSelector.tsx`

```typescript
// ❌ 框架级存在，缺少完整实现

interface KnowledgeDocumentSelectorProps {
  selectedDocumentIds: string[]
  onChange: (documentIds: string[]) => void
}

export default function KnowledgeDocumentSelector({
  selectedDocumentIds,
  onChange
}: KnowledgeDocumentSelectorProps) {
  // 需要实现:
  // 1. 从后端加载文档列表
  // 2. 搜索过滤
  // 3. 复选框多选
  // 4. 已选文档显示
  // 5. 删除已选项
  
  return (
    <div>
      {/* 已选文档 */}
      {/* 搜索框 */}
      {/* 文档列表 */}
    </div>
  )
}
```

**完成标准**:
- [ ] 从 API 加载文档列表
- [ ] 搜索过滤功能
- [ ] 复选框多选
- [ ] 已选项显示和删除
- [ ] 加载状态
- [ ] 错误处理
- [ ] 响应式设计

**估计工期**: 4-5 小时

---

#### 3. 节点配置中的 RAG 配置面板 (MEDIUM PRIORITY)

**文件**: `frontend/src/components/workflow/PropertiesPanel.tsx`

**缺口**: 在现有属性面板中添加 RAG 配置区域

```typescript
// 现有代码中需要添加:
{nodeData.type === 'llm' && (
  <>
    {/* 现有 LLM 配置 */}
    
    {/* ❌ 缺失: RAG 配置区域 */}
    <div className="border-t pt-4 mt-4">
      <label className="flex items-center space-x-2">
        <input
          type="checkbox"
          checked={nodeData.modelConfig?.enableRag || false}
          onChange={...}
        />
        <span>启用知识库 (RAG)</span>
      </label>
      
      {nodeData.modelConfig?.enableRag && (
        <div className="mt-4 space-y-4">
          {/* 文档选择器 */}
          <KnowledgeDocumentSelector ... />
          
          {/* 检索参数 */}
          <div className="space-y-2">
            <label>相似度阈值</label>
            <input type="number" min="0" max="1" step="0.1" />
          </div>
          
          <div className="space-y-2">
            <label>返回结果数</label>
            <input type="number" min="1" max="20" />
          </div>
        </div>
      )}
    </div>
  </>
)}
```

**完成标准**:
- [ ] 添加 RAG 启用复选框
- [ ] 集成 KnowledgeDocumentSelector
- [ ] 添加检索参数输入
- [ ] 保存到节点状态
- [ ] 与 Zustand store 集成

**估计工期**: 3-4 小时

---

#### 4. 执行面板 RAG 结果展示 (MEDIUM PRIORITY)

**文件**: `frontend/src/components/workflow/ExecutionPanel.tsx` 或新文件

```typescript
// ❌ 需要在执行面板中处理 rag_search 事件

// 现有代码中添加:
const handleWebSocketMessage = (event: WSEvent) => {
  switch (event.type) {
    case 'rag_search':
      // ❌ 缺失处理逻辑
      setRagSearchResults(event.payload)
      break
    // ... 其他事件
  }
}

// 在执行面板中展示:
{nodeStatus === 'rag_searching' && ragSearchResults && (
  <div className="bg-blue-50 p-4 rounded border border-blue-200">
    <h3 className="font-semibold text-sm mb-2">检索结果</h3>
    {ragSearchResults.map(result => (
      <div key={result.documentId} className="mb-2 text-sm">
        <div className="font-medium">{result.title}</div>
        <div className="text-gray-600">相关度: {(result.score * 100).toFixed(1)}%</div>
      </div>
    ))}
  </div>
)}
```

**完成标准**:
- [ ] WebSocket 消息处理
- [ ] 状态管理 (rag search results)
- [ ] UI 展示组件
- [ ] 与流式输出整合
- [ ] 样式设计

**估计工期**: 3-4 小时

---

#### 5. 前端知识库类型定义 (LOW PRIORITY)

**文件**: `frontend/src/types/knowledge.ts`

```typescript
// ❌ 完全缺失

export interface KBDocument {
  id: string
  filename: string
  fileSize: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  chunkCount: number
  createdAt: string
  metadata?: Record<string, any>
}

export interface KBChunk {
  id: string
  documentId: string
  chunkIndex: number
  content: string
  score?: number
}

export interface KBSearchResult {
  documentId: string
  chunkId: string
  title: string
  content: string
  score: number
}

export interface SearchQuery {
  query: string
  topK?: number
  minScore?: number
  documentIds?: string[]
}
```

**完成标准**:
- [ ] 所有类型定义完整
- [ ] 与后端 schemas 对应
- [ ] TypeScript strict mode 通过

**估计工期**: 1-2 小时

---

## 🎯 分阶段实施时间表

### Week 1 (Current Week) - RAG 基础 DAY 6-7

**目标**: 完成后端所有基础服务和 API

| 任务 | 工期 | 优先级 | 负责 |
|------|------|--------|------|
| EmbeddingService 实现 | 5h | P0 | Backend |
| DocumentProcessor 实现 | 7h | P0 | Backend |
| 知识库 API 端点 | 9h | P0 | Backend |
| RAG Service 完善 | 4h | P0 | Backend |
| 数据库迁移脚本 | 2h | P0 | DBA |
| **小计** | **27h** | - | - |

**验收标准**:
- [ ] 所有 API 端点可调用
- [ ] 单元测试通过 (>80% 覆盖)
- [ ] Swagger 文档完整
- [ ] 无数据库错误

---

### Week 1 (Current Week) - RAG 前端 DAY 8-9

**目标**: 完成前端 UI 和集成

| 任务 | 工期 | 优先级 | 负责 |
|------|------|--------|------|
| 知识库管理页面 | 7h | P0 | Frontend |
| 文档选择器组件 | 4h | P0 | Frontend |
| 节点配置 RAG 面板 | 3h | P0 | Frontend |
| 执行面板集成 | 3h | P0 | Frontend |
| 类型定义 | 1h | P0 | Frontend |
| **小计** | **18h** | - | - |

**验收标准**:
- [ ] 所有页面正常渲染
- [ ] 可上传文件并处理
- [ ] 可搜索文档
- [ ] WebSocket 事件正常显示
- [ ] 无 console 错误

---

### Week 2 - RAG 集成与测试 DAY 10-14

**目标**: 端到端集成和性能优化

| 任务 | 工期 | 优先级 | 负责 |
|------|------|--------|------|
| 集成测试 | 6h | P1 | QA/Backend |
| 性能优化 (缓存) | 4h | P1 | Backend |
| 端到端流程验证 | 4h | P1 | QA |
| 文档完整更新 | 3h | P1 | Tech Writer |
| **小计** | **17h** | - | - |

**验收标准**:
- [ ] 完整工作流可执行
- [ ] RAG 检索准确性 > 75%
- [ ] API 延迟 < 2s
- [ ] 文档完整且可用

---

### Week 3 - Copilot 集成 DAY 15-21

**目标**: 自然语言驱动画布编辑

| 任务 | 工期 | 优先级 | 负责 |
|------|------|--------|------|
| CopilotKit SDK 集成 | 4h | P1 | Frontend |
| useCopilotReadable 实现 | 3h | P1 | Frontend |
| useCopilotAction 实现 | 6h | P1 | Frontend |
| 后端 Copilot bridge | 4h | P1 | Backend |
| 测试 & 优化 | 5h | P1 | QA |
| **小计** | **22h** | - | - |

---

## 📋 代码实现优先级矩阵

```
紧急性 ▲
        │
        ├─ HIGH: 数据库迁移、EmbeddingService、DocumentProcessor
        │        知识库 API、前端知识库页面
        │
        ├─ MEDIUM: RAG Service 完善、文档选择器、执行面板集成
        │
        └─ LOW: 性能优化、监控、Copilot 集成
        
        └─────────────────────────────────────> 重要性
```

---

## 💻 关键代码片段模板

### 1. EmbeddingService 核心实现

```python
class EmbeddingService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = "text-embedding-3-small"
        self.client = AsyncOpenAI(api_key=self.api_key)
    
    async def embed_text(self, text: str) -> List[float]:
        try:
            response = await self.client.embeddings.create(
                input=text,
                model=self.model,
                dimensions=1536
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            raise
    
    async def embed_batch(self, texts: List[str], batch_size: int = 100):
        """Process texts in batches to respect API limits"""
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            response = await self.client.embeddings.create(
                input=batch,
                model=self.model,
                dimensions=1536
            )
            results.extend([item.embedding for item in response.data])
        return results
```

### 2. DocumentProcessor 核心实现

```python
class DocumentProcessor:
    @staticmethod
    async def extract_text(file_path: str, mime_type: str) -> str:
        """Extract text from various file formats"""
        if mime_type == 'application/pdf':
            return await extract_from_pdf(file_path)
        elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
            return await extract_from_docx(file_path)
        elif mime_type == 'text/plain':
            return open(file_path).read()
        else:
            raise ValueError(f"Unsupported mime type: {mime_type}")
    
    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = 500,
        overlap: int = 100
    ) -> List[str]:
        """Split text into overlapping chunks"""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - overlap
        return chunks
    
    @staticmethod
    def compute_hash(content: str) -> str:
        """Compute SHA256 hash of content"""
        return hashlib.sha256(content.encode()).hexdigest()
```

### 3. 知识库 API 端点核心实现

```python
@router.post("/documents")
async def upload_document(
    file: UploadFile,
    source_type: str = "file",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload and process document"""
    
    # 1. 验证文件
    if file.size > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(status_code=413, detail="File too large")
    
    # 2. 保存文件
    file_path = f"/tmp/{file.filename}"
    with open(file_path, 'wb') as f:
        f.write(await file.read())
    
    # 3. 创建文档记录
    doc = KBDocument(
        user_id=current_user.id,
        filename=file.filename,
        source_type=source_type,
        status="processing"
    )
    db.add(doc)
    await db.commit()
    
    # 4. 后台任务处理（异步）
    asyncio.create_task(process_document_async(doc.id, file_path))
    
    return KBDocumentResponse.model_validate(doc)

async def process_document_async(doc_id: UUID, file_path: str):
    """Background task: extract, chunk, embed, store"""
    try:
        # 提取文本
        text = await DocumentProcessor.extract_text(file_path, "application/pdf")
        
        # 分片
        chunks = DocumentProcessor.chunk_text(text)
        
        # 向量化
        embeddings = await EmbeddingService().embed_batch(chunks)
        
        # 存储
        async with AsyncSessionLocal() as db:
            for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                kb_chunk = KBChunk(
                    document_id=doc_id,
                    chunk_index=i,
                    content=chunk_text,
                    embedding=embedding
                )
                db.add(kb_chunk)
            
            # 更新文档状态
            doc = await db.get(KBDocument, doc_id)
            doc.status = "completed"
            doc.chunk_count = len(chunks)
            
            await db.commit()
    except Exception as e:
        logger.error(f"Document processing failed: {e}")
        async with AsyncSessionLocal() as db:
            doc = await db.get(KBDocument, doc_id)
            doc.status = "failed"
            await db.commit()
```

---

## ✅ 验收清单

### RAG 功能完成清单

```
后端基础设施:
  ☐ EmbeddingService 实现与测试
  ☐ DocumentProcessor 实现与测试
  ☐ RAG Service 完善
  ☐ 知识库 API 6 个端点
  ☐ 数据库迁移脚本
  ☐ SQLAlchemy 模型
  ☐ Pydantic schemas
  
前端 UI:
  ☐ 知识库管理页面
  ☐ 文档选择器组件
  ☐ 节点配置 RAG 面板
  ☐ 执行面板 RAG 结果展示
  
集成与测试:
  ☐ 端到端工作流测试
  ☐ WebSocket 事件推送
  ☐ 错误处理
  ☐ 性能基准测试
  ☐ 文档完整
```

---

**下一步行动**: 
1. 确认负责人和时间表
2. 启动 EmbeddingService 和 DocumentProcessor 实现
3. 准备数据库迁移脚本 review
