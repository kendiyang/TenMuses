# TenMuses - AI Workflow Orchestration Platform

TenMuses 是一个基于可视化画布的 AI 工作流编排平台，支持多智能体协作、人在回路（HITL）、知识库检索（RAG）等高级功能。

## 🎯 项目特性

- **可视化工作流编辑器**：基于 React Flow 的无限画布，拖拽式构建 AI 工作流
- **多智能体编排**：支持 LangGraph 动态图构建，实现复杂的智能体协作模式
- **实时流式输出**：WebSocket 实时推送执行状态和 Token 流
- **人在回路（HITL）**：支持工作流执行过程中的人工干预和确认
- **知识库集成（RAG）**：文档上传、向量化检索，增强 AI 输出质量
- **模板市场**：分享、购买、Fork 工作流模板，支持创作者变现
- **实时协作**：基于 Yjs 的多人协作编辑

## 📁 项目结构

```
TenMuses/
├── frontend/          # Next.js 前端应用
│   ├── src/
│   │   ├── app/      # Next.js App Router 页面
│   │   ├── components/  # React 组件
│   │   ├── lib/      # 工具库（API 客户端、WebSocket 等）
│   │   ├── stores/   # Zustand 状态管理
│   │   └── types/    # TypeScript 类型定义
│   └── package.json
│
├── backend/           # FastAPI 后端应用
│   ├── app/
│   │   ├── api/      # API 路由
│   │   ├── core/     # 核心配置（数据库、安全等）
│   │   ├── models/   # SQLAlchemy 数据模型
│   │   ├── schemas/  # Pydantic 数据模式
│   │   └── services/ # 业务逻辑服务
│   └── requirements.txt
│
├── services/          # 微服务
│   ├── graph-orchestrator/  # LangGraph 编排服务
│   └── workflow-service/    # 工作流执行服务
│
├── docs/             # 文档
│   ├── design.md     # 详细设计文档
│   └── analysis.md   # 需求分析
│
└── README.md
```

## 🚀 快速开始

### 前置要求

- Node.js 18+
- Python 3.11+
- PostgreSQL 14+
- OpenAI API Key 或 Anthropic API Key

### 1. 克隆项目

```bash
git clone <repository-url>
cd TenMuses
```

### 2. 设置后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入数据库连接和 API Keys

# 启动服务
python -m app.main
```

后端将在 `http://localhost:8000` 启动

### 3. 设置前端

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.local.example .env.local

# 启动开发服务器
npm run dev
```

前端将在 `http://localhost:3000` 启动

### 4. 设置数据库

```bash
# 创建数据库
createdb tenmuses

# 数据库会在后端启动时自动创建表结构
```

## 📖 开发阶段

项目采用分阶段开发策略：

### Phase 0: 基础设施（当前阶段）✅
- [x] 前端工程搭建（Next.js + TypeScript + Tailwind）
- [x] 后端工程搭建（FastAPI + SQLAlchemy）
- [x] 数据库模型设计
- [x] 基础认证系统（JWT）
- [x] LLM 客户端封装

### Phase 1: MVP - 基础画布 + 静态执行（进行中）
- [ ] React Flow 画布基础功能
- [ ] 简单节点类型（Research、Writer、Reviewer）
- [ ] 静态 LangGraph 工作流
- [ ] WebSocket 流式输出
- [ ] 工作流持久化

### Phase 2: Enhanced MVP
- [ ] 动态图构建工厂
- [ ] HITL 中断机制
- [ ] RAG 知识库集成
- [ ] CopilotKit 集成

### Phase 2.5: 模板市场
- [ ] 模板发布与管理
- [ ] 支付集成（Stripe）
- [ ] 创作者中心

### Phase 3: Production
- [ ] 多人协作（Yjs）
- [ ] MCP 深度集成
- [ ] 监控与可观测性
- [ ] 安全与合规

## 🛠️ 技术栈

### 前端
- **框架**: Next.js 14 (App Router)
- **语言**: TypeScript
- **UI**: Tailwind CSS
- **画布**: React Flow
- **状态管理**: Zustand
- **数据获取**: TanStack Query
- **WebSocket**: 原生 WebSocket API

### 后端
- **框架**: FastAPI
- **语言**: Python 3.11+
- **数据库**: PostgreSQL + SQLAlchemy
- **认证**: JWT (python-jose)
- **AI 框架**: LangChain + LangGraph
- **LLM**: OpenAI / Anthropic

## 📝 API 文档

启动后端服务后，访问以下地址查看 API 文档：

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🤝 贡献指南

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 📄 许可证

[MIT License](LICENSE)

## 🔗 相关链接

- [详细设计文档](docs/design.md)
- [需求分析](docs/analysis.md)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [React Flow 文档](https://reactflow.dev/)
## 集成测试（可选）

集成测试会与真实的 LLM 提供商和 LangGraph 运行时交互，可能会产生 API 调用费用。出于安全和成本考虑，这些测试默认不在 CI 中自动运行。

如何在本地运行集成测试：

1. 在仓库根目录设置环境变量：

```bash
export RUN_LANGGRAPH_INTEGRATION=1
export OPENAI_API_KEY="sk-..."  # 或 ANTHROPIC_API_KEY
```

2. 在 `backend` 虚拟环境中运行：

```bash
cd backend
pytest -q -m integration
```

在 GitHub Actions 中运行：

- 将 `OPENAI_API_KEY`（或 `ANTHROPIC_API_KEY`）添加到仓库 Secrets。
- 在 `.github/workflows/backend-tests.yml` 中将 `RUN_LANGGRAPH_INTEGRATION` 设为 `true`（或触发的是集成测试 workflow，见下文）。

注意：`scripts/run-integration.sh` 会在本地检测不到 Postgres 时自动尝试用 Docker 启动一个名为 `tenmuses-integration-db` 的 Postgres 容器（需要安装 Docker 并有权限运行 Docker 命令）。

使用 docker-compose（可选）

如果你更喜欢使用 docker-compose 管理集成环境，我们提供了 `docker-compose.integration.yml`，用法如下：

```bash
# 启动（后台）
docker-compose -f docker-compose.integration.yml up -d

# 停止并移除容器
docker-compose -f docker-compose.integration.yml down
```

将 docker-compose 与集成脚本配合使用：

```bash
# 在另外一个终端准备好环境变量
export RUN_LANGGRAPH_INTEGRATION=1
export OPENAI_API_KEY="sk-..."
# 启动集成服务（Postgres + Redis + MinIO）
docker-compose -f docker-compose.integration.yml up -d
# 运行集成测试
./scripts/run-integration.sh
# 清理
docker-compose -f docker-compose.integration.yml down
```

本 compose 文件还会启动：
- Redis（默认端口 `6379`）
- MinIO（API 端口 `9000`，默认 `MINIO_ROOT_USER=minioadmin` / `MINIO_ROOT_PASSWORD=minioadmin`）

MinIO 的凭据可以通过环境变量 `MINIO_ROOT_USER` 和 `MINIO_ROOT_PASSWORD` 来覆盖，脚本与 docker-compose 会读取这些变量以便在 CI/本地保持一致。

CI：集成测试工作流（`Integration tests (on-demand)`）现已使用 `docker-compose.integration.yml` 启动 Postgres/Redis/MinIO（通过 `docker compose up -d`），并在测试完成后自动清理（`docker compose down -v`）。如需在仓库 Actions 中运行此工作流，请在 GitHub Secrets 中添加你的 `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`，然后在 Actions -> Workflows 手动触发 `Integration tests (on-demand)`。

可配置的本地集成环境（可选）

- 为方便本地调试，你可以复制仓库根目录下的 `.env.integration.example` 为 `.env.integration`，并根据需要修改以下变量：
  - `POSTGRES_CONTAINER`, `POSTGRES_IMAGE`
  - `REDIS_CONTAINER`, `REDIS_IMAGE`
  - `MINIO_CONTAINER`, `MINIO_IMAGE`
  - `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD`
  - `DATABASE_URL`（可选）

- `scripts/run-integration.sh` 会优先加载 `.env.integration`（如果存在），并据此启动/复用容器。这样可以让团队更容易共享和复现集成环境配置。

这样可以让本地与 CI 的集成环境行为一致，更易复现与排查问题。

## 📧 联系方式

如有问题或建议，请提交 Issue 或联系项目维护者。

Quick start (suggested):

- Backend: see backend/requirements.txt and backend/app/main.py
- Frontend: see frontend/README.md

Next steps:
- Install backend dependencies and run `uvicorn backend.app.main:app --reload`
- Initialize frontend with `npm install` (if using Next.js)
