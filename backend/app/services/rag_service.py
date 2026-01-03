"""RAG Service - Retrieval and Context Generation with Advanced Vector Search"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from sqlalchemy.orm import joinedload
from uuid import UUID

from app.models.knowledge import KBDocument, KBChunk
from app.services.embedding_service import EmbeddingService, EmbeddingServiceException
from app.schemas.knowledge import KBSearchResultItem

logger = logging.getLogger(__name__)


class RAGService:
    """RAG 服务 - 向量检索和上下文格式化，支持多种检索策略"""
    
    def __init__(self, db: AsyncSession):
        """
        初始化 RAG 服务
        
        Args:
            db: 异步数据库会话
        """
        self.db = db
        self.embedding_service = EmbeddingService()
        logger.info("RAGService initialized")
    
    async def search_documents(
        self,
        query: str,
        user_id: UUID,
        top_k: int = 5,
        document_ids: Optional[List[UUID]] = None,
        min_score: float = 0.7
    ) -> List[KBSearchResultItem]:
        """
        搜索文档（文档级别检索）
        
        Args:
            query: 搜索查询文本
            user_id: 用户 ID
            top_k: 返回结果数量
            document_ids: 可选的文档 ID 筛选列表
            min_score: 最小相似度阈值
            
        Returns:
            搜索结果列表
            
        Raises:
            ValueError: 查询参数无效
            EmbeddingServiceException: 向量化失败
        """
        try:
            if not query or not isinstance(query, str):
                raise ValueError("查询文本无效")
            
            if top_k < 1 or top_k > 100:
                raise ValueError("top_k 必须在 1-100 之间")
            
            logger.info(f"Searching documents for user {user_id} with query: {query[:50]}...")
            
            # 1. 查询向量化
            try:
                query_embedding = await self.embedding_service.embed_text(query)
            except EmbeddingServiceException as e:
                logger.error(f"Failed to embed query: {str(e)}")
                raise
            
            # 2. 构建数据库查询
            stmt = select(
                KBDocument.id,
                KBDocument.title,
                KBDocument.content,
                KBDocument.doc_metadata,
                KBDocument.created_at,
                # pgvector 的余弦距离查询
                KBDocument.embedding.cosine_distance(query_embedding).label("distance")
            ).where(
                and_(
                    KBDocument.user_id == user_id,
                    KBDocument.status == "completed",
                    KBDocument.embedding.isnot(None)
                )
            )
            
            # 可选：筛选特定文档
            if document_ids:
                if not all(isinstance(doc_id, UUID) for doc_id in document_ids):
                    raise ValueError("文档 ID 格式无效")
                stmt = stmt.where(KBDocument.id.in_(document_ids))
            
            # 3. 按相似度排序并限制结果数
            stmt = stmt.order_by("distance").limit(top_k)
            
            # 4. 执行查询
            result = await self.db.execute(stmt)
            rows = result.all()
            
            logger.info(f"Found {len(rows)} documents for query")
            
            # 5. 格式化结果
            results = []
            for row in rows:
                distance = row.distance
                # 余弦距离范围 [0, 2]，0 表示完全相似
                score = max(0, 1 - distance / 2)  # 转换为 [0, 1] 的相似度
                
                if score >= min_score:
                    results.append(KBSearchResultItem(
                        document_id=row.id,
                        chunk_id=None,
                        content=row.content[:500] if row.content else "无内容",
                        score=float(score),
                        metadata={
                            **(row.doc_metadata or {}),
                            "title": row.title,
                            "created_at": row.created_at.isoformat() if row.created_at else None
                        }
                    ))
            
            logger.info(f"Returned {len(results)} results with min_score {min_score}")
            return results
        
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            raise
    
    async def search_chunks(
        self,
        query: str,
        user_id: UUID,
        top_k: int = 10,
        document_ids: Optional[List[UUID]] = None,
        min_score: float = 0.7,
        deduplicate: bool = False
    ) -> List[KBSearchResultItem]:
        """
        搜索分片（分片级别检索，更精确）
        
        Args:
            query: 搜索查询文本
            user_id: 用户 ID
            top_k: 返回结果数量
            document_ids: 可选的文档 ID 筛选列表
            min_score: 最小相似度阈值
            deduplicate: 是否去重相同文档的多个分片
            
        Returns:
            搜索结果列表（包含分片内容）
            
        Raises:
            ValueError: 查询参数无效
            EmbeddingServiceException: 向量化失败
        """
        try:
            if not query or not isinstance(query, str):
                raise ValueError("查询文本无效")
            
            if top_k < 1 or top_k > 100:
                raise ValueError("top_k 必须在 1-100 之间")
            
            logger.info(f"Searching chunks for user {user_id}, top_k={top_k}, deduplicate={deduplicate}")
            
            # 1. 查询向量化
            try:
                query_embedding = await self.embedding_service.embed_text(query)
            except EmbeddingServiceException as e:
                logger.error(f"Failed to embed query: {str(e)}")
                raise
            
            # 2. 构建数据库查询（分片级别）
            stmt = select(
                KBChunk.id,
                KBChunk.document_id,
                KBChunk.content,
                KBChunk.chunk_index,
                KBChunk.chunk_metadata,
                KBChunk.token_count,
                KBDocument.title,
                KBDocument.doc_metadata,
                KBChunk.embedding.cosine_distance(query_embedding).label("distance")
            ).join(
                KBDocument, KBChunk.document_id == KBDocument.id
            ).where(
                and_(
                    KBDocument.user_id == user_id,
                    KBDocument.status == "completed",
                    KBChunk.embedding.isnot(None)
                )
            )
            
            # 可选：筛选特定文档
            if document_ids:
                if not all(isinstance(doc_id, UUID) for doc_id in document_ids):
                    raise ValueError("文档 ID 格式无效")
                stmt = stmt.where(KBDocument.id.in_(document_ids))
            
            # 3. 按相似度排序并限制结果数（取更多结果以便去重）
            fetch_k = top_k * 2 if deduplicate else top_k
            stmt = stmt.order_by("distance").limit(fetch_k)
            
            # 4. 执行查询
            result = await self.db.execute(stmt)
            rows = result.all()
            
            logger.info(f"Found {len(rows)} chunks for query")
            
            # 5. 格式化结果
            results = []
            doc_ids_seen = set()
            
            for row in rows:
                distance = row.distance
                score = max(0, 1 - distance / 2)
                
                if score < min_score:
                    continue
                
                # 去重：每个文档只保留最相关的分片
                if deduplicate and row.document_id in doc_ids_seen:
                    continue
                
                if deduplicate:
                    doc_ids_seen.add(row.document_id)
                
                results.append(KBSearchResultItem(
                    document_id=row.document_id,
                    chunk_id=row.id,
                    content=row.content,
                    score=float(score),
                    metadata={
                        **(row.doc_metadata or {}),
                        **{(row.chunk_metadata or {})},
                        "title": row.title,
                        "chunk_index": row.chunk_index,
                        "token_count": row.token_count
                    }
                ))
                
                if len(results) >= top_k:
                    break
            
            logger.info(f"Returned {len(results)} chunks with min_score {min_score}")
            return results
        
        except Exception as e:
            logger.error(f"Error searching chunks: {str(e)}")
            raise
    
    def format_context(
        self,
        results: List[KBSearchResultItem],
        include_metadata: bool = True,
        separator: str = "\n---\n"
    ) -> str:
        """
        格式化检索结果为 LLM 上下文
        
        Args:
            results: 搜索结果列表
            include_metadata: 是否包含元数据（来源、相关度等）
            separator: 结果之间的分隔符
            
        Returns:
            格式化的上下文字符串，可直接注入 LLM Prompt
        """
        if not results:
            return "没有找到相关的知识库内容。"
        
        context_parts = []
        
        for i, result in enumerate(results, 1):
            title = result.metadata.get("title", "未知标题")
            score_percent = int(result.score * 100)
            
            content = result.content.strip() if result.content else "无内容"
            
            if include_metadata:
                chunk_index = result.metadata.get("chunk_index", "")
                chunk_info = f" (部分 {chunk_index})" if chunk_index is not None else ""
                
                header = f"[来源 {i}] {title}{chunk_info} - 相关度 {score_percent}%"
                context_parts.append(f"{header}\n{content}")
            else:
                context_parts.append(content)
        
        return separator.join(context_parts)
    
    async def get_document_summary(self, document_id: UUID, user_id: UUID) -> Optional[Dict[str, Any]]:
        """获取文档的汇总信息"""
        stmt = select(
            KBDocument.id,
            KBDocument.title,
            KBDocument.content,
            KBDocument.status,
            KBDocument.chunk_count,
            KBDocument.created_at,
            func.count(KBChunk.id).label("chunk_count_actual")
        ).where(
            and_(
                KBDocument.id == document_id,
                KBDocument.user_id == user_id
            )
        ).join(
            KBChunk, KBDocument.id == KBChunk.document_id, isouter=True
        ).group_by(KBDocument.id)
        
        result = await self.db.execute(stmt)
        row = result.one_or_none()
        
        if not row:
            return None
        
        return {
            "id": str(row.id),
            "title": row.title,
            "status": row.status,
            "chunk_count": row.chunk_count_actual,
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "summary": row.content[:200] if row.content else ""
        }
    
    async def delete_document(self, document_id: UUID, user_id: UUID) -> bool:
        """删除文档及其所有分片"""
        # 验证所有权
        stmt = select(KBDocument).where(
            and_(
                KBDocument.id == document_id,
                KBDocument.user_id == user_id
            )
        )
        
        result = await self.db.execute(stmt)
        document = result.scalar_one_or_none()
        
        if not document:
            logger.warning(f"Document {document_id} not found for user {user_id}")
            return False
        
        await self.db.delete(document)
        await self.db.commit()
        
        logger.info(f"Deleted document {document_id} and all its chunks")
        return True
