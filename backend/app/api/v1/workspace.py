"""
Workspace API endpoints - 用户工作空间概览
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import List, Dict, Any
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.workflow import Workflow, WorkflowRun
from app.schemas.workflow import WorkflowResponse

router = APIRouter()


@router.get("/workspace")
async def get_workspace_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    获取用户工作空间概览
    
    返回：
    - recent_workflows: 最近编辑的工作流（最多10个）
    - statistics: 用户统计信息
    - featured_templates: 推荐模板（暂时返回空列表）
    """
    
    # 获取最近的工作流（按更新时间排序）
    stmt = (
        select(Workflow)
        .where(Workflow.owner_id == current_user.id)
        .order_by(desc(Workflow.updated_at))
        .limit(10)
    )
    result = await db.execute(stmt)
    recent_workflows = result.scalars().all()
    
    # 统计用户的工作流总数
    stmt_count = (
        select(func.count(Workflow.id))
        .where(Workflow.owner_id == current_user.id)
    )
    result_count = await db.execute(stmt_count)
    total_workflows = result_count.scalar() or 0
    
    # 统计用户的运行次数
    stmt_runs = (
        select(func.count(WorkflowRun.id))
        .join(Workflow, WorkflowRun.workflow_id == Workflow.id)
        .where(Workflow.owner_id == current_user.id)
    )
    result_runs = await db.execute(stmt_runs)
    total_runs = result_runs.scalar() or 0
    
    # 转换工作流为响应格式
    workflow_responses = []
    for workflow in recent_workflows:
        # 获取最后运行时间
        stmt_last_run = (
            select(WorkflowRun.started_at)
            .where(WorkflowRun.workflow_id == workflow.id)
            .order_by(desc(WorkflowRun.started_at))
            .limit(1)
        )
        result_last_run = await db.execute(stmt_last_run)
        last_run_at = result_last_run.scalar()
        
        workflow_dict = WorkflowResponse.model_validate(workflow).model_dump()
        workflow_dict['last_run_at'] = last_run_at.isoformat() if last_run_at else None
        workflow_dict['nodes_count'] = len(workflow.canvas_json.get('nodes', [])) if workflow.canvas_json else 0
        workflow_responses.append(workflow_dict)
    
    return {
        "recent_workflows": workflow_responses,
        "statistics": {
            "total_workflows": total_workflows,
            "total_runs": total_runs,
            "total_templates": 0  # 暂时返回0，后续实现模板功能后更新
        },
        "featured_templates": []  # 暂时返回空列表，后续实现模板功能后更新
    }


@router.get("/workspace/recent")
async def get_recent_workflows(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    获取最近编辑的工作流
    
    参数：
    - limit: 返回数量限制，默认10
    """
    
    stmt = (
        select(Workflow)
        .where(Workflow.owner_id == current_user.id)
        .order_by(desc(Workflow.updated_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    workflows = result.scalars().all()
    
    workflow_list = []
    for workflow in workflows:
        # 获取最后运行时间
        stmt_last_run = (
            select(WorkflowRun.started_at)
            .where(WorkflowRun.workflow_id == workflow.id)
            .order_by(desc(WorkflowRun.started_at))
            .limit(1)
        )
        result_last_run = await db.execute(stmt_last_run)
        last_run_at = result_last_run.scalar()
        
        workflow_dict = WorkflowResponse.model_validate(workflow).model_dump()
        workflow_dict['status'] = 'draft'  # 暂时硬编码，后续扩展模型后更新
        workflow_dict['nodes_count'] = len(workflow.canvas_json.get('nodes', [])) if workflow.canvas_json else 0
        workflow_dict['last_run_at'] = last_run_at.isoformat() if last_run_at else None
        workflow_list.append(workflow_dict)
    
    return {"workflows": workflow_list}
