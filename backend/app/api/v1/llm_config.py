"""LLM Configuration management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User, UserRole
from app.models.llm_config import LLMConfig
from app.schemas.llm_config import (
    LLMConfigCreate,
    LLMConfigUpdate,
    LLMConfigResponse,
    LLMConfigDetailResponse,
    LLMConfigListResponse,
)
from app.services.llm_client import llm_client

router = APIRouter()

@router.get("/llm-configs", response_model=list[LLMConfigListResponse])
async def list_active_configs(db: AsyncSession = Depends(get_db)):
    """
    Get list of active LLM configurations for client selection.
    No auth required - public endpoint for UI model picker.
    """
    stmt = select(LLMConfig).where(LLMConfig.is_active == True).order_by(LLMConfig.priority)
    result = await db.execute(stmt)
    configs = result.scalars().all()
    return [
        LLMConfigListResponse(
            id=str(config.id),
            provider=config.provider,
            model_name=config.model_name,
            display_name=config.display_name,
            priority=config.priority,
        )
        for config in configs
    ]

@router.get("/llm-configs/admin", response_model=list[LLMConfigDetailResponse])
async def list_all_configs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all LLM configurations (admin only).
    Includes decrypted API keys - admin access required.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    stmt = select(LLMConfig).order_by(LLMConfig.priority)
    result = await db.execute(stmt)
    configs = result.scalars().all()
    
    return [
        LLMConfigDetailResponse(
            id=str(config.id),
            provider=config.provider,
            model_name=config.model_name,
            display_name=config.display_name,
            base_url=config.base_url,
            is_active=config.is_active,
            priority=config.priority,
            description=config.description,
            api_key=config.get_api_key(),
            created_at=config.created_at,
            updated_at=config.updated_at,
        )
        for config in configs
    ]

@router.post("/llm-configs", response_model=LLMConfigResponse)
async def create_config(
    config_data: LLMConfigCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create new LLM configuration (admin only).
    API key is encrypted before storage.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Check if config already exists
    stmt = select(LLMConfig).where(
        (LLMConfig.provider == config_data.provider) &
        (LLMConfig.model_name == config_data.model_name)
    )
    existing = await db.execute(stmt)
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Config for {config_data.provider} {config_data.model_name} already exists"
        )
    
    # Create new config
    config = LLMConfig(
        provider=config_data.provider,
        model_name=config_data.model_name,
        display_name=config_data.display_name,
        base_url=config_data.base_url,
        is_active=config_data.is_active,
        priority=config_data.priority,
        description=config_data.description,
    )
    config.set_api_key(config_data.api_key)
    
    db.add(config)
    await db.commit()
    await db.refresh(config)
    
    # Update client cache
    await llm_client.ensure_initialized()
    
    return LLMConfigResponse.model_validate(config)

@router.put("/llm-configs/{config_id}", response_model=LLMConfigResponse)
async def update_config(
    config_id: str,
    config_data: LLMConfigUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update LLM configuration (admin only).
    If API key is provided, it will be re-encrypted.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get config
    try:
        from uuid import UUID
        config_uuid = UUID(config_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid config ID"
        )
    
    stmt = select(LLMConfig).where(LLMConfig.id == config_uuid)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Config not found"
        )
    
    # Update fields
    if config_data.model_name is not None:
        config.model_name = config_data.model_name
    if config_data.display_name is not None:
        config.display_name = config_data.display_name
    if config_data.base_url is not None:
        config.base_url = config_data.base_url
    if config_data.is_active is not None:
        config.is_active = config_data.is_active
    if config_data.priority is not None:
        config.priority = config_data.priority
    if config_data.description is not None:
        config.description = config_data.description
    if config_data.api_key is not None:
        config.set_api_key(config_data.api_key)
    
    await db.commit()
    await db.refresh(config)
    
    # Update client cache
    await llm_client.ensure_initialized()
    
    return LLMConfigResponse.model_validate(config)

@router.delete("/llm-configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_config(
    config_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete LLM configuration (admin only).
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get config
    try:
        from uuid import UUID
        config_uuid = UUID(config_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid config ID"
        )
    
    stmt = select(LLMConfig).where(LLMConfig.id == config_uuid)
    result = await db.execute(stmt)
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Config not found"
        )
    
    await db.delete(config)
    await db.commit()
    
    # Update client cache
    await llm_client.ensure_initialized()
