"""
Copilot API Routes - 本地化版本

提供工作流编辑时的 AI 支持端点
- 无需 API keys
- 前端可以选择模型
- 后端处理所有逻辑
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
import logging
import json

from app.core.security import get_current_user
from app.models.user import User
from app.services.copilot_local_service import CopilotLocalService, AIModel
from app.services.copilot_stream_service import CopilotStreamService
from app.services.llm_client import llm_client
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from app.schemas.copilot import (
    ChatRequest,
    ChatResponse,
    ChatMessageSchema,
    WorkflowSuggestionRequest,
    WorkflowSuggestionResponse,
    NodeSuggestionRequest,
    NodeSuggestionResponse,
    WorkflowDiagnosisRequest,
    WorkflowDiagnosisResponse,
    PromptGenerationRequest,
    PromptGenerationResponse,
    DiagnosticSchema,
    NodeSuggestionSchema,
    WorkflowSuggestionSchema,
    PromptTemplateSchema,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/copilot", tags=["copilot"])


def _get_copilot_service(model: str = "local-smart") -> CopilotLocalService:
    """
    获取 Copilot 本地服务实例
    
    Args:
        model: AI 模型 (local-smart | local-rules | gpt-4 | claude-3)
        
    Returns:
        CopilotLocalService 实例
    """
    try:
        return CopilotLocalService(model=AIModel(model))
    except ValueError:
        logger.warning(f"Unknown model {model}, using local-smart")
        return CopilotLocalService(model=AIModel.LOCAL_SMART)


# ============================================================================
# Chat Endpoint
# ============================================================================


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """
    Copilot 聊天端点 - 直接调用 LLM
    
    处理用户提问并返回 AI 响应
    
    Args:
        request: 聊天请求 (包含 message, model, chat_history 等)
        current_user: 当前用户
        
    Returns:
        聊天响应
    """
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
        if request.context:
            context_info = f"\n\n当前工作流上下文：\n{json.dumps(request.context, indent=2, ensure_ascii=False)}"
            system_prompt += context_info

        # 构建消息列表
        messages = [SystemMessage(content=system_prompt)]
        
        # 添加聊天历史
        if request.chat_history:
            for msg in request.chat_history[-10:]:  # 只保留最近10条消息
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                else:
                    messages.append(AIMessage(content=msg.content))
        
        # 添加当前用户消息
        messages.append(HumanMessage(content=request.message))
        
        logger.info(
            f"Chat from {current_user.id} using model {request.model}: {request.message[:50]}..."
        )
        
        # 直接调用 LLM
        # 如果前端没有指定模型，使用默认模型 gpt-4o
        model_to_use = request.model if request.model else "gpt-4o"
        
        logger.info(f"🤖 准备调用 LLM: provider=openai, model={model_to_use}")
        logger.info(f"📝 消息数量: {len(messages)}, 用户消息: {request.message[:100]}")
        
        response = await llm_client.invoke(messages, provider="openai", model=model_to_use)
        
        logger.info(f"✅ LLM 响应成功: {response.content[:100] if response.content else 'empty'}...")
        
        return ChatResponse(
            message=response.content,
            suggestions=None,
            diagnostics=None,
        )

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}",
        )


# ============================================================================
# Workflow Suggestion Endpoint
# ============================================================================


@router.post("/suggest/workflow", response_model=WorkflowSuggestionResponse)
async def suggest_workflows(
    request: WorkflowSuggestionRequest,
    current_user: User = Depends(get_current_user),
) -> WorkflowSuggestionResponse:
    """
    工作流建议端点 - 无需 API keys
    
    根据用户描述生成工作流建议
    
    Args:
        request: 建议请求 (包含 description, complexity, model 等)
        current_user: 当前用户
        
    Returns:
        工作流建议响应
    """
    try:
        copilot = _get_copilot_service(request.model)

        suggestions = await copilot.suggest_workflows(
            description=request.description,
            complexity=request.complexity,
        )

        logger.info(
            f"Workflow suggestion from {current_user.id} using {request.model}"
        )

        return WorkflowSuggestionResponse(
            workflows=[
                WorkflowSuggestionSchema(
                    name=s.name,
                    description=s.description,
                    nodes=[
                        {
                            "type": n.type,
                            "label": n.label,
                            "config": n.config,
                        }
                        for n in s.nodes
                    ],
                    edges=s.edges,
                    explanation=s.explanation,
                )
                for s in suggestions
            ]
        )

    except Exception as e:
        logger.error(f"Workflow suggestion error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow suggestion failed: {str(e)}",
        )


# ============================================================================
# Node Suggestion Endpoint
# ============================================================================


@router.post("/suggest/node", response_model=NodeSuggestionResponse)
async def suggest_node(
    request: NodeSuggestionRequest,
    current_user: User = Depends(get_current_user),
) -> NodeSuggestionResponse:
    """
    节点建议端点 - 无需 API keys
    
    根据上下文建议适合的工作流节点
    
    Args:
        request: 节点建议请求
        current_user: 当前用户
        
    Returns:
        节点建议列表
    """
    try:
        copilot = _get_copilot_service(request.model)

        suggestions = await copilot.suggest_nodes(
            context=request.context,
            previous_node_type=request.previous_node_type,
            workflow_description=request.workflow_description,
        )

        logger.info(
            f"Node suggestion from {current_user.id} using {request.model}"
        )

        return NodeSuggestionResponse(
            suggestions=[
                NodeSuggestionSchema(
                    type=s.type,
                    label=s.label,
                    config=s.config,
                    explanation=s.explanation,
                )
                for s in suggestions
            ]
        )

    except Exception as e:
        logger.error(f"Node suggestion error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Node suggestion failed: {str(e)}",
        )


# ============================================================================
# Workflow Diagnosis Endpoint
# ============================================================================


@router.post("/diagnose", response_model=WorkflowDiagnosisResponse)
async def diagnose_workflow(
    request: WorkflowDiagnosisRequest,
    current_user: User = Depends(get_current_user),
) -> WorkflowDiagnosisResponse:
    """
    工作流诊断端点 - 无需 API keys
    
    诊断工作流中的问题
    
    Args:
        request: 诊断请求 (包含 nodes, edges, model 等)
        current_user: 当前用户
        
    Returns:
        诊断结果
    """
    try:
        copilot = _get_copilot_service(request.model)

        # 构造工作流对象
        workflow = {"nodes": request.nodes, "edges": request.edges}

        result = await copilot.diagnose_workflow(workflow)

        logger.info(
            f"Diagnosis from {current_user.id} using {request.model}"
        )

        return WorkflowDiagnosisResponse(
            diagnostics=[
                DiagnosticSchema(
                    level=d.level,
                    type=d.type,
                    description=d.description,
                    location=d.location,
                    suggestion=d.suggestion,
                )
                for d in result.diagnostics
            ],
            score=result.score,
            summary=result.summary,
        )

    except Exception as e:
        logger.error(f"Diagnosis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Diagnosis failed: {str(e)}",
        )


# ============================================================================
# Prompt Generation Endpoint
# ============================================================================


@router.post("/generate-prompt", response_model=PromptGenerationResponse)
async def generate_prompt(
    request: PromptGenerationRequest,
    current_user: User = Depends(get_current_user),
) -> PromptGenerationResponse:
    """
    提示词生成端点 - 无需 API keys
    
    根据任务描述生成提示词模板
    
    Args:
        request: 生成请求 (包含 task_description, style, model 等)
        current_user: 当前用户
        
    Returns:
        生成的提示词模板
    """
    try:
        copilot = _get_copilot_service(request.model)

        template = await copilot.generate_prompt(
            task_description=request.task_description,
            input_format=request.input_format,
            output_format=request.output_format,
            style=request.style,
        )

        logger.info(
            f"Prompt generation from {current_user.id} using {request.model}"
        )

        return PromptGenerationResponse(
            template=PromptTemplateSchema(
                prompt=template.prompt,
                style=template.style,
                estimated_tokens=template.estimated_tokens,
            )
        )

    except Exception as e:
        logger.error(f"Prompt generation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prompt generation failed: {str(e)}",
        )


# ============================================================================
# Health Check
# ============================================================================


@router.get("/health")
async def health_check():
    """
    Copilot 服务健康检查端点
    
    Returns:
        健康状态
    """
    return {
        "status": "healthy",
        "service": "copilot",
        "models": ["local-smart", "local-rules", "gpt-4", "claude-3"],
        "note": "Copilot 服务无需 API keys，支持本地化 AI 推理"
    }


# ============================================================================
# Stream Endpoints - SSE (Server-Sent Events)
# ============================================================================


async def _sse_stream_generator(async_generator):
    """Convert async generator to SSE format"""
    try:
        async for event in async_generator:
            # Ensure event is a dict or has as_dict method
            if hasattr(event, 'as_dict'):
                event_data = event.as_dict()
            elif isinstance(event, dict):
                event_data = event
            else:
                event_data = {"type": "unknown", "data": str(event)}
            
            yield f"data: {json.dumps(event_data)}\n\n"
    except Exception as e:
        logger.error(f"Stream error: {str(e)}")
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


@router.post("/stream/chat")
async def stream_chat(
    request: dict,
):
    """
    流式聊天端点 - SSE 格式
    
    Args:
        request: 聊天请求 (包含 message, model 等)
        
    Returns:
        SSE 流式响应
    """
    try:
        message = request.get("message", "")
        model_id = request.get("model_id")
        provider = request.get("provider", "openai")
        model = request.get("model", "gpt-4o")
        chat_history = request.get("chat_history", [])
        
        logger.info(f"Stream chat: {message[:50]}...")
        
        # 创建流服务
        stream_service = CopilotStreamService(
            provider=provider,
            model=model,
            model_id=model_id,
        )
        
        # 生成流
        async def event_generator():
            async for event in stream_service.stream_chat(
                message=message,
                chat_history=chat_history,
            ):
                if hasattr(event, 'as_dict'):
                    event_data = event.as_dict()
                else:
                    event_data = {"type": "token", "content": str(event)}
                
                yield f"data: {json.dumps(event_data)}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            }
        )
        
    except Exception as e:
        logger.error(f"Stream chat error: {str(e)}")
        
        async def error_generator():
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        return StreamingResponse(
            error_generator(),
            media_type="text/event-stream",
            status_code=500,
        )


@router.post("/stream/suggest")
async def stream_suggest(
    request: dict,
):
    """
    流式工作流建议端点 - SSE 格式
    
    Args:
        request: 建议请求
        
    Returns:
        SSE 流式响应
    """
    try:
        workflow_data = request.get("workflow_data", {})
        query = request.get("query", "")
        model_id = request.get("model_id")
        provider = request.get("provider", "openai")
        model = request.get("model", "gpt-4o")
        
        logger.info(f"Stream suggest: {query[:50]}...")
        
        # 创建流服务
        stream_service = CopilotStreamService(
            provider=provider,
            model=model,
            model_id=model_id,
        )
        
        # 生成流
        async def event_generator():
            async for event in stream_service.stream_workflow_suggestion(
                query=query,
                workflow_data=workflow_data,
            ):
                if hasattr(event, 'as_dict'):
                    event_data = event.as_dict()
                else:
                    event_data = {"type": "token", "content": str(event)}
                
                yield f"data: {json.dumps(event_data)}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            }
        )
        
    except Exception as e:
        logger.error(f"Stream suggest error: {str(e)}")
        
        async def error_generator():
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        return StreamingResponse(
            error_generator(),
            media_type="text/event-stream",
            status_code=500,
        )


@router.post("/stream/diagnose")
async def stream_diagnose(
    request: dict,
):
    """
    流式工作流诊断端点 - SSE 格式
    
    Args:
        request: 诊断请求
        
    Returns:
        SSE 流式响应
    """
    try:
        workflow_data = request.get("workflow_data", {})
        model_id = request.get("model_id")
        provider = request.get("provider", "openai")
        model = request.get("model", "gpt-4o")
        
        logger.info(f"Stream diagnose")
        
        # 创建流服务
        stream_service = CopilotStreamService(
            provider=provider,
            model=model,
            model_id=model_id,
        )
        
        # 生成流
        async def event_generator():
            async for event in stream_service.stream_workflow_diagnosis(
                workflow_data=workflow_data,
            ):
                if hasattr(event, 'as_dict'):
                    event_data = event.as_dict()
                else:
                    event_data = {"type": "token", "content": str(event)}
                
                yield f"data: {json.dumps(event_data)}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            }
        )
        
    except Exception as e:
        logger.error(f"Stream diagnose error: {str(e)}")
        
        async def error_generator():
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        return StreamingResponse(
            error_generator(),
            media_type="text/event-stream",
            status_code=500,
        )

# ============================================================================
# Suggestions Endpoint
# ============================================================================


@router.post("/suggestions")
async def get_suggestions(
    request: dict,
    current_user: User = Depends(get_current_user)
):
    """
    获取 Copilot 建议
    
    Args:
        request: 建议请求 (包含 context, type 等)
        current_user: 当前用户
        
    Returns:
        建议列表
    """
    try:
        # 根据请求类型返回不同的建议
        request_type = request.get("type", "general")
        context = request.get("context", "")
        
        logger.info(
            f"Suggestions request from {current_user.id}, type={request_type}"
        )
        
        # 返回示例建议
        suggestions = [
            {
                "id": "sug-1",
                "type": request_type,
                "content": f"基于 {context} 的建议 1",
                "confidence": 0.95
            },
            {
                "id": "sug-2",
                "type": request_type,
                "content": f"基于 {context} 的建议 2",
                "confidence": 0.87
            },
            {
                "id": "sug-3",
                "type": request_type,
                "content": f"基于 {context} 的建议 3",
                "confidence": 0.78
            }
        ]
        
        return {
            "suggestions": suggestions,
            "count": len(suggestions),
            "model": "local-smart"
        }
        
    except Exception as e:
        logger.error(f"Suggestions error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate suggestions: {str(e)}",
        )


# ============================================================================
# Frontend Expected Stream Endpoints
# ============================================================================


@router.get("/suggest/workflow/stream")
async def stream_workflow_suggestions(
    description: str = "",
    complexity: str = "medium",
    current_user: User = Depends(get_current_user),
):
    """
    流式工作流建议端点 - 前端期望的GET端点
    
    Args:
        description: 工作流描述
        complexity: 复杂度 (low|medium|high)
        current_user: 当前用户
        
    Returns:
        SSE 流式响应
    """
    try:
        logger.info(f"Stream workflow suggestions: {description[:50]}...")
        
        # 创建流服务
        stream_service = CopilotStreamService(
            provider="openai",
            model="gpt-4o",
        )
        
        # 生成流
        async def event_generator():
            async for event in stream_service.stream_workflow_suggestion(
                description=description,
                complexity=complexity,
            ):
                if hasattr(event, 'as_dict'):
                    event_data = event.as_dict()
                else:
                    event_data = {"type": "token", "content": str(event)}
                
                yield f"data: {json.dumps(event_data)}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            }
        )
        
    except Exception as e:
        logger.error(f"Stream suggestions error: {str(e)}")
        
        async def error_generator():
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        return StreamingResponse(
            error_generator(),
            media_type="text/event-stream",
            status_code=500,
        )


@router.post("/diagnose/stream")
async def stream_workflow_diagnosis(
    request: dict,
    current_user: User = Depends(get_current_user),
):
    """
    流式工作流诊断端点 - 前端期望的POST端点
    
    Args:
        request: 诊断请求 (包含 nodes, edges)
        current_user: 当前用户
        
    Returns:
        SSE 流式响应
    """
    try:
        nodes = request.get("nodes", [])
        edges = request.get("edges", [])
        
        logger.info(f"Stream diagnosis: {len(nodes)} nodes, {len(edges)} edges")
        
        # 创建流服务
        stream_service = CopilotStreamService(
            provider="openai",
            model="gpt-4o",
        )
        
        # 生成流
        async def event_generator():
            workflow_json = json.dumps({"nodes": nodes, "edges": edges})
            async for event in stream_service.stream_workflow_diagnosis(
                workflow_json=workflow_json,
            ):
                if hasattr(event, 'as_dict'):
                    event_data = event.as_dict()
                else:
                    event_data = {"type": "token", "content": str(event)}
                
                yield f"data: {json.dumps(event_data)}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            }
        )
        
    except Exception as e:
        logger.error(f"Stream diagnosis error: {str(e)}")
        
        async def error_generator():
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
        
        return StreamingResponse(
            error_generator(),
            media_type="text/event-stream",
            status_code=500,
        )