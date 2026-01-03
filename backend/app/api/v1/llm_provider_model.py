"""LLM Provider and Model API endpoints - 新架构"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.llm_provider import LLMProvider
from app.models.llm_model import LLMModel

router = APIRouter(prefix="/llm-config", tags=["LLM Configuration"])


# ============================================================================
# 供应商端点
# ============================================================================

@router.get("/providers")
async def list_providers(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取所有 LLM 供应商列表
    
    Args:
        active_only: 是否只返回激活的供应商
    
    Returns:
        List[Provider]: 供应商列表
    """
    query = select(LLMProvider).order_by(LLMProvider.priority)
    
    if active_only:
        query = query.where(LLMProvider.is_active == True)
    
    result = await db.execute(query)
    providers = result.scalars().all()
    
    return [
        {
            "id": str(provider.id),
            "name": provider.name,
            "display_name": provider.display_name,
            "base_url": provider.base_url,
            "is_active": provider.is_active,
            "priority": provider.priority,
            "description": provider.description,
            "icon_url": provider.icon_url,
            "created_at": provider.created_at.isoformat() if provider.created_at else None,
            "updated_at": provider.updated_at.isoformat() if provider.updated_at else None,
        }
        for provider in providers
    ]


@router.get("/providers/{provider_id}")
async def get_provider(
    provider_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个供应商详情"""
    result = await db.execute(
        select(LLMProvider).where(LLMProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider {provider_id} not found"
        )
    
    return {
        "id": str(provider.id),
        "name": provider.name,
        "display_name": provider.display_name,
        "base_url": provider.base_url,
        "is_active": provider.is_active,
        "priority": provider.priority,
        "description": provider.description,
        "icon_url": provider.icon_url,
        "created_at": provider.created_at.isoformat() if provider.created_at else None,
        "updated_at": provider.updated_at.isoformat() if provider.updated_at else None,
    }


# ============================================================================
# 模型端点
# ============================================================================

@router.get("/models")
async def list_models(
    provider_id: UUID = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取所有模型列表
    
    Args:
        provider_id: 可选，过滤特定供应商的模型
        active_only: 是否只返回激活的模型
    
    Returns:
        List[Model]: 模型列表
    """
    query = select(LLMModel).order_by(LLMModel.priority)
    
    if provider_id:
        query = query.where(LLMModel.provider_id == provider_id)
    
    if active_only:
        query = query.where(LLMModel.is_active == True)
    
    result = await db.execute(query)
    models = result.scalars().all()
    
    return [
        {
            "id": str(model.id),
            "provider_id": str(model.provider_id),
            "model_name": model.model_name,
            "display_name": model.display_name,
            "model_family": model.model_family,
            "version": model.version,
            "default_temperature": model.default_temperature,
            "default_max_tokens": model.default_max_tokens,
            "default_top_p": model.default_top_p,
            "context_window": model.context_window,
            "supports_streaming": model.supports_streaming,
            "supports_function_calling": model.supports_function_calling,
            "supports_vision": model.supports_vision,
            "supports_json_mode": model.supports_json_mode,
            "cost_per_1k_input_tokens": model.cost_per_1k_input_tokens,
            "cost_per_1k_output_tokens": model.cost_per_1k_output_tokens,
            "is_active": model.is_active,
            "priority": model.priority,
            "description": model.description,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None,
        }
        for model in models
    ]


@router.get("/models/{model_id}")
async def get_model(
    model_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取单个模型详情"""
    result = await db.execute(
        select(LLMModel).where(LLMModel.id == model_id)
    )
    model = result.scalar_one_or_none()
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model {model_id} not found"
        )
    
    return {
        "id": str(model.id),
        "provider_id": str(model.provider_id),
        "model_name": model.model_name,
        "display_name": model.display_name,
        "model_family": model.model_family,
        "version": model.version,
        "default_temperature": model.default_temperature,
        "default_max_tokens": model.default_max_tokens,
        "default_top_p": model.default_top_p,
        "context_window": model.context_window,
        "supports_streaming": model.supports_streaming,
        "supports_function_calling": model.supports_function_calling,
        "supports_vision": model.supports_vision,
        "supports_json_mode": model.supports_json_mode,
        "cost_per_1k_input_tokens": model.cost_per_1k_input_tokens,
        "cost_per_1k_output_tokens": model.cost_per_1k_output_tokens,
        "is_active": model.is_active,
        "priority": model.priority,
        "description": model.description,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None,
    }


@router.get("/providers/{provider_id}/models")
async def list_provider_models(
    provider_id: UUID,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取特定供应商的所有模型"""
    # 验证供应商存在
    provider_result = await db.execute(
        select(LLMProvider).where(LLMProvider.id == provider_id)
    )
    provider = provider_result.scalar_one_or_none()
    
    if not provider:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider {provider_id} not found"
        )
    
    # 获取模型
    query = select(LLMModel).where(LLMModel.provider_id == provider_id).order_by(LLMModel.priority)
    
    if active_only:
        query = query.where(LLMModel.is_active == True)
    
    result = await db.execute(query)
    models = result.scalars().all()
    
    return [
        {
            "id": str(model.id),
            "provider_id": str(model.provider_id),
            "model_name": model.model_name,
            "display_name": model.display_name,
            "model_family": model.model_family,
            "is_active": model.is_active,
            "supports_streaming": model.supports_streaming,
            "supports_function_calling": model.supports_function_calling,
            "supports_vision": model.supports_vision,
        }
        for model in models
    ]
