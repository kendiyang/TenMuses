"""
Copilot Service - AI 助手服务

提供工作流编辑时的 AI 支持：
- 聊天对话
- 工作流建议
- 节点建议
- 工作流诊断
- 提示词生成

改进：使用新的 LLMClient 架构，支持多个 LLM 供应商
"""

import json
import re
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logging
from langchain_core.messages import HumanMessage, SystemMessage

from app.services.llm_client import llm_client

logger = logging.getLogger(__name__)


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


class PromptTemplate(BaseModel):
    """生成的提示词模板"""
    prompt: str
    style: str  # "structured" | "detailed" | "concise"
    estimated_tokens: int


# ============================================================================
# Copilot Service
# ============================================================================

class CopilotService:
    """
    AI Copilot 服务
    
    使用新的 LLMClient 为工作流编辑提供智能建议和支持
    
    改进：
    - 支持多个 LLM 供应商（OpenAI、Anthropic 等）
    - 使用统一的 LLMClient 接口
    - 自动故障转移到环境变量配置
    - 支持模型 ID 或 provider/model 名称
    """

    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4-turbo-preview",
        model_id: Optional[str] = None,
    ):
        """
        初始化 Copilot 服务
        
        Args:
            provider: LLM 供应商 ("openai" | "anthropic")
            model: 模型名称 (例如 "gpt-4-turbo-preview")
            model_id: 模型 UUID (可选，优先使用)
        """
        self.provider = provider
        self.model = model
        self.model_id = model_id
        self.system_prompt = self._build_system_prompt()
        logger.info(
            f"Copilot service initialized with provider={provider}, "
            f"model={model}, model_id={model_id}"
        )

    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是 TenMuses 工作流编辑助手（Copilot）。

你的职责是帮助用户设计和优化工作流。你对以下方面有专业知识：

1. **工作流设计**: 了解 TenMuses 中的各种节点类型（LLM、Tool、Router、Interrupt、RAG 等）
2. **最佳实践**: 提供工作流设计的最佳实践和常见模式
3. **问题诊断**: 识别工作流中的问题（断开的连接、缺失的输入、死循环等）
4. **节点建议**: 根据上下文建议适合的节点
5. **提示词生成**: 为 LLM 节点生成高质量的提示词

回复风格：
- 保持简洁、专业、有用
- 提供具体的建议和例子
- 使用清晰的结构和格式
- 如果需要生成 JSON 或代码，使用代码块

工作流节点类型：
- LLM: 调用大语言模型
- Tool: 调用工具函数
- Router: 条件路由
- Interrupt: 人工干预
- RAG: 检索增强生成
- Start: 起始节点
- End: 结束节点"""

    # ========================================================================
    # Chat API
    # ========================================================================

    async def chat(
        self,
        message: str,
        chat_history: List[ChatMessage] = None,
        workflow_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        处理聊天消息
        
        Args:
            message: 用户消息
            chat_history: 聊天历史
            workflow_context: 工作流上下文信息
            
        Returns:
            AI 的回复
        """
        if chat_history is None:
            chat_history = []

        # 构造系统提示词
        system_content = self.system_prompt
        if workflow_context:
            system_content += self._build_workflow_context(workflow_context)

        # 构造消息列表 (LangChain format)
        messages = [SystemMessage(content=system_content)]
        
        # 添加聊天历史
        for msg in chat_history:
            if msg.role == "user":
                messages.append(HumanMessage(content=msg.content))
            else:
                from langchain_core.messages import AIMessage
                messages.append(AIMessage(content=msg.content))
        
        # 添加当前消息
        messages.append(HumanMessage(content=message))

        try:
            # 使用新的 LLMClient 调用
            response = await llm_client.invoke(
                messages,
                model_id=self.model_id if self.model_id else None,
                provider=self.provider if not self.model_id else None,
                model=self.model if not self.model_id else None,
                temperature=0.7,
                max_tokens=1000,
            )
            
            result = response.content if hasattr(response, 'content') else str(response)
            logger.debug(f"Chat response generated successfully")
            return result
            
        except Exception as e:
            logger.error(f"Copilot chat error: {e}", exc_info=True)
            raise

    # ========================================================================
    # Workflow Suggestion
    # ========================================================================

    async def suggest_workflows(
        self,
        description: str,
        complexity: str = "medium",
    ) -> List[WorkflowSuggestion]:
        """
        建议工作流模板
        
        Args:
            description: 工作流需求描述
            complexity: 复杂度 (simple | medium | advanced)
            
        Returns:
            工作流建议列表
        """
        prompt = f"""根据以下需求，建议 3 个工作流模板：

需求描述: {description}
复杂度: {complexity}

请返回有效的 JSON 格式（用 ```json``` 包围）：
{{
  "workflows": [
    {{
      "name": "工作流名称",
      "description": "简短描述",
      "nodes": [
        {{"type": "Start", "label": "开始"}},
        {{"type": "LLM", "label": "处理", "config": {{"model": "gpt-4"}}}},
        {{"type": "End", "label": "结束"}}
      ],
      "edges": [
        {{"from": "start", "to": "process"}},
        {{"from": "process", "to": "end"}}
      ],
      "explanation": "为什么推荐这个工作流"
    }}
  ]
}}

确保：
1. 返回有效的 JSON
2. 每个工作流包含 3-5 个节点
3. 节点和边的连接正确
4. 有清晰的解释说明"""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt),
        ]

        try:
            # 使用新的 LLMClient 调用
            response = await llm_client.invoke(
                messages,
                model_id=self.model_id if self.model_id else None,
                provider=self.provider if not self.model_id else None,
                model=self.model if not self.model_id else None,
                temperature=0.7,
                max_tokens=2000,
            )
            content = response.content if hasattr(response, 'content') else str(response)

            # 解析 JSON
            workflows = self._parse_json_response(content, "workflows")
            if workflows:
                return [
                    WorkflowSuggestion(**w) for w in workflows if self._validate_workflow(w)
                ]
            return []
        except Exception as e:
            logger.error(f"Failed to suggest workflows: {e}", exc_info=True)
            return []

    # ========================================================================
    # Node Suggestion
    # ========================================================================

    async def suggest_nodes(
        self,
        context: str,
        previous_node_type: Optional[str] = None,
        workflow_description: Optional[str] = None,
    ) -> List[NodeSuggestion]:
        """
        建议工作流中的下一个节点
        
        Args:
            context: 用户描述的下一步操作
            previous_node_type: 前一个节点的类型
            workflow_description: 工作流整体描述
            
        Returns:
            节点建议列表
        """
        prompt = f"""根据以下上下文，建议 2-3 个适合的工作流节点：

{f'前一个节点类型: {previous_node_type}' if previous_node_type else ''}
下一步操作: {context}
{f'工作流描述: {workflow_description}' if workflow_description else ''}

请返回有效的 JSON 格式（用 ```json``` 包围）：
{{
  "suggestions": [
    {{
      "type": "节点类型",
      "label": "节点标签",
      "config": {{"key": "value"}},
      "explanation": "为什么推荐这个节点"
    }}
  ]
}}

可用的节点类型: LLM, Tool, Router, Interrupt, RAG"""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt),
        ]

        try:
            # 使用新的 LLMClient 调用
            response = await llm_client.invoke(
                messages,
                model_id=self.model_id if self.model_id else None,
                provider=self.provider if not self.model_id else None,
                model=self.model if not self.model_id else None,
                temperature=0.7,
                max_tokens=1000,
            )
            content = response.content if hasattr(response, 'content') else str(response)

            # 解析 JSON
            suggestions = self._parse_json_response(content, "suggestions")
            if suggestions:
                return [NodeSuggestion(**s) for s in suggestions]
            return []
        except Exception as e:
            logger.error(f"Failed to suggest nodes: {e}", exc_info=True)
            return []

    # ========================================================================
    # Workflow Diagnosis
    # ========================================================================

    async def diagnose_workflow(self, workflow: Dict[str, Any]) -> WorkflowDiagnosisResult:
        """
        诊断工作流问题
        
        Args:
            workflow: 工作流对象 {nodes: [...], edges: [...]}
            
        Returns:
            诊断结果
        """
        prompt = f"""请诊断以下工作流的问题：

工作流: {json.dumps(workflow, indent=2, ensure_ascii=False)}

请返回有效的 JSON 格式（用 ```json``` 包围）：
{{
  "diagnostics": [
    {{
      "level": "error|warning|info",
      "type": "问题类型",
      "description": "问题描述",
      "location": {{"node_id": "xxx"}},
      "suggestion": "解决建议"
    }}
  ],
  "score": 75,
  "summary": "工作流整体评估"
}}

检查以下问题：
1. 是否有未连接的节点
2. 是否有缺失的必需输入
3. 是否有无限循环
4. 节点配置是否完整
5. 错误处理是否充分"""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt),
        ]

        try:
            # 使用新的 LLMClient 调用
            response = await llm_client.invoke(
                messages,
                model_id=self.model_id if self.model_id else None,
                provider=self.provider if not self.model_id else None,
                model=self.model if not self.model_id else None,
                temperature=0.5,
                max_tokens=1500,
            )
            content = response.content if hasattr(response, 'content') else str(response)

            # 解析 JSON
            result_dict = self._parse_json_response_single(content)
            if result_dict:
                diagnostics = [
                    Diagnostic(**d) for d in result_dict.get("diagnostics", [])
                ]
                return WorkflowDiagnosisResult(
                    diagnostics=diagnostics,
                    score=result_dict.get("score", 50),
                    summary=result_dict.get("summary", ""),
                )
            return WorkflowDiagnosisResult(diagnostics=[], score=0, summary="")
        except Exception as e:
            logger.error(f"Failed to diagnose workflow: {e}", exc_info=True)
            return WorkflowDiagnosisResult(diagnostics=[], score=0, summary="诊断失败")

    # ========================================================================
    # Prompt Template Generation
    # ========================================================================

    async def generate_prompt_template(
        self,
        task_description: str,
        input_format: str = "text",
        output_format: str = "text",
        examples: List[Dict[str, str]] = None,
        style: str = "structured",
    ) -> PromptTemplate:
        """
        为 LLM 节点生成提示词模板
        
        Args:
            task_description: 任务描述
            input_format: 输入格式描述
            output_format: 输出格式描述
            examples: 示例列表
            style: 提示词风格 (structured | detailed | concise)
            
        Returns:
            生成的提示词模板
        """
        examples_str = ""
        if examples:
            examples_str = "\n\n示例：\n" + "\n".join(
                [f"输入: {e['input']}\n输出: {e['output']}" for e in examples]
            )

        prompt = f"""根据以下信息生成一个高质量的 LLM 提示词模板：

任务: {task_description}
输入格式: {input_format}
输出格式: {output_format}
风格: {style}
{examples_str}

请生成一个清晰、详细的提示词。使用 {{{{INPUT}}}} 作为输入占位符。

返回格式（用 ```prompt``` 包围）：
```prompt
[你的提示词]
```

确保提示词：
1. 清晰定义任务
2. 提供具体的指导
3. 包含输入/输出格式说明
4. 如果适用，包含示例"""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=prompt),
        ]

        try:
            # 使用新的 LLMClient 调用
            response = await llm_client.invoke(
                messages,
                model_id=self.model_id if self.model_id else None,
                provider=self.provider if not self.model_id else None,
                model=self.model if not self.model_id else None,
                temperature=0.7,
                max_tokens=1500,
            )
            content = response.content if hasattr(response, 'content') else str(response)

            # 解析提示词
            prompt_content = self._extract_code_block(content, "prompt")
            if not prompt_content:
                prompt_content = content  # 如果没有代码块，直接使用内容

            # 估计 token 数
            estimated_tokens = len(prompt_content.split()) * 1.3  # 粗略估计

            return PromptTemplate(
                prompt=prompt_content.strip(),
                style=style,
                estimated_tokens=int(estimated_tokens),
            )
        except Exception as e:
            logger.error(f"Failed to generate prompt template: {e}", exc_info=True)
            raise

    # ========================================================================
    # 辅助方法
    # ========================================================================

    def _build_workflow_context(self, context: Dict[str, Any]) -> str:
        """构建工作流上下文提示"""
        context_str = "\n\n当前工作流上下文："
        if context.get("workflow_description"):
            context_str += f"\n- 描述: {context['workflow_description']}"
        if context.get("nodes"):
            context_str += f"\n- 节点数: {len(context['nodes'])}"
        if context.get("edges"):
            context_str += f"\n- 连接数: {len(context['edges'])}"
        return context_str

    def _parse_json_response(self, content: str, key: str) -> Optional[List]:
        """
        从响应中解析 JSON 数组
        
        Args:
            content: 响应内容
            key: 要提取的键
            
        Returns:
            解析的列表，如果解析失败返回 None
        """
        try:
            # 尝试从 markdown 代码块中提取 JSON
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content

            # 解析 JSON
            data = json.loads(json_str)
            return data.get(key, [])
        except (json.JSONDecodeError, IndexError) as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return None

    def _parse_json_response_single(self, content: str) -> Optional[Dict]:
        """
        从响应中解析单个 JSON 对象
        
        Args:
            content: 响应内容
            
        Returns:
            解析的字典，如果解析失败返回 None
        """
        try:
            # 尝试从 markdown 代码块中提取 JSON
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content

            # 解析 JSON
            return json.loads(json_str)
        except (json.JSONDecodeError, IndexError) as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return None

    def _extract_code_block(self, content: str, language: str = "") -> Optional[str]:
        """
        从响应中提取代码块
        
        Args:
            content: 响应内容
            language: 代码语言（如 'python', 'prompt'）
            
        Returns:
            代码块内容，如果不存在返回 None
        """
        pattern = f"```{language}\\n(.*?)```" if language else r"```\n(.*?)```"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1)
        return None

    def _validate_workflow(self, workflow: Dict[str, Any]) -> bool:
        """
        验证工作流结构
        
        Args:
            workflow: 工作流对象
            
        Returns:
            是否有效
        """
        return (
            "name" in workflow
            and "nodes" in workflow
            and "edges" in workflow
            and len(workflow["nodes"]) > 0
        )
