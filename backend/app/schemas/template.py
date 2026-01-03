from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from uuid import UUID


class TemplateBase(BaseModel):
    name: str
    description: str
    category: str
    tags: Optional[List[str]] = None


class TemplateCreate(TemplateBase):
    workflow_id: UUID


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    icon_url: Optional[str] = None
    preview_images: Optional[List[str]] = None
    is_published: Optional[bool] = None


class TemplateResponse(TemplateBase):
    id: UUID
    workflow_id: UUID
    author_id: UUID
    icon_url: Optional[str] = None
    preview_images: Optional[List[str]] = None
    use_count: int
    favorite_count: int
    rating: float
    review_count: int
    is_featured: bool
    is_published: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    """Simplified template response for list views"""
    id: UUID
    name: str
    description: str
    category: str
    tags: Optional[List[str]] = None
    icon_url: Optional[str] = None
    author_id: UUID
    use_count: int
    favorite_count: int
    rating: float
    is_featured: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class TemplateReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class TemplateReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None


class TemplateReviewResponse(BaseModel):
    id: UUID
    template_id: UUID
    user_id: UUID
    rating: int
    comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FavoriteResponse(BaseModel):
    id: UUID
    user_id: UUID
    template_id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True
