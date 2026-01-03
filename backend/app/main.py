from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

# 配置日志
logger = logging.getLogger(__name__)

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1 import (
    auth,
    workflows,
    websocket,
    dynamic,
    knowledge,
    copilot,
    llm_config,
    suggestions,
    templates,
    context,
    config,
)
from app.api.v1 import llm_provider_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting TenMuses API Server...")
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created")
    
    yield
    
    # Shutdown
    print("👋 Shutting down TenMuses API Server...")
    await engine.dispose()

app = FastAPI(
    title="TenMuses API",
    description="AI Workflow Orchestration Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加请求日志中间件
@app.middleware("http")
async def log_requests(request, call_next):
    logger.info(f"📨 {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"✅ {request.method} {request.url.path} -> {response.status_code}")
    return response

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["workflows"])
app.include_router(dynamic.router, prefix="/api", tags=["dynamic"])
app.include_router(websocket.router, prefix="/api/v1", tags=["websocket"])
app.include_router(knowledge.router, prefix="/api/v1", tags=["knowledge"])
app.include_router(copilot.router, prefix="/api/v1", tags=["copilot"])
app.include_router(llm_config.router, prefix="/api/v1", tags=["llm-config"])
app.include_router(llm_provider_model.router, prefix="/api/v1", tags=["llm-provider-model"])
app.include_router(config.router, prefix="/api/v1", tags=["config"])
app.include_router(suggestions.router, prefix="/api/v1", tags=["suggestions"])
app.include_router(templates.router, prefix="/api/v1", tags=["templates"])
app.include_router(context.router, prefix="/api/v1", tags=["context"])

@app.get("/")
async def root():
    return {
        "message": "TenMuses API",
        "version": "0.1.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
