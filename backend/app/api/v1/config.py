"""
LLM Configuration management API endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.llm_config import LLMConfig
from app.services.config_service import ConfigService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["configuration"])


class LLMConfigResponse(BaseModel):
    """Response model for LLM configuration."""
    id: str
    provider: str
    model_name: str
    display_name: str
    base_url: str | None
    is_active: bool
    priority: int
    description: str | None
    created_at: str
    updated_at: str


class LLMConfigCreate(BaseModel):
    """Request model to create/update LLM configuration."""
    provider: str = Field(..., description="Provider name: openai, anthropic, etc.")
    model_name: str = Field(..., description="Model name: gpt-4-turbo-preview, etc.")
    api_key: str = Field(..., description="API key (will be encrypted)")
    base_url: str | None = Field(None, description="Optional custom base URL")
    display_name: str | None = Field(None, description="Display name for UI")
    description: str | None = Field(None, description="Description")
    priority: int = Field(100, description="Priority order (lower = higher priority)")


@router.get("/llm/providers", response_model=List[LLMConfigResponse])
async def list_llm_providers(
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all available LLM provider configurations."""
    configs = await ConfigService.list_providers(db, active_only=active_only)
    return [
        LLMConfigResponse(
            id=str(config.id),
            provider=config.provider,
            model_name=config.model_name,
            display_name=config.display_name,
            base_url=config.base_url,
            is_active=config.is_active,
            priority=config.priority,
            description=config.description,
            created_at=config.created_at.isoformat(),
            updated_at=config.updated_at.isoformat(),
        )
        for config in configs
    ]


@router.post("/llm/providers", response_model=LLMConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_or_update_llm_provider(
    data: LLMConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update an LLM provider configuration."""
    try:
        config = await ConfigService.save_provider_config(
            db,
            provider=data.provider,
            model_name=data.model_name,
            api_key=data.api_key,
            base_url=data.base_url,
            display_name=data.display_name,
            description=data.description,
            priority=data.priority,
        )
        
        await db.commit()
        
        return LLMConfigResponse(
            id=str(config.id),
            provider=config.provider,
            model_name=config.model_name,
            display_name=config.display_name,
            base_url=config.base_url,
            is_active=config.is_active,
            priority=config.priority,
            description=config.description,
            created_at=config.created_at.isoformat(),
            updated_at=config.updated_at.isoformat(),
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Error creating LLM config: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating LLM configuration: {str(e)}"
        )


@router.get("/llm/providers/{provider}", response_model=LLMConfigResponse)
async def get_llm_provider(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get configuration for a specific LLM provider."""
    config = await ConfigService.get_provider_config(db, provider, use_env_fallback=False)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration for provider '{provider}' not found"
        )
    
    return LLMConfigResponse(
        id=str(config.id),
        provider=config.provider,
        model_name=config.model_name,
        display_name=config.display_name,
        base_url=config.base_url,
        is_active=config.is_active,
        priority=config.priority,
        description=config.description,
        created_at=config.created_at.isoformat(),
        updated_at=config.updated_at.isoformat(),
    )


@router.patch("/llm/providers/{provider}/toggle", response_model=LLMConfigResponse)
async def toggle_llm_provider(
    provider: str,
    is_active: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Activate or deactivate an LLM provider configuration."""
    config = await ConfigService.toggle_provider(db, provider, is_active=is_active)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration for provider '{provider}' not found"
        )
    
    await db.commit()
    
    return LLMConfigResponse(
        id=str(config.id),
        provider=config.provider,
        model_name=config.model_name,
        display_name=config.display_name,
        base_url=config.base_url,
        is_active=config.is_active,
        priority=config.priority,
        description=config.description,
        created_at=config.created_at.isoformat(),
        updated_at=config.updated_at.isoformat(),
    )


@router.get("/llm/openai")
async def get_openai_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get OpenAI configuration (API key hidden)."""
    config = await ConfigService.get_openai_config(db, use_env_fallback=True)
    
    if not config["api_key"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="OpenAI configuration not found"
        )
    
    return {
        "provider": "openai",
        "has_api_key": bool(config["api_key"]),
        "base_url": config["base_url"] or "https://api.openai.com/v1",
    }


@router.get("/llm/anthropic")
async def get_anthropic_config(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get Anthropic configuration (API key hidden)."""
    config = await ConfigService.get_anthropic_config(db, use_env_fallback=True)
    
    if not config["api_key"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anthropic configuration not found"
        )
    
    return {
        "provider": "anthropic",
        "has_api_key": bool(config["api_key"]),
        "base_url": config["base_url"] or "https://api.anthropic.com",
    }


@router.get("/llm/available-models")
async def get_available_models(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all available LLM models (from new provider-model architecture).
    
    This endpoint returns all active models with their configuration.
    Useful for frontend dropdowns and model selection.
    """
    from app.models.llm_model import LLMModel
    from app.models.llm_provider import LLMProvider
    from sqlalchemy import select
    
    try:
        stmt = (
            select(LLMModel, LLMProvider)
            .join(LLMProvider, LLMModel.provider_id == LLMProvider.id)
            .where(
                LLMModel.is_active == True,
                LLMProvider.is_active == True
            )
            .order_by(LLMProvider.priority.asc(), LLMModel.priority.asc())
        )
        
        result = await db.execute(stmt)
        rows = result.all()
        
        models = []
        for model, provider in rows:
            models.append({
                "id": str(model.id),
                "model_name": model.model_name,
                "display_name": model.display_name,
                "provider_id": str(provider.id),
                "provider_name": provider.name,
                "provider_display_name": provider.display_name,
                "model_family": model.model_family,
                "supports_streaming": model.supports_streaming,
                "supports_function_calling": model.supports_function_calling,
                "supports_vision": model.supports_vision,
                "context_window": model.context_window,
                "default_temperature": model.default_temperature,
                "description": model.description,
            })
        
        return {
            "models": models,
            "count": len(models)
        }
    
    except Exception as e:
        logger.error(f"Error fetching available models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch available models"
        )

