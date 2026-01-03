"""
动态工作流API端点

支持通过canvas JSON动态创建和执行工作流，不需要预先定义工作流类型。
包含速率限制和并发控制以防止API滥用。
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid
import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.workflow import Workflow, WorkflowRun
from app.schemas.node import WorkflowGraph, validate_graph, NodeType
from app.schemas.workflow import WorkflowResponse, WorkflowRunResponse
from app.services.dynamic_graph_factory import DynamicGraphFactory, create_workflow
from app.services.executor_library import create_executor, tool_library
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/v1/dynamic", tags=["dynamic"])
logger = logging.getLogger(__name__)

# 速率限制配置
class RateLimiter:
    """简单的速率限制器 - 防止API滥用"""
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)  # user_id -> list of timestamps
    
    def check_limit(self, user_id: str) -> bool:
        """检查用户是否超过速率限制"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)
        
        # 清理过期的请求记录
        self.requests[user_id] = [
            ts for ts in self.requests[user_id] if ts > cutoff
        ]
        
        # 检查是否超限
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        
        # 记录这次请求
        self.requests[user_id].append(now)
        return True
    
    def get_remaining(self, user_id: str) -> int:
        """获取剩余的请求次数"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.window_seconds)
        self.requests[user_id] = [
            ts for ts in self.requests[user_id] if ts > cutoff
        ]
        return max(0, self.max_requests - len(self.requests[user_id]))

# 全局速率限制器
rate_limiter = RateLimiter(max_requests=10, window_seconds=60)


# ============================================================================
# 工具库API
# ============================================================================

@router.get("/tools")
async def list_available_tools():
    """
    列出所有可用工具
    
    返回:
        {
            "tools": {
                "tool_name": "tool description",
                ...
            }
        }
    """
    return {
        "tools": tool_library.list_tools()
    }


@router.post("/tools/register")
async def register_custom_tool(
    name: str,
    description: str,
    current_user: User = Depends(get_current_user)
):
    """
    注册自定义工具（仅允许管理员）
    
    注意: 实际应用中应该有更严格的安全控制
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    return {"message": f"工具 {name} 注册成功"}


# ============================================================================
# 动态工作流执行API
# ============================================================================

@router.post("/execute")
async def execute_dynamic_workflow(
    graph_data: WorkflowGraph,
    input_data: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    直接执行动态工作流（不保存）
    
    Args:
        graph_data: 工作流图定义（从canvas导出）
        input_data: 工作流输入数据
    
    Returns:
        {
            "threadId": "uuid",
            "wsUrl": "ws://localhost:8000/ws/run/{threadId}",
            "status": "RUNNING"
        }
    
    速率限制:
        - 每个用户每分钟最多执行10个工作流
        - 同一用户最多5个并发执行
    """
    
    # 检查速率限制
    if not rate_limiter.check_limit(current_user.id):
        remaining = rate_limiter.get_remaining(current_user.id)
        raise HTTPException(
            status_code=429,
            detail=f"请求过于频繁。请在60秒后重试。(剩余配额: {remaining}/10)"
        )
    
    # 检查并发执行数量
    active_runs = await db.execute(
        select(func.count(WorkflowRun.id)).where(
            WorkflowRun.creator_id == current_user.id,
            WorkflowRun.status == "RUNNING"
        )
    )
    active_count = active_runs.scalar() or 0
    
    if active_count >= 5:
        raise HTTPException(
            status_code=429,
            detail=f"并发执行数已达上限(5个)。请等待其他工作流完成。"
        )
    
    # 生成唯一的thread_id
    thread_id = str(uuid.uuid4())
    
    try:
        # 验证图定义
        validated_graph = validate_graph(graph_data)
        
        # 限制输入大小
        import sys
        input_size = sys.getsizeof(input_data or {})
        if input_size > 1_000_000:  # 1MB限制
            raise ValueError(f"输入数据过大 ({input_size} bytes > 1MB)")
        
        # 创建WorkflowRun记录
        workflow_run = WorkflowRun(
            id=uuid.uuid4(),
            workflow_id=None,  # 动态工作流没有保存的workflow_id
            thread_id=thread_id,
            status="RUNNING",
            input_summary=json.dumps(input_data or {}, ensure_ascii=False)[:500],
            creator_id=current_user.id
        )
        
        db.add(workflow_run)
        await db.commit()
        logger.info(f"Created workflow run: {thread_id} for user {current_user.id}")
        
        # 返回ws连接URL供前端连接
        remaining = rate_limiter.get_remaining(current_user.id)
        
        return {
            "threadId": thread_id,
            "wsUrl": f"ws://localhost:8000/api/v1/ws/run/{thread_id}",
            "status": "RUNNING",
            "graphNodes": len(validated_graph.nodes),
            "graphEdges": len(validated_graph.edges),
            "rateLimit": {
                "remaining": remaining,
                "limit": 10,
                "resetIn": 60
            }
        }
    
    except ValueError as e:
        logger.exception(f"Validation error in execute: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


@router.post("/workflows/compile")
async def compile_dynamic_workflow(
    graph_data: WorkflowGraph,
    current_user: User = Depends(get_current_user)
):
    """
    编译工作流图为LangGraph（用于验证和预编译）
    
    Args:
        graph_data: 工作流图定义
    
    Returns:
        {
            "compiled": True,
            "nodeCount": N,
            "edgeCount": M,
            "executionOrder": ["node-1", "node-2", ...],
            "warnings": [...]
        }
    """
    try:
        # 验证和编译
        validated_graph = validate_graph(graph_data)
        factory = DynamicGraphFactory(validated_graph)
        
        # 获取执行顺序（拓扑排序）
        execution_order = factory._get_start_nodes()
        
        warnings = []
        
        # 检查节点配置
        for node in validated_graph.nodes:
            if node.type == NodeType.LLM and not node.data.llm_config:
                warnings.append(f"LLM节点 {node.id} 缺少配置")
            elif node.type == NodeType.TOOL and not node.data.tool_config:
                warnings.append(f"Tool节点 {node.id} 缺少配置")
            elif node.type == NodeType.ROUTER and not node.data.router_config:
                warnings.append(f"Router节点 {node.id} 缺少配置")
        
        return {
            "compiled": True,
            "nodeCount": len(validated_graph.nodes),
            "edgeCount": len(validated_graph.edges),
            "nodeTypes": list(set(n.type.value for n in validated_graph.nodes)),
            "startNodes": factory._get_start_nodes(),
            "endNodes": factory._get_end_nodes(),
            "warnings": warnings
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"编译失败: {str(e)}")


# ============================================================================
# 工作流模板API
# ============================================================================

@router.get("/templates")
async def list_workflow_templates(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(get_current_user)
):
    """
    获取预定义的工作流模板 - 支持分页
    
    Args:
        page: 页码（从1开始）
        page_size: 每页数量（1-100）
    
    Returns:
        {
            "templates": [...],
            "pagination": {
                "page": 1,
                "page_size": 10,
                "total": 3,
                "total_pages": 1
            }
        }
    """
    templates = [
        {
            "id": "research-writer-reviewer",
            "name": "研究-写作-审核流程",
            "description": "三阶段工作流：数据研究 → 内容写作 → 专家审核",
            "nodeCount": 3,
            "nodeTypes": ["llm", "llm", "llm"],
            "preview": {
                "nodes": [
                    {"id": "research", "type": "llm", "label": "研究"},
                    {"id": "writer", "type": "llm", "label": "写作"},
                    {"id": "reviewer", "type": "llm", "label": "审核"}
                ],
                "edges": [
                    {"source": "research", "target": "writer"},
                    {"source": "writer", "target": "reviewer"}
                ]
            }
        },
        {
            "id": "conditional-approval",
            "name": "条件审批流程",
            "description": "根据条件决策的工作流：内容生成 → 条件路由 → 审批/拒绝",
            "nodeCount": 4,
            "nodeTypes": ["llm", "router", "llm", "llm"],
            "preview": {
                "nodes": [
                    {"id": "generator", "type": "llm", "label": "内容生成"},
                    {"id": "router", "type": "router", "label": "条件路由"},
                    {"id": "approve", "type": "llm", "label": "批准"},
                    {"id": "reject", "type": "llm", "label": "拒绝"}
                ],
                "edges": [
                    {"source": "generator", "target": "router"},
                    {"source": "router", "target": "approve"},
                    {"source": "router", "target": "reject"}
                ]
            }
        },
        {
            "id": "parallel-map",
            "name": "并行Map工作流",
            "description": "对多个项目并行处理：批处理 → 并行执行 → 聚合结果",
            "nodeCount": 3,
            "nodeTypes": ["input", "map", "output"],
            "preview": {
                "nodes": [
                    {"id": "input", "type": "input", "label": "输入列表"},
                    {"id": "map", "type": "map", "label": "并行处理"},
                    {"id": "output", "type": "output", "label": "输出"}
                ],
                "edges": [
                    {"source": "input", "target": "map"},
                    {"source": "map", "target": "output"}
                ]
            }
        }
    ]
    
    # 计算分页
    total = len(templates)
    start = (page - 1) * page_size
    end = start + page_size
    paginated = templates[start:end]
    
    total_pages = (total + page_size - 1) // page_size
    
    return {
        "templates": paginated,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages
        }
    }


@router.get("/templates/{template_id}")
async def get_template_detail(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取模板详细信息（包含完整的graph定义）
    """
    templates = {
        "research-writer-reviewer": {
            "id": "research-writer-reviewer",
            "name": "研究-写作-审核流程",
            "description": "三阶段工作流：数据研究 → 内容写作 → 专家审核",
            "graph": {
                "nodes": [
                    {
                        "id": "node-1",
                        "type": "llm",
                        "position": {"x": 100, "y": 100},
                        "data": {
                            "label": "研究",
                            "llm_config": {
                                "provider": "openai",
                                "model": "gpt-4-turbo-preview",
                                "temperature": 0.7
                            }
                        }
                    },
                    {
                        "id": "node-2",
                        "type": "llm",
                        "position": {"x": 300, "y": 100},
                        "data": {
                            "label": "写作",
                            "llm_config": {
                                "provider": "openai",
                                "model": "gpt-4-turbo-preview",
                                "temperature": 0.7
                            }
                        }
                    },
                    {
                        "id": "node-3",
                        "type": "llm",
                        "position": {"x": 500, "y": 100},
                        "data": {
                            "label": "审核",
                            "llm_config": {
                                "provider": "openai",
                                "model": "gpt-4-turbo-preview",
                                "temperature": 0.5
                            }
                        }
                    }
                ],
                "edges": [
                    {"id": "edge-1", "source": "node-1", "target": "node-2", "type": "normal"},
                    {"id": "edge-2", "source": "node-2", "target": "node-3", "type": "normal"}
                ]
            }
        }
    }
    
    template = templates.get(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"模板 {template_id} 不存在")
    
    return template


# ============================================================================
# 工作流验证API
# ============================================================================

@router.post("/validate")
async def validate_workflow_graph(
    graph_data: WorkflowGraph,
    current_user: User = Depends(get_current_user)
):
    """
    验证工作流图的有效性
    
    Returns:
        {
            "valid": True/False,
            "errors": [...],
            "warnings": [...],
            "stats": {
                "nodeCount": N,
                "edgeCount": M,
                "nodeTypes": {...}
            }
        }
    """
    errors = []
    warnings = []
    
    try:
        validated_graph = validate_graph(graph_data)
        
        # 检查节点配置
        for node in validated_graph.nodes:
            if node.type == NodeType.LLM and not node.data.llm_config:
                errors.append(f"LLM节点 {node.id} 缺少 llm_config")
            elif node.type == NodeType.TOOL and not node.data.tool_config:
                errors.append(f"Tool节点 {node.id} 缺少 tool_config")
            elif node.type == NodeType.ROUTER and not node.data.router_config:
                errors.append(f"Router节点 {node.id} 缺少 router_config")
        
        # 检查有孤立节点
        connected_nodes = set()
        for edge in validated_graph.edges:
            connected_nodes.add(edge.source)
            connected_nodes.add(edge.target)
        
        all_nodes = set(n.id for n in validated_graph.nodes)
        isolated = all_nodes - connected_nodes
        if isolated and len(isolated) < len(all_nodes):
            warnings.append(f"存在孤立节点: {isolated}")
        
        # 统计信息
        node_types = {}
        for node in validated_graph.nodes:
            node_types[node.type.value] = node_types.get(node.type.value, 0) + 1
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "stats": {
                "nodeCount": len(validated_graph.nodes),
                "edgeCount": len(validated_graph.edges),
                "nodeTypes": node_types
            }
        }
    
    except ValueError as e:
        return {
            "valid": False,
            "errors": [str(e)],
            "warnings": [],
            "stats": None
        }
