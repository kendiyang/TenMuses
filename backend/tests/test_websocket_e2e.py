import pytest

# Skip this E2E test if FastAPI/Starlette aren't properly installed in the environment (requires real FastAPI/Starlette to run)
try:
    import fastapi as _fastapi
    import starlette as _starlette
    _ws_ready = hasattr(_fastapi, 'middleware') and hasattr(_starlette, 'testclient')
except Exception:
    _ws_ready = False

pytestmark = pytest.mark.skipif(not _ws_ready, reason='FastAPI/Starlette not fully available; skipping WebSocket e2e test')

from starlette.testclient import TestClient


@pytest.mark.parametrize("thread_id", ["thread-e2e-1"])
def test_websocket_run_streams_events(monkeypatch, thread_id):
    # Import app here so module import doesn't fail in environments without full FastAPI
    from app.main import app

    sent = []

    # Create an async generator simulating LangGraph events
    async def fake_stream(input_text: str):
        yield {"event": "on_chain_start", "name": "research"}
        yield {"event": "on_chat_model_stream", "data": {"chunk": {"content": "hello"}}}
        yield {"event": "on_chain_end", "name": "research"}

    # Patch stream_workflow implementation
    monkeypatch.setattr('app.services.langgraph_service.langgraph_service.stream_workflow', lambda input_text: fake_stream(input_text))

    with TestClient(app) as client:
        with client.websocket_connect(f"/ws/run/{thread_id}") as ws:
            # initial connected message
            msg = ws.receive_json()
            assert msg.get('type') == 'connected'

            # send start action
            ws.send_json({"action": "start", "input": "test input"})

            types = set()
            # Collect messages until run_completed or timeout
            for _ in range(10):
                m = ws.receive_json()
                types.add(m.get('type'))
                if m.get('type') == 'run_completed':
                    break

            assert 'run_started' in types
            assert 'node_started' in types
            assert 'token' in types
            assert 'node_status' in types
            assert 'run_completed' in types
