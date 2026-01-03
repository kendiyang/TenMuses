from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID, uuid4
import asyncio

from app.core.database import get_db, AsyncSessionLocal
from app.models.user import User
from app.models.workflow import Workflow, WorkflowRun, RunStatus
from app.models.template import Template
from app.schemas.workflow import (
    WorkflowCreate,
    WorkflowUpdate,
    WorkflowResponse,
    WorkflowRunCreate,
    WorkflowRunResponse,
    BatchDeleteRequest
)
from app.schemas.template import TemplateCreate, TemplateResponse
from app.api.v1.auth import get_current_user
from app.api.v1.websocket import manager
from app.services.langgraph_service import langgraph_service

router = APIRouter()

@router.get("", response_model=List[WorkflowResponse])
async def list_workflows(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all workflows for the current user."""
    result = await db.execute(
        select(Workflow).where(Workflow.owner_id == current_user.id)
    )
    workflows = result.scalars().all()
    return [WorkflowResponse.model_validate(w) for w in workflows]

@router.post("", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow_data: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new workflow."""
    workflow = Workflow(
        owner_id=current_user.id,
        title=workflow_data.title,
        description=workflow_data.description,
        canvas_json=workflow_data.canvas_json or {"nodes": [], "edges": [], "viewport": {"x": 0, "y": 0, "zoom": 1}},
        source_template_id=workflow_data.source_template_id,
        is_public=workflow_data.is_public,
        tags=workflow_data.tags or []
    )
    
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    
    return WorkflowResponse.model_validate(workflow)

@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific workflow."""
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
    
    return WorkflowResponse.model_validate(workflow)

@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: UUID,
    workflow_data: WorkflowUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a workflow."""
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
    
    # Update fields
    if workflow_data.title is not None:
        workflow.title = workflow_data.title
    if workflow_data.description is not None:
        workflow.description = workflow_data.description
    if workflow_data.canvas_json is not None:
        workflow.canvas_json = workflow_data.canvas_json
    if workflow_data.is_public is not None:
        workflow.is_public = workflow_data.is_public
    if workflow_data.tags is not None:
        workflow.tags = workflow_data.tags
    if workflow_data.status is not None:
        from app.models.workflow import WorkflowStatus
        workflow.status = WorkflowStatus(workflow_data.status).value
    
    await db.commit()
    await db.refresh(workflow)
    
    return WorkflowResponse.model_validate(workflow)

@router.delete("/{workflow_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a workflow."""
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
    
    await db.delete(workflow)
    await db.commit()

@router.post("/batch-delete", status_code=status.HTTP_204_NO_CONTENT)
async def batch_delete_workflows(
    request: BatchDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Batch delete multiple workflows."""
    if not request.workflow_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No workflow IDs provided"
        )
    
    # Fetch workflows to verify ownership
    result = await db.execute(
        select(Workflow).where(
            Workflow.id.in_(request.workflow_ids),
            Workflow.owner_id == current_user.id
        )
    )
    workflows = result.scalars().all()
    
    # Delete all found workflows
    for workflow in workflows:
        await db.delete(workflow)
    
    await db.commit()

@router.post("/{workflow_id}/duplicate", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_workflow(
    workflow_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Duplicate an existing workflow."""
    # Get original workflow
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.owner_id == current_user.id
        )
    )
    original = result.scalar_one_or_none()
    
    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow not found"
        )
    
    # Create duplicate with new ID
    import copy
    duplicate = Workflow(
        owner_id=current_user.id,
        title=f"{original.title} (Copy)",
        description=original.description,
        canvas_json=copy.deepcopy(original.canvas_json),
        source_template_id=original.source_template_id,
        is_public=False,  # Duplicates are private by default
        tags=copy.deepcopy(original.tags) if original.tags else []
    )
    
    db.add(duplicate)
    await db.commit()
    await db.refresh(duplicate)
    
    return WorkflowResponse.model_validate(duplicate)

@router.post("/{workflow_id}/publish", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def publish_workflow_as_template(
    workflow_id: UUID,
    template_data: TemplateCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Publish a workflow as a marketplace template"""
    
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
    
    # Check if template already exists for this workflow
    result = await db.execute(
        select(Template).where(Template.workflow_id == workflow_id)
    )
    existing_template = result.scalar_one_or_none()
    
    if existing_template:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This workflow is already published as a template"
        )
    
    # Create template
    template = Template(
        workflow_id=workflow_id,
        author_id=current_user.id,
        name=template_data.name,
        description=template_data.description,
        category=template_data.category,
        tags=template_data.tags or [],
        is_published=True
    )
    
    db.add(template)
    
    # Update workflow status to published
    workflow.status = 'published'
    
    await db.commit()
    await db.refresh(template)
    
    return TemplateResponse.model_validate(template)

@router.post("/{workflow_id}/run", response_model=WorkflowRunResponse)
async def run_workflow(
    workflow_id: UUID,
    run_data: WorkflowRunCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start a workflow execution."""
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
    
    # Create workflow run
    thread_id = uuid4()
    workflow_run = WorkflowRun(
        workflow_id=workflow_id,
        thread_id=thread_id,
        status=RunStatus.RUNNING.value,
        input_summary=run_data.input[:200] if run_data.input else None
    )

    db.add(workflow_run)
    
    # Update workflow last_run_at
    from datetime import datetime
    workflow.last_run_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(workflow_run)

    # Optionally start server-side execution in background
    if getattr(run_data, 'start_server_side', False):
        thread_id_str = str(thread_id)
        # Schedule background runner
        asyncio.create_task(_execute_and_stream(thread_id_str, run_data.input or ""))

    return WorkflowRunResponse(
        id=workflow_run.id,
        workflow_id=workflow_run.workflow_id,
        thread_id=workflow_run.thread_id,
        status=workflow_run.status if isinstance(workflow_run.status, str) else workflow_run.status.value,
        input_summary=workflow_run.input_summary,
        started_at=workflow_run.started_at,
        finished_at=workflow_run.finished_at,
        ws_url=f"ws://localhost:8000/ws/run/{thread_id}"
    )


async def _execute_and_stream(thread_id_str: str, input_text: str):
    """Background runner to execute LangGraph workflow and stream events to connected clients."""
    try:
        # Notify run started
        await manager.send_message(thread_id_str, {
            "type": "run_started",
            "threadId": thread_id_str,
            "payload": {"inputSummary": input_text[:200]}
        })

        current_node = None

        async for event in langgraph_service.stream_workflow(input_text):
            event_type = event.get("event")

            if event_type == "on_chain_start":
                node_name = event.get("name", "")
                if node_name:
                    current_node = node_name
                    await manager.send_message(thread_id_str, {
                        "type": "node_started",
                        "threadId": thread_id_str,
                        "nodeId": node_name,
                        "payload": {"label": node_name.capitalize()}
                    })
                    await manager.send_message(thread_id_str, {
                        "type": "node_status",
                        "threadId": thread_id_str,
                        "nodeId": node_name,
                        "payload": {"status": "executing"}
                    })

            elif event_type == "on_chain_end":
                node_name = event.get("name", "")
                if node_name:
                    await manager.send_message(thread_id_str, {
                        "type": "node_status",
                        "threadId": thread_id_str,
                        "nodeId": node_name,
                        "payload": {"status": "completed"}
                    })

            elif event_type == "on_chat_model_stream":
                data = event.get("data", {})
                chunk = data.get("chunk")
                
                # chunk 可能是 AIMessageChunk 对象或字典
                content = ""
                if chunk:
                    if hasattr(chunk, "content"):
                        content = chunk.content
                    elif isinstance(chunk, dict):
                        content = chunk.get("content", "")
                
                if content and current_node:
                    await manager.send_message(thread_id_str, {
                        "type": "token",
                        "threadId": thread_id_str,
                        "nodeId": current_node,
                        "payload": {"content": content, "finished": False}
                    })

        # Run completion
        await manager.send_message(thread_id_str, {
            "type": "run_completed",
            "threadId": thread_id_str,
            "payload": {"status": "completed", "durationMs": 0}
        })

        # Update run status in DB to completed
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(WorkflowRun).where(WorkflowRun.thread_id == UUID(thread_id_str)))
            run = result.scalar_one_or_none()
            if run:
                run.status = RunStatus.COMPLETED.value
                session.add(run)
                await session.commit()

    except Exception as e:
        # Stream error
        await manager.send_message(thread_id_str, {
            "type": "error",
            "threadId": thread_id_str,
            "payload": {"message": str(e), "code": "EXECUTION_ERROR", "fatal": True}
        })

        # Mark run as failed
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(WorkflowRun).where(WorkflowRun.thread_id == UUID(thread_id_str)))
                run = result.scalar_one_or_none()
                if run:
                    run.status = RunStatus.FAILED.value
                    session.add(run)
                    await session.commit()
        except Exception:
            pass

