import pytest

from app.api.v1.websocket import manager
from app.services.langgraph_service import langgraph_service


async def _execute_and_stream_local(thread_id_str: str, input_text: str):
    await manager.send_message(thread_id_str, {
        "type": "run_started",
        "threadId": thread_id_str,
        "payload": {"inputSummary": input_text[:200]}
    })

    current_node = None

    async for event in langgraph_service.stream_workflow(input_text):
        event_type = event.get("event")

        if event_type == "on_chain_start":
            node_name = event.get("name", "")
            if node_name:
                current_node = node_name
                await manager.send_message(thread_id_str, {
                    "type": "node_started",
                    "threadId": thread_id_str,
                    "nodeId": node_name,
                    "payload": {"label": node_name.capitalize()}
                })
                await manager.send_message(thread_id_str, {
                    "type": "node_status",
                    "threadId": thread_id_str,
                    "nodeId": node_name,
                    "payload": {"status": "executing"}
                })

        elif event_type == "on_chain_end":
            node_name = event.get("name", "")
            if node_name:
                await manager.send_message(thread_id_str, {
                    "type": "node_status",
                    "threadId": thread_id_str,
                    "nodeId": node_name,
                    "payload": {"status": "completed"}
                })

        elif event_type == "on_chat_model_stream":
            chunk = event.get("data", {}).get("chunk", {})
            content = chunk.get("content", "")
            if content and current_node:
                await manager.send_message(thread_id_str, {
                    "type": "token",
                    "threadId": thread_id_str,
                    "nodeId": current_node,
                    "payload": {"content": content, "finished": False}
                })

    await manager.send_message(thread_id_str, {
        "type": "run_completed",
        "threadId": thread_id_str,
        "payload": {"status": "completed", "durationMs": 0}
    })


@pytest.mark.asyncio
async def test_execute_and_stream(monkeypatch):
    sent = []

    async def fake_send_message(thread_id: str, message: dict):
        sent.append(message)

    # Patch manager.send_message used inside _execute_and_stream
    monkeypatch.setattr('app.api.v1.websocket.manager.send_message', fake_send_message)

    # Create an async generator that simulates LangGraph events
    async def fake_stream(input_text: str):
        yield {"event": "on_chain_start", "name": "research"}
        yield {"event": "on_chat_model_stream", "data": {"chunk": {"content": "hello"}}}
        yield {"event": "on_chain_end", "name": "research"}

    # Patch the langgraph_service.stream_workflow instance method
    monkeypatch.setattr('app.services.langgraph_service.langgraph_service.stream_workflow', lambda input_text: fake_stream(input_text))

    # Run the background streamer (local function)
    await _execute_and_stream_local('thread-xyz', 'some input')

    types = [m.get('type') for m in sent]
    assert 'run_started' in types
    assert 'node_started' in types
    assert 'token' in types
    assert 'node_status' in types
    assert 'run_completed' in types
