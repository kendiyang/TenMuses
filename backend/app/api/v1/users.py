from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import os
import uuid
from pathlib import Path
import aiofiles

from app.core.database import get_db
from app.core.cache import cache_service, CacheKeys, CacheTTL
from app.models.user import User
from app.models.workflow import Workflow, WorkflowRun
from app.models.template import Template, Favorite
from app.api.v1.auth import get_current_user
from pydantic import BaseModel

router = APIRouter()

# 配置上传路径
UPLOAD_DIR = Path("uploads/avatars")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 允许的文件类型
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


class UserStatistics(BaseModel):
    total_workflows: int
    total_runs: int
    total_templates_published: int
    total_favorites: int
    most_used_template_id: str | None = None
    last_run_at: str | None = None


@router.get("/users/me/statistics", response_model=UserStatistics)
async def get_user_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get statistics for the current user"""
    
    # Check cache first
    cache_key = CacheKeys.user_statistics(str(current_user.id))
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return UserStatistics(**cached_data)
    
    # Total workflows
    workflows_result = await db.execute(
        select(func.count(Workflow.id)).where(Workflow.owner_id == current_user.id)
    )
    total_workflows = workflows_result.scalar() or 0
    
    # Total runs
    runs_result = await db.execute(
        select(func.count(WorkflowRun.id))
        .join(Workflow, Workflow.id == WorkflowRun.workflow_id)
        .where(Workflow.owner_id == current_user.id)
    )
    total_runs = runs_result.scalar() or 0
    
    # Total templates published
    templates_result = await db.execute(
        select(func.count(Template.id)).where(Template.author_id == current_user.id)
    )
    total_templates_published = templates_result.scalar() or 0
    
    # Total favorites
    favorites_result = await db.execute(
        select(func.count(Favorite.id)).where(Favorite.user_id == current_user.id)
    )
    total_favorites = favorites_result.scalar() or 0
    
    # Most used template
    most_used_result = await db.execute(
        select(Template.id)
        .where(Template.author_id == current_user.id)
        .order_by(Template.use_count.desc())
        .limit(1)
    )
    most_used_template_id = most_used_result.scalar()
    
    # Last run
    last_run_result = await db.execute(
        select(WorkflowRun.finished_at)
        .join(Workflow, Workflow.id == WorkflowRun.workflow_id)
        .where(Workflow.owner_id == current_user.id)
        .order_by(WorkflowRun.finished_at.desc())
        .limit(1)
    )
    last_run_at = last_run_result.scalar()
    
    stats = UserStatistics(
        total_workflows=total_workflows,
        total_runs=total_runs,
        total_templates_published=total_templates_published,
        total_favorites=total_favorites,
        most_used_template_id=str(most_used_template_id) if most_used_template_id else None,
        last_run_at=last_run_at.isoformat() if last_run_at else None
    )
    
    # Cache the result
    await cache_service.set(
        cache_key,
        stats.model_dump(),
        ttl=CacheTTL.USER_STATISTICS
    )
    
    return stats


@router.post("/users/me/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload user avatar"""
    
    # 验证文件类型
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # 验证文件大小
    content = await file.read()
    file_size = len(content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # 生成唯一文件名
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # 保存文件
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)
    
    # 删除旧头像（如果存在）
    if current_user.avatar_url:
        old_file_path = Path(current_user.avatar_url.lstrip('/'))
        if old_file_path.exists():
            try:
                os.remove(old_file_path)
            except Exception:
                pass  # 忽略删除失败
    
    # 更新用户头像URL
    avatar_url = f"/uploads/avatars/{unique_filename}"
    current_user.avatar_url = avatar_url
    
    await db.commit()
    await db.refresh(current_user)
    
    return {
        "message": "Avatar uploaded successfully",
        "avatar_url": avatar_url
    }


@router.delete("/users/me/avatar")
async def delete_avatar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete user avatar"""
    
    if not current_user.avatar_url:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No avatar to delete"
        )
    
    # 删除文件
    file_path = Path(current_user.avatar_url.lstrip('/'))
    if file_path.exists():
        try:
            os.remove(file_path)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete avatar file: {str(e)}"
            )
    
    # 更新数据库
    current_user.avatar_url = None
    await db.commit()
    
    return {"message": "Avatar deleted successfully"}
