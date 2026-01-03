from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID


class WorkflowShareCreate(BaseModel):
    permission: str  # "view", "edit", "execute"
    is_public: bool = False
    max_uses: Optional[int] = None
    expires_at: Optional[datetime] = None
    description: Optional[str] = None


class WorkflowShareUpdate(BaseModel):
    permission: Optional[str] = None
    is_public: Optional[bool] = None
    max_uses: Optional[int] = None
    expires_at: Optional[datetime] = None
    description: Optional[str] = None


class WorkflowShareResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    owner_id: UUID
    share_token: str
    share_url: Optional[str] = None
    permission: str
    is_public: bool
    max_uses: Optional[int] = None
    current_uses: int
    expires_at: Optional[datetime] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WorkflowShareAccessResponse(BaseModel):
    id: UUID
    share_id: UUID
    access_token: Optional[str] = None
    accessed_by: Optional[UUID] = None
    accessed_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    class Config:
        from_attributes = True
