"""Knowledge Base Models - RAG System"""
from sqlalchemy import Column, String, Integer, Text, TIMESTAMP, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import uuid

from app.core.database import Base


class KBDocument(Base):
    """知识库文档模型"""
    __tablename__ = "kb_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    workspace_id = Column(UUID(as_uuid=True), nullable=True)
    
    # 来源信息
    source_type = Column(String(50), nullable=False)  # file, url, text
    source_url = Column(Text, nullable=True)
    filename = Column(String(500), nullable=True)
    file_size = Column(Integer, nullable=True)
    
    # 内容
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=True)
    
    # 向量表示（文档级聚合）
    embedding = Column(Vector(1536), nullable=True)
    
    # 元数据（使用 doc_metadata 避免保留字冲突）
    doc_metadata = Column(JSONB, default=dict, name="metadata")
    chunk_count = Column(Integer, default=1)
    
    # 处理状态
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    
    # 时间戳
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    processed_at = Column(TIMESTAMP, nullable=True)
    
    # 关系
    user = relationship("User", back_populates="kb_documents")
    chunks = relationship("KBChunk", back_populates="document", cascade="all, delete-orphan")


class KBChunk(Base):
    """知识库分片模型 - 细粒度检索单位"""
    __tablename__ = "kb_chunks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("kb_documents.id", ondelete="CASCADE"), nullable=False)
    
    # 分片信息
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=True)
    
    # 向量表示（分片级）
    embedding = Column(Vector(1536), nullable=True)
    
    # 元数据（使用 chunk_metadata 避免保留字冲突）
    chunk_metadata = Column(JSONB, default=dict, name="metadata")
    
    # 时间戳
    created_at = Column(TIMESTAMP, default=func.now())
    
    # 关系
    document = relationship("KBDocument", back_populates="chunks")
