"""
Copilot Service Tests
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.copilot_service import (
    CopilotService,
    ChatMessage,
    WorkflowSuggestion,
    NodeSuggestion,
    Diagnostic,
)


@pytest.fixture
def copilot_service():
    """创建 CopilotService 实例用于测试"""
    with patch("app.services.copilot_service.llm_client"):
        return CopilotService(provider="openai", model="gpt-4-turbo-preview")


@pytest.mark.asyncio
class TestCopilotChat:
    """测试 Chat 功能"""

    async def test_chat_basic(self, copilot_service):
        """测试基础聊天"""
        # 模拟 LLMClient 的 invoke 方法
        from langchain_core.messages import AIMessage
        mock_response = AIMessage(content="测试响应")

        with patch("app.services.copilot_service.llm_client.invoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            
            response = await copilot_service.chat("你好，帮我建议一个工作流")

            assert isinstance(response, str)
            assert len(response) > 0
            assert response == "测试响应"

    async def test_chat_with_history(self, copilot_service):
        """测试带历史记录的聊天"""
        from langchain_core.messages import AIMessage
        mock_response = AIMessage(content="继续之前的讨论")

        with patch("app.services.copilot_service.llm_client.invoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            
            chat_history = [
                ChatMessage(role="user", content="什么是工作流?"),
                ChatMessage(role="assistant", content="工作流是..."),
            ]

            response = await copilot_service.chat(
                "那如何创建一个?",
                chat_history=chat_history,
            )

            assert "继续之前的讨论" in response

    async def test_chat_with_context(self, copilot_service):
        """测试带上下文的聊天"""
        from langchain_core.messages import AIMessage
        mock_response = AIMessage(content="基于你的工作流...")

        with patch("app.services.copilot_service.llm_client.invoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            
            context = {
                "workflow_description": "数据处理工作流",
                "nodes": [{"type": "Tool"}, {"type": "LLM"}],
            }

            response = await copilot_service.chat("如何优化这个工作流?", workflow_context=context)

            assert "基于你的工作流" in response


@pytest.mark.asyncio
class TestWorkflowSuggestion:
    """测试工作流建议功能"""

    async def test_suggest_workflows(self, copilot_service):
        """测试工作流建议"""
        from langchain_core.messages import AIMessage
        
        mock_response = AIMessage(content="""```json
{
  "workflows": [
    {
      "name": "数据处理工作流",
      "description": "从 API 获取数据并处理",
      "nodes": [
        {"type": "Start", "label": "开始"},
        {"type": "Tool", "label": "获取数据", "config": {}},
        {"type": "LLM", "label": "处理", "config": {}},
        {"type": "End", "label": "结束"}
      ],
      "edges": [
        {"from": "start", "to": "fetch"},
        {"from": "fetch", "to": "process"},
        {"from": "process", "to": "end"}
      ],
      "explanation": "这个工作流通过 Tool 获取数据"
    }
  ]
}
```""")

        with patch("app.services.copilot_service.llm_client.invoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            
            workflows = await copilot_service.suggest_workflows(
                description="创建一个数据处理工作流"
            )

            assert len(workflows) > 0
            assert workflows[0].name == "数据处理工作流"
            assert len(workflows[0].nodes) == 4
            assert len(workflows[0].edges) == 3

    async def test_suggest_workflows_different_complexity(self, copilot_service):
        """测试不同复杂度的工作流建议"""
        from langchain_core.messages import AIMessage
        
        mock_response = AIMessage(content="""```json
{
  "workflows": [
    {
      "name": "简单工作流",
      "description": "简单测试",
      "nodes": [{"type": "Start"}, {"type": "End"}],
      "edges": [{"from": "start", "to": "end"}],
      "explanation": "简单"
    }
  ]
}
```""")

        with patch("app.services.copilot_service.llm_client.invoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            
            workflows = await copilot_service.suggest_workflows(
                description="简单工作流", complexity="simple"
            )

            assert len(workflows) > 0


@pytest.mark.asyncio
class TestNodeSuggestion:
    """测试节点建议功能"""

    async def test_suggest_nodes(self, copilot_service):
        """测试节点建议"""
        from langchain_core.messages import AIMessage
        
        mock_response = AIMessage(content="""```json
{
  "suggestions": [
    {
      "type": "Router",
      "label": "条件路由",
      "config": {"condition": "result == 'success'"},
      "explanation": "用于根据结果路由"
    },
    {
      "type": "LLM",
      "label": "进一步处理",
      "config": {"model": "gpt-4"},
      "explanation": "用于生成更详细输出"
    }
  ]
}
```""")

        with patch("app.services.copilot_service.llm_client.invoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            
            suggestions = await copilot_service.suggest_nodes(
                context="根据结果进行路由处理"
            )

            assert len(suggestions) == 2
            assert suggestions[0].type == "Router"
            assert suggestions[1].type == "LLM"


@pytest.mark.asyncio
class TestWorkflowDiagnosis:
    """测试工作流诊断功能"""

    async def test_diagnose_workflow(self, copilot_service):
        """测试工作流诊断"""
        from langchain_core.messages import AIMessage
        
        mock_response = AIMessage(content="""```json
{
  "diagnostics": [
    {
      "level": "warning",
      "type": "disconnected_node",
      "description": "节点 process 没有输出连接",
      "location": {"node_id": "process"},
      "suggestion": "添加从 process 到 output 的连接"
    }
  ],
  "score": 75,
  "summary": "工作流缺少一个连接"
}
```""")

        with patch("app.services.copilot_service.llm_client.invoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            
            workflow = {
                "nodes": [
                    {"id": "start", "type": "Start"},
                    {"id": "process", "type": "LLM"},
                ],
                "edges": [],
            }

            result = await copilot_service.diagnose_workflow(workflow)

            assert result.score == 75
            assert len(result.diagnostics) > 0
            assert result.diagnostics[0].level == "warning"


@pytest.mark.asyncio
class TestPromptGeneration:
    """测试提示词生成功能"""

    async def test_generate_prompt(self, copilot_service):
        """测试提示词生成"""
        from langchain_core.messages import AIMessage
        
        prompt_content = """你是一个数据分类专家。

任务: 将输入的文本分类

输入格式: 单行文本
输出格式: JSON"""

        mock_response = AIMessage(content=f"""```prompt
{prompt_content}
```""")

        with patch("app.services.copilot_service.llm_client.invoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            
            template = await copilot_service.generate_prompt_template(
                task_description="数据分类",
                input_format="单行文本",
                output_format="JSON",
            )

            assert template.prompt is not None
            assert len(template.prompt) > 0
            assert template.style == "structured"
            assert template.estimated_tokens > 0


@pytest.mark.asyncio
class TestErrorHandling:
    """测试错误处理"""

    async def test_chat_api_error(self, copilot_service):
        """测试 Chat API 错误"""
        with patch("app.services.copilot_service.llm_client.invoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.side_effect = Exception("API Error")

            with pytest.raises(Exception):
                await copilot_service.chat("测试")

    async def test_invalid_json_response(self, copilot_service):
        """测试无效的 JSON 响应"""
        from langchain_core.messages import AIMessage
        
        mock_response = AIMessage(content="这不是 JSON")

        with patch("app.services.copilot_service.llm_client.invoke", new_callable=AsyncMock) as mock_invoke:
            mock_invoke.return_value = mock_response
            
            workflows = await copilot_service.suggest_workflows("测试")

            assert workflows == []


class TestJSONParsing:
    """测试 JSON 解析功能"""

    def test_parse_json_from_code_block(self, copilot_service):
        """测试从代码块解析 JSON"""
        content = """```json
{"workflows": [{"name": "test"}]}
```"""

        result = copilot_service._parse_json_response(content, "workflows")

        assert result is not None
        assert len(result) == 1
        assert result[0]["name"] == "test"

    def test_parse_json_without_code_block(self, copilot_service):
        """测试直接解析 JSON"""
        content = '{"workflows": [{"name": "test"}]}'

        result = copilot_service._parse_json_response(content, "workflows")

        assert result is not None
        assert len(result) == 1

    def test_extract_code_block(self, copilot_service):
        """测试代码块提取"""
        content = """```python
def hello():
    print("world")
```"""

        result = copilot_service._extract_code_block(content, "python")

        assert result is not None
        assert 'print("world")' in result
