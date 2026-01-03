from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

class WorkflowBase(BaseModel):
    title: str
    description: Optional[str] = None
    is_public: bool = False
    tags: Optional[List[str]] = None

class WorkflowCreate(WorkflowBase):
    canvas_json: Optional[Dict[str, Any]] = None
    source_template_id: Optional[UUID] = None

class WorkflowUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    canvas_json: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None

class WorkflowResponse(WorkflowBase):
    id: UUID
    owner_id: UUID
    canvas_json: Dict[str, Any]
    source_template_id: Optional[UUID] = None
    status: str
    last_run_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class BatchDeleteRequest(BaseModel):
    workflow_ids: List[UUID]

class WorkflowRunCreate(BaseModel):
    input: str
    initial_state: Optional[Dict[str, Any]] = None
    start_server_side: Optional[bool] = False

class WorkflowRunResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    thread_id: UUID
    status: str
    input_summary: Optional[str] = None
    started_at: datetime
    finished_at: Optional[datetime] = None
    ws_url: str
    
    class Config:
        from_attributes = True
