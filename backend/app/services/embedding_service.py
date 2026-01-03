"""Embedding Service - 向量化服务（新架构）

使用 LLMClient 统一接口，支持多供应商和数据库配置
"""
import logging
import asyncio
from typing import List, Optional
from langchain_community.embeddings import OpenAIEmbeddings
from app.models.llm_model import LLMModel
from app.models.llm_provider import LLMProvider
# Note: Anthropic doesn't have a dedicated embeddings model yet
# from langchain_anthropic import AnthropicEmbeddings
from app.services.llm_client import llm_client
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingServiceException(Exception):
    """Embedding 服务异常基类"""
    pass


class EmbeddingService:
    """向量化服务 - 使用新 LLMClient 架构
    
    支持多供应商（OpenAI, Anthropic 等）
    从数据库读取配置（API 密钥、base_url）
    """
    
    def __init__(
        self,
        provider: str = "openai",
        model: str = "text-embedding-3-large",
        model_id: Optional[str] = None,
        dimensions: int = 3072
    ):
        """初始化 Embedding 服务（新架构）
        
        Args:
            provider: 供应商名称 (openai | anthropic | ...)
            model: 模型名称 (text-embedding-3-large | text-embedding-3-small | ...)
            model_id: 模型 UUID（优先级更高，从数据库读取）
            dimensions: 向量维度
        
        注意：
        - text-embedding-3-large: 3072 维（推荐）
        - text-embedding-3-small: 1536 维
        """
        self.provider = provider
        self.model = model
        self.model_id = model_id
        self.dimensions = dimensions
        self.max_retries = 3
        self.retry_delay = 1  # 秒
        self._verified = False
        self._embedding_client = None
        
        logger.info(
            f"EmbeddingService initialized: provider={provider}, model={model}, "
            f"model_id={model_id}, dimensions={dimensions}"
        )
    
    async def _get_embedding_client(self):
        """获取或创建嵌入客户端
        
        根据供应商创建对应的 LangChain 嵌入客户端
        """
        if self._embedding_client is not None:
            return self._embedding_client
        
        try:
            # 获取 API key 和 base_url
            api_key = None
            base_url = None
            
            # 如果指定了 model_id，从数据库获取配置
            if self.model_id:
                from app.core.database import AsyncSessionLocal
                async with AsyncSessionLocal() as session:
                    from sqlalchemy import select
                    
                    # 获取模型
                    model_result = await session.execute(
                        select(LLMModel).where(LLMModel.id == self.model_id)
                    )
                    model_obj = model_result.scalars().first()
                    
                    if model_obj and model_obj.provider_id:
                        # 获取提供商
                        provider_result = await session.execute(
                            select(LLMProvider).where(LLMProvider.id == model_obj.provider_id)
                        )
                        provider_obj = provider_result.scalars().first()
                        
                        if provider_obj:
                            try:
                                api_key = provider_obj.get_api_key()
                            except Exception as decrypt_err:
                                logger.warning(f"Decrypt provider api_key failed, fallback to env: {decrypt_err}")
                                api_key = settings.OPENAI_API_KEY or None
                            base_url = provider_obj.base_url
                            self.provider = provider_obj.name.lower()
                            logger.info(f"Loaded embedding config from model_id: {self.model_id}")
            else:
                # 从数据库获取第一个活跃的提供商和对应的 embedding 模型
                from app.core.database import AsyncSessionLocal
                async with AsyncSessionLocal() as session:
                    from sqlalchemy import select
                    
                    # 获取提供商
                    provider_result = await session.execute(
                        select(LLMProvider).where(LLMProvider.is_active == True).limit(1)
                    )
                    provider_obj = provider_result.scalars().first()
                    
                    if provider_obj:
                        try:
                            api_key = provider_obj.get_api_key()
                        except Exception as decrypt_err:
                            logger.warning(f"Decrypt provider api_key failed, fallback to env: {decrypt_err}")
                            api_key = settings.OPENAI_API_KEY or None
                        base_url = provider_obj.base_url
                        self.provider = provider_obj.name.lower()
                        logger.info(f"Loaded embedding provider from database: {self.provider}")
            
            # 创建 OpenAI 嵌入客户端
            
            # 为了简化，我们直接从配置创建 LangChain 嵌入对象
            if self.provider.lower() == "openai":
                # 使用 API key 和 base_url 创建 OpenAI embeddings
                openai_kwargs = {
                    "model": self.model,
                }
                
                if self.dimensions:
                    openai_kwargs["dimensions"] = self.dimensions
                
                # 如果有 API key，使用它
                if api_key:
                    openai_kwargs["api_key"] = api_key
                
                # 如果有 base_url，使用它
                if base_url:
                    openai_kwargs["base_url"] = base_url
                
                self._embedding_client = OpenAIEmbeddings(**openai_kwargs)
                logger.info(f"Created OpenAI embedding client for model: {self.model}")
            elif self.provider.lower() == "anthropic":
                # Note: Anthropic doesn't currently support embeddings
                # Fallback to OpenAI for now
                logger.warning(f"Anthropic embeddings not yet supported, falling back to OpenAI")
                self._embedding_client = OpenAIEmbeddings(
                    model="text-embedding-3-large",
                    dimensions=3072,
                    api_key=api_key if api_key else None,
                    base_url=base_url if base_url else None
                )
            else:
                logger.warning(f"Unknown provider: {self.provider}, using OpenAI")
                self._embedding_client = OpenAIEmbeddings(
                    model=self.model,
                    dimensions=self.dimensions if self.dimensions else 3072,
                    api_key=api_key if api_key else None,
                    base_url=base_url if base_url else None
                )
            
            return self._embedding_client
            
        except Exception as e:
            logger.error(f"Failed to get embedding client: {e}", exc_info=True)
            raise EmbeddingServiceException(f"无法获取嵌入客户端: {e}")
    
    async def verify_connection(self) -> bool:
        """验证嵌入服务连接
        
        Returns:
            连接是否正常
            
        Raises:
            EmbeddingServiceException: 验证失败
        """
        try:
            client = await self._get_embedding_client()
            # 测试向量化
            result = await asyncio.to_thread(client.embed_query, "test")
            
            if result and len(result) > 0:
                self._verified = True
                logger.info(f"Embedding service connection verified: {self.provider}/{self.model}")
                return True
            else:
                raise EmbeddingServiceException("嵌入结果为空")
                
        except Exception as e:
            logger.error(f"Embedding service verification failed: {e}", exc_info=True)
            raise EmbeddingServiceException(f"验证失败: {e}")
    
    async def embed_text(
        self,
        text: str,
        retry_on_failure: bool = True
    ) -> List[float]:
        """单个文本向量化
        
        Args:
            text: 要向量化的文本
            retry_on_failure: 失败时是否重试
            
        Returns:
            向量
            
        Raises:
            EmbeddingServiceException: 向量化失败
        """
        if not text or not isinstance(text, str):
            raise EmbeddingServiceException("文本输入无效")
        
        # 截断过长的文本
        text = text[:8000]
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Embedding text (attempt {attempt + 1}/{self.max_retries})")
                client = await self._get_embedding_client()
                
                # 在线程池中运行（LangChain 是同步的）
                embedding = await asyncio.to_thread(client.embed_query, text)
                
                logger.debug(f"Successfully embedded text of length {len(text)}")
                return embedding
                
            except Exception as e:
                if attempt < self.max_retries - 1 and retry_on_failure:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Embedding failed, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.warning(f"Embedding failed, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Embedding failed after {self.max_retries} attempts: {e}", exc_info=True)
                    raise EmbeddingServiceException(f"向量化失败: {e}")
        
        raise EmbeddingServiceException("向量化失败，所有重试均已尝试")
    
    async def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 100,
        retry_on_failure: bool = True
    ) -> List[List[float]]:
        """批量文本向量化
        
        Args:
            texts: 要向量化的文本列表
            batch_size: 批处理大小
            retry_on_failure: 失败时是否重试
            
        Returns:
            向量列表
            
        Raises:
            EmbeddingServiceException: 批量处理失败
        """
        if not texts or not isinstance(texts, list):
            raise EmbeddingServiceException("文本列表输入无效")
        
        logger.info(f"Embedding {len(texts)} texts in batches of {batch_size}")
        all_embeddings = []
        
        # 预处理：清理和截断文本
        cleaned_texts = []
        for text in texts:
            if isinstance(text, str):
                cleaned_texts.append(text[:8000])
            else:
                logger.warning(f"Skipping non-string text: {type(text)}")
                cleaned_texts.append("")
        
        # 分批处理
        for batch_num, i in enumerate(range(0, len(cleaned_texts), batch_size)):
            batch = cleaned_texts[i:i + batch_size]
            
            for attempt in range(self.max_retries):
                try:
                    logger.debug(f"Processing batch {batch_num + 1} (attempt {attempt + 1}/{self.max_retries})")
                    client = await self._get_embedding_client()
                    
                    # 在线程池中运行批量嵌入
                    batch_embeddings = await asyncio.to_thread(client.embed_documents, batch)
                    all_embeddings.extend(batch_embeddings)
                    
                    logger.debug(f"Batch {batch_num + 1} completed with {len(batch_embeddings)} embeddings")
                    break
                    
                except Exception as e:
                    if attempt < self.max_retries - 1 and retry_on_failure:
                        wait_time = self.retry_delay * (2 ** attempt)
                        logger.warning(f"Batch {batch_num + 1} failed, retrying in {wait_time}s: {e}")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error(f"Batch {batch_num + 1} failed after retries: {e}", exc_info=True)
                        raise EmbeddingServiceException(f"批处理失败: {e}")
        
        if len(all_embeddings) != len(cleaned_texts):
            logger.warning(
                f"Embedding count mismatch: got {len(all_embeddings)}, "
                f"expected {len(cleaned_texts)}"
            )
        
        logger.info(f"Successfully embedded {len(all_embeddings)} texts")
        return all_embeddings
    
    async def embed_documents(
        self,
        documents: List[dict],
        text_field: str = "content"
    ) -> List[dict]:
        """
        向量化文档列表
        
        Args:
            documents: 文档字典列表
            text_field: 包含文本内容的字段名
            
        Returns:
            包含向量的文档列表
        """
        texts = [doc.get(text_field, "") for doc in documents]
        embeddings = await self.embed_batch(texts)
        
        for doc, embedding in zip(documents, embeddings):
            doc["embedding"] = embedding
        
        return documents
    
    def get_embedding_dimension(self) -> int:
        """获取向量维度"""
        return self.dimensions
    
    def get_model_name(self) -> str:
        """获取使用的模型名称"""
        return self.model
    
    def get_provider(self) -> str:
        """获取供应商名称"""
        return self.provider