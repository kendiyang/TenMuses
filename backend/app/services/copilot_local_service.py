"""
Copilot Local Service - 本地化 AI 助手服务

不依赖 OpenAI API key，使用本地 LLM 或模拟 AI 逻辑
前端可以选择不同的模型/模式
"""

import json
import re
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
import logging
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from app.services.llm_client import llm_client

logger = logging.getLogger(__name__)


# ============================================================================
# 模型枚举
# ============================================================================

class AIModel(str, Enum):
    """可用的 AI 模型"""
    # 本地模式（不需要 API key）
    LOCAL_SMART = "local-smart"  # 智能本地模式
    LOCAL_RULES = "local-rules"  # 基于规则的本地模式
    
    # 外部 API（可选）
    GPT4 = "gpt-4"  # OpenAI GPT-4
    CLAUDE3 = "claude-3"  # Anthropic Claude 3


# ============================================================================
# 数据模型
# ============================================================================

class ChatMessage(BaseModel):
    """聊天消息"""
    role: str  # "user" | "assistant"
    content: str


class NodeConfig(BaseModel):
    """节点配置建议"""
    type: str
    label: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)


class WorkflowSuggestion(BaseModel):
    """工作流建议"""
    name: str
    description: str
    nodes: List[NodeConfig]
    edges: List[Dict[str, str]]  # [{"from": "node_1", "to": "node_2"}]
    explanation: str


class NodeSuggestion(BaseModel):
    """单个节点的建议"""
    type: str
    label: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    explanation: str


class Diagnostic(BaseModel):
    """工作流诊断问题"""
    level: str  # "error" | "warning" | "info"
    type: str  # "disconnected_node" | "missing_input" | "infinite_loop" | ...
    description: str
    location: Optional[Dict[str, Any]] = None
    suggestion: str


class WorkflowDiagnosisResult(BaseModel):
    """工作流诊断结果"""
    diagnostics: List[Diagnostic]
    score: int  # 0-100
    summary: str


# ============================================================================
# Copilot Local Service
# ============================================================================

class CopilotLocalService:
    """
    本地化 Copilot 服务
    
    不依赖外部 API，提供以下功能：
    - 智能本地模式：基于内置规则和启发式算法
    - 规则模式：基于预定义规则的简单推荐
    - 易于扩展：可添加外部 LLM 集成
    """

    def __init__(self, model: AIModel = AIModel.LOCAL_SMART):
        """
        初始化 Copilot 服务
        
        Args:
            model: 使用的 AI 模型
        """
        self.model = model
        logger.info(f"Copilot Local Service initialized with model: {model}")

    # ========================================================================
    # Chat API
    # ========================================================================

    async def chat(
        self,
        message: str,
        chat_history: Optional[List[ChatMessage]] = None,
        workflow_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        处理聊天消息
        
        Args:
            message: 用户消息
            chat_history: 聊天历史
            workflow_context: 工作流上下文（节点、边等）
            
        Returns:
            助手回复
        """
        if self.model == AIModel.LOCAL_SMART:
            return await self._chat_smart(message, chat_history, workflow_context)
        elif self.model == AIModel.LOCAL_RULES:
            return await self._chat_rules(message, chat_history)
        else:
            return await self._chat_external(message, chat_history, workflow_context)

    async def _chat_smart(
        self,
        message: str,
        chat_history: Optional[List[ChatMessage]] = None,
        workflow_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """智能本地聊天 - 使用真实 LLM"""
        try:
            # 构建系统提示
            system_prompt = """你是一个工作流设计专家助手，专注于帮助用户设计和优化 LangGraph 工作流。

你的职责包括：
1. 回答工作流设计相关的问题
2. 提供节点和边的配置建议
3. 诊断工作流中的问题
4. 生成适合的提示词模板
5. 解释工作流概念和最佳实践

请用友好、专业的语气回答用户问题。如果用户询问具体的工作流设计，请提供具体的节点类型和配置建议。"""

            # 添加工作流上下文
            if workflow_context:
                context_info = f"\n\n当前工作流上下文：\n{json.dumps(workflow_context, indent=2, ensure_ascii=False)}"
                system_prompt += context_info

            # 构建消息列表
            messages = [SystemMessage(content=system_prompt)]
            
            # 添加聊天历史
            if chat_history:
                for msg in chat_history[-10:]:  # 只保留最近10条消息
                    if msg.role == "user":
                        messages.append(HumanMessage(content=msg.content))
                    else:
                        messages.append(AIMessage(content=msg.content))
            
            # 添加当前用户消息
            messages.append(HumanMessage(content=message))
            
            # 调用 LLM - 使用第一个可用的模型
            logger.info(f"Calling LLM for chat: {message[:50]}...")
            
            # 获取第一个可用模型
            available_models = await llm_client.get_available_models()
            if not available_models:
                raise ValueError("没有可用的 LLM 模型配置")
            
            # 使用第一个支持聊天的模型
            chat_model = None
            for model in available_models:
                # 排除嵌入模型
                if 'embedding' not in model['model_name'].lower():
                    chat_model = model
                    break
            
            if not chat_model:
                raise ValueError("没有找到适合聊天的 LLM 模型")
            
            logger.info(f"Using model: {chat_model['model_name']}")
            
            # 使用 model_id 调用
            response = await llm_client.invoke(messages, model_id=chat_model['model_id'])
            
            return response.content
            
        except ValueError as e:
            # LLM 配置错误
            error_msg = str(e)
            logger.error(f"LLM configuration error: {error_msg}")
            return (
                "❌ Copilot 当前无法使用，LLM 配置未正确设置。\n\n"
                f"错误详情:\n{error_msg}\n\n"
                "请联系管理员配置 LLM 供应商和模型。"
            )
        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            # 回退到简单响应
            return self._get_fallback_response(message)

    def _get_fallback_response(self, message: str) -> str:
        """获取回退响应（当 LLM 调用失败时）"""
        lower_msg = message.lower()
        
        if any(word in lower_msg for word in ["workflow", "工作流", "help", "帮助"]):
            return (
                "我可以帮你设计和优化工作流。\n\n"
                "你可以问我：\n"
                "1. 建议一个工作流 - 我会生成工作流建议\n"
                "2. 下一步应该是什么节点 - 我会推荐适合的节点\n"
                "3. 这个工作流有什么问题 - 我会进行诊断\n"
                "4. 生成提示词 - 我会创建对应的提示词\n\n"
                "请告诉我你的需求，我会尽力帮助！"
            )
        elif any(word in lower_msg for word in ["rag", "document", "search", "文档", "搜索"]):
            return (
                "对于 RAG（检索增强生成）工作流，我建议：\n"
                "1. 文档输入节点：加载和处理文档\n"
                "2. 向量化节点：将文本转换为向量\n"
                "3. 检索节点：根据查询搜索相关文档\n"
                "4. LLM 节点：生成基于检索结果的回复\n"
                "5. 输出节点：返回最终结果\n\n"
                "这个工作流很适合处理大量文档数据。"
            )
        else:
            return (
                f"我理解你的需求：{message}\n\n"
                "我可以帮你：\n"
                "• 生成工作流建议\n"
                "• 推荐下一个节点\n"
                "• 诊断工作流问题\n"
                "• 生成提示词\n\n"
                "请具体告诉我你想做什么。"
            )

    async def _chat_rules(
        self,
        message: str,
        chat_history: Optional[List[ChatMessage]] = None,
    ) -> str:
        """基于规则的聊天 - 回退模式"""
        return self._get_fallback_response(message)

    async def _chat_external(
        self,
        message: str,
        chat_history: Optional[List[ChatMessage]] = None,
        workflow_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """使用外部 LLM 的聊天 - 与 smart 模式相同"""
        return await self._chat_smart(message, chat_history, workflow_context)

    # ========================================================================
    # Workflow Suggestion API
    # ========================================================================

    async def suggest_workflows(
        self,
        description: str,
        complexity: str = "medium",
    ) -> List[WorkflowSuggestion]:
        """
        生成工作流建议
        
        Args:
            description: 工作流需求描述
            complexity: 复杂度 (simple | medium | advanced)
            
        Returns:
            工作流建议列表
        """
        if self.model == AIModel.LOCAL_SMART:
            return await self._suggest_workflows_smart(description, complexity)
        else:
            return await self._suggest_workflows_rules(description, complexity)

    async def _suggest_workflows_smart(
        self,
        description: str,
        complexity: str = "medium",
    ) -> List[WorkflowSuggestion]:
        """智能工作流建议 - 使用真实 LLM"""
        try:
            # 构建提示词
            prompt = f"""作为工作流设计专家，请为以下需求设计一个 LangGraph 工作流：

需求描述：{description}
复杂度级别：{complexity}

请生成 1-2 个工作流建议，每个建议包含：
1. name: 工作流名称
2. description: 简短描述
3. nodes: 节点列表，每个节点包含 type（类型）、label（标签）、config（配置）
4. edges: 边列表，格式为 {{"from": "node_id", "to": "node_id"}}
5. explanation: 详细说明

常见节点类型：Start, End, LLM, Tool, Condition, Input, Output

请以 JSON 格式返回，格式如下：
```json
{{
  "workflows": [
    {{
      "name": "工作流名称",
      "description": "简短描述",
      "nodes": [
        {{"type": "Start", "label": "开始", "config": {{}}}},
        {{"type": "Tool", "label": "处理", "config": {{"action": "process"}}}},
        {{"type": "End", "label": "结束", "config": {{}}}}
      ],
      "edges": [
        {{"from": "start", "to": "process"}},
        {{"from": "process", "to": "end"}}
      ],
      "explanation": "详细说明"
    }}
  ]
}}
```"""

            messages = [
                SystemMessage(content="你是一个 LangGraph 工作流设计专家。请严格按照 JSON 格式返回结果。"),
                HumanMessage(content=prompt)
            ]
            
            # 获取可用的聊天模型
            available_models = await llm_client.get_available_models()
            # 过滤掉 embedding 模型
            chat_models = [m for m in available_models if 'embed' not in m['model_name'].lower()]
            if not chat_models:
                logger.warning("No chat models available, using fallback")
                return self._get_fallback_workflows(description)
            
            chat_model = chat_models[0]
            logger.info(f"Using model: {chat_model['model_name']} (ID: {chat_model['model_id']})")
            
            # 调用 LLM
            logger.info(f"Calling LLM for workflow suggestion: {description[:50]}...")
            response = await llm_client.invoke(messages, model_id=chat_model['model_id'])
            
            # 解析 JSON 响应
            content = response.content
            # 提取 JSON 部分（处理 markdown 代码块）
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接解析
                json_str = content
            
            result = json.loads(json_str)
            workflows_data = result.get("workflows", [])
            
            # 转换为 WorkflowSuggestion 对象
            suggestions = []
            for wf_data in workflows_data:
                suggestions.append(
                    WorkflowSuggestion(
                        name=wf_data["name"],
                        description=wf_data["description"],
                        nodes=[NodeConfig(**node) for node in wf_data["nodes"]],
                        edges=wf_data["edges"],
                        explanation=wf_data["explanation"]
                    )
                )
            
            return suggestions if suggestions else self._get_fallback_workflows(description)
            
        except ValueError as e:
            # LLM 配置错误
            error_msg = str(e)
            logger.error(f"LLM configuration error: {error_msg}")
            # 返回空列表，让调用者处理
            return []
        except Exception as e:
            logger.error(f"LLM workflow suggestion error: {e}")
            # 回退到规则模式
            return self._get_fallback_workflows(description)
    
    def _get_fallback_workflows(self, description: str) -> List[WorkflowSuggestion]:
        """获取回退工作流建议"""
        lower_desc = description.lower()
        suggestions = []

        # RAG 工作流
        if any(word in lower_desc for word in ["rag", "document", "search", "文档", "检索"]):
            suggestions.append(
                WorkflowSuggestion(
                    name="RAG 文档处理工作流",
                    description="从文档中检索信息并使用 LLM 生成回复",
                    nodes=[
                        NodeConfig(type="Start", label="开始"),
                        NodeConfig(type="Tool", label="文档加载", config={"action": "load_documents"}),
                        NodeConfig(type="Tool", label="向量化", config={"action": "vectorize"}),
                        NodeConfig(type="Tool", label="检索", config={"action": "retrieve"}),
                        NodeConfig(type="LLM", label="生成回复", config={"model": "gpt-4"}),
                        NodeConfig(type="End", label="结束"),
                    ],
                    edges=[
                        {"from": "start", "to": "load"},
                        {"from": "load", "to": "vectorize"},
                        {"from": "vectorize", "to": "retrieve"},
                        {"from": "retrieve", "to": "generate"},
                        {"from": "generate", "to": "end"},
                    ],
                    explanation="这个工作流处理文档数据：先加载和向量化文档，根据查询检索相关部分，最后用 LLM 生成答案。",
                )
            )

        # 如果没有特定匹配，返回通用建议
        if not suggestions:
            suggestions.append(
                WorkflowSuggestion(
                    name="通用工作流",
                    description="一个简单的通用工作流模板",
                    nodes=[
                        NodeConfig(type="Start", label="开始"),
                        NodeConfig(type="Tool", label="处理"),
                        NodeConfig(type="End", label="结束"),
                    ],
                    edges=[
                        {"from": "start", "to": "process"},
                        {"from": "process", "to": "end"},
                    ],
                    explanation="一个基础工作流，可根据需要扩展。",
                )
            )

        return suggestions

    async def _suggest_workflows_rules(
        self,
        description: str,
        complexity: str = "medium",
    ) -> List[WorkflowSuggestion]:
        """基于规则的工作流建议"""
        # 简化版：只返回最常见的几个工作流
        return [
            WorkflowSuggestion(
                name="基础工作流",
                description="一个简单的三步工作流",
                nodes=[
                    NodeConfig(type="Start", label="开始"),
                    NodeConfig(type="Tool", label="处理"),
                    NodeConfig(type="End", label="结束"),
                ],
                edges=[
                    {"from": "start", "to": "process"},
                    {"from": "process", "to": "end"},
                ],
                explanation="基础工作流模板。",
            )
        ]

    # ========================================================================
    # Node Suggestion API
    # ========================================================================

    async def suggest_nodes(
        self,
        context: str,
        previous_node_type: Optional[str] = None,
        workflow_description: Optional[str] = None,
    ) -> List[NodeSuggestion]:
        """
        推荐下一个节点
        
        Args:
            context: 下一步操作描述
            previous_node_type: 前一个节点类型
            workflow_description: 整体工作流描述
            
        Returns:
            节点建议列表
        """
        if self.model == AIModel.LOCAL_SMART:
            return await self._suggest_nodes_smart(context, previous_node_type)
        else:
            return await self._suggest_nodes_rules(previous_node_type)

    async def _suggest_nodes_smart(
        self,
        context: str,
        previous_node_type: Optional[str] = None,
    ) -> List[NodeSuggestion]:
        """智能节点推荐"""
        lower_context = context.lower()
        suggestions = []

        # 根据上下文推荐节点
        if any(word in lower_context for word in ["process", "llm", "ai", "生成", "处理", "智能"]):
            suggestions.append(
                NodeSuggestion(
                    type="LLM",
                    label="LLM 处理",
                    config={"model": "gpt-4", "temperature": 0.7},
                    explanation="使用大语言模型进行智能处理和生成。",
                )
            )

        if any(word in lower_context for word in ["if", "condition", "check", "条件", "判断", "检查"]):
            suggestions.append(
                NodeSuggestion(
                    type="Router",
                    label="条件路由",
                    config={"condition": "result == 'success'"},
                    explanation="根据条件选择不同的执行路径。",
                )
            )

        if any(word in lower_context for word in ["api", "call", "fetch", "tool", "请求", "调用"]):
            suggestions.append(
                NodeSuggestion(
                    type="Tool",
                    label="工具调用",
                    config={"action": "call_api"},
                    explanation="调用外部工具或 API。",
                )
            )

        if any(word in lower_context for word in ["database", "sql", "store", "save", "数据库", "存储"]):
            suggestions.append(
                NodeSuggestion(
                    type="Database",
                    label="数据库操作",
                    config={"action": "save", "table": "data"},
                    explanation="将结果保存到数据库。",
                )
            )

        # 如果没有特定匹配，返回通用建议
        if not suggestions:
            suggestions = [
                NodeSuggestion(
                    type="Tool",
                    label="通用处理",
                    config={},
                    explanation="处理当前步骤的通用节点。",
                ),
                NodeSuggestion(
                    type="LLM",
                    label="AI 助手",
                    config={"model": "gpt-4"},
                    explanation="使用 AI 进行智能处理。",
                ),
            ]

        return suggestions

    async def _suggest_nodes_rules(
        self,
        previous_node_type: Optional[str] = None,
    ) -> List[NodeSuggestion]:
        """基于规则的节点推荐"""
        # 简化版：根据前一个节点类型推荐
        if previous_node_type == "Start":
            return [
                NodeSuggestion(
                    type="Tool",
                    label="处理",
                    config={},
                    explanation="开始后通常是处理节点。",
                ),
                NodeSuggestion(
                    type="LLM",
                    label="AI 处理",
                    config={"model": "gpt-4"},
                    explanation="或者使用 AI 进行处理。",
                ),
            ]
        else:
            return [
                NodeSuggestion(
                    type="End",
                    label="结束",
                    config={},
                    explanation="流程可以结束。",
                )
            ]

    # ========================================================================
    # Workflow Diagnosis API
    # ========================================================================

    async def diagnose_workflow(self, workflow: Dict[str, Any]) -> WorkflowDiagnosisResult:
        """
        诊断工作流
        
        Args:
            workflow: 工作流对象 {"nodes": [...], "edges": [...]}
            
        Returns:
            诊断结果
        """
        if self.model == AIModel.LOCAL_SMART:
            return await self._diagnose_workflow_smart(workflow)
        else:
            return await self._diagnose_workflow_rules(workflow)

    async def _diagnose_workflow_smart(
        self, workflow: Dict[str, Any]
    ) -> WorkflowDiagnosisResult:
        """智能工作流诊断"""
        diagnostics = []
        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])

        # 检查节点连接
        node_ids = {n.get("id") for n in nodes if n.get("id")}
        for node in nodes:
            node_id = node.get("id")
            has_output = any(e.get("from") == node_id for e in edges)
            has_input = any(e.get("to") == node_id for e in edges)

            if node.get("type") not in ["Start", "End"] and not (has_input and has_output):
                if not has_output and node.get("type") != "End":
                    diagnostics.append(
                        Diagnostic(
                            level="warning",
                            type="disconnected_node",
                            description=f"节点 '{node.get('label', node_id)}' 没有输出连接",
                            location={"node_id": node_id},
                            suggestion="添加连接到此节点的输出",
                        )
                    )

        # 检查无效的边
        for edge in edges:
            from_node = edge.get("from")
            to_node = edge.get("to")
            if from_node not in node_ids or to_node not in node_ids:
                diagnostics.append(
                    Diagnostic(
                        level="error",
                        type="invalid_edge",
                        description=f"边 {from_node} -> {to_node} 引用了不存在的节点",
                        location={"edge": edge},
                        suggestion="检查边的源和目标节点 ID",
                    )
                )

        # 计算工作流分数
        max_issues = max(1, len(nodes))
        score = max(0, 100 - (len(diagnostics) * (100 // max_issues)))

        summary = f"检查了 {len(nodes)} 个节点和 {len(edges)} 条边。" if not diagnostics else f"发现 {len(diagnostics)} 个问题。"

        return WorkflowDiagnosisResult(
            diagnostics=diagnostics,
            score=score,
            summary=summary,
        )

    async def _diagnose_workflow_rules(
        self, workflow: Dict[str, Any]
    ) -> WorkflowDiagnosisResult:
        """基于规则的工作流诊断"""
        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])

        summary = f"工作流包含 {len(nodes)} 个节点和 {len(edges)} 条边。"

        return WorkflowDiagnosisResult(
            diagnostics=[],
            score=80,
            summary=summary,
        )

    # ========================================================================
    # Prompt Generation API
    # ========================================================================

    async def generate_prompt(
        self,
        task_description: str,
        input_format: str = "text",
        output_format: str = "text",
        style: str = "structured",
    ) -> PromptTemplate:
        """
        生成提示词模板
        
        Args:
            task_description: 任务描述
            input_format: 输入格式
            output_format: 输出格式
            style: 提示词风格 (structured | detailed | concise)
            
        Returns:
            生成的提示词模板
        """
        if self.model == AIModel.LOCAL_SMART:
            return await self._generate_prompt_smart(task_description, style)
        else:
            return await self._generate_prompt_rules(task_description)

    async def _generate_prompt_smart(
        self, task_description: str, style: str = "structured"
    ) -> PromptTemplate:
        """智能提示词生成"""
        if style == "structured":
            prompt = f"""## 任务
{task_description}

## 要求
1. 详细理解任务需求
2. 按步骤完成任务
3. 提供清晰的输出

## 步骤
- 分析输入
- 执行处理
- 验证结果
- 输出答案"""
        elif style == "detailed":
            prompt = f"""你是一个专业的 AI 助手。你的任务是：

{task_description}

请：
1. 仔细理解并分析这个任务
2. 考虑所有相关的上下文和细节
3. 提供详细、全面的解答
4. 解释你的思考过程
5. 确保答案的准确性和完整性"""
        else:  # concise
            prompt = f"""Task: {task_description}

Provide a concise, direct answer."""

        estimated_tokens = len(prompt.split()) * 1.3  # 粗估 token 数

        return PromptTemplate(
            prompt=prompt,
            style=style,
            estimated_tokens=int(estimated_tokens),
        )

    async def _generate_prompt_rules(self, task_description: str) -> PromptTemplate:
        """基于规则的提示词生成"""
        prompt = f"Task: {task_description}\n\nPlease complete this task step by step."

        return PromptTemplate(
            prompt=prompt,
            style="structured",
            estimated_tokens=len(prompt.split()),
        )
