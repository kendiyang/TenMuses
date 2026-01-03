# LLM 架构改进修复计划

**目标**: 完成后端全部 LLM 相关代码的新架构迁移  
**预计工时**: 3-4 小时  
**优先级**: 🔴 高（安全问题）

---

## 🚨 立即需要修复的问题

### 问题 1: EmbeddingService 硬编码 API 密钥（安全关键）

**位置**: `backend/app/services/embedding_service.py` (第 24-30 行)

**当前代码**:
```python
class EmbeddingService:
    def __init__(self, base_url: str = None, api_key: str = None, model: str = None):
        # 使用传入参数或默认值
        final_base_url = base_url or "https://chrisapius.top/v1"  # ❌ 硬编码
        final_api_key = api_key or "sk-wvbHvCfLHCvCf0kHEB8xTOInLVfZtDe4rNB0FiHQxgbQ0OhY"  # ❌ 硬编码！
        
        kwargs = {"api_key": final_api_key}
        if final_base_url:
            kwargs["base_url"] = final_base_url
        
        self.client = AsyncOpenAI(**kwargs)  # ❌ 旧架构
```

**修复步骤**:

#### Step 1: 替换为新架构
```python
from app.services.llm_client import llm_client
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(
        self, 
        provider: str = "openai",
        model: str = "text-embedding-3-small",
        model_id: Optional[str] = None,
        dimensions: int = 1536
    ):
        """
        初始化向量化服务（新架构）
        
        Args:
            provider: 供应商名称 (openai | anthropic | ...)
            model: 模型名称 (text-embedding-3-small | ...)
            model_id: 模型 UUID（优先级更高）
            dimensions: 向量维度
        """
        self.provider = provider
        self.model = model
        self.model_id = model_id
        self.dimensions = dimensions
        self.max_retries = 3
        self.retry_delay = 1
        self._verified = False
        
        logger.info(
            f"EmbeddingService initialized: "
            f"provider={provider}, model={model}, dimensions={dimensions}"
        )
    
    async def verify_connection(self) -> bool:
        """验证 LLM 连接"""
        try:
            client = await llm_client.get_client(
                provider=self.provider,
                model=self.model
            ) if not self.model_id else await llm_client.get_client_by_model_id(self.model_id)
            
            # 测试向量化
            result = await client.embed_query("test")
            self._verified = True
            logger.info("LLM 连接验证成功")
            return True
        except Exception as e:
            logger.error(f"LLM 连接验证失败: {e}")
            return False
    
    async def embed_text(self, text: str, retry_on_failure: bool = True) -> List[float]:
        """单个文本向量化"""
        if not text or not isinstance(text, str):
            raise EmbeddingServiceException("文本输入无效")
        
        text = text[:8000]  # 截断过长文本
        
        for attempt in range(self.max_retries):
            try:
                client = await llm_client.get_client(
                    provider=self.provider,
                    model=self.model
                ) if not self.model_id else await llm_client.get_client_by_model_id(self.model_id)
                
                result = await client.embed_query(text)
                logger.debug(f"成功向量化文本 (尝试 {attempt + 1})")
                return result
            except Exception as e:
                if attempt < self.max_retries - 1 and retry_on_failure:
                    await asyncio.sleep(self.retry_delay * (2 ** attempt))
                    continue
                raise EmbeddingServiceException(f"向量化失败: {e}")
```

#### Step 2: 更新调用方
找到所有 EmbeddingService 的使用位置：
```bash
grep -r "EmbeddingService(" backend/app --include="*.py" | grep -v test | grep -v ".pyc"
```

然后更新调用代码：
```python
# ❌ 旧方式
service = EmbeddingService(api_key="hardcoded-key")

# ✅ 新方式
service = EmbeddingService(provider="openai", model="text-embedding-3-small")
# 或使用 model_id
service = EmbeddingService(model_id="uuid-xxx")
```

#### Step 3: 测试验证
```python
async def test_embedding_service():
    service = EmbeddingService(provider="openai")
    
    # 验证连接（需要配置 API 密钥）
    if OPENAI_API_KEY:
        assert await service.verify_connection()
    
    # 向量化测试文本
    embedding = await service.embed_text("Hello, world!")
    assert isinstance(embedding, list)
    assert len(embedding) == 1536  # OpenAI 默认维度
```

---

### 问题 2: CopilotStreamService 使用旧 AsyncOpenAI

**位置**: `backend/app/services/copilot_stream_service.py`

**当前问题**:
```python
# ❌ 旧架构
from openai import AsyncOpenAI

class CopilotStreamService:
    def __init__(self, openai_api_key: str | None = None, model: str = "gpt-4-turbo-preview", base_url: str | None = None):
        self.model = model
        kwargs = {"api_key": openai_api_key or settings.OPENAI_API_KEY}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = AsyncOpenAI(**kwargs)  # ❌ 不使用新架构
```

**修复步骤**:

#### Step 1: 更新导入和初始化
```python
from app.services.llm_client import llm_client
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class CopilotStreamService:
    """
    Copilot 流式服务 - 使用新 LLMClient 架构
    """
    
    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4-turbo-preview",
        model_id: Optional[str] = None
    ):
        """
        初始化服务
        
        Args:
            provider: 供应商 (openai | anthropic)
            model: 模型名称
            model_id: 模型 UUID（优先）
        """
        self.provider = provider
        self.model = model
        self.model_id = model_id
        logger.info(f"CopilotStreamService initialized: provider={provider}, model={model}")
```

#### Step 2: 更新 stream_chat 方法
```python
async def stream_chat(
    self,
    message: str,
    chat_history: List[Dict[str, str]] = None,
    workflow_context: Optional[str] = None,
) -> AsyncGenerator[ChatStreamEvent, None]:
    """流式聊天 - 使用新架构"""
    if chat_history is None:
        chat_history = []
    
    # 构造系统提示词
    system = self._build_system_prompt()
    if workflow_context:
        system += f"\n\n工作流上下文：\n{workflow_context}"
    
    # 转换为 LangChain 消息格式
    messages = [SystemMessage(content=system)]
    for msg in chat_history:
        if msg.get("role") == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=message))
    
    try:
        # 发送开始事件
        yield ChatStreamEvent("chat_started", {"threadId": None, "timestamp": None})
        
        # 使用 llm_client 流式调用
        full_content = ""
        async for token in llm_client.stream(
            messages,
            model_id=self.model_id,
            provider=self.provider if not self.model_id else None,
            model=self.model if not self.model_id else None,
            temperature=0.7,
            max_tokens=1000
        ):
            full_content += token
            yield ChatStreamEvent("token", {
                "content": token,
                "finished": False
            })
        
        # 发送完成事件
        yield ChatStreamEvent("token", {
            "content": "",
            "finished": True
        })
        
        yield ChatStreamEvent("chat_completed", {
            "content": full_content,
            "total_tokens": len(full_content) // 4,  # 粗略估计
        })
    
    except Exception as e:
        logger.error(f"Stream chat error: {e}", exc_info=True)
        yield ChatStreamEvent("error", {
            "message": f"流式聊天出错: {str(e)}",
            "code": "STREAM_ERROR"
        })
```

#### Step 3: 更新测试
```python
# ✅ 新的测试方式
@pytest.mark.asyncio
async def test_stream_chat():
    service = CopilotStreamService(provider="openai", model="gpt-4-turbo-preview")
    
    with patch("app.services.llm_client.llm_client.stream") as mock_stream:
        async def mock_tokens():
            yield "Hello"
            yield " "
            yield "world"
        
        mock_stream.return_value = mock_tokens()
        
        events = []
        async for event in service.stream_chat("Hi"):
            events.append(event)
        
        # 验证事件
        assert events[0].type == "chat_started"
        assert events[-1].type == "chat_completed"
        token_events = [e for e in events if e.type == "token"]
        assert len(token_events) > 0
```

---

### 问题 3: 测试代码过时的 Mock

**位置**: `backend/tests/test_copilot_service.py` 和 `backend/tests/test_copilot_stream_service.py`

**当前问题**:
```python
# ❌ 过时的 mock
with patch("app.services.copilot_service.AsyncOpenAI"):
    service = CopilotService(openai_api_key="test-key")
```

**修复步骤**:

#### test_copilot_service.py - 更新 fixture
```python
from unittest.mock import AsyncMock, patch
from langchain_core.messages import AIMessage
from app.services.copilot_service import CopilotService

@pytest.fixture
def copilot_service():
    """创建 CopilotService 实例用于测试"""
    return CopilotService(
        provider="openai",
        model="gpt-4-turbo-preview"
    )

@pytest.mark.asyncio
async def test_copilot_chat(copilot_service):
    """测试基础聊天"""
    with patch("app.services.copilot_service.llm_client.invoke") as mock_invoke:
        mock_invoke.return_value = AIMessage(content="测试响应")
        
        response = await copilot_service.chat("你好")
        
        assert response == "测试响应"
        mock_invoke.assert_called_once()
```

#### test_copilot_stream_service.py - 更新 fixture
```python
from app.services.copilot_stream_service import CopilotStreamService

@pytest.fixture
def stream_service():
    """创建 CopilotStreamService 实例"""
    return CopilotStreamService(
        provider="openai",
        model="gpt-4-turbo-preview"
    )

@pytest.mark.asyncio
async def test_stream_chat_basic(stream_service):
    """测试基础流式聊天"""
    with patch("app.services.copilot_stream_service.llm_client.stream") as mock_stream:
        async def mock_tokens():
            yield "Hello"
            yield " "
            yield "world"
        
        mock_stream.return_value = mock_tokens()
        
        events = []
        async for event in stream_service.stream_chat("Hi"):
            events.append(event)
        
        assert len(events) > 0
        assert events[0].type == "chat_started"
```

---

### 问题 4: 示例代码过时

**位置**: `backend/app/examples/database_config_example.py`

**修复步骤**:

更新为新架构示例：
```python
"""
示例：使用新 LLMClient 架构的各种方式
"""

from typing import Optional, List
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from app.services.llm_client import llm_client

# 方式 1: 通过 model_id（推荐）
async def example_with_model_id():
    """通过模型 UUID 调用 LLM"""
    messages = [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content="What is AI?"),
    ]
    
    response = await llm_client.invoke(
        messages,
        model_id="550e8400-e29b-41d4-a716-446655440000"  # 实际的 UUID
    )
    
    return response.content

# 方式 2: 通过 provider + model（向后兼容）
async def example_with_provider_model():
    """通过提供商和模型名称调用 LLM"""
    messages = [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content="What is AI?"),
    ]
    
    response = await llm_client.invoke(
        messages,
        provider="openai",
        model="gpt-4-turbo-preview"
    )
    
    return response.content

# 方式 3: 流式调用
async def example_stream():
    """流式调用 LLM"""
    messages = [HumanMessage(content="Tell me a story")]
    
    full_text = ""
    async for token in llm_client.stream(
        messages,
        provider="openai",
        model="gpt-4-turbo-preview"
    ):
        print(token, end="", flush=True)
        full_text += token
    
    return full_text

# 方式 4: 获取可用模型列表
async def example_list_models():
    """列出所有可用的模型"""
    models = await llm_client.get_available_models()
    
    for model in models:
        print(f"Model: {model['display_name']}")
        print(f"  Provider: {model['provider_display_name']}")
        print(f"  Model ID: {model['model_id']}")
        print()

# 方式 5: 创建服务类
class MyLLMService:
    """创建自定义 LLM 服务的最佳实践"""
    
    def __init__(
        self,
        provider: str = "openai",
        model: Optional[str] = None,
        model_id: Optional[str] = None
    ):
        self.provider = provider
        self.model = model
        self.model_id = model_id
    
    async def process_query(self, query: str) -> str:
        """处理用户查询"""
        messages = [HumanMessage(content=query)]
        
        response = await llm_client.invoke(
            messages,
            model_id=self.model_id,
            provider=self.provider if not self.model_id else None,
            model=self.model if not self.model_id else None,
        )
        
        return response.content
    
    async def stream_response(self, query: str):
        """流式返回响应"""
        messages = [HumanMessage(content=query)]
        
        async for token in llm_client.stream(
            messages,
            model_id=self.model_id,
            provider=self.provider if not self.model_id else None,
            model=self.model if not self.model_id else None,
        ):
            yield token

# 使用示例
async def main():
    # 方式 1: 使用 model_id
    result1 = await example_with_model_id()
    print(f"Result 1: {result1}")
    
    # 方式 2: 使用 provider + model
    result2 = await example_with_provider_model()
    print(f"Result 2: {result2}")
    
    # 方式 3: 流式调用
    print("Streaming result:")
    result3 = await example_stream()
    
    # 方式 4: 列出模型
    await example_list_models()
    
    # 方式 5: 使用服务类
    service = MyLLMService(provider="openai", model="gpt-4-turbo-preview")
    result5 = await service.process_query("What is Python?")
    print(f"Service result: {result5}")
```

---

## 📋 修复执行清单

### 优先级 1: 安全修复（立即）

- [ ] **EmbeddingService 移除硬编码密钥**
  - [ ] 备份当前代码
  - [ ] 实现新架构
  - [ ] 测试验证
  - [ ] 找出所有调用位置并更新
  - [ ] 提交代码

- [ ] **CopilotStreamService 迁移**
  - [ ] 移除 AsyncOpenAI 导入
  - [ ] 更新初始化方法
  - [ ] 更新 stream_chat 方法
  - [ ] 更新其他流式方法
  - [ ] 测试验证

### 优先级 2: 测试更新（同时进行）

- [ ] **更新 test_copilot_service.py**
  - [ ] 移除旧的 AsyncOpenAI mock
  - [ ] 创建新的 llm_client mock
  - [ ] 更新所有测试用例
  - [ ] 运行测试确保通过

- [ ] **更新 test_copilot_stream_service.py**
  - [ ] 移除旧的 AsyncOpenAI mock
  - [ ] 创建新的 llm_client mock
  - [ ] 更新所有测试用例
  - [ ] 运行流式测试

### 优先级 3: 文档和示例（完成后）

- [ ] **更新 database_config_example.py**
  - [ ] 用新方式替换旧示例
  - [ ] 添加多种使用模式
  - [ ] 添加最佳实践注释

- [ ] **创建迁移指南**
  - [ ] 列出所有变更
  - [ ] 提供转换脚本
  - [ ] 添加常见问题

---

## 🧪 验证步骤

### 测试命令
```bash
# 运行所有 LLM 相关测试
cd backend
pytest tests/test_llm_client.py -v
pytest tests/test_copilot_service.py -v
pytest tests/test_copilot_stream_service.py -v

# 运行特定测试
pytest tests/test_copilot_service.py::TestCopilotChat::test_chat_basic -v
pytest tests/test_copilot_stream_service.py::test_stream_chat_basic -v

# 检查代码中是否还有 AsyncOpenAI
grep -r "AsyncOpenAI" backend/app --include="*.py" | grep -v test | grep -v ".pyc" | grep -v examples

# 检查硬编码的 API 密钥
grep -r "sk-" backend/app --include="*.py" | grep -v test | grep -v ".pyc"
grep -r "api_key" backend/app --include="*.py" | grep -v "get_api_key"
```

### 端对端验证
```bash
# 启动后端服务
cd backend
python -m uvicorn app.main:app --reload

# 在另一个终端运行测试
python test_llm_integration_e2e.py
```

---

## ✅ 完成标准

修复完成的标志：

1. **没有硬编码密钥**
   - [ ] EmbeddingService 中没有硬编码 API 密钥
   - [ ] 没有硬编码 base_url

2. **使用新架构**
   - [ ] CopilotStreamService 使用 llm_client
   - [ ] EmbeddingService 使用 llm_client
   - [ ] 所有服务都支持 model_id

3. **测试通过**
   - [ ] 所有单元测试通过
   - [ ] 所有集成测试通过
   - [ ] E2E 测试通过

4. **向后兼容**
   - [ ] 旧接口继续工作（带警告）
   - [ ] 环境变量回退工作
   - [ ] 数据库配置优先级正确

5. **文档完整**
   - [ ] 示例代码已更新
   - [ ] 迁移指南已创建
   - [ ] API 文档已更新

---

**预计完成时间**: 3-4 小时  
**难度**: 中等  
**风险**: 低（修改隔离，充分的回退机制）

