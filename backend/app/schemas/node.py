"""
节点类型定义和Schema - 支持灵活的工作流配置

这个模块定义了所有支持的节点类型和它们的配置Schema，
使得前端可以通过JSON描述任意的工作流图，后端动态编译成LangGraph。
"""

from typing import Any, Dict, List, Optional, Literal, Union
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================================
# 节点类型枚举
# ============================================================================

class NodeType(str, Enum):
    """支持的节点类型"""
    # 基础节点
    LLM = "llm"
    TOOL = "tool"
    ROUTER = "router"
    MAP = "map"
    
    # Phase 1 兼容节点
    RESEARCH = "research"
    WRITER = "writer"
    REVIEWER = "reviewer"
    
    # 输入/输出节点
    INPUT = "input"
    OUTPUT = "output"


class EdgeType(str, Enum):
    """边的类型"""
    NORMAL = "normal"  # 普通边
    CONDITIONAL = "conditional"  # 条件边


# ============================================================================
# LLM 节点配置
# ============================================================================

class LLMNodeConfig(BaseModel):
    """LLM节点运行时配置（工作流节点使用）"""
    provider: Literal["openai", "anthropic"] = "openai"
    model: str = "gpt-4-turbo-preview"
    temperature: float = Field(default=0.7, ge=0, le=1)
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    
    # RAG 配置
    enable_rag: bool = Field(default=False, description="是否启用知识库检索")
    knowledge_documents: List[str] = Field(default_factory=list, description="知识库文档ID列表")
    rag_mode: Literal["document", "chunk"] = Field(default="chunk", description="检索模式: 文档级或分片级")
    rag_top_k: int = Field(default=5, ge=1, le=20, description="检索结果数量")
    rag_min_score: float = Field(default=0.5, ge=0.0, le=1.0, description="最小相关性阈值")
    
    class Config:
        json_schema_extra = {
            "example": {
                "provider": "openai",
                "model": "gpt-4-turbo-preview",
                "temperature": 0.7,
                "max_tokens": 2000,
                "system_prompt": "You are a helpful assistant.",
                "enable_rag": True,
                "knowledge_documents": ["doc-1", "doc-2"],
                "rag_mode": "chunk",
                "rag_top_k": 5,
                "rag_min_score": 0.5
            }
        }


# ============================================================================
# Tool 节点配置
# ============================================================================

class ToolConfig(BaseModel):
    """Tool节点配置"""
    tool_name: str = Field(description="工具名称，需在工具库中注册")
    tool_input_schema: Dict[str, Any] = Field(default_factory=dict, description="工具输入schema")
    required_inputs: List[str] = Field(default_factory=list, description="必需的输入字段")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tool_name": "web_search",
                "tool_input_schema": {
                    "query": {"type": "string", "description": "搜索查询"}
                },
                "required_inputs": ["query"]
            }
        }


# ============================================================================
# Router 节点配置 - 条件路由
# ============================================================================

class RouterCondition(BaseModel):
    """单个路由条件"""
    target_node_id: str = Field(description="目标节点ID")
    condition: str = Field(description="条件表达式，如'output.score > 0.8'或'action == \"approve\"'")
    
    class Config:
        json_schema_extra = {
            "example": {
                "target_node_id": "node-2",
                "condition": "output.score > 0.8"
            }
        }


class RouterConfig(BaseModel):
    """Router节点配置 - 基于LLM或字段值的动态路由"""
    router_type: Literal["llm", "field"] = "llm"
    
    # 对于 LLM router
    llm_config: Optional[LLMNodeConfig] = None
    routing_prompt: Optional[str] = None  # 指导LLM如何路由
    
    # 对于 field router - 基于前面节点输出字段的值
    source_field: Optional[str] = None  # 用于路由决策的字段，如"decision"
    
    conditions: List[RouterCondition] = Field(default_factory=list, description="路由条件列表")
    default_target: Optional[str] = None  # 默认路由目标
    
    class Config:
        json_schema_extra = {
            "example": {
                "router_type": "llm",
                "llm_config": {
                    "provider": "openai",
                    "model": "gpt-4",
                    "temperature": 0.7
                },
                "routing_prompt": "Decide which node to route to based on the input.",
                "conditions": [
                    {
                        "target_node_id": "node-approve",
                        "condition": "decision == 'approve'"
                    },
                    {
                        "target_node_id": "node-reject",
                        "condition": "decision == 'reject'"
                    }
                ],
                "default_target": "node-review"
            }
        }


# ============================================================================
# Map 节点配置 - Map-Reduce 并行执行
# ============================================================================

class MapConfig(BaseModel):
    """Map节点配置 - 对列表项并行执行相同操作"""
    items_source: str = Field(description="数据源，如'input.items'")
    item_executor: Dict[str, Any] = Field(description="针对单个item的执行器配置")
    parallel_count: int = Field(default=5, ge=1, description="并行度")
    reduce_type: Literal["concat", "aggregate", "custom"] = "concat"
    
    class Config:
        json_schema_extra = {
            "example": {
                "items_source": "input.articles",
                "item_executor": {
                    "type": "llm",
                    "config": {
                        "model": "gpt-4",
                        "prompt": "Summarize this article"
                    }
                },
                "parallel_count": 5,
                "reduce_type": "concat"
            }
        }


# ============================================================================
# 通用节点数据
# ============================================================================

class NodeData(BaseModel):
    """节点数据 - 前端发送的节点信息"""
    label: str = Field(description="节点显示名称")
    description: Optional[str] = None
    
    # 节点执行配置
    llm_config: Optional[LLMNodeConfig] = None
    tool_config: Optional[ToolConfig] = None
    router_config: Optional[RouterConfig] = None
    map_config: Optional[MapConfig] = None
    
    # HITL 配置
    interrupt_before: bool = Field(default=False, description="是否在执行前中断并等待确认")
    interrupt_after: bool = Field(default=False, description="是否在执行后中断等待审查")
    
    # 额外配置
    cache_result: bool = Field(default=False, description="是否缓存结果")
    timeout: Optional[int] = Field(default=None, description="超时时间(秒)")
    retry_count: int = Field(default=0, description="失败重试次数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "label": "AI分析",
                "description": "使用GPT-4分析内容",
                "llm_config": {
                    "provider": "openai",
                    "model": "gpt-4-turbo-preview",
                    "temperature": 0.7
                },
                "interrupt_before": False,
                "cache_result": True
            }
        }


# ============================================================================
# 边定义
# ============================================================================

class EdgeData(BaseModel):
    """边的数据"""
    # 对于条件边
    condition: Optional[str] = None  # 条件表达式
    condition_type: Optional[Literal["llm", "field", "always"]] = "always"
    
    class Config:
        json_schema_extra = {
            "example": {
                "condition": "output.approved == true",
                "condition_type": "field"
            }
        }


class NodePosition(BaseModel):
    """节点位置"""
    x: float
    y: float


class Edge(BaseModel):
    """边定义"""
    id: str
    source: str = Field(description="源节点ID")
    target: str = Field(description="目标节点ID")
    type: EdgeType = EdgeType.NORMAL
    data: Optional[EdgeData] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "edge-1-2",
                "source": "node-1",
                "target": "node-2",
                "type": "normal"
            }
        }


class Node(BaseModel):
    """节点定义 - 前端发送的完整节点"""
    id: str
    type: NodeType
    position: NodePosition
    data: NodeData
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "node-1",
                "type": "llm",
                "position": {"x": 100, "y": 100},
                "data": {
                    "label": "AI分析",
                    "llm_config": {
                        "provider": "openai",
                        "model": "gpt-4-turbo-preview",
                        "temperature": 0.7
                    }
                }
            }
        }


# ============================================================================
# 工作流图定义
# ============================================================================

class WorkflowGraph(BaseModel):
    """工作流图定义 - 从canvas_json提取"""
    nodes: List[Node] = Field(description="节点列表")
    edges: List[Edge] = Field(description="边列表")
    viewport: Optional[Dict[str, float]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "nodes": [
                    {
                        "id": "node-1",
                        "type": "llm",
                        "position": {"x": 100, "y": 100},
                        "data": {
                            "label": "Research",
                            "llm_config": {
                                "model": "gpt-4-turbo-preview",
                                "provider": "openai"
                            }
                        }
                    },
                    {
                        "id": "node-2",
                        "type": "llm",
                        "position": {"x": 300, "y": 100},
                        "data": {
                            "label": "Writer",
                            "llm_config": {
                                "model": "gpt-4-turbo-preview",
                                "provider": "openai"
                            }
                        }
                    }
                ],
                "edges": [
                    {
                        "id": "edge-1-2",
                        "source": "node-1",
                        "target": "node-2",
                        "type": "normal"
                    }
                ]
            }
        }


# ============================================================================
# 验证工具
# ============================================================================

def validate_graph(graph_data: Union[Dict, WorkflowGraph]) -> WorkflowGraph:
    """验证并规范化工作流图"""
    if isinstance(graph_data, dict):
        graph_data = WorkflowGraph(**graph_data)
    
    # 验证节点ID唯一性
    node_ids = [n.id for n in graph_data.nodes]
    if len(node_ids) != len(set(node_ids)):
        raise ValueError("节点ID必须唯一")
    
    # 验证边的源和目标节点存在
    node_id_set = set(node_ids)
    for edge in graph_data.edges:
        if edge.source not in node_id_set:
            raise ValueError(f"边 {edge.id} 的源节点 {edge.source} 不存在")
        if edge.target not in node_id_set:
            raise ValueError(f"边 {edge.id} 的目标节点 {edge.target} 不存在")
    
    # 检测循环依赖 (新增)
    if _has_cycle(graph_data):
        raise ValueError("工作流存在循环依赖。请检查节点之间的连接关系。")
    
    # 验证没有孤立节点（可选，先不强制）
    # connected_nodes = set()
    # for edge in graph_data.edges:
    #     connected_nodes.add(edge.source)
    #     connected_nodes.add(edge.target)
    # isolated = node_id_set - connected_nodes
    # if isolated:
    #     warnings.warn(f"孤立节点: {isolated}")
    
    return graph_data


def _has_cycle(graph: WorkflowGraph) -> bool:
    """
    检测有向图中是否存在循环依赖
    
    使用DFS（深度优先搜索）算法：
    - WHITE (0): 未访问
    - GRAY (1): 正在访问（在当前路径中）
    - BLACK (2): 已完成访问
    
    如果访问过程中遇到GRAY节点，说明存在循环。
    """
    from enum import IntEnum
    
    class Color(IntEnum):
        WHITE = 0
        GRAY = 1
        BLACK = 2
    
    # 构建邻接表
    adj_list = {node.id: [] for node in graph.nodes}
    for edge in graph.edges:
        adj_list[edge.source].append(edge.target)
    
    # 初始化颜色
    color = {node_id: Color.WHITE for node_id in adj_list}
    
    def dfs_visit(node_id: str) -> bool:
        """DFS访问，返回True表示发现循环"""
        color[node_id] = Color.GRAY
        
        # 访问所有相邻节点
        for neighbor in adj_list[node_id]:
            if color[neighbor] == Color.GRAY:
                # 发现回边，说明存在循环
                return True
            elif color[neighbor] == Color.WHITE:
                # 继续DFS
                if dfs_visit(neighbor):
                    return True
        
        color[node_id] = Color.BLACK
        return False
    
    # 对所有节点进行DFS
    for node_id in adj_list:
        if color[node_id] == Color.WHITE:
            if dfs_visit(node_id):
                return True
    
    return False

# ============================================================================
# Backward Compatibility Aliases
# ============================================================================
# Legacy name for LLMNodeConfig - kept for backward compatibility with existing code
LLMConfig = LLMNodeConfig