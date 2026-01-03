"""
Copilot Schemas - Pydantic 数据模型
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ============================================================================
# Chat
# ============================================================================

class ChatMessageSchema(BaseModel):
    """聊天消息"""
    role: str = Field(..., description="消息角色: user | assistant")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    """Chat API 请求"""
    message: str = Field(..., description="用户消息")
    chat_history: List[ChatMessageSchema] = Field(
        default_factory=list, description="聊天历史"
    )
    model: str = Field(
        default="local-smart",
        description="AI 模型选择: local-smart | local-rules | gpt-4 | claude-3"
    )
    context: Optional[Dict[str, Any]] = Field(None, description="工作流上下文")
    workflow_id: Optional[str] = Field(None, description="工作流线程 ID")


class ChatResponse(BaseModel):
    """Chat API 响应"""
    message: str = Field(..., description="助手回复")
    suggestions: Optional[Dict[str, Any]] = Field(None, description="建议信息")
    diagnostics: Optional[List[Dict[str, Any]]] = Field(None, description="诊断信息")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "根据你的需求，我建议这样的工作流...",
                "suggestions": {
                    "workflows": [...],
                    "nodes": [...],
                },
                "diagnostics": None,
            }
        }


# ============================================================================
# Workflow Suggestion
# ============================================================================

class NodeConfigSchema(BaseModel):
    """节点配置"""
    type: str = Field(..., description="节点类型")
    label: Optional[str] = Field(None, description="节点标签")
    config: Dict[str, Any] = Field(default_factory=dict, description="节点配置")


class EdgeSchema(BaseModel):
    """边连接"""
    from_node: str = Field(..., alias="from", description="源节点 ID")
    to_node: str = Field(..., alias="to", description="目标节点 ID")

    class Config:
        populate_by_name = True


class WorkflowSuggestionSchema(BaseModel):
    """工作流建议"""
    name: str = Field(..., description="工作流名称")
    description: str = Field(..., description="工作流描述")
    nodes: List[NodeConfigSchema] = Field(..., description="节点列表")
    edges: List[Dict[str, str]] = Field(..., description="边列表")
    explanation: str = Field(..., description="推荐说明")


class WorkflowSuggestionRequest(BaseModel):
    """工作流建议请求"""
    description: str = Field(..., description="工作流需求描述")
    complexity: str = Field(
        default="medium",
        description="复杂度: simple | medium | advanced",
    )
    model: str = Field(
        default="local-smart",
        description="AI 模型选择: local-smart | local-rules | gpt-4 | claude-3"
    )


class WorkflowSuggestionResponse(BaseModel):
    """工作流建议响应"""
    workflows: List[WorkflowSuggestionSchema]

    class Config:
        json_schema_extra = {
            "example": {
                "workflows": [
                    {
                        "name": "数据处理工作流",
                        "description": "从 API 获取数据并处理",
                        "nodes": [
                            {"type": "Start", "label": "开始"},
                            {
                                "type": "Tool",
                                "label": "获取数据",
                                "config": {"api": "https://..."},
                            },
                            {
                                "type": "LLM",
                                "label": "处理",
                                "config": {"model": "gpt-4"},
                            },
                            {"type": "End", "label": "结束"},
                        ],
                        "edges": [
                            {"from": "start", "to": "fetch"},
                            {"from": "fetch", "to": "process"},
                            {"from": "process", "to": "end"},
                        ],
                        "explanation": "这个工作流通过 Tool 节点获取数据，然后用 LLM 处理",
                    }
                ]
            }
        }


# ============================================================================
# Node Suggestion
# ============================================================================

class NodeSuggestionSchema(BaseModel):
    """单个节点建议"""
    type: str = Field(..., description="节点类型")
    label: Optional[str] = Field(None, description="节点标签")
    config: Dict[str, Any] = Field(default_factory=dict, description="节点配置")
    explanation: str = Field(..., description="推荐说明")


class NodeSuggestionRequest(BaseModel):
    """节点建议请求"""
    context: str = Field(..., description="下一步操作描述")
    previous_node_type: Optional[str] = Field(None, description="前一个节点类型")
    workflow_description: Optional[str] = Field(None, description="工作流整体描述")
    model: str = Field(
        default="local-smart",
        description="AI 模型选择: local-smart | local-rules | gpt-4 | claude-3"
    )


class NodeSuggestionResponse(BaseModel):
    """节点建议响应"""
    suggestions: List[NodeSuggestionSchema]

    class Config:
        json_schema_extra = {
            "example": {
                "suggestions": [
                    {
                        "type": "Router",
                        "label": "条件路由",
                        "config": {"condition": "result == 'success'"},
                        "explanation": "用于根据前一个节点的结果进行路由",
                    },
                    {
                        "type": "LLM",
                        "label": "进一步处理",
                        "config": {"model": "gpt-4"},
                        "explanation": "用于生成更详细的输出",
                    },
                ]
            }
        }


# ============================================================================
# Workflow Diagnosis
# ============================================================================

class DiagnosticSchema(BaseModel):
    """诊断问题"""
    level: str = Field(..., description="问题级别: error | warning | info")
    type: str = Field(..., description="问题类型")
    description: str = Field(..., description="问题描述")
    location: Optional[Dict[str, Any]] = Field(None, description="问题位置")
    suggestion: str = Field(..., description="解决建议")


class WorkflowDiagnosisRequest(BaseModel):
    """工作流诊断请求"""
    nodes: List[Dict[str, Any]] = Field(..., description="节点列表")
    edges: List[Dict[str, Any]] = Field(..., description="边列表")
    model: str = Field(
        default="local-smart",
        description="AI 模型选择: local-smart | local-rules | gpt-4 | claude-3"
    )


class WorkflowDiagnosisResponse(BaseModel):
    """工作流诊断响应"""
    diagnostics: List[DiagnosticSchema] = Field(..., description="诊断结果")
    score: int = Field(..., description="工作流质量评分 (0-100)")
    summary: str = Field(..., description="诊断摘要")

    class Config:
        json_schema_extra = {
            "example": {
                "diagnostics": [
                    {
                        "level": "warning",
                        "type": "disconnected_node",
                        "description": "节点 process 没有输出连接",
                        "location": {"node_id": "process"},
                        "suggestion": "添加从 process 到 output 的连接",
                    }
                ],
                "score": 75,
                "summary": "工作流缺少一个连接，但整体结构清晰",
            }
        }


# ============================================================================
# Prompt Template Generation
# ============================================================================

class PromptExampleSchema(BaseModel):
    """提示词示例"""
    input: str = Field(..., description="输入示例")
    output: str = Field(..., description="输出示例")


class PromptGenerationRequest(BaseModel):
    """提示词生成请求"""
    task_description: str = Field(..., description="任务描述")
    input_format: str = Field(default="text", description="输入格式")
    output_format: str = Field(default="text", description="输出格式")
    examples: List[PromptExampleSchema] = Field(default_factory=list, description="示例")
    style: str = Field(
        default="structured",
        description="提示词风格: structured | detailed | concise",
    )
    model: str = Field(
        default="local-smart",
        description="AI 模型选择: local-smart | local-rules | gpt-4 | claude-3"
    )


class PromptTemplateSchema(BaseModel):
    """生成的提示词模板"""
    prompt: str = Field(..., description="提示词内容")
    style: str = Field(..., description="风格")
    estimated_tokens: int = Field(..., description="估计 token 数")


class PromptGenerationResponse(BaseModel):
    """提示词生成响应"""
    template: PromptTemplateSchema

    class Config:
        json_schema_extra = {
            "example": {
                "template": {
                    "prompt": """你是一个数据分类专家。

任务: 将输入的文本分类到以下类别之一: 政治、体育、娱乐、其他

输入格式: 单行文本
输出格式: JSON {"text": "原始文本", "category": "...", "confidence": 0.0-1.0}

现在请对以下文本进行分类:
{{INPUT}}""",
                    "style": "structured",
                    "estimated_tokens": 250,
                }
            }
        }
