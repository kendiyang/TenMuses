"""
重构后的 LLM Client - 只使用数据库配置

主要特性:
1. 支持通过 model_id 获取配置（推荐）
2. 支持 provider + model_name 方式（向后兼容）
3. 优化缓存机制：带TTL的配置缓存
4. 所有配置从数据库加载，不依赖环境变量
"""

from typing import Optional, AsyncIterator, Dict, Any, Tuple
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import BaseMessage
from tenacity import retry, stop_after_attempt, wait_exponential
import time
import logging
import httpx
import urllib3
import ssl
import os

from app.core.database import AsyncSessionLocal
from app.models.llm_provider import LLMProvider
from app.models.llm_model import LLMModel
from sqlalchemy import select

# 禁用SSL警告（用于开发/测试环境）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 禁用SSL验证（用于代理服务器）
# 设置环境变量禁用SSL验证，这样OpenAI SDK内部创建的httpx也会继承
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['CURL_CA_BUNDLE'] = ''
ssl._create_default_https_context = ssl._create_unverified_context

logger = logging.getLogger(__name__)


class LLMClient:
    """
    统一的 LLM 客户端，支持多供应商
    
    架构:
        - 供应商表 (llm_providers): 存储 API key 和 base_url
        - 模型表 (llm_models): 存储模型配置，关联到供应商
    
    使用方式:
        # 方式1: 通过model_id (推荐)
        await client.invoke(messages, model_id="uuid-xxx")
        
        # 方式2: 通过provider+model_name (向后兼容)
        await client.invoke(messages, provider="openai", model="gpt-4o")
    """
    
    def __init__(self):
        # 缓存: model_id -> (LLMModel, LLMProvider)
        self.model_cache: Dict[str, Tuple[LLMModel, LLMProvider]] = {}
        
        # 缓存: (provider_name, model_name) -> (LLMModel, LLMProvider)
        self.legacy_cache: Dict[Tuple[str, str], Tuple[LLMModel, LLMProvider]] = {}
        
        # 缓存配置
        self.cache_ttl = 300  # 5分钟
        self.last_cache_update = 0
        self._initialized = False
    
    async def _load_configs_from_db(self, force_refresh: bool = False) -> None:
        """
        从数据库加载配置
        
        Args:
            force_refresh: 强制刷新缓存
        """
        current_time = time.time()
        
        # 如果缓存未过期且不强制刷新，跳过
        if not force_refresh and (current_time - self.last_cache_update) < self.cache_ttl:
            return
        
        try:
            async with AsyncSessionLocal() as session:
                # 加载所有激活的模型和供应商（使用JOIN）
                stmt = (
                    select(LLMModel, LLMProvider)
                    .join(LLMProvider, LLMModel.provider_id == LLMProvider.id)
                    .where(
                        LLMModel.is_active == True,
                        LLMProvider.is_active == True
                    )
                    .order_by(LLMModel.priority.asc())
                )
                
                result = await session.execute(stmt)
                rows = result.all()
                
                # 清空并重建缓存
                self.model_cache.clear()
                self.legacy_cache.clear()
                
                for model, provider in rows:
                    # 按 model_id 缓存
                    model_id = str(model.id)
                    self.model_cache[model_id] = (model, provider)
                    
                    # 按 (provider_name, model_name) 缓存（向后兼容）
                    cache_key = (provider.name, model.model_name)
                    self.legacy_cache[cache_key] = (model, provider)
                
                self.last_cache_update = current_time
                self._initialized = True
                logger.info(
                    f"Loaded {len(self.model_cache)} LLM models from database "
                    f"({len(set(p.name for _, p in self.model_cache.values()))} providers)"
                )
                
        except Exception as e:
            logger.error(f"Failed to load LLM configs from database: {e}")
            # 继续使用环境变量回退
    
    async def ensure_initialized(self) -> None:
        """确保配置已从数据库加载"""
        if not self._initialized:
            await self._load_configs_from_db()
    
    def _build_client(
        self,
        provider: LLMProvider,
        model: LLMModel,
        **override_params
    ) -> Any:
        """
        构建 LLM 客户端实例
        
        Args:
            provider: 供应商配置
            model: 模型配置
            **override_params: 覆盖参数（如temperature）
        
        Returns:
            LangChain chat model 实例
        """
        # 基础参数
        params = {
            "api_key": provider.get_api_key(),
            "model": model.model_name,
            "temperature": override_params.get("temperature", model.default_temperature),
            "streaming": True,
        }
        
        # base_url
        if provider.base_url:
            params["base_url"] = provider.base_url
        
        # 注意: SSL验证配置在llm_client.py顶部全局设置 (_create_default_https_context = _create_unverified_context)
        # provider.verify_ssl字段用于未来扩展（如支持代理证书白名单）
        
        # max_tokens
        if "max_tokens" in override_params:
            params["max_tokens"] = override_params["max_tokens"]
        elif model.default_max_tokens:
            params["max_tokens"] = model.default_max_tokens
        
        # top_p
        if "top_p" in override_params:
            params["top_p"] = override_params["top_p"]
        elif model.default_top_p:
            params["top_p"] = model.default_top_p
        
        # 合并其他参数
        for key, value in override_params.items():
            if key not in params:
                params[key] = value
        
        # 根据供应商创建客户端
        provider_name = provider.name.lower()
        
        if provider_name == "openai":
            return ChatOpenAI(**params)
        elif provider_name == "anthropic":
            return ChatAnthropic(**params)
        else:
            raise ValueError(f"Unsupported provider: {provider.name}")
    
    async def get_client_by_model_id(
        self,
        model_id: str,
        **kwargs
    ) -> Any:
        """
        通过模型ID获取客户端（推荐使用）
        
        Args:
            model_id: 模型UUID
            **kwargs: 覆盖参数
        
        Returns:
            LangChain chat model 实例
            
        Raises:
            ValueError: 当模型未找到或不活跃时
        """
        await self.ensure_initialized()
        
        # 从缓存查找
        if model_id in self.model_cache:
            model, provider = self.model_cache[model_id]
            return self._build_client(provider, model, **kwargs)
        
        # 如果缓存中没有，尝试从数据库实时加载
        try:
            async with AsyncSessionLocal() as session:
                stmt = (
                    select(LLMModel, LLMProvider)
                    .join(LLMProvider, LLMModel.provider_id == LLMProvider.id)
                    .where(
                        LLMModel.id == model_id,
                        LLMModel.is_active == True,
                        LLMProvider.is_active == True
                    )
                )
                result = await session.execute(stmt)
                row = result.one_or_none()
                
                if row:
                    model, provider = row
                    # 更新缓存
                    self.model_cache[model_id] = (model, provider)
                    return self._build_client(provider, model, **kwargs)
        
        except Exception as e:
            logger.error(f"Failed to load model {model_id} from database: {e}")
        
        # 未找到模型
        error_msg = (
            f"❌ LLM 配置错误: 未找到 ID='{model_id}' 的模型或模型未激活。\n"
            f"请检查:\n"
            f"  1. 模型是否存在: 访问 /api/v1/llm-provider-model/models\n"
            f"  2. 模型是否激活: is_active = true\n"
            f"  3. 关联的供应商是否激活\n"
            f"  4. 供应商是否有有效的 API Key"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    async def get_client(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        通过供应商和模型名称获取客户端（向后兼容）
        
        Args:
            provider: 供应商名称
            model: 模型名称（必须提供）
            **kwargs: 覆盖参数
        
        Returns:
            LangChain chat model 实例
            
        Raises:
            ValueError: 当配置未找到时
        """
        await self.ensure_initialized()
        
        # 如果指定了模型，尝试从缓存查找
        if model:
            cache_key = (provider.lower(), model)
            if cache_key in self.legacy_cache:
                model_obj, provider_obj = self.legacy_cache[cache_key]
                return self._build_client(provider_obj, model_obj, **kwargs)
            
            # 尝试从数据库实时加载
            try:
                async with AsyncSessionLocal() as session:
                    stmt = (
                        select(LLMModel, LLMProvider)
                        .join(LLMProvider, LLMModel.provider_id == LLMProvider.id)
                        .where(
                            LLMProvider.name == provider,
                            LLMModel.model_name == model,
                            LLMModel.is_active == True,
                            LLMProvider.is_active == True
                        )
                    )
                    result = await session.execute(stmt)
                    row = result.one_or_none()
                    
                    if row:
                        model_obj, provider_obj = row
                        # 更新缓存
                        self.legacy_cache[cache_key] = (model_obj, provider_obj)
                        return self._build_client(provider_obj, model_obj, **kwargs)
            except Exception as e:
                logger.error(f"Failed to load model {model} from database: {e}")
        
        # 没有找到配置
        error_msg = (
            f"❌ LLM 配置错误: 未找到 provider='{provider}', model='{model}' 的配置。\n"
            f"请在数据库中配置 LLM 供应商和模型:\n"
            f"  1. 访问 /api/v1/llm-provider-model/providers 查看供应商\n"
            f"  2. 访问 /api/v1/llm-provider-model/models 查看模型\n"
            f"  3. 确保供应商有有效的 API Key\n"
            f"  4. 确保模型和供应商都是 active 状态"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def invoke(
        self,
        messages: list[BaseMessage],
        model_id: Optional[str] = None,
        provider: str = "openai",
        model: Optional[str] = None,
        **kwargs
    ) -> BaseMessage:
        """
        调用 LLM（带重试）
        
        Args:
            messages: 消息列表
            model_id: 模型ID（优先使用，新架构）
            provider: 供应商名称（回退，旧架构）
            model: 模型名称（回退，旧架构）
            **kwargs: 其他参数
        
        Returns:
            LLM 响应消息
        """
        if model_id:
            client = await self.get_client_by_model_id(model_id, **kwargs)
        else:
            client = await self.get_client(provider, model, **kwargs)
        
        return await client.ainvoke(messages)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def stream(
        self,
        messages: list[BaseMessage],
        model_id: Optional[str] = None,
        provider: str = "openai",
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        流式调用 LLM（带重试）
        
        Args:
            messages: 消息列表
            model_id: 模型ID（优先使用，新架构）
            provider: 供应商名称（回退，旧架构）
            model: 模型名称（回退，旧架构）
            **kwargs: 其他参数
        
        Yields:
            文本片段
        """
        if model_id:
            client = await self.get_client_by_model_id(model_id, **kwargs)
        else:
            client = await self.get_client(provider, model, **kwargs)
        
        async for chunk in client.astream(messages):
            if hasattr(chunk, 'content'):
                yield chunk.content
    
    async def get_available_models(self) -> list[dict]:
        """
        获取所有可用模型列表
        
        Returns:
            模型信息列表
        """
        await self.ensure_initialized()
        
        models_list = []
        for model_id, (model, provider) in self.model_cache.items():
            models_list.append({
                "model_id": model_id,
                "model_name": model.model_name,
                "display_name": model.display_name,
                "provider_name": provider.name,
                "provider_display_name": provider.display_name,
                "model_family": model.model_family,
                "supports_streaming": model.supports_streaming,
                "supports_function_calling": model.supports_function_calling,
                "context_window": model.context_window,
                "default_temperature": model.default_temperature,
            })
        
        return models_list
    
    async def refresh_cache(self) -> None:
        """强制刷新缓存"""
        await self._load_configs_from_db(force_refresh=True)


# 全局单例实例
llm_client = LLMClient()
