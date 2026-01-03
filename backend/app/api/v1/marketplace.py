from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel

from app.core.database import get_db
from app.core.cache import cache_service, CacheKeys, CacheTTL
from app.models.user import User
from app.models.template import Template, TemplateReview, Favorite
from app.models.workflow import Workflow
from app.schemas.template import (
    TemplateResponse,
    TemplateListResponse,
    TemplateReviewCreate,
    TemplateReviewResponse,
    FavoriteResponse
)
from app.schemas.workflow import WorkflowResponse, WorkflowCreate
from app.api.v1.auth import get_current_user

router = APIRouter()


class PaginatedTemplateResponse(BaseModel):
    """Paginated template list response"""
    items: List[TemplateListResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


@router.get("/templates", response_model=PaginatedTemplateResponse)
async def list_templates(
    category: Optional[str] = None,
    tags: Optional[str] = Query(None, description="Comma-separated tags"),
    search: Optional[str] = None,
    sort_by: str = Query("popular", regex="^(popular|recent|rating)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List templates in marketplace with filtering, sorting, and pagination"""
    
    # Check cache first
    cache_key = CacheKeys.marketplace_templates(
        category=category,
        tags=tags,
        search=search,
        sort_by=sort_by,
        page=page,
        page_size=page_size
    )
    
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return PaginatedTemplateResponse(**cached_data)
    
    # 构建基础查询
    base_query = select(Template).where(Template.is_published == True)
    count_query = select(func.count(Template.id)).where(Template.is_published == True)
    
    # Apply filters
    if category:
        base_query = base_query.where(Template.category == category)
        count_query = count_query.where(Template.category == category)
    
    if tags:
        tag_list = [tag.strip() for tag in tags.split(",")]
        base_query = base_query.where(Template.tags.overlap(tag_list))
        count_query = count_query.where(Template.tags.overlap(tag_list))
    
    if search:
        search_pattern = f"%{search}%"
        search_filter = (Template.name.ilike(search_pattern)) | (Template.description.ilike(search_pattern))
        base_query = base_query.where(search_filter)
        count_query = count_query.where(search_filter)
    
    # 获取总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply sorting
    if sort_by == "popular":
        base_query = base_query.order_by(Template.use_count.desc())
    elif sort_by == "recent":
        base_query = base_query.order_by(Template.created_at.desc())
    elif sort_by == "rating":
        base_query = base_query.order_by(Template.rating.desc())
    
    # Apply pagination
    offset = (page - 1) * page_size
    base_query = base_query.limit(page_size).offset(offset)
    
    result = await db.execute(base_query)
    templates = result.scalars().all()
    
    # 计算总页数
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    response = PaginatedTemplateResponse(
        items=[TemplateListResponse.model_validate(t) for t in templates],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
    
    # Cache the result
    await cache_service.set(
        cache_key,
        response.model_dump(),
        ttl=CacheTTL.MARKETPLACE_TEMPLATES
    )
    
    return response


@router.get("/templates/featured", response_model=List[TemplateListResponse])
async def list_featured_templates(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """Get featured templates"""
    
    # Check cache first
    cache_key = CacheKeys.featured_templates()
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return [TemplateListResponse(**item) for item in cached_data]
    
    result = await db.execute(
        select(Template)
        .where(and_(Template.is_published == True, Template.is_featured == True))
        .order_by(Template.rating.desc())
        .limit(limit)
    )
    templates = result.scalars().all()
    
    response = [TemplateListResponse.model_validate(t) for t in templates]
    
    # Cache the result
    await cache_service.set(
        cache_key,
        [item.model_dump() for item in response],
        ttl=CacheTTL.FEATURED_TEMPLATES
    )
    
    return response


@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get template details"""
    
    # Check cache first
    cache_key = CacheKeys.template_detail(str(template_id))
    cached_data = await cache_service.get(cache_key)
    if cached_data:
        return TemplateResponse(**cached_data)
    
    result = await db.execute(
        select(Template).where(Template.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    response = TemplateResponse.model_validate(template)
    
    # Cache the result
    await cache_service.set(
        cache_key,
        response.model_dump(),
        ttl=CacheTTL.TEMPLATE_DETAIL
    )
    
    return response


@router.post("/templates/{template_id}/use", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow_from_template(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new workflow from a template"""
    
    # Get template
    result = await db.execute(
        select(Template).where(Template.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Get source workflow
    result = await db.execute(
        select(Workflow).where(Workflow.id == template.workflow_id)
    )
    source_workflow = result.scalar_one_or_none()
    
    if not source_workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source workflow not found"
        )
    
    # Create new workflow from template
    import copy
    new_workflow = Workflow(
        owner_id=current_user.id,
        title=f"{template.name}",
        description=template.description,
        canvas_json=copy.deepcopy(source_workflow.canvas_json),
        source_template_id=template_id,
        is_public=False,
        tags=copy.deepcopy(template.tags) if template.tags else []
    )
    
    db.add(new_workflow)
    
    # Increment template use count
    template.use_count += 1
    
    await db.commit()
    await db.refresh(new_workflow)
    
    return WorkflowResponse.model_validate(new_workflow)


@router.post("/templates/{template_id}/reviews", response_model=TemplateReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    template_id: UUID,
    review_data: TemplateReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create or update a review for a template"""
    
    # Check if template exists
    result = await db.execute(
        select(Template).where(Template.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check if user already reviewed
    result = await db.execute(
        select(TemplateReview).where(
            and_(
                TemplateReview.template_id == template_id,
                TemplateReview.user_id == current_user.id
            )
        )
    )
    existing_review = result.scalar_one_or_none()
    
    if existing_review:
        # Update existing review
        existing_review.rating = review_data.rating
        if review_data.comment is not None:
            existing_review.comment = review_data.comment
        review = existing_review
    else:
        # Create new review
        review = TemplateReview(
            template_id=template_id,
            user_id=current_user.id,
            rating=review_data.rating,
            comment=review_data.comment
        )
        db.add(review)
        template.review_count += 1
    
    # Recalculate template rating
    result = await db.execute(
        select(func.avg(TemplateReview.rating))
        .where(TemplateReview.template_id == template_id)
    )
    avg_rating = result.scalar() or 0.0
    template.rating = float(avg_rating)
    
    await db.commit()
    await db.refresh(review)
    
    return TemplateReviewResponse.model_validate(review)


@router.get("/templates/{template_id}/reviews", response_model=List[TemplateReviewResponse])
async def list_reviews(
    template_id: UUID,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """List reviews for a template"""
    
    result = await db.execute(
        select(TemplateReview)
        .where(TemplateReview.template_id == template_id)
        .order_by(TemplateReview.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    reviews = result.scalars().all()
    
    return [TemplateReviewResponse.model_validate(r) for r in reviews]


@router.post("/templates/{template_id}/favorite", response_model=FavoriteResponse, status_code=status.HTTP_201_CREATED)
async def add_favorite(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Add template to favorites"""
    
    # Check if template exists
    result = await db.execute(
        select(Template).where(Template.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    # Check if already favorited
    result = await db.execute(
        select(Favorite).where(
            and_(
                Favorite.template_id == template_id,
                Favorite.user_id == current_user.id
            )
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        return FavoriteResponse.model_validate(existing)
    
    # Create favorite
    favorite = Favorite(
        user_id=current_user.id,
        template_id=template_id
    )
    db.add(favorite)
    
    # Increment favorite count
    template.favorite_count += 1
    
    await db.commit()
    await db.refresh(favorite)
    
    return FavoriteResponse.model_validate(favorite)


@router.delete("/templates/{template_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    template_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove template from favorites"""
    
    result = await db.execute(
        select(Favorite).where(
            and_(
                Favorite.template_id == template_id,
                Favorite.user_id == current_user.id
            )
        )
    )
    favorite = result.scalar_one_or_none()
    
    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Favorite not found"
        )
    
    # Get template to decrement count
    result = await db.execute(
        select(Template).where(Template.id == template_id)
    )
    template = result.scalar_one_or_none()
    
    if template:
        template.favorite_count = max(0, template.favorite_count - 1)
    
    await db.delete(favorite)
    await db.commit()


@router.get("/favorites", response_model=List[TemplateListResponse])
async def list_user_favorites(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List current user's favorite templates"""
    
    result = await db.execute(
        select(Template)
        .join(Favorite, Favorite.template_id == Template.id)
        .where(Favorite.user_id == current_user.id)
        .order_by(Favorite.created_at.desc())
    )
    templates = result.scalars().all()
    
    return [TemplateListResponse.model_validate(t) for t in templates]
