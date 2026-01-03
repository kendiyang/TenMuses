from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class KBDocumentCreate(BaseModel):
    """创建知识库文档请求"""
    source_type: str = Field(..., description="file, url, or text")
    source_url: Optional[str] = None
    filename: Optional[str] = None
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KBDocumentUpdate(BaseModel):
    """更新知识库文档请求"""
    filename: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class KBDocumentResponse(BaseModel):
    """知识库文档响应"""
    id: UUID
    user_id: UUID
    source_type: str
    source_url: Optional[str]
    filename: Optional[str]
    file_size: Optional[int]
    content_hash: Optional[str]
    metadata: Dict[str, Any] = Field(alias="doc_metadata")
    chunk_count: int
    status: str
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

class KBChunkResponse(BaseModel):
    """知识库分片响应"""
    id: UUID
    document_id: UUID
    chunk_index: int
    content: str
    token_count: Optional[int]
    metadata: Dict[str, Any] = Field(alias="chunk_metadata")
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class KBSearchRequest(BaseModel):
    """知识库搜索请求"""
    query: str = Field(..., description="搜索查询文本")
    top_k: int = Field(5, ge=1, le=50, description="返回结果数量")
    document_ids: Optional[List[UUID]] = None
    min_score: float = Field(0.7, ge=0.0, le=1.0, description="最小相似度阈值")
    search_chunks: bool = False  # True: 搜索分片, False: 搜索文档


class KBSearchResultItem(BaseModel):
    """搜索结果项"""
    document_id: UUID
    chunk_id: Optional[UUID] = None
    content: str
    score: float
    metadata: Dict[str, Any]


class KBSearchResponse(BaseModel):
    """知识库搜索响应"""
    results: List[KBSearchResultItem]
    total: int
    query: str
