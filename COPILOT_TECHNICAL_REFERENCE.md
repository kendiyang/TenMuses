# Copilot 本地化系统 - 技术参考

详细的实现、架构和扩展指南。

---

## 目录

1. [系统架构](#系统架构)
2. [核心组件](#核心组件)
3. [请求流程](#请求流程)
4. [数据模型](#数据模型)
5. [实现细节](#实现细节)
6. [扩展指南](#扩展指南)
7. [测试](#测试)

---

## 系统架构

### 整体结构

```
┌─────────────────────────────────────────────────┐
│              FastAPI 应用 (app/main.py)          │
│  - 路由注册                                      │
│  - 中间件配置                                    │
│  - 依赖注入                                      │
└──────┬──────────────────────────┬───────────────┘
       │                          │
       ↓                          ↓
┌──────────────────┐      ┌──────────────────┐
│ API 路由层        │      │ 认证中间件        │
│ (api/v1/)        │      │ (JWT验证)         │
│ - /auth/*        │      │ - get_current_user│
│ - /workflows/*   │      │ - token生成/验证  │
│ - /copilot/*     │      └──────────────────┘
└──────┬───────────┘
       │
       ↓
┌──────────────────────────────────────┐
│        Copilot API 路由              │
│     (api/v1/copilot.py)             │
│                                      │
│ @router.post("/chat")                │
│ @router.post("/suggest/workflow")    │
│ @router.post("/suggest/node")        │
│ @router.post("/diagnose")            │
│ @router.post("/generate-prompt")     │
│ @router.get("/health")               │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────┐
│   CopilotLocalService                │
│ (services/copilot_local_service.py) │
│                                      │
│ AIModel(Enum):                       │
│  - LOCAL_SMART                       │
│  - LOCAL_RULES                       │
│  - GPT4                              │
│  - CLAUDE3                           │
│                                      │
│ CopilotLocalService:                │
│  - __init__(model)                   │
│  - chat() ✨                         │
│  - suggest_workflows() ✨            │
│  - suggest_nodes() ✨                │
│  - diagnose_workflow() ✨            │
│  - generate_prompt() ✨              │
│                                      │
│ 内部方法:                            │
│  - _chat_smart()                     │
│  - _chat_rules()                     │
│  - _detect_task_type()               │
│  - _suggest_workflows_smart()        │
│  - 等等...                           │
└──────┬───────────────────────────────┘
       │
       ↓
┌──────────────────────────────────────┐
│     本地 AI 推理引擎                  │
│                                      │
│ Smart Mode (启发式):                 │
│  - 任务类型检测                      │
│  - 模式匹配                          │
│  - 规则应用                          │
│  - 推理逻辑                          │
│                                      │
│ Rules Mode (基于规则):               │
│  - 预定义响应                        │
│  - 映射表查询                        │
│  - 快速返回                          │
└──────────────────────────────────────┘
```

### 依赖关系

```
Pydantic v2
├── BaseModel (数据验证)
├── Field (字段定义)
└── ValidationError (错误处理)

FastAPI
├── APIRouter (路由)
├── Depends (依赖注入)
├── HTTPException (异常)
└── Security (认证)

Python asyncio
├── async/await (异步操作)
└── Task (并发)

SQLAlchemy
├── Base (模型基类)
├── AsyncSession (数据库会话)
└── Column, Integer, String, ... (列定义)
```

---

## 核心组件

### 1. CopilotLocalService

**位置**: `backend/app/services/copilot_local_service.py`

**职责**:
- 提供统一的 AI 服务接口
- 支持多种模型
- 执行本地推理逻辑

**关键代码**:

```python
from enum import Enum
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class AIModel(Enum):
    """支持的 AI 模型"""
    LOCAL_SMART = "local-smart"
    LOCAL_RULES = "local-rules"
    GPT4 = "gpt-4"
    CLAUDE3 = "claude-3"

class NodeConfig(BaseModel):
    """节点配置"""
    type: str
    label: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)

class WorkflowSuggestion(BaseModel):
    """工作流建议"""
    name: str
    description: str
    nodes: List[NodeConfig]
    edges: List[Dict[str, str]]
    explanation: str

class CopilotLocalService:
    """本地 Copilot 服务"""
    
    def __init__(self, model: AIModel = AIModel.LOCAL_SMART):
        self.model = model
        self._validate_model()
    
    async def chat(
        self,
        message: str,
        chat_history: Optional[List] = None,
        workflow_context: Optional[Dict] = None
    ) -> str:
        """聊天方法"""
        if self.model in [AIModel.LOCAL_SMART, AIModel.GPT4, AIModel.CLAUDE3]:
            return await self._chat_smart(message, chat_history, workflow_context)
        else:
            return await self._chat_rules(message)
    
    async def suggest_workflows(
        self,
        description: str,
        complexity: str = "medium"
    ) -> List[WorkflowSuggestion]:
        """工作流建议"""
        if self.model in [AIModel.LOCAL_SMART, AIModel.GPT4]:
            return await self._suggest_workflows_smart(description, complexity)
        else:
            return await self._suggest_workflows_rules()
    
    # ... 其他方法 ...
```

### 2. API 路由

**位置**: `backend/app/api/v1/copilot.py`

**职责**:
- HTTP 端点处理
- 请求验证
- 响应格式化
- 错误处理

**关键代码**:

```python
from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
from app.services.copilot_local_service import CopilotLocalService, AIModel
from app.schemas.copilot import ChatRequest, ChatResponse

router = APIRouter(prefix="/copilot", tags=["copilot"])

def _get_copilot_service(model: str = "local-smart") -> CopilotLocalService:
    """获取服务实例"""
    try:
        return CopilotLocalService(model=AIModel(model))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model: {model}"
        )

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
) -> ChatResponse:
    """聊天端点"""
    try:
        copilot = _get_copilot_service(request.model)
        
        message = await copilot.chat(
            message=request.message,
            chat_history=request.chat_history,
            workflow_context=request.workflow_context
        )
        
        logger.info(f"Chat from {current_user.id} using {request.model}")
        
        return ChatResponse(message=message)
    
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 3. 数据模型 (Schemas)

**位置**: `backend/app/schemas/copilot.py`

**职责**:
- 请求/响应验证
- 文档生成
- 类型检查

**关键代码**:

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息")
    chat_history: Optional[List['ChatMessageSchema']] = None
    workflow_context: Optional[Dict[str, Any]] = None
    model: str = Field(
        default="local-smart",
        description="AI 模型"
    )

class ChatResponse(BaseModel):
    """聊天响应"""
    message: str = Field(..., description="响应消息")
    suggestions: Optional[List[str]] = None

class WorkflowSuggestionRequest(BaseModel):
    """工作流建议请求"""
    description: str = Field(..., description="工作流描述")
    complexity: str = Field(default="medium", description="复杂度")
    model: str = Field(default="local-smart", description="AI 模型")
```

---

## 请求流程

### 完整的请求-响应周期

```
用户操作
   │
   ↓
前端发送请求 (含 model 字段)
   │
   ├─ POST /api/v1/copilot/chat
   ├─ Authorization: Bearer <token>
   ├─ {
   │   "message": "...",
   │   "model": "local-smart"
   │ }
   │
   ↓
FastAPI 接收请求
   │
   ├─ 验证请求格式 (Pydantic)
   ├─ 解析 JSON
   ├─ 创建 ChatRequest 对象
   │
   ↓
认证中间件
   │
   ├─ 提取 Bearer token
   ├─ 验证签名
   ├─ 获取 current_user
   │
   ↓
路由处理器 (@router.post("/chat"))
   │
   ├─ 接收 request 和 current_user
   ├─ 调用 _get_copilot_service(model)
   ├─ 创建 CopilotLocalService 实例
   │
   ↓
CopilotLocalService.chat()
   │
   ├─ 选择推理模式 (smart/rules)
   ├─ 执行本地逻辑
   ├─ 返回字符串响应
   │
   ↓
构造响应对象
   │
   ├─ 创建 ChatResponse(message="...")
   ├─ Pydantic 序列化为 JSON
   │
   ↓
返回 HTTP 200
   │
   ├─ Content-Type: application/json
   ├─ {
   │   "message": "...",
   │   "suggestions": []
   │ }
   │
   ↓
前端接收响应
   │
   └─ 渲染用户界面
```

### 错误处理流程

```
错误发生
   │
   ├─ Pydantic 验证错误
   │  └─ HTTPException(422, "validation error")
   │
   ├─ 模型不支持
   │  └─ HTTPException(400, "invalid model")
   │
   ├─ 业务逻辑错误
   │  └─ HTTPException(500, "service error")
   │
   ├─ 认证失败
   │  └─ HTTPException(401, "unauthorized")
   │
   └─ 其他异常
      └─ HTTPException(500, "internal error")
```

---

## 数据模型

### 请求模型

```
ChatRequest
├─ message: str (必须)
├─ chat_history: List[ChatMessageSchema] (可选)
├─ workflow_context: Dict (可选)
└─ model: str (默认: local-smart)

WorkflowSuggestionRequest
├─ description: str (必须)
├─ complexity: str (默认: medium)
└─ model: str (默认: local-smart)

NodeSuggestionRequest
├─ context: str (必须)
├─ previous_node_type: str (必须)
├─ workflow_description: str (必须)
└─ model: str (默认: local-smart)

WorkflowDiagnosisRequest
├─ nodes: List[Dict] (必须)
├─ edges: List[Dict] (必须)
└─ model: str (默认: local-smart)

PromptGenerationRequest
├─ task_description: str (必须)
├─ input_format: str (必须)
├─ output_format: str (必须)
└─ model: str (默认: local-smart)
```

### 响应模型

```
ChatResponse
├─ message: str
└─ suggestions: List[str] (可选)

WorkflowSuggestionResponse
└─ workflows: List[WorkflowSuggestionSchema]
   ├─ name: str
   ├─ description: str
   ├─ nodes: List[NodeConfigSchema]
   │  ├─ type: str
   │  ├─ label: str
   │  └─ config: Dict
   ├─ edges: List[Dict]
   └─ explanation: str

NodeSuggestionResponse
└─ suggestions: List[NodeSuggestionSchema]
   ├─ type: str
   ├─ label: str
   ├─ config: Dict
   └─ explanation: str

WorkflowDiagnosisResponse
├─ diagnostics: List[DiagnosticSchema]
│  ├─ level: str (error/warning/info)
│  ├─ type: str
│  ├─ description: str
│  ├─ location: Dict
│  └─ suggestion: str
├─ score: int (0-100)
└─ summary: str

PromptGenerationResponse
├─ template: str
├─ variables: List[str]
└─ example_output: str
```

---

## 实现细节

### Smart Mode (本地智能推理)

#### 聊天智能推理

```python
async def _chat_smart(self, message, chat_history, workflow_context):
    """智能聊天"""
    # 1. 分析用户意图
    intent = self._extract_intent(message)
    
    # 2. 结合工作流上下文
    if workflow_context:
        context_info = self._analyze_workflow_context(workflow_context)
    else:
        context_info = None
    
    # 3. 生成相关回应
    response = self._generate_response(intent, context_info)
    
    return response

def _extract_intent(self, message: str) -> str:
    """提取用户意图"""
    keywords = {
        'create': ['create', 'build', '创建', '构建'],
        'debug': ['debug', 'error', '调试', '错误'],
        'optimize': ['optimize', 'improve', '优化', '改进'],
        'explain': ['explain', 'how', 'what', '解释', '如何', '什么'],
    }
    
    message_lower = message.lower()
    for intent, keys in keywords.items():
        if any(key in message_lower for key in keys):
            return intent
    
    return 'general'
```

#### 工作流建议智能推理

```python
async def _suggest_workflows_smart(self, description, complexity):
    """智能工作流建议"""
    # 1. 检测任务类型
    task_type = self._detect_task_type(description)
    
    # 2. 根据任务类型和复杂度返回建议
    if task_type == 'rag':
        return self._get_rag_workflows(complexity)
    elif task_type == 'data_processing':
        return self._get_data_processing_workflows(complexity)
    elif task_type == 'content_generation':
        return self._get_content_generation_workflows(complexity)
    else:
        return self._get_generic_workflows(complexity)

def _detect_task_type(self, description: str) -> str:
    """检测任务类型"""
    rag_keywords = ['rag', 'document', 'retrieve', 'embedding', '文档', '检索']
    data_keywords = ['data', 'process', 'transform', 'filter', '数据', '处理']
    content_keywords = ['write', 'generate', 'content', 'article', '写作', '生成']
    
    description_lower = description.lower()
    
    if any(k in description_lower for k in rag_keywords):
        return 'rag'
    elif any(k in description_lower for k in data_keywords):
        return 'data_processing'
    elif any(k in description_lower for k in content_keywords):
        return 'content_generation'
    
    return 'generic'
```

### Rules Mode (基于规则)

```python
async def _chat_rules(self, message: str) -> str:
    """基于规则的聊天"""
    rules = {
        'rag': "You should use a RAG workflow with embeddings and retrieval.",
        'workflow': "Workflows consist of nodes connected by edges.",
        'node': "Nodes are processing units in a workflow.",
        'default': "I'm a workflow assistant. How can I help?"
    }
    
    # 简单的规则匹配
    if 'rag' in message.lower():
        return rules['rag']
    elif 'workflow' in message.lower():
        return rules['workflow']
    elif 'node' in message.lower():
        return rules['node']
    
    return rules['default']
```

---

## 扩展指南

### 添加新的 AI 模型

1. **修改 AIModel 枚举**:

```python
class AIModel(Enum):
    LOCAL_SMART = "local-smart"
    LOCAL_RULES = "local-rules"
    GPT4 = "gpt-4"
    CLAUDE3 = "claude-3"
    CUSTOM_MODEL = "custom-model"  # 新增
```

2. **添加对应的实现方法**:

```python
async def chat(self, message, chat_history, workflow_context):
    if self.model == AIModel.CUSTOM_MODEL:
        return await self._chat_custom(message)
    # ... 其他分支
```

3. **实现推理逻辑**:

```python
async def _chat_custom(self, message: str) -> str:
    """自定义模型聊天"""
    # 实现自定义逻辑
    return "Custom response"
```

### 添加新的 API 端点

1. **定义 Schema**:

```python
class CustomRequest(BaseModel):
    param1: str = Field(..., description="参数1")
    model: str = Field(default="local-smart")

class CustomResponse(BaseModel):
    result: str
```

2. **添加 API 路由**:

```python
@router.post("/custom", response_model=CustomResponse)
async def custom_endpoint(
    request: CustomRequest,
    current_user: User = Depends(get_current_user)
) -> CustomResponse:
    """自定义端点"""
    copilot = _get_copilot_service(request.model)
    result = await copilot.custom_method(request.param1)
    return CustomResponse(result=result)
```

3. **实现服务方法**:

```python
async def custom_method(self, param: str) -> str:
    """自定义方法"""
    if self.model == AIModel.LOCAL_SMART:
        return await self._custom_smart(param)
    else:
        return await self._custom_rules(param)
```

### 改进推理逻辑

提高 Smart Mode 的智能程度：

```python
def _extract_intent(self, message: str) -> str:
    """使用更高级的 NLP 技术"""
    # 可以集成：
    # - spaCy for NER
    # - NLTK for tokenization
    # - TextBlob for sentiment
    # - sklearn for classification
    
    from sklearn.feature_extraction.text import TfidfVectorizer
    
    # 使用 TF-IDF 进行文本分类
    # ...
    
    return detected_intent
```

---

## 测试

### 单元测试

```python
# tests/test_copilot_local_service.py

import pytest
from app.services.copilot_local_service import (
    CopilotLocalService,
    AIModel
)

@pytest.mark.asyncio
async def test_chat_smart():
    """测试智能聊天"""
    service = CopilotLocalService(model=AIModel.LOCAL_SMART)
    result = await service.chat("How do I create a RAG workflow?")
    assert isinstance(result, str)
    assert len(result) > 0

@pytest.mark.asyncio
async def test_suggest_workflows():
    """测试工作流建议"""
    service = CopilotLocalService(model=AIModel.LOCAL_SMART)
    workflows = await service.suggest_workflows(
        "Create a document processing pipeline"
    )
    assert len(workflows) > 0
    assert hasattr(workflows[0], 'name')
    assert hasattr(workflows[0], 'nodes')

@pytest.mark.asyncio
async def test_diagnose_workflow():
    """测试工作流诊断"""
    service = CopilotLocalService()
    workflow = {
        "nodes": [{"id": "1", "type": "Start"}],
        "edges": []
    }
    result = await service.diagnose_workflow(workflow)
    assert hasattr(result, 'diagnostics')
    assert hasattr(result, 'score')
```

### 集成测试

```bash
# 运行所有集成测试
cd /Users/mg/Workspace/TenMuses
python run-integration-tests.py

# 运行特定测试
python -m pytest tests/test_integration_copilot.py -v

# 生成覆盖率报告
pytest --cov=app.services.copilot_local_service tests/
```

### 性能测试

```python
import time
import asyncio

async def benchmark_chat():
    """基准测试：聊天性能"""
    service = CopilotLocalService(AIModel.LOCAL_SMART)
    
    start = time.time()
    await service.chat("test message")
    elapsed = time.time() - start
    
    print(f"Chat latency: {elapsed*1000:.2f}ms")
    assert elapsed < 0.2  # 应该少于 200ms

asyncio.run(benchmark_chat())
```

---

## 调试技巧

### 启用详细日志

```python
import logging

# 设置日志级别
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

logger.debug("详细信息")
logger.info("一般信息")
logger.warning("警告")
logger.error("错误")
```

### 检查服务状态

```bash
# 检查健康状态
curl http://localhost:8000/api/v1/copilot/health | jq

# 查看可用模型
curl http://localhost:8000/api/v1/copilot/health | jq '.available_models'
```

### 调试请求

```bash
# 启用 verbose 日志
curl -v http://localhost:8000/api/v1/copilot/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "model": "local-smart"}'

# 使用 httpie 进行更好的格式化
http POST http://localhost:8000/api/v1/copilot/chat \
  Authorization:"Bearer <token>" \
  message="test" \
  model="local-smart"
```

---

## 性能优化

### 缓存层

```python
from functools import lru_cache

class CopilotLocalService:
    @lru_cache(maxsize=128)
    def _get_cached_response(self, key: str) -> str:
        """缓存常见响应"""
        # ...
        pass
```

### 批处理

```python
async def batch_chat(self, messages: List[str]) -> List[str]:
    """批量处理聊天"""
    results = await asyncio.gather(
        *[self.chat(msg) for msg in messages]
    )
    return results
```

### 异步优化

```python
async def suggest_workflows_optimized(self, description, complexity):
    """并行执行多个任务"""
    task_type, complexity_score = await asyncio.gather(
        self._detect_task_type_async(description),
        self._evaluate_complexity_async(complexity)
    )
    # ...
```

---

## 总结

Copilot 本地化系统是一个可扩展、高性能、无外部依赖的 AI 助手框架。

**核心优势**:
- ✅ 完全本地化
- ✅ 快速响应
- ✅ 易于扩展
- ✅ 生产就绪

**快速开始**:
1. 查看 `COPILOT_LOCAL_QUICKSTART.md`
2. 查看 API 文档：`http://localhost:8000/docs`
3. 运行测试：`python run-integration-tests.py`
4. 开始集成：选择 `model: "local-smart"`
