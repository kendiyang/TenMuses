"""Knowledge Base API Endpoints - RAG System"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List, Optional
import tempfile
import os
import logging

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.knowledge import KBDocument, KBChunk
from app.schemas.knowledge import (
    KBDocumentCreate,
    KBDocumentResponse,
    KBSearchRequest,
    KBSearchResponse,
)
from app.services.document_processor import DocumentProcessor
from app.services.embedding_service import EmbeddingService
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kb", tags=["Knowledge Base"])

# 文件类型映射
MIME_TYPE_MAP = {
    "pdf": "application/pdf",
    "txt": "text/plain",
    "md": "text/markdown",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@router.post("/documents", response_model=KBDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    上传文档到知识库
    
    支持格式: PDF, TXT, Markdown, DOCX
    """
    try:
        # 1. 验证文件类型
        file_ext = os.path.splitext(file.filename)[1].lower().lstrip(".")
        mime_type = MIME_TYPE_MAP.get(file_ext)
        
        if not mime_type:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file_ext}。支持: pdf, txt, md, docx"
            )
        
        # 2. 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # 3. 提取文本
            processor = DocumentProcessor()
            text_content = processor.extract_text(tmp_path, mime_type)
            
            if not text_content.strip():
                raise HTTPException(
                    status_code=400,
                    detail="文件为空或无法提取内容"
                )
            
            # 4. 计算哈希（去重）
            content_hash = processor.compute_hash(text_content)
            
            # 检查是否已存在
            from sqlalchemy import select
            existing = await db.execute(
                select(KBDocument).where(
                    KBDocument.user_id == current_user.id,
                    KBDocument.content_hash == content_hash
                )
            )
            if existing.scalar_one_or_none():
                raise HTTPException(
                    status_code=409,
                    detail="该文档已存在（内容重复）"
                )
            
            # 5. 分片文本
            chunks = processor.chunk_text(text_content)
            
            # 6. 创建文档记录
            document = KBDocument(
                user_id=current_user.id,
                source_type="file",
                filename=file.filename,
                file_size=len(content),
                content=text_content,
                content_hash=content_hash,
                doc_metadata={"original_filename": file.filename},
                chunk_count=len(chunks),
                status="pending"
            )
            
            db.add(document)
            await db.flush()  # 获取 document.id
            
            # 7. 异步处理向量化（这里我们先标记为完成，实际应该放在后台任务中）
            try:
                # 从数据库获取 embedding 模型配置
                from sqlalchemy import select
                from app.models.llm_model import LLMModel
                
                embedding_model = await db.execute(
                    select(LLMModel).where(
                        LLMModel.model_name == "text-embedding-3-large"
                    ).limit(1)
                )
                embedding_model_obj = embedding_model.scalars().first()
                
                # 使用模型 ID 初始化 embedding service
                embedding_service = EmbeddingService(
                    provider="openai",
                    model="text-embedding-3-large",
                    model_id=str(embedding_model_obj.id) if embedding_model_obj else None,
                    dimensions=3072
                )
                
                # 向量化文档摘要
                summary = text_content[:1000]
                doc_embedding = await embedding_service.embed_text(summary)
                document.embedding = doc_embedding
                
                # 创建分片记录并向量化
                chunk_texts = [chunk[0] for chunk in chunks]
                chunk_embeddings = await embedding_service.embed_batch(chunk_texts)
                
                for i, (chunk_text, token_count) in enumerate(chunks):
                    chunk = KBChunk(
                        document_id=document.id,
                        chunk_index=i,
                        content=chunk_text,
                        token_count=token_count,
                        embedding=chunk_embeddings[i],
                        chunk_metadata={"chunk_index": i}
                    )
                    db.add(chunk)
            except Exception as e:
                logger.error(f"向量化处理失败: {str(e)}")
                # 如果向量化失败，继续保存文档但标记为需要重新处理
                document.status = "embedding_failed"
                logger.warning(f"文档 {document.id} 已保存但向量化失败，需要后续处理")
            
            # 8. 标记为已处理
            document.status = "completed"
            document.processed_at = __import__("datetime").datetime.utcnow()
            
            await db.commit()
            await db.refresh(document)
            
            return KBDocumentResponse.model_validate(document)
        
        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
    
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"文档处理失败: {str(e)}"
        )


@router.get("/documents", response_model=List[KBDocumentResponse])
async def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    列出用户的知识库文档
    """
    from sqlalchemy import select
    
    stmt = select(KBDocument).where(KBDocument.user_id == current_user.id)
    
    if status:
        stmt = stmt.where(KBDocument.status == status)
    
    stmt = stmt.order_by(KBDocument.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(stmt)
    documents = result.scalars().all()
    
    return [KBDocumentResponse.model_validate(doc) for doc in documents]


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    删除文档及其所有分片
    """
    from sqlalchemy import select
    
    document = await db.execute(
        select(KBDocument).where(
            KBDocument.id == document_id,
            KBDocument.user_id == current_user.id
        )
    )
    doc = document.scalar_one_or_none()
    
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    await db.delete(doc)
    await db.commit()
    
    return {"message": "文档已删除"}


@router.post("/search", response_model=KBSearchResponse)
async def search_knowledge_base(
    request: KBSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    搜索知识库
    
    支持文档级和分片级搜索
    """
    rag_service = RAGService(db)
    
    if request.search_chunks:
        results = await rag_service.search_chunks(
            query=request.query,
            user_id=current_user.id,
            top_k=request.top_k,
            document_ids=request.document_ids,
            min_score=request.min_score
        )
    else:
        results = await rag_service.search_documents(
            query=request.query,
            user_id=current_user.id,
            top_k=request.top_k,
            document_ids=request.document_ids,
            min_score=request.min_score
        )
    
    return KBSearchResponse(
        results=results,
        total=len(results),
        query=request.query
    )


@router.get("/search/context")
async def get_search_context(
    query: str,
    top_k: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    搜索并返回格式化的 LLM 上下文
    
    直接用于注入 LangGraph 节点的 Prompt
    """
    rag_service = RAGService(db)
    
    results = await rag_service.search_chunks(
        query=query,
        user_id=current_user.id,
        top_k=top_k
    )
    
    context = rag_service.format_context(results)
    
    return {
        "context": context,
        "result_count": len(results),
        "query": query
    }
