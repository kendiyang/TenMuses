from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from uuid import UUID
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.user import User
from app.models.workflow import Workflow
from app.models.workflow_share import WorkflowShare, WorkflowShareAccess, SharePermission
from app.schemas.workflow_share import (
    WorkflowShareCreate,
    WorkflowShareUpdate,
    WorkflowShareResponse,
    WorkflowShareAccessResponse
)
from app.api.v1.auth import get_current_user

router = APIRouter()


@router.post("/workflows/{workflow_id}/share", response_model=WorkflowShareResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow_share(
    workflow_id: UUID,
    share_data: WorkflowShareCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a shareable link for a workflow"""
    
    # Verify workflow exists and user owns it
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.owner_id == current_user.id
        )
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # Create share
    share = WorkflowShare(
        workflow_id=workflow_id,
        owner_id=current_user.id,
        permission=share_data.permission,
        is_public=share_data.is_public,
        max_uses=str(share_data.max_uses) if share_data.max_uses else None,
        expires_at=share_data.expires_at,
        description=share_data.description
    )
    
    db.add(share)
    await db.commit()
    await db.refresh(share)
    
    # Convert current_uses to int for response
    share_response = WorkflowShareResponse.model_validate(share)
    share_response.current_uses = int(share.current_uses)
    if share.max_uses:
        share_response.max_uses = int(share.max_uses)
    
    return share_response


@router.get("/workflows/{workflow_id}/shares", response_model=List[WorkflowShareResponse])
async def list_workflow_shares(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all shares for a workflow"""
    
    # Verify workflow exists and user owns it
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.owner_id == current_user.id
        )
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # Get shares
    result = await db.execute(
        select(WorkflowShare)
        .where(WorkflowShare.workflow_id == workflow_id)
        .order_by(WorkflowShare.created_at.desc())
    )
    shares = result.scalars().all()
    
    responses = []
    for share in shares:
        response = WorkflowShareResponse.model_validate(share)
        response.current_uses = int(share.current_uses)
        if share.max_uses:
            response.max_uses = int(share.max_uses)
        responses.append(response)
    
    return responses


@router.get("/shares/{share_token}", response_model=WorkflowShareResponse)
async def get_share_by_token(
    share_token: str,
    db: AsyncSession = Depends(get_db)
):
    """Get share details by token (public endpoint for verification)"""
    
    result = await db.execute(
        select(WorkflowShare).where(WorkflowShare.share_token == share_token)
    )
    share = result.scalar_one_or_none()
    
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found"
        )
    
    # Check if share is valid
    if not share.is_valid():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Share link has expired or usage limit exceeded"
        )
    
    response = WorkflowShareResponse.model_validate(share)
    response.current_uses = int(share.current_uses)
    if share.max_uses:
        response.max_uses = int(share.max_uses)
    
    return response


@router.get("/workflows/{workflow_id}/shares/{share_id}", response_model=WorkflowShareResponse)
async def get_workflow_share(
    workflow_id: UUID,
    share_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific share for a workflow"""
    
    result = await db.execute(
        select(WorkflowShare).where(
            WorkflowShare.id == share_id,
            WorkflowShare.workflow_id == workflow_id,
            WorkflowShare.owner_id == current_user.id
        )
    )
    share = result.scalar_one_or_none()
    
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found"
        )
    
    response = WorkflowShareResponse.model_validate(share)
    response.current_uses = int(share.current_uses)
    if share.max_uses:
        response.max_uses = int(share.max_uses)
    
    return response


@router.put("/workflows/{workflow_id}/shares/{share_id}", response_model=WorkflowShareResponse)
async def update_workflow_share(
    workflow_id: UUID,
    share_id: UUID,
    update_data: WorkflowShareUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a workflow share"""
    
    result = await db.execute(
        select(WorkflowShare).where(
            WorkflowShare.id == share_id,
            WorkflowShare.workflow_id == workflow_id,
            WorkflowShare.owner_id == current_user.id
        )
    )
    share = result.scalar_one_or_none()
    
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found"
        )
    
    # Update fields
    if update_data.permission is not None:
        share.permission = update_data.permission
    if update_data.is_public is not None:
        share.is_public = update_data.is_public
    if update_data.max_uses is not None:
        share.max_uses = str(update_data.max_uses) if update_data.max_uses else None
    if update_data.expires_at is not None:
        share.expires_at = update_data.expires_at
    if update_data.description is not None:
        share.description = update_data.description
    
    await db.commit()
    await db.refresh(share)
    
    response = WorkflowShareResponse.model_validate(share)
    response.current_uses = int(share.current_uses)
    if share.max_uses:
        response.max_uses = int(share.max_uses)
    
    return response


@router.delete("/workflows/{workflow_id}/shares/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow_share(
    workflow_id: UUID,
    share_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a workflow share"""
    
    result = await db.execute(
        select(WorkflowShare).where(
            WorkflowShare.id == share_id,
            WorkflowShare.workflow_id == workflow_id,
            WorkflowShare.owner_id == current_user.id
        )
    )
    share = result.scalar_one_or_none()
    
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found"
        )
    
    await db.delete(share)
    await db.commit()


@router.post("/shares/{share_token}/access", response_model=WorkflowShareAccessResponse, status_code=status.HTTP_201_CREATED)
async def record_share_access(
    share_token: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Record access to a shared workflow"""
    
    result = await db.execute(
        select(WorkflowShare).where(WorkflowShare.share_token == share_token)
    )
    share = result.scalar_one_or_none()
    
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found"
        )
    
    # Check if share is valid
    if not share.is_valid():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Share link has expired or usage limit exceeded"
        )
    
    # Record access
    access = WorkflowShareAccess(
        share_id=share.id,
        accessed_by=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    
    # Increment usage count
    share.current_uses = str(int(share.current_uses) + 1)
    
    db.add(access)
    await db.commit()
    await db.refresh(access)
    
    return WorkflowShareAccessResponse.model_validate(access)


@router.get("/workflows/{workflow_id}/shares/{share_id}/access", response_model=List[WorkflowShareAccessResponse])
async def get_share_access_log(
    workflow_id: UUID,
    share_id: UUID,
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get access log for a share"""
    
    # Verify share ownership
    result = await db.execute(
        select(WorkflowShare).where(
            WorkflowShare.id == share_id,
            WorkflowShare.workflow_id == workflow_id,
            WorkflowShare.owner_id == current_user.id
        )
    )
    share = result.scalar_one_or_none()
    
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found"
        )
    
    # Get access log
    result = await db.execute(
        select(WorkflowShareAccess)
        .where(WorkflowShareAccess.share_id == share_id)
        .order_by(WorkflowShareAccess.accessed_at.desc())
        .limit(limit)
    )
    accesses = result.scalars().all()
    
    return [WorkflowShareAccessResponse.model_validate(a) for a in accesses]
