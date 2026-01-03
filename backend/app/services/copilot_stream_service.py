"""
Copilot Stream Service - 流式响应服务

提供 SSE (Server-Sent Events) 流式响应支持
"""

import asyncio
import json
import logging
from typing import AsyncGenerator, List, Optional, Dict, Any

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.services.llm_client import llm_client

logger = logging.getLogger(__name__)


class ChatStreamEvent:
    """聊天流事件"""
    
    def __init__(self, event_type: str, data: Dict[str, Any]):
        self.type = event_type
        self.data = data
    
    def to_sse(self) -> str:
        """转换为 SSE 格式"""
        return f"data: {json.dumps({'type': self.type, **self.data})}\n\n"

    def as_dict(self) -> Dict[str, Any]:
        """Dictionary view used in tests."""
        return {"type": self.type, **self.data}

    def get(self, key: str, default: Any = None) -> Any:
        return self.as_dict().get(key, default)


class CopilotStreamService:
    """Copilot 流式服务 - 使用 LLMClient 统一接口"""
    
    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o",
        model_id: Optional[str] = None,
    ):
        """
        初始化 Copilot 流式服务
        
        Args:
            provider: LLM 提供商 ('openai' 或 'anthropic')
            model: 模型名称（默认 gpt-4o）
            model_id: 数据库配置的模型 ID（优先级高于 provider/model）
        """
        self.provider = provider
        self.model = model
        self.model_id = model_id
        self._llm_client = None
    
    async def _get_llm_client(self):
        """获取或创建 LLM 客户端（支持缓存）"""
        if self._llm_client is not None:
            return self._llm_client
        
        # 如果提供了 model_id，则从数据库读取配置
        if self.model_id:
            self._llm_client = await llm_client.get_client_by_model_id(self.model_id)
            if self._llm_client:
                return self._llm_client
        
        # 否则使用 provider 和 model 参数
        self._llm_client = await llm_client.get_client(
            provider=self.provider,
            model=self.model
        )
        
        return self._llm_client
    
    async def stream_chat(
        self,
        message: str,
        chat_history: List[Dict[str, str]] = None,
        workflow_context: Optional[str] = None,
    ) -> AsyncGenerator[ChatStreamEvent, None]:
        """
        流式聊天
        
        Args:
            message: 用户消息
            chat_history: 聊天历史列表 [{"role": "user/assistant", "content": "..."}, ...]
            workflow_context: 工作流上下文信息
            
        Yields:
            ChatStreamEvent 事件
        """
        if chat_history is None:
            chat_history = []
        
        # 构造系统提示词
        system = self._build_system_prompt()
        if workflow_context:
            system += f"\n\n工作流上下文：\n{workflow_context}"
        
        # 构造消息列表 - 转换为 BaseMessage 对象
        messages = [SystemMessage(content=system)]
        
        # 处理聊天历史
        for msg in chat_history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "assistant":
                messages.append(AIMessage(content=content))
            else:
                messages.append(HumanMessage(content=content))
        
        # 添加当前用户消息
        messages.append(HumanMessage(content=message))
        
        try:
            # 发送开始事件
            yield ChatStreamEvent("chat_started", {
                "threadId": None,
                "timestamp": None
            })
            
            # 调用 LLM 客户端进行流式聊天
            full_content = ""
            
            # 使用 llm_client.stream() 进行流式响应
            async for token in llm_client.stream(
                messages=messages,
                provider=self.provider,
                model=self.model,
                temperature=0.7,
                max_tokens=1000,
            ):
                # token 应该是字符串
                content = str(token) if token else ""
                
                full_content += content
                yield ChatStreamEvent("token", {
                    "content": content,
                    "finished": False,
                    "timestamp": None
                })

            yield ChatStreamEvent("chat_completed", {
                "content": full_content,
                "tokenCount": len(full_content) // 4,
                "timestamp": None
            })

        except Exception as e:
            logger.error(f"Stream chat error: {e}", exc_info=True)
            yield ChatStreamEvent("error", {
                "message": str(e),
                "code": "STREAM_ERROR",
                "fatal": True
            })
    
    async def stream_workflow_suggestion(
        self,
        description: str,
        complexity: str = "medium",
    ) -> AsyncGenerator[ChatStreamEvent, None]:
        """
        流式工作流建议
        
        Args:
            description: 需求描述
            complexity: 复杂度等级
            
        Yields:
            ChatStreamEvent 事件
        """
        prompt = f"""根据以下需求，建议 3 个工作流模板：

需求描述: {description}
复杂度: {complexity}

请逐个生成建议，每个建议包含：
1. 工作流名称
2. 简短描述
3. 关键步骤
4. 适用场景

返回纯文本格式，清晰易读。"""
        
        try:
            yield ChatStreamEvent("suggestion_started", {
                "type": "workflow",
                "timestamp": None
            })

            full_content = ""
            messages = [
                SystemMessage(content="你是工作流设计助手，提供专业的工作流建议。"),
                HumanMessage(content=prompt)
            ]

            # 使用 llm_client.stream() 进行流式响应
            async for token in llm_client.stream(
                messages=messages,
                provider=self.provider,
                model=self.model,
                temperature=0.7,
                max_tokens=2000,
            ):
                # token 应该是字符串
                content = str(token) if token else ""
                
                full_content += content
                yield ChatStreamEvent("suggestion_token", {
                    "content": content,
                    "type": "workflow",
                    "finished": False
                })

            yield ChatStreamEvent("suggestion_completed", {
                "type": "workflow",
                "content": full_content
            })

        except Exception as e:
            logger.error(f"Stream workflow suggestion error: {e}", exc_info=True)
            yield ChatStreamEvent("error", {
                "message": str(e),
                "code": "SUGGESTION_ERROR",
                "fatal": True
            })
    
    async def stream_workflow_diagnosis(
        self,
        workflow_json: str,
    ) -> AsyncGenerator[ChatStreamEvent, None]:
        """
        流式工作流诊断
        
        Args:
            workflow_json: 工作流 JSON 字符串
            
        Yields:
            ChatStreamEvent 事件
        """
        prompt = f"""请诊断以下工作流，识别潜在问题：

工作流定义：
{workflow_json}

请按以下格式返回诊断结果：
1. 工作流评分 (0-100)
2. 关键问题列表
3. 优化建议

返回纯文本格式，清晰易读。"""
        
        try:
            yield ChatStreamEvent("diagnosis_started", {
                "timestamp": None
            })

            full_content = ""
            messages = [
                SystemMessage(content="你是工作流诊断专家，提供详细的问题分析和改进建议。"),
                HumanMessage(content=prompt)
            ]

            # 使用 llm_client.stream() 进行流式响应
            async for token in llm_client.stream(
                messages=messages,
                provider=self.provider,
                model=self.model,
                temperature=0.7,
                max_tokens=1500,
            ):
                # token 应该是字符串
                content = str(token) if token else ""
                
                full_content += content
                yield ChatStreamEvent("diagnosis_token", {
                    "content": content,
                    "finished": False
                })

            yield ChatStreamEvent("diagnosis_completed", {
                "content": full_content
            })

        except Exception as e:
            logger.error(f"Stream workflow diagnosis error: {e}", exc_info=True)
            yield ChatStreamEvent("error", {
                "message": str(e),
                "code": "DIAGNOSIS_ERROR",
                "fatal": True
            })
    
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
- 逐步解释你的思路

工作流节点类型：
- LLM: 调用大语言模型
- Tool: 调用工具函数
- Router: 条件路由
- Interrupt: 人工干预
- RAG: 检索增强生成
- Start: 起始节点
- End: 结束节点"""
    
    def get_provider(self) -> str:
        """获取 LLM 提供商名称"""
        return self.provider
