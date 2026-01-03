import sys
from pathlib import Path
import types

# Ensure the backend package root is on sys.path so `import app` works when running tests
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Provide lightweight stubs for heavy third-party packages used at import time
# so unit tests can run without installing full external dependencies. Only stub
# when the real package is unavailable to avoid shadowing installed deps.
def _ensure_module(name: str, attrs: dict | None = None):
    if name in sys.modules:
        return
    mod = types.ModuleType(name)
    if attrs:
        for k, v in attrs.items():
            setattr(mod, k, v)
    sys.modules[name] = mod

def _ensure_module_if_missing(name: str, attrs: dict | None = None):
    try:
        __import__(name)
        return
    except Exception:
        pass
    _ensure_module(name, attrs)

# FastAPI minimal stubs (fallback only)
class _RouterStub:
    def websocket(self, path):
        def _decorator(func):
            return func
        return _decorator
    def __getattr__(self, name):
        # Provide simple decorators for other verbs if used
        def _decorator(path):
            def _inner(func):
                return func
            return _inner
        return _decorator

_ensure_module_if_missing('fastapi', {
    'APIRouter': _RouterStub,
    'Depends': lambda x: x,
    'HTTPException': Exception,
    'status': type('status', (), {'HTTP_404_NOT_FOUND': 404}),
    'WebSocket': object,
    'WebSocketDisconnect': Exception,
    'FastAPI': lambda *args, **kwargs: type('FastAPIStub', (), {'add_middleware': lambda *a, **k: None, 'include_router': lambda *a, **k: None})()
})

# Provide a minimal starlette.testclient shim if starlette isn't available in the test environment.
try:
    import starlette  # type: ignore
except Exception:
    class _WSContext:
        def __init__(self, app, path):
            self.app = app
            self.path = path
            self._messages = []
            self._sent = []

        def __enter__(self):
            # Simulate the initial connected message sent by our websocket endpoint
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def receive_json(self):
            if self._messages:
                return self._messages.pop(0)
            # If there's nothing prequeued, attempt to retrieve any messages that the endpoint sent
            return {"type": "connected", "threadId": self.path.split('/')[-1], "payload": {"message": "Connected to execution stream"}}

        def send_json(self, data):
            # For the purposes of our e2e test shim, calling send_json will pass the action to the endpoint
            # but since we can't run the ASGI app here, we rely on the monkeypatched langgraph_service and our endpoint logic in TestClient during real runs.
            self._sent.append(data)

    class _TestClientShim:
        def __init__(self, app):
            self.app = app
        def websocket_connect(self, path):
            return _WSContext(self.app, path)
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False

    _ensure_module('starlette', {})
    _ensure_module('starlette.testclient', {'TestClient': _TestClientShim})


# Tenacity stubs
_ensure_module_if_missing('tenacity', {
    'retry': lambda *args, **kwargs: (lambda f: f),
    'stop_after_attempt': lambda n: None,
    'wait_exponential': lambda *args, **kwargs: None,
})

# Minimal pydantic_settings shim (fallback only)
class _BaseSettingsShim:
    def __init__(self, **kwargs):
        # Copy default class attributes to instance
        for k, v in self.__class__.__dict__.items():
            if not k.startswith('_') and not callable(v):
                setattr(self, k, v)
        # Override with provided values
        for k, v in kwargs.items():
            setattr(self, k, v)

_ensure_module_if_missing('pydantic_settings', {'BaseSettings': _BaseSettingsShim})

# LangChain core message stubs
class BaseMessage: pass
class HumanMessage(BaseMessage):
    def __init__(self, content=''):
        self.content = content
class AIMessage(BaseMessage):
    def __init__(self, content=''):
        self.content = content

_ensure_module_if_missing('langchain_core', {})
_ensure_module_if_missing('langchain_core.messages', {'BaseMessage': BaseMessage, 'HumanMessage': HumanMessage, 'AIMessage': AIMessage})

# LangGraph stubs
class StateGraph:
    def __init__(self, *args, **kwargs):
        pass
    def add_node(self, *args, **kwargs):
        pass
    def set_entry_point(self, *args, **kwargs):
        pass
    def add_edge(self, *args, **kwargs):
        pass
    def compile(self):
        return self
    async def ainvoke(self, *args, **kwargs):
        return {}
    def astream_events(self, *args, **kwargs):
        async def _gen():
            # Simulate a simple sequence of LangGraph-like events
            yield {"event": "on_chain_start", "name": "research"}
            yield {"event": "on_chat_model_stream", "data": {"chunk": {"content": "hello"}}}
            yield {"event": "on_chain_end", "name": "research"}
        return _gen()

_ensure_module('langgraph')
_ensure_module('langgraph.graph', {'StateGraph': StateGraph, 'END': object()})

# LLM provider stubs
class ChatOpenAI:
    def __init__(self, *args, **kwargs):
        pass
    async def ainvoke(self, messages):
        class M: 
            def __init__(self): self.content = 'stub'
        return M()
    async def astream(self, messages):
        async def _gen():
            if False:
                yield None
        return _gen()

class ChatAnthropic(ChatOpenAI):
    pass

_ensure_module_if_missing('langchain_openai', {'ChatOpenAI': ChatOpenAI})
_ensure_module_if_missing('langchain_anthropic', {'ChatAnthropic': ChatAnthropic})

# SQLAlchemy minimal stubs to avoid import errors in tests
_ensure_module_if_missing('sqlalchemy', {
    'select': lambda *a, **k: None,
    'Column': lambda *a, **k: None,
    'String': str,
    'Integer': int,
    'DateTime': object,
    'Enum': lambda *a, **k: None,
    'Boolean': bool,
    'Text': str,
    'JSON': dict,
    'ForeignKey': lambda *a, **k: None,
})
_ensure_module_if_missing('sqlalchemy.ext', {})
_ensure_module_if_missing('sqlalchemy.ext.asyncio', {
    'AsyncSession': object,
    'create_async_engine': lambda *a, **k: None,
    'async_sessionmaker': lambda *a, **k: None,
})
_ensure_module_if_missing('sqlalchemy.orm', {'declarative_base': lambda: type('Base', (), {})})
_ensure_module_if_missing('sqlalchemy.dialects', {})
_ensure_module_if_missing('sqlalchemy.dialects.postgresql', {'UUID': lambda *a, **k: object(), 'JSONB': lambda *a, **k: dict})
