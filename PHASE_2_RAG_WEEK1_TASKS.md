# Phase 2 RAG 模块 - 第一周任务清单

**目标**: 实现 RAG 知识库基础设施，支持文档上传、向量化、检索

**预计完成时间**: 5-7 个工作日

---

## 📋 Day 1-2: 数据库与模型设计

### ✅ 任务清单

- [ ] **安装 pgvector 扩展**
  ```bash
  # 连接到 PostgreSQL
  psql -U postgres -d tenmuses
  
  # 安装扩展
  CREATE EXTENSION IF NOT EXISTS vector;
  
  # 验证安装
  SELECT * FROM pg_extension WHERE extname = 'vector';
  ```

- [ ] **创建数据库表**
  
  创建文件: `backend/alembic/versions/003_add_knowledge_base_tables.py`
  
  ```python
  """Add knowledge base tables
  
  Revision ID: 003
  Create Date: 2026-01-01
  """
  from alembic import op
  import sqlalchemy as sa
  from sqlalchemy.dialects import postgresql
  
  def upgrade():
      # kb_documents 表
      op.create_table(
          'kb_documents',
          sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
          sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
          sa.Column('workspace_id', postgresql.UUID(as_uuid=True)),
          sa.Column('source_type', sa.String(50), nullable=False),
          sa.Column('source_url', sa.Text),
          sa.Column('filename', sa.String(500)),
          sa.Column('file_size', sa.Integer),
          sa.Column('content', sa.Text, nullable=False),
          sa.Column('content_hash', sa.String(64)),
          sa.Column('metadata', postgresql.JSONB, default={}),
          sa.Column('chunk_count', sa.Integer, default=1),
          sa.Column('status', sa.String(50), default='pending'),
          sa.Column('created_at', sa.TIMESTAMP, default=sa.func.now()),
          sa.Column('updated_at', sa.TIMESTAMP, default=sa.func.now()),
          sa.Column('processed_at', sa.TIMESTAMP),
          sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
      )
      
      # 添加向量列
      op.execute('ALTER TABLE kb_documents ADD COLUMN embedding vector(1536)')
      
      # kb_chunks 表
      op.create_table(
          'kb_chunks',
          sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
          sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
          sa.Column('chunk_index', sa.Integer, nullable=False),
          sa.Column('content', sa.Text, nullable=False),
          sa.Column('token_count', sa.Integer),
          sa.Column('metadata', postgresql.JSONB, default={}),
          sa.Column('created_at', sa.TIMESTAMP, default=sa.func.now()),
          sa.ForeignKeyConstraint(['document_id'], ['kb_documents.id'], ondelete='CASCADE')
      )
      
      op.execute('ALTER TABLE kb_chunks ADD COLUMN embedding vector(1536)')
      
      # 创建索引
      op.create_index('idx_kb_documents_user', 'kb_documents', ['user_id', 'created_at'])
      op.create_index('idx_kb_documents_status', 'kb_documents', ['status'])
      op.create_index('idx_kb_chunks_document', 'kb_chunks', ['document_id', 'chunk_index'])
      
      # 创建向量索引 (HNSW)
      op.execute('CREATE INDEX ON kb_documents USING hnsw (embedding vector_cosine_ops)')
      op.execute('CREATE INDEX ON kb_chunks USING hnsw (embedding vector_cosine_ops)')
  
  def downgrade():
      op.drop_table('kb_chunks')
      op.drop_table('kb_documents')
  ```

- [ ] **创建 SQLAlchemy 模型**
  
  创建文件: `backend/app/models/knowledge.py`
  
  ```python
  """Knowledge Base Models"""
  from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, ForeignKey, func
  from sqlalchemy.dialects.postgresql import UUID, JSONB
  from sqlalchemy.orm import relationship
  from pgvector.sqlalchemy import Vector
  import uuid
  
  from app.core.database import Base
  
  class KBDocument(Base):
      __tablename__ = "kb_documents"
      
      id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
      workspace_id = Column(UUID(as_uuid=True), nullable=True)
      
      # 来源
      source_type = Column(String(50), nullable=False)  # file, url, text
      source_url = Column(Text, nullable=True)
      filename = Column(String(500), nullable=True)
      file_size = Column(Integer, nullable=True)
      
      # 内容
      content = Column(Text, nullable=False)
      content_hash = Column(String(64), nullable=True)
      
      # 向量
      embedding = Column(Vector(1536), nullable=True)
      
      # 元数据
      metadata = Column(JSONB, default={})
      chunk_count = Column(Integer, default=1)
      
      # 状态
      status = Column(String(50), default="pending")  # pending, processing, completed, failed
      
      # 时间
      created_at = Column(TIMESTAMP, default=func.now())
      updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
      processed_at = Column(TIMESTAMP, nullable=True)
      
      # 关系
      user = relationship("User", back_populates="kb_documents")
      chunks = relationship("KBChunk", back_populates="document", cascade="all, delete-orphan")
  
  class KBChunk(Base):
      __tablename__ = "kb_chunks"
      
      id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
      document_id = Column(UUID(as_uuid=True), ForeignKey("kb_documents.id", ondelete="CASCADE"), nullable=False)
      
      # 分片
      chunk_index = Column(Integer, nullable=False)
      content = Column(Text, nullable=False)
      token_count = Column(Integer, nullable=True)
      
      # 向量
      embedding = Column(Vector(1536), nullable=True)
      
      # 元数据
      metadata = Column(JSONB, default={})
      
      # 时间
      created_at = Column(TIMESTAMP, default=func.now())
      
      # 关系
      document = relationship("KBDocument", back_populates="chunks")
  ```

- [ ] **创建 Pydantic Schemas**
  
  创建文件: `backend/app/schemas/knowledge.py`
  
  ```python
  """Knowledge Base Schemas"""
  from pydantic import BaseModel, Field
  from typing import Optional, List, Dict, Any
  from datetime import datetime
  from uuid import UUID
  
  # 文档创建
  class KBDocumentCreate(BaseModel):
      source_type: str = Field(..., description="file, url, text")
      source_url: Optional[str] = None
      filename: Optional[str] = None
      content: str
      metadata: Dict[str, Any] = {}
  
  # 文档更新
  class KBDocumentUpdate(BaseModel):
      filename: Optional[str] = None
      metadata: Optional[Dict[str, Any]] = None
  
  # 文档响应
  class KBDocumentResponse(BaseModel):
      id: UUID
      user_id: UUID
      source_type: str
      source_url: Optional[str]
      filename: Optional[str]
      file_size: Optional[int]
      content_hash: Optional[str]
      metadata: Dict[str, Any]
      chunk_count: int
      status: str
      created_at: datetime
      updated_at: datetime
      processed_at: Optional[datetime]
      
      class Config:
          from_attributes = True
  
  # 分片响应
  class KBChunkResponse(BaseModel):
      id: UUID
      document_id: UUID
      chunk_index: int
      content: str
      token_count: Optional[int]
      metadata: Dict[str, Any]
      created_at: datetime
      
      class Config:
          from_attributes = True
  
  # 搜索请求
  class KBSearchRequest(BaseModel):
      query: str
      top_k: int = Field(5, ge=1, le=50)
      document_ids: Optional[List[UUID]] = None
      min_score: float = Field(0.7, ge=0.0, le=1.0)
      search_chunks: bool = False  # True: 搜索分片, False: 搜索文档
  
  # 搜索结果项
  class KBSearchResultItem(BaseModel):
      document_id: UUID
      chunk_id: Optional[UUID] = None
      content: str
      score: float
      metadata: Dict[str, Any]
  
  # 搜索响应
  class KBSearchResponse(BaseModel):
      results: List[KBSearchResultItem]
      total: int
      query: str
  ```

- [ ] **更新 User 模型**
  
  在 `backend/app/models/user.py` 中添加关系：
  
  ```python
  # 在 User 类中添加
  kb_documents = relationship("KBDocument", back_populates="user")
  ```

---

## 📋 Day 2-3: 文档处理服务

### ✅ 任务清单

- [ ] **安装依赖**
  ```bash
  cd backend
  source ../.venv/bin/activate
  pip install pgvector unstructured pypdf python-magic tiktoken
  ```

- [ ] **创建文档处理器**
  
  创建文件: `backend/app/services/document_processor.py`
  
  ```python
  """Document Processing Service"""
  import hashlib
  import tiktoken
  from typing import List, Tuple
  from pathlib import Path
  
  class DocumentProcessor:
      def __init__(self, max_chunk_tokens: int = 500):
          self.max_chunk_tokens = max_chunk_tokens
          self.encoding = tiktoken.get_encoding("cl100k_base")
      
      def extract_text(self, file_path: str, mime_type: str) -> str:
          """从文件提取文本"""
          if mime_type == "application/pdf":
              return self._extract_pdf(file_path)
          elif mime_type in ["text/plain", "text/markdown"]:
              return self._extract_text(file_path)
          elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
              return self._extract_docx(file_path)
          else:
              raise ValueError(f"Unsupported file type: {mime_type}")
      
      def _extract_pdf(self, file_path: str) -> str:
          """提取 PDF 文本"""
          from pypdf import PdfReader
          
          reader = PdfReader(file_path)
          text_parts = []
          
          for page in reader.pages:
              text = page.extract_text()
              if text:
                  text_parts.append(text)
          
          return "\n\n".join(text_parts)
      
      def _extract_text(self, file_path: str) -> str:
          """读取纯文本文件"""
          with open(file_path, 'r', encoding='utf-8') as f:
              return f.read()
      
      def _extract_docx(self, file_path: str) -> str:
          """提取 DOCX 文本"""
          from docx import Document
          
          doc = Document(file_path)
          return "\n\n".join([para.text for para in doc.paragraphs if para.text])
      
      def chunk_text(self, text: str) -> List[Tuple[str, int]]:
          """
          将文本分片
          返回: [(chunk_text, token_count), ...]
          """
          # 按段落分割
          paragraphs = text.split("\n\n")
          
          chunks = []
          current_chunk = []
          current_tokens = 0
          
          for para in paragraphs:
              para = para.strip()
              if not para:
                  continue
              
              para_tokens = len(self.encoding.encode(para))
              
              # 如果单个段落超过限制，强制分割
              if para_tokens > self.max_chunk_tokens:
                  if current_chunk:
                      chunk_text = "\n\n".join(current_chunk)
                      chunks.append((chunk_text, current_tokens))
                      current_chunk = []
                      current_tokens = 0
                  
                  # 分割大段落
                  sentences = para.split(". ")
                  for sent in sentences:
                      sent_tokens = len(self.encoding.encode(sent))
                      if current_tokens + sent_tokens > self.max_chunk_tokens:
                          if current_chunk:
                              chunk_text = ". ".join(current_chunk) + "."
                              chunks.append((chunk_text, current_tokens))
                          current_chunk = [sent]
                          current_tokens = sent_tokens
                      else:
                          current_chunk.append(sent)
                          current_tokens += sent_tokens
              
              # 正常累积
              elif current_tokens + para_tokens > self.max_chunk_tokens:
                  chunk_text = "\n\n".join(current_chunk)
                  chunks.append((chunk_text, current_tokens))
                  current_chunk = [para]
                  current_tokens = para_tokens
              else:
                  current_chunk.append(para)
                  current_tokens += para_tokens
          
          # 最后一个 chunk
          if current_chunk:
              chunk_text = "\n\n".join(current_chunk)
              chunks.append((chunk_text, current_tokens))
          
          return chunks
      
      def compute_hash(self, content: str) -> str:
          """计算内容哈希（用于去重）"""
          return hashlib.sha256(content.encode()).hexdigest()
  ```

- [ ] **创建单元测试**
  
  创建文件: `backend/tests/test_document_processor.py`
  
  ```python
  import pytest
  from app.services.document_processor import DocumentProcessor
  
  def test_chunk_text():
      processor = DocumentProcessor(max_chunk_tokens=100)
      
      text = "这是第一段。\n\n这是第二段。\n\n这是第三段。"
      chunks = processor.chunk_text(text)
      
      assert len(chunks) > 0
      for chunk_text, token_count in chunks:
          assert token_count <= 100
          assert len(chunk_text) > 0
  
  def test_compute_hash():
      processor = DocumentProcessor()
      
      hash1 = processor.compute_hash("test content")
      hash2 = processor.compute_hash("test content")
      hash3 = processor.compute_hash("different content")
      
      assert hash1 == hash2
      assert hash1 != hash3
  ```

---

## 📋 Day 3-4: 向量化服务

### ✅ 任务清单

- [ ] **创建嵌入服务**
  
  创建文件: `backend/app/services/embedding_service.py`
  
  ```python
  """Embedding Service"""
  from typing import List
  from openai import AsyncOpenAI
  from app.core.config import settings
  
  class EmbeddingService:
      def __init__(self):
          self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
          self.model = "text-embedding-3-small"
          self.dimensions = 1536
      
      async def embed_text(self, text: str) -> List[float]:
          """
          单个文本向量化
          """
          response = await self.client.embeddings.create(
              model=self.model,
              input=text,
              dimensions=self.dimensions
          )
          
          return response.data[0].embedding
      
      async def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
          """
          批量文本向量化
          """
          all_embeddings = []
          
          # 分批处理
          for i in range(0, len(texts), batch_size):
              batch = texts[i:i + batch_size]
              
              response = await self.client.embeddings.create(
                  model=self.model,
                  input=batch,
                  dimensions=self.dimensions
              )
              
              batch_embeddings = [item.embedding for item in response.data]
              all_embeddings.extend(batch_embeddings)
          
          return all_embeddings
  ```

- [ ] **创建 RAG 服务**
  
  创建文件: `backend/app/services/rag_service.py`
  
  ```python
  """RAG Service"""
  from typing import List, Optional, Dict, Any
  from sqlalchemy.ext.asyncio import AsyncSession
  from sqlalchemy import select, func
  from uuid import UUID
  
  from app.models.knowledge import KBDocument, KBChunk
  from app.services.embedding_service import EmbeddingService
  from app.schemas.knowledge import KBSearchResultItem
  
  class RAGService:
      def __init__(self, db: AsyncSession):
          self.db = db
          self.embedding_service = EmbeddingService()
      
      async def search_documents(
          self,
          query: str,
          user_id: UUID,
          top_k: int = 5,
          document_ids: Optional[List[UUID]] = None,
          min_score: float = 0.7
      ) -> List[KBSearchResultItem]:
          """
          搜索文档（文档级别）
          """
          # 1. 查询向量化
          query_embedding = await self.embedding_service.embed_text(query)
          
          # 2. 构建查询
          stmt = select(
              KBDocument.id,
              KBDocument.content,
              KBDocument.metadata,
              KBDocument.embedding.cosine_distance(query_embedding).label("distance")
          ).where(
              KBDocument.user_id == user_id,
              KBDocument.status == "completed"
          )
          
          # 可选：筛选特定文档
          if document_ids:
              stmt = stmt.where(KBDocument.id.in_(document_ids))
          
          # 3. 相似度排序
          stmt = stmt.order_by("distance").limit(top_k)
          
          # 4. 执行查询
          result = await self.db.execute(stmt)
          rows = result.all()
          
          # 5. 格式化结果
          results = []
          for row in rows:
              score = 1 - row.distance  # 余弦距离转相似度
              
              if score >= min_score:
                  results.append(KBSearchResultItem(
                      document_id=row.id,
                      chunk_id=None,
                      content=row.content[:500],  # 截取前500字符
                      score=score,
                      metadata=row.metadata
                  ))
          
          return results
      
      async def search_chunks(
          self,
          query: str,
          user_id: UUID,
          top_k: int = 10,
          document_ids: Optional[List[UUID]] = None,
          min_score: float = 0.7
      ) -> List[KBSearchResultItem]:
          """
          搜索分片（分片级别，更精确）
          """
          query_embedding = await self.embedding_service.embed_text(query)
          
          stmt = select(
              KBChunk.id,
              KBChunk.document_id,
              KBChunk.content,
              KBChunk.metadata,
              KBDocument.metadata.label("doc_metadata"),
              KBChunk.embedding.cosine_distance(query_embedding).label("distance")
          ).join(
              KBDocument, KBChunk.document_id == KBDocument.id
          ).where(
              KBDocument.user_id == user_id,
              KBDocument.status == "completed"
          )
          
          if document_ids:
              stmt = stmt.where(KBDocument.id.in_(document_ids))
          
          stmt = stmt.order_by("distance").limit(top_k)
          
          result = await self.db.execute(stmt)
          rows = result.all()
          
          results = []
          for row in rows:
              score = 1 - row.distance
              
              if score >= min_score:
                  results.append(KBSearchResultItem(
                      document_id=row.document_id,
                      chunk_id=row.id,
                      content=row.content,
                      score=score,
                      metadata={**row.doc_metadata, **row.metadata}
                  ))
          
          return results
      
      def format_context(self, results: List[KBSearchResultItem]) -> str:
          """
          格式化检索结果为 LLM 上下文
          """
          context_parts = []
          
          for i, result in enumerate(results, 1):
              filename = result.metadata.get("filename", "未知来源")
              context_parts.append(
                  f"[{i}] {result.content}\n来源: {filename} (相关度: {result.score:.2f})"
              )
          
          return "\n\n".join(context_parts)
  ```

---

## 📋 Day 4-5: API 端点实现

### ✅ 任务清单

详见下一个文件...

---

## ✅ 本周验收标准

- [ ] 数据库表创建成功，向量索引生效
- [ ] 文档处理器能够提取 PDF/TXT/DOCX 内容
- [ ] 文本分片逻辑正确，token 数不超限
- [ ] 向量化服务能正常调用 OpenAI API
- [ ] RAG 检索返回相关结果（手动测试）

---

**下一步**: Day 4-5 实现 API 端点并完成前端集成
