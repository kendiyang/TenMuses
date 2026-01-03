import pytest

from app.services.langgraph_service import LangGraphService, langgraph_service


@pytest.mark.asyncio
async def test_create_static_workflow_compiles():
    svc = LangGraphService()
    graph = svc.create_static_workflow()
    assert graph is not None


@pytest.mark.asyncio
async def test_stream_workflow_yields_events(monkeypatch):
    # Mock llm_client.invoke to return a predictable object
    async def fake_invoke(messages, provider="openai", model=None, **kwargs):
        class M:
            def __init__(self, content):
                self.content = content
        return M("fake-response")

    monkeypatch.setattr('app.services.langgraph_service.llm_client.invoke', fake_invoke)

    svc = LangGraphService()
    svc.create_static_workflow()

    events = []
    # Only collect a few events to assert on
    async for e in svc.stream_workflow("test input"):
        events.append(e)
        if len(events) >= 3:
            break

    assert any(e.get("event") in ("on_chain_start", "on_chain_end", "on_chat_model_stream") for e in events)
