# TenMuses — design.md 深度分析

## 概要
`design.md` 描述了一个以画布 + 工作流为核心、支持多智能体编排、HITL（人在回路）、RAG 和模板市场的复杂平台。核心目标是让用户通过可视化工作流构建和执行复杂的 AI 流程，并为创作者提供变现渠道。

## 关键模块与优先级（摘录）
- Canvas & Workflow（前端 React Flow） — 高优先级（MVP 必需）
- Workflow Service / LangGraph 集成（后端） — 高优先级
- Execution Orchestrator（动态图编译、节点执行） — 中高优先级
- HITL、RAG、Copilot 集成、模板市场 — 中期功能
- 协作（Yjs）、监控、MCP 集成、支付 — 生产级迭代项

## 技术建议（与文档一致）
- 前端：Next.js + TypeScript + React Flow
- 后端：FastAPI + Uvicorn；LangGraph / LangChain 作执行层
- 数据库：PostgreSQL；向量检索：pgvector / Chroma
- 协作：Yjs + Hocuspocus / y-websocket
- 缓存/队列：Redis（会话、速率限制、任务队列）

## 风险与待决事项
- 动态图到执行图的语义映射需反复打磨（节点 schema 与边条件）
- LLM 成本和速率需设计埋点与限额策略（Prometheus 指标）
- HITL 的 UX 需要前端与后端紧密合作（中断、恢复、版本管理）
- 支付与分账合规性（不同地区税务/提现）

## 建议的仓库目录结构（单仓 monorepo）
- backend/ — FastAPI 服务
  - app/
    - main.py
    - api/
    - core/
    - services/
- frontend/ — Next.js 前端
- services/
  - graph-orchestrator/
  - workflow-service/
- scripts/ — 部署/辅助脚本
- tests/ — 单元与集成测试
- docs/ — 设计与分析文档

## 近期可执行的工作（优先级顺序）
1. Phase0 骨架：Next.js 基础画布 demo + FastAPI 最小 API（health、auth stub）
2. Phase1 MVP：持久化工作流、静态 LangGraph 流程、WebSocket Token 流式输出
3. Phase2：动态图编译、HITL、RAG、Copilot 初步集成

## 本次提交（已创建）
- 初始化仓库目录与占位文件
- 新增 `docs/analysis.md`（本文件）以便快速对齐

如需，我可以：
- 根据偏好生成可运行的后端（完整 requirements + uvicorn 启动脚本）
- scaffold 前端 Next.js 项目并集成 React Flow demo
- 将 design.md 的 API 段落拆成 OpenAPI 模板

请告诉我你要优先进行的下一步。