# Copilot / AI Agent Instructions for TenMuses

Quick, targeted guidance to help an AI coding agent be productive in this repo.

## Big-picture architecture
- **Frontend**: Next.js (App Router), TypeScript, Tailwind. Entry: `frontend/src/app`. UI uses React Flow for the visual workflow canvas and Zustand for client state.
- **Backend**: FastAPI (async) with SQLAlchemy async ORM. Entry: `backend/app/main.py` (runs `uvicorn app.main:app`).
- **Services**: `services/graph-orchestrator` and `services/workflow-service` are placeholders for additional microservices integrating LangGraph and workflow runners.
- **AI Layer**: `backend/app/services/llm_client.py` (OpenAI / Anthropic integration) and `backend/app/services/langgraph_service.py` (builds LangGraph workflows and streams events).

## How to run (developer workflows) ✅
- Backend:
  - Install: `cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
  - Configure: copy `.env.example` → `.env` and set `DATABASE_URL`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `JWT_SECRET_KEY`.
  - Run (dev): `uvicorn app.main:app --reload` or `python -m app.main` (the latter calls uvicorn per `main.py`).
  - API docs: `http://localhost:8000/docs`
- Frontend:
  - Install: `cd frontend && npm install`
  - Configure: copy `env.local.example` → `.env.local` and set `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_WS_URL`.
  - Run (dev): `npm run dev` (default `http://localhost:3000`).
- DB: create DB (e.g., `createdb tenmuses`); tables are auto-created on backend startup via `Base.metadata.create_all`.

## Key patterns and conventions (do these exactly) 🔧
- **Async everywhere (backend)**: Use `AsyncSession`, `async def` handlers, and `await` idioms. Use `get_db()` dependency which yields an `AsyncSession` and commits on successful yield.
- **Pydantic v2 + SQLAlchemy interop**: Many response models use `model_validate()` (from Pydantic v2) and schemas use `Config.from_attributes = True` so convert SQLAlchemy models to Pydantic responses via `WorkflowResponse.model_validate(sqlalchemy_obj)`.
- **Auth flow**: JWT auth via `app.core.security` (create/verify tokens). Protected endpoints use `get_current_user` dependency which expects a `Bearer` token.
- **LLM usage**:
  - Use `llm_client.invoke(...)` for non-streaming calls and `llm_client.stream(...)` for streaming. Provider names: `"openai"` or `"anthropic"`.
  - Default models are set in `llm_client` (e.g., `gpt-4-turbo-preview`, `claude-3-sonnet-20240229`). Respect `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` env vars.
- **LangGraph workflow structure**:
  - Static example in `LangGraphService.create_static_workflow()` shows nodes: `research` → `writer` → `reviewer`.
  - To add nodes, implement async node functions that accept and return the typed `WorkflowState` and then `add_node(...)`, `add_edge(...)`, `compile()`.
  - Streaming events: `graph.astream_events(..., version="v1")` yields events with types used by the backend WebSocket streamer (see below).

## Integration points & message shapes (important for features) 📡
- **WebSocket endpoint**: `GET /ws/run/{thread_id}` (see `backend/app/api/v1/websocket.py`).
  - Expected client action: send `{"action":"start","input":"..."}` to start a run.
  - Common event types emitted:
    - `connected` — initial handshake
    - `run_started` / `run_completed`
    - `node_started` / `node_status` (payload includes `nodeId`, `status`, `label`)
    - `token` — streaming token fragments: payload `{ content: string, finished: bool }` (client uses these to progressively render output)
    - `error` — `{ message, code, fatal }`
- **Frontend WebSocket client**: `frontend/src/lib/websocket-client.ts` — uses `type` field to route events; supports wildcard listeners under `'*'`.
- **API base path**: `frontend` Axios client is configured with `baseURL: ${API_URL}/api/v1` and uses `localStorage` key `accessToken` for JWT auth.

## Where to change things (concrete file references) 📌
- Add backend API routes: `backend/app/api/v1/*.py` (currently `auth.py`, `workflows.py`, `websocket.py`).
- Add DB models: `backend/app/models/*.py` and corresponding Pydantic schemas: `backend/app/schemas/*.py` (remember `from_attributes = True` for responses).
- Add LLM/Graph nodes: `backend/app/services/langgraph_service.py` (see `create_static_workflow`).
- Client-side UI/behavior: `frontend/src/components/` and `frontend/src/app/workflows` pages.

## Useful examples (copyable snippets) ✂️
- Start a workflow run response includes `ws_url`:
  - `ws://localhost:8000/ws/run/{thread_id}` — the frontend connects to this and sends `{"action":"start","input":"..."}`.
- Stream tokens from a node (backend event sample):
  - `{ "type":"token", "threadId":"...", "nodeId":"writer", "payload": { "content": "...", "finished": false }}`

## Gaps & caveats (what an agent should watch out for) ⚠️
- No DB migration tooling committed (Alembic not present); schema changes are currently applied via `Base.metadata.create_all`.
- `services/` microservices are scaffolds; check with maintainers before implementing distributed runtimes.
- Tests are sparse/missing — verify behavior manually when adding features.

---
If anything here is unclear or you want me to expand with suggested PR templates, example unit tests, or a checklist for adding new LangGraph nodes, tell me which area to flesh out next. ✅