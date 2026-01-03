"""
Copilot API Integration Tests
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4

from app.main import app
from app.models.user import User
from app.core.security import get_current_user


@pytest.fixture
def client(test_user):
    """创建测试客户端并模拟认证"""
    # 覆盖 get_current_user 依赖，返回测试用户
    app.dependency_overrides[get_current_user] = lambda: test_user
    yield TestClient(app)
    # 清理
    app.dependency_overrides.clear()


@pytest.fixture
def test_user():
    """创建测试用户"""
    # 创建一个模拟用户对象（不需要真实数据库）
    user = MagicMock(spec=User)
    user.id = uuid4()  # 使用真实的 UUID
    user.username = "testuser"
    user.email = "test@example.com"
    user.hashed_password = "hashed_password"
    return user


@pytest.fixture
def auth_headers(test_user):
    """获取认证令牌"""
    from app.core.security import create_access_token

    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


class TestCopilotAPIChat:
    """测试 Chat API"""

    @patch("app.api.v1.copilot.CopilotService")
    def test_chat_success(self, mock_service_class, client, auth_headers):
        """测试成功的聊天请求"""
        mock_service = MagicMock()
        mock_service.chat = AsyncMock(return_value="这是来自 AI 的响应")
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/v1/copilot/chat",
            json={
                "message": "你好，帮我建议一个工作流",
                "chat_history": [],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["message"] == "这是来自 AI 的响应"

    @patch("app.api.v1.copilot.CopilotService")
    def test_chat_with_history(self, mock_service_class, client, auth_headers):
        """测试带聊天历史的聊天请求"""
        mock_service = MagicMock()
        mock_service.chat = AsyncMock(return_value="基于你的历史...")
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/v1/copilot/chat",
            json={
                "message": "继续",
                "chat_history": [
                    {"role": "user", "content": "hello"},
                    {"role": "assistant", "content": "hi"},
                ],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200

    def test_chat_unauthorized(self, client):
        """测试未授权的聊天请求"""
        response = client.post(
            "/api/v1/copilot/chat",
            json={"message": "test"},
        )

        assert response.status_code == 403


class TestCopilotAPIWorkflowSuggestion:
    """测试工作流建议 API"""

    @patch("app.api.v1.copilot.CopilotService")
    def test_suggest_workflow_success(self, mock_service_class, client, auth_headers):
        """测试成功的工作流建议请求"""
        mock_service = MagicMock()

        mock_workflow = MagicMock()
        mock_workflow.name = "数据处理工作流"
        mock_workflow.description = "测试"
        mock_workflow.nodes = []
        mock_workflow.edges = []
        mock_workflow.explanation = "推荐原因"

        mock_service.suggest_workflows = AsyncMock(return_value=[mock_workflow])
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/v1/copilot/suggest/workflow",
            json={
                "description": "创建数据处理工作流",
                "complexity": "medium",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert "workflows" in response.json()

    @patch("app.api.v1.copilot.CopilotService")
    def test_suggest_workflow_simple(self, mock_service_class, client, auth_headers):
        """测试简单复杂度的工作流建议"""
        mock_service = MagicMock()
        mock_workflow = MagicMock()
        mock_workflow.name = "简单工作流"
        mock_workflow.description = "简单"
        mock_workflow.nodes = []
        mock_workflow.edges = []
        mock_workflow.explanation = "简单原因"

        mock_service.suggest_workflows = AsyncMock(return_value=[mock_workflow])
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/v1/copilot/suggest/workflow",
            json={
                "description": "简单工作流",
                "complexity": "simple",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200


class TestCopilotAPINodeSuggestion:
    """测试节点建议 API"""

    @patch("app.api.v1.copilot.CopilotService")
    def test_suggest_node_success(self, mock_service_class, client, auth_headers):
        """测试成功的节点建议请求"""
        mock_service = MagicMock()

        mock_node = MagicMock()
        mock_node.type = "Router"
        mock_node.label = "条件路由"
        mock_node.config = {}
        mock_node.explanation = "推荐原因"

        mock_service.suggest_nodes = AsyncMock(return_value=[mock_node])
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/v1/copilot/suggest/node",
            json={
                "context": "根据结果进行路由",
                "previous_node_type": "LLM",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert "suggestions" in response.json()

    @patch("app.api.v1.copilot.CopilotService")
    def test_suggest_node_without_context(self, mock_service_class, client, auth_headers):
        """测试不带上下文的节点建议"""
        mock_service = MagicMock()
        mock_node = MagicMock()
        mock_node.type = "Tool"
        mock_node.label = None
        mock_node.config = {}
        mock_node.explanation = "推荐"

        mock_service.suggest_nodes = AsyncMock(return_value=[mock_node])
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/v1/copilot/suggest/node",
            json={
                "context": "下一步操作",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200


class TestCopilotAPIDiagnosis:
    """测试工作流诊断 API"""

    @patch("app.api.v1.copilot.CopilotService")
    def test_diagnose_workflow_success(self, mock_service_class, client, auth_headers):
        """测试成功的诊断请求"""
        mock_service = MagicMock()

        mock_diagnostic = MagicMock()
        mock_diagnostic.level = "warning"
        mock_diagnostic.type = "disconnected_node"
        mock_diagnostic.description = "节点未连接"
        mock_diagnostic.location = {"node_id": "node1"}
        mock_diagnostic.suggestion = "连接节点"

        from app.services.copilot_service import WorkflowDiagnosisResult

        mock_result = WorkflowDiagnosisResult(
            diagnostics=[mock_diagnostic],
            score=75,
            summary="有一个警告",
        )

        mock_service.diagnose_workflow = AsyncMock(return_value=mock_result)
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/v1/copilot/diagnose",
            json={
                "nodes": [{"id": "node1", "type": "LLM"}],
                "edges": [],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 75

    @patch("app.api.v1.copilot.CopilotService")
    def test_diagnose_workflow_no_issues(self, mock_service_class, client, auth_headers):
        """测试没有问题的工作流诊断"""
        mock_service = MagicMock()

        from app.services.copilot_service import WorkflowDiagnosisResult

        mock_result = WorkflowDiagnosisResult(
            diagnostics=[],
            score=100,
            summary="工作流无问题",
        )

        mock_service.diagnose_workflow = AsyncMock(return_value=mock_result)
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/v1/copilot/diagnose",
            json={
                "nodes": [{"id": "node1", "type": "Start"}],
                "edges": [],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 100


class TestCopilotAPIPromptGeneration:
    """测试提示词生成 API"""

    @patch("app.api.v1.copilot.CopilotService")
    def test_generate_prompt_success(self, mock_service_class, client, auth_headers):
        """测试成功的提示词生成"""
        mock_service = MagicMock()

        from app.services.copilot_service import PromptTemplate

        mock_template = PromptTemplate(
            prompt="你是一个助手。\n任务: {{INPUT}}",
            style="structured",
            estimated_tokens=250,
        )

        mock_service.generate_prompt_template = AsyncMock(return_value=mock_template)
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/v1/copilot/generate-prompt",
            json={
                "task_description": "数据分类",
                "input_format": "文本",
                "output_format": "分类标签",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "template" in data
        assert data["template"]["style"] == "structured"

    @patch("app.api.v1.copilot.CopilotService")
    def test_generate_prompt_with_examples(self, mock_service_class, client, auth_headers):
        """测试带示例的提示词生成"""
        mock_service = MagicMock()

        from app.services.copilot_service import PromptTemplate

        mock_template = PromptTemplate(
            prompt="示例在内...",
            style="detailed",
            estimated_tokens=500,
        )

        mock_service.generate_prompt_template = AsyncMock(return_value=mock_template)
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/v1/copilot/generate-prompt",
            json={
                "task_description": "分类",
                "examples": [
                    {"input": "示例输入", "output": "示例输出"},
                ],
                "style": "detailed",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200


class TestCopilotAPIHealth:
    """测试健康检查"""

    @patch("app.api.v1.copilot.CopilotService")
    def test_health_check_success(self, mock_service_class, client):
        """测试健康检查成功"""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        response = client.get("/api/v1/copilot/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @patch("app.api.v1.copilot.CopilotService")
    def test_health_check_failure(self, mock_service_class, client):
        """测试健康检查失败"""
        mock_service_class.side_effect = Exception("API key missing")

        response = client.get("/api/v1/copilot/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"


class TestCopilotAPIErrors:
    """测试错误处理"""

    @patch("app.api.v1.copilot.CopilotService")
    def test_api_error_handling(self, mock_service_class, client, auth_headers):
        """测试 API 错误处理"""
        mock_service = MagicMock()
        mock_service.chat = AsyncMock(side_effect=Exception("OpenAI API Error"))
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/v1/copilot/chat",
            json={"message": "test"},
            headers=auth_headers,
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
