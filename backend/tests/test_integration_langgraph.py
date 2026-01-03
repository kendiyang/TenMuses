import os
import pytest

from app.services.langgraph_service import LangGraphService


pytestmark = pytest.mark.integration


@pytest.mark.skipif(not os.environ.get('RUN_LANGGRAPH_INTEGRATION'), reason='Integration tests disabled')
@pytest.mark.asyncio
async def test_langgraph_integration_with_real_llm():
    """Optional integration test that runs LangGraph against a real LLM provider.
    Enable by setting RUN_LANGGRAPH_INTEGRATION=1 and providing valid OPENAI_API_KEY / ANTHROPIC_API_KEY in env.
    """
    svc = LangGraphService()
    svc.create_static_workflow()

    # Execute workflow (non-streaming) and assert it returns a dict-like state
    result = await svc.execute_workflow('Integration test: summarize AI trends')
    assert isinstance(result, dict)
    assert 'final_content' in result or 'draft_content' in result
