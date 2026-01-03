"""
Phase 4 - Copilot Integration Tests (Backend)

Complete integration test suite for:
- Streaming endpoints and event generation
- Context serialization
- Template processing
- Suggestion storage API
- End-to-end workflows
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from typing import AsyncIterator, Generator
import sys
import os

# Debug fixture to print sys.path and langchain_core location
@pytest.fixture(autouse=True)
def debug_sys_path():
    print("--- sys.path from pytest ---")
    for p in sys.path:
        print(p)
    print("--------------------------")
    
    try:
        import langchain_core
        print(f"langchain_core imported successfully")
        if hasattr(langchain_core, '__file__'):
            print(f"langchain_core path: {langchain_core.__file__}")
    except ImportError as e:
        print(f"Failed to import langchain_core: {e}")
        
    print("--- Searching for langchain_core.py in sys.path ---")
    for p in sys.path:
        if not p or not os.path.isdir(p):
            continue
        potential_conflict = os.path.join(p, "langchain_core.py")
        if os.path.exists(potential_conflict):
            print(f"Found conflicting file: {potential_conflict}")
    print("-------------------------------------------------")

# Test fixtures
@pytest.fixture
def client():
    """FastAPI test client"""
    from app.main import app
    return TestClient(app)


@pytest.fixture
async def async_client():
    """Async HTTP client for streaming tests"""
    from app.main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_workflow():
    """Sample workflow data"""
    return {
        "id": "test-workflow-1",
        "name": "Test Workflow",
        "nodes": [
            {
                "id": "llm-1",
                "type": "llm",
                "label": "OpenAI LLM",
                "data": {"model": "gpt-4o"}
            },
            {
                "id": "search-1",
                "type": "search",
                "label": "RAG Search",
                "data": {"topK": 5}
            },
            {
                "id": "output-1",
                "type": "output",
                "label": "Output",
                "data": {}
            }
        ],
        "edges": [
            {"source": "search-1", "target": "llm-1"},
            {"source": "llm-1", "target": "output-1"}
        ]
    }


@pytest.fixture
def sample_suggestions():
    """Sample suggestion data"""
    return [
        {
            "id": "sugg-1",
            "type": "improvement",
            "content": "Consider using async operations",
            "timestamp": "2024-01-01T12:00:00Z",
            "favorite": False
        },
        {
            "id": "sugg-2",
            "type": "refactoring",
            "content": "Extract helper function",
            "timestamp": "2024-01-01T12:05:00Z",
            "favorite": True
        }
    ]


@pytest.fixture
def sample_template():
    """Sample template data"""
    return {
        "id": "template-1",
        "name": "RAG Query",
        "content": "Based on {{context}}, answer {{question}} in {{language}}",
        "variables": {
            "context": "relevant documents",
            "question": "What is the question?",
            "language": "English"
        }
    }


# Step 1: Stream Response Tests
class TestStreamResponseSupport:
    """Test Phase 4 Step 1: Streaming Response Support"""

    @pytest.mark.asyncio
    async def test_stream_chat_endpoint(self, async_client):
        """Test SSE streaming for chat endpoint"""
        async with async_client.stream(
            "POST",
            "/api/v1/copilot/stream/chat",
            json={"message": "Hello", "model": "gpt-4o"}
        ) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]
            
            # Read streaming events
            events = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    try:
                        events.append(json.loads(data))
                    except json.JSONDecodeError:
                        pass
            
            # Should have multiple token events
            token_events = [e for e in events if e.get("type") == "token"]
            assert len(token_events) > 0

    @pytest.mark.asyncio
    async def test_stream_suggest_endpoint(self, async_client):
        """Test SSE streaming for suggestion endpoint"""
        async with async_client.stream(
            "POST",
            "/api/v1/copilot/stream/suggest",
            json={
                "workflow_data": {"nodes": [], "edges": []},
                "query": "optimize this workflow"
            }
        ) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_stream_diagnose_endpoint(self, async_client):
        """Test SSE streaming for diagnosis endpoint"""
        async with async_client.stream(
            "POST",
            "/api/v1/copilot/stream/diagnose",
            json={"workflow_data": {"nodes": [], "edges": []}}
        ) as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]

    def test_stream_service_initialization(self):
        """Test CopilotStreamService initializes correctly"""
        from app.services.copilot_stream_service import CopilotStreamService
        
        service = CopilotStreamService()
        assert service is not None

    @pytest.mark.asyncio
    async def test_stream_service_generate_chat_events(self):
        """Test stream service generates chat events"""
        from app.services.copilot_stream_service import CopilotStreamService
        
        service = CopilotStreamService()
        events = []
        
        async for event in service.stream_chat("test message"):
            events.append(event)
        
        # Should have streaming events
        assert len(events) > 0
        
        # Should have token events
        token_events = [e for e in events if e.get("type") == "token"]
        assert len(token_events) > 0


# Step 2: Suggestion History Tests
class TestSuggestionHistory:
    """Test Phase 4 Step 2: Suggestion History and Favorites"""

    def test_save_suggestion(self, client, sample_suggestions):
        """Test saving suggestion to database"""
        response = client.post(
            "/api/v1/suggestions",
            json=sample_suggestions[0]
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["id"] == sample_suggestions[0]["id"]

    def test_get_suggestions(self, client):
        """Test retrieving suggestions"""
        response = client.get("/api/v1/suggestions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_filter_suggestions_by_type(self, client):
        """Test filtering suggestions by type"""
        response = client.get(
            "/api/v1/suggestions",
            params={"type": "improvement"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # All should be improvement type
        for item in data:
            assert item["type"] == "improvement"

    def test_search_suggestions(self, client):
        """Test searching suggestions"""
        response = client.get(
            "/api/v1/suggestions/search",
            params={"query": "async"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Results should match query
        for item in data:
            assert "async" in item["content"].lower()

    def test_favorite_suggestion(self, client):
        """Test toggling favorite status"""
        # First save a suggestion
        response = client.post(
            "/api/v1/suggestions",
            json={
                "id": "test-sugg",
                "type": "improvement",
                "content": "Test suggestion",
                "favorite": False
            }
        )
        assert response.status_code in [200, 201]
        
        # Toggle favorite
        response = client.post(
            "/api/v1/suggestions/test-sugg/favorite"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["favorite"] == True

    def test_export_suggestions(self, client):
        """Test exporting suggestions"""
        response = client.get(
            "/api/v1/suggestions/export",
            params={"format": "json"}
        )
        assert response.status_code == 200
        
        # Should be valid JSON
        data = response.json()
        assert isinstance(data, list)

    def test_import_suggestions(self, client):
        """Test importing suggestions"""
        suggestions = [
            {
                "id": "import-1",
                "type": "improvement",
                "content": "Imported suggestion",
                "favorite": False
            }
        ]
        
        response = client.post(
            "/api/v1/suggestions/import",
            json={"suggestions": suggestions}
        )
        assert response.status_code in [200, 201]


# Step 3: Template Engine Tests
class TestTemplateEngine:
    """Test Phase 4 Step 3: Prompt Template Editor"""

    def test_parse_template_variables(self):
        """Test parsing template variables"""
        from app.services.template_service import TemplateService
        
        service = TemplateService()
        template = "Hello {{firstName}} {{lastName}}"
        
        result = service.parse(template)
        
        assert result["isValid"] == True
        assert "firstName" in result["variables"]
        assert "lastName" in result["variables"]

    def test_render_template(self):
        """Test rendering template with context"""
        from app.services.template_service import TemplateService
        
        service = TemplateService()
        template = "Hello {{name}}"
        context = {"name": "Alice"}
        
        result = service.render(template, context)
        
        assert result["isValid"] == True
        assert result["content"] == "Hello Alice"

    def test_template_with_default_values(self):
        """Test template with default values"""
        from app.services.template_service import TemplateService
        
        service = TemplateService()
        template = "Welcome {{name:User}}"
        context = {}  # name not provided
        
        result = service.render(template, context)
        
        assert result["content"] == "Welcome User"

    def test_invalid_template_syntax(self):
        """Test template with invalid syntax"""
        from app.services.template_service import TemplateService
        
        service = TemplateService()
        template = "Hello {{invalid-name}}"  # Invalid variable name
        
        result = service.parse(template)
        
        assert result["isValid"] == False
        assert len(result["errors"]) > 0

    def test_template_with_filters(self):
        """Test template with variable filters"""
        from app.services.template_service import TemplateService
        
        service = TemplateService()
        template = "Hello {{name|upper}}"
        context = {"name": "alice"}
        
        result = service.render(template, context)
        
        assert result["content"] == "Hello ALICE"

    def test_save_template(self, client, sample_template):
        """Test saving template"""
        response = client.post(
            "/api/v1/templates",
            json=sample_template
        )
        assert response.status_code in [200, 201]
        data = response.json()
        assert data["id"] == sample_template["id"]

    def test_get_templates(self, client):
        """Test retrieving templates"""
        response = client.get("/api/v1/templates")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_apply_template_to_message(self, client):
        """Test applying template to message"""
        response = client.post(
            "/api/v1/templates/apply",
            json={
                "template_id": "template-1",
                "variables": {
                    "name": "Alice",
                    "topic": "workflows"
                }
            }
        )
        assert response.status_code == 200


# Step 4: Context Control Tests
class TestContextControl:
    """Test Phase 4 Step 4: Context Control and Optimization"""

    def test_create_context_items(self):
        """Test creating context items from workflow"""
        from app.services.context_service import ContextService
        
        service = ContextService()
        workflow_data = {
            "nodes": [
                {"id": "1", "type": "llm", "label": "LLM"},
                {"id": "2", "type": "search", "label": "Search"}
            ],
            "edges": []
        }
        
        items = service.create_context_items(workflow_data)
        
        assert len(items) == 2
        assert all(item["tokens"] > 0 for item in items)

    def test_estimate_tokens(self):
        """Test token estimation"""
        from app.services.context_service import ContextService
        
        service = ContextService()
        text = "x" * 400  # 400 chars
        tokens = service.estimate_tokens(text)
        
        assert tokens == 100  # 400 / 4

    def test_analyze_context(self):
        """Test context analysis"""
        from app.services.context_service import ContextService
        
        service = ContextService()
        workflow_data = {
            "nodes": [
                {"id": str(i), "type": "default", "label": f"Node {i}"}
                for i in range(15)
            ],
            "edges": []
        }
        
        items = service.create_context_items(workflow_data)
        analysis = service.analyze(items)
        
        assert analysis["totalItems"] == 15
        assert "suggestions" in analysis

    def test_optimize_for_token_limit(self):
        """Test context optimization for token limit"""
        from app.services.context_service import ContextService
        
        service = ContextService()
        workflow_data = {
            "nodes": [
                {"id": "1", "type": "llm", "label": "LLM"},
                {"id": "2", "type": "search", "label": "Search"},
                {"id": "3", "type": "output", "label": "Output"}
            ],
            "edges": []
        }
        
        items = service.create_context_items(workflow_data)
        optimized = service.optimize_for_token_limit(items, 100)
        
        # Should select high importance items first
        selected_tokens = sum(
            item["tokens"] for item in optimized 
            if item.get("selected", False)
        )
        assert selected_tokens <= 100

    def test_serialize_context(self, client):
        """Test context serialization"""
        response = client.post(
            "/api/v1/context/serialize",
            json={
                "nodes": [{"id": "1", "label": "Test"}],
                "edges": []
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "nodes" in data
        assert "edges" in data

    def test_get_context_suggestions(self, client):
        """Test getting context suggestions"""
        response = client.post(
            "/api/v1/context/suggestions",
            json={
                "nodes": [
                    {"id": "1", "type": "llm"},
                    {"id": "2", "type": "search"}
                ],
                "edges": []
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)


# End-to-End Integration Tests
class TestEndToEndIntegration:
    """End-to-end workflow tests"""

    @pytest.mark.asyncio
    async def test_full_chat_workflow(self, async_client):
        """Test complete chat workflow"""
        # 1. Start streaming chat
        async with async_client.stream(
            "POST",
            "/api/v1/copilot/stream/chat",
            json={"message": "Analyze my workflow", "model": "gpt-4o"}
        ) as response:
            assert response.status_code == 200
            events = []
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        events.append(json.loads(line[6:]))
                    except:
                        pass
            
            assert len(events) > 0

    @pytest.mark.asyncio
    async def test_template_with_context_workflow(self, async_client):
        """Test template application within context"""
        # 1. Save template
        # 2. Apply with context
        # 3. Get suggestion
        response = await async_client.post(
            "/api/v1/templates",
            json={
                "id": "wf-template-1",
                "name": "Query",
                "content": "Query {{query}} in {{context}}"
            }
        )
        assert response.status_code in [200, 201]

    @pytest.mark.asyncio
    async def test_context_optimization_workflow(self, async_client):
        """Test context selection and optimization"""
        # 1. Create context from workflow
        # 2. Analyze for suggestions
        # 3. Optimize for token limit
        # 4. Use in request
        response = await async_client.post(
            "/api/v1/context/suggestions",
            json={
                "nodes": [
                    {"id": "1", "type": "llm", "label": "LLM"},
                    {"id": "2", "type": "search", "label": "Search"}
                ],
                "edges": []
            }
        )
        assert response.status_code == 200


# Error Handling Tests
class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_empty_template(self):
        """Test handling empty template"""
        from app.services.template_service import TemplateService
        
        service = TemplateService()
        result = service.parse("")
        
        assert result["isValid"] == True
        assert result["variables"] == []

    def test_missing_context_variable(self):
        """Test handling missing context variables"""
        from app.services.template_service import TemplateService
        
        service = TemplateService()
        template = "Hello {{name}}"
        context = {}  # name missing
        
        result = service.render(template, context)
        
        assert result["isValid"] == False or len(result.get("warnings", [])) > 0

    def test_large_context(self):
        """Test handling very large context"""
        from app.services.context_service import ContextService
        
        service = ContextService()
        workflow_data = {
            "nodes": [
                {"id": str(i), "type": "default", "label": f"Node {i}"}
                for i in range(1000)
            ],
            "edges": []
        }
        
        items = service.create_context_items(workflow_data)
        assert len(items) == 1000

    def test_invalid_json(self, client):
        """Test handling invalid JSON"""
        response = client.post(
            "/api/v1/suggestions",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 422]

    def test_missing_required_field(self, client):
        """Test handling missing required fields"""
        response = client.post(
            "/api/v1/suggestions",
            json={"type": "improvement"}  # missing required fields
        )
        assert response.status_code in [400, 422]


# Performance Tests
class TestPerformance:
    """Test performance characteristics"""

    def test_template_rendering_performance(self):
        """Test template rendering is fast"""
        from app.services.template_service import TemplateService
        import time
        
        service = TemplateService()
        template = "Test {{var1}} {{var2}} {{var3}}"
        context = {"var1": "a", "var2": "b", "var3": "c"}
        
        start = time.time()
        for _ in range(10000):
            service.render(template, context)
        elapsed = time.time() - start
        
        # Should complete 10k renders in < 1 second
        assert elapsed < 1.0

    def test_context_analysis_performance(self):
        """Test context analysis is fast"""
        from app.services.context_service import ContextService
        import time
        
        service = ContextService()
        workflow_data = {
            "nodes": [
                {"id": str(i), "type": "default", "label": f"Node {i}"}
                for i in range(500)
            ],
            "edges": []
        }
        
        start = time.time()
        items = service.create_context_items(workflow_data)
        analysis = service.analyze(items)
        elapsed = time.time() - start
        
        # Should complete in < 100ms
        assert elapsed < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
