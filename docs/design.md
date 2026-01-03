以下文档按「可直接落地实施」的粒度编写，涵盖：

1. 系统与模块设计  
2. 数据库设计（核心表 + 关系）  
3. 前后端交互与通信协议  
4. 主要接口设计（REST / WebSocket）  
5. 分阶段实施路线图（MVP → 生产级）  
6. 分阶段 TODO 列表（可直接导入项目管理工具）

---

# 一、系统与模块设计

## 1.1 系统总体架构

### 1.1.1 分层视图

- **客户端层（Web / 后续可扩展 Desktop）**
  - 技术栈：Next.js (React)、TypeScript
  - 子模块：
    - 无限画布工作台（React Flow）
    - Workflow Copilot（CopilotKit）
    - 模板市场（Template Marketplace）
    - 创作者中心（Creator Dashboard）
    - 实时协作 UI（Yjs + Awareness）
- **服务网关层（API Gateway）**
  - 技术栈：FastAPI + Uvicorn
  - 职责：
    - REST API（CRUD / 业务逻辑）
    - WebSocket（执行流 + HITL）
    - 认证与鉴权（JWT / OAuth）
- **编排与执行层（Orchestration & Agents）**
  - 技术栈：LangGraph + LangChain
  - 职责：
    - 动态图构建工厂（Dynamic Graph Factory）
    - 多智能体编排（Supervisor / Map-Reduce 等模式）
    - HITL 中断与恢复
    - RAG 检索与上下文管理
    - MCP 工具接入
- **协作与同步层（Collaboration）**
  - 技术栈：Yjs + y-websocket / Hocuspocus
  - 职责：
    - 多人画布协作
    - 光标与选区同步
    - 画布状态持久化（与 Workflow 模型互通）
- **数据与存储层**
  - PostgreSQL：业务数据 + LangGraph Checkpoint
  - 向量库（Chroma / pgvector）：知识库与模板语义检索
  - 对象存储（S3 / R2）：预览图、附件
  - 缓存（Redis）：会话状态、速率限制、热数据
- **第三方与支付层**
  - LLM 提供商：OpenAI / Anthropic 等
  - 支付：Stripe / 支付宝 / PayPal（按地区扩展）
  - MCP Server：GitHub、Slack、内部 API 等

### 1.1.2 逻辑模块划分

#### A. 画布与工作流模块（Canvas & Workflow）

- `canvas-frontend`
  - React Flow 画布
  - 自定义智能节点组件（Smart Nodes）
  - Workflow 属性面板
  - 执行状态展示（流式 Token、日志、可视化 Tool 调用）
- `workflow-service`
  - 工作流 CRUD（保存、加载、克隆、版本管理）
  - 工作流执行 API（调用 LangGraph）
  - 与 LangGraph Checkpointer 集成（线程与时间旅行）

#### B. 执行与智能体模块（Agents & Execution）

- `graph-orchestrator`
  - 动态图构建工厂：将前端 JSON（nodes + edges）转换为 LangGraph `StateGraph`
  - 节点执行器库：LLM 节点、Tool 节点、Router 节点、Map-Reduce 节点等
  - 条件边逻辑（LLM 输出 → 下一步路由）
- `hitl-engine`
  - 节点级中断配置与执行（`interrupt_before`）
  - 用户修改输入后恢复执行（`Command(resume=...)`）

#### C. Copilot 与语义控制模块

- `copilot-frontend`
  - Copilot Chat 面板
  - `useCopilotReadable`：选择性暴露画布状态
  - `useCopilotAction`：自然语言驱动 UI 操作（添加节点、连线、重命名等）
- `copilot-bridge`
  - 将 Copilot 前端上下文显式注入 LangGraph 初始 State
  - 解决 CopilotKit 与 LangGraph 的数据断层问题

#### D. 模板市场与 UGC 模块（Template Marketplace & UGC）

- `marketplace-service`
  - 模板发布 / 审核 / 搜索 / 浏览 / 下载计数
  - 模板版本管理（变更记录）
- `monetization-service`
  - 价格模型（免费 / 打赏 / 一次性付费 / 订阅）
  - 支付与分账（平台抽成 + 创作者收益）
  - 钱包与提现
- `social-service`
  - 评分与评论
  - 收藏 / 关注 / Fork 关系
  - 模板推荐（热门、相关）

#### E. 知识库与 RAG 模块

- `knowledge-service`
  - 文档上传 / 分片 / 向量化
  - 相似度检索（面向特定工作流 / 用户）
- `rag-integration`
  - 将检索结果嵌入 LLM 节点 Prompt
  - 节点级配置是否启用 RAG

#### F. 实时协作模块

- `collaboration-service`
  - Yjs WebSocket 同步服务
  - Canvas 状态（nodes / edges / viewport）的 CRDT 持久化
  - 与 `workflows` 表的映射（每个 Workflow 对应一个 Y.Doc）

#### G. 监控与可观测性模块

- `observability`
  - Prometheus 指标：执行次数、时延、失败率、Token 用量
  - OpenTelemetry Tracing：工作流级 Trace、节点级 Span
  - 日志聚合（ELK / Loki）

---

# 二、数据库设计

以下是核心业务表的逻辑结构（省略技术字段如 `deleted_at`、审计字段时可按需扩展）。

## 2.1 用户与权限

### 2.1.1 用户表 `users`

| 字段           | 类型           | 说明                          |
|----------------|----------------|-------------------------------|
| `id`           | UUID PK        | 用户 ID                       |
| `email`        | VARCHAR        | 邮箱（唯一）                 |
| `username`     | VARCHAR        | 昵称                          |
| `password_hash`| VARCHAR        | 密码哈希（如使用本地登录）   |
| `avatar_url`   | VARCHAR        | 头像                          |
| `role`         | VARCHAR        | `user` / `admin`             |
| `creator_level`| INT            | 创作者等级 $1$–$4$           |
| `created_at`   | TIMESTAMP      | 创建时间                      |
| `updated_at`   | TIMESTAMP      | 更新时间                      |

### 2.1.2 鉴权相关（可选）

- `auth_providers`（第三方 OAuth）
- `api_keys`（如需开放 API）

## 2.2 工作流与执行

### 2.2.1 工作流表 `workflows`

| 字段                | 类型      | 说明                                      |
|---------------------|-----------|-------------------------------------------|
| `id`                | UUID PK   | 工作流 ID                                 |
| `owner_id`          | UUID FK   | 对应 `users.id`                          |
| `title`             | VARCHAR   | 工作流名称                                |
| `description`       | TEXT      | 描述                                      |
| `canvas_json`       | JSONB     | React Flow 的 `nodes`+`edges`+`viewport` |
| `source_template_id`| UUID FK   | 如由模板实例化，则记录模板 ID            |
| `is_public`         | BOOLEAN   | 是否对外公开（工作流分享）               |
| `created_at`        | TIMESTAMP | 创建时间                                  |
| `updated_at`        | TIMESTAMP | 更新时间                                  |

### 2.2.2 执行 Run 表 `workflow_runs`

| 字段          | 类型      | 说明                                  |
|---------------|-----------|---------------------------------------|
| `id`          | UUID PK   | Run ID                               |
| `workflow_id` | UUID FK   | 对应 `workflows.id`                 |
| `thread_id`   | UUID      | LangGraph 的 Thread 标识            |
| `status`      | VARCHAR   | `running` `completed` `failed` 等   |
| `input_summary`| TEXT     | 本次执行的用户输入摘要              |
| `started_at`  | TIMESTAMP | 开始时间                             |
| `finished_at` | TIMESTAMP | 结束时间                             |

### 2.2.3 LangGraph Checkpoint（简版）

可直接使用官方 `langgraph-checkpoint-postgres` 方案，对应表如：

- `checkpoints`
  - `thread_id`
  - `checkpoint_id`
  - `checkpoint_ns`
  - `values` (`JSONB`)
  - `metadata` (`JSONB`)
  - `created_at`

## 2.3 知识库（RAG）

### 2.3.1 文档表 `kb_documents`

| 字段         | 类型        | 说明                                   |
|--------------|-------------|----------------------------------------|
| `id`         | UUID PK     | 文档 ID                                |
| `user_id`    | UUID FK     | 文档所属用户                           |
| `workspace_id`| UUID FK?   | 如有空间/团队划分                     |
| `source_type`| VARCHAR     | `file` `url` `text`                    |
| `source_url` | VARCHAR     | 原始链接（如网页）                     |
| `content`    | TEXT        | 原始文本（全文或摘要）                |
| `embedding`  | VECTOR      | 向量（如维度 $1536$）                 |
| `metadata`   | JSONB       | 额外元数据                             |
| `created_at` | TIMESTAMP   |                                        |

索引：`IVFFLAT` on `embedding`（pgvector）或外部向量库。

## 2.4 模板市场与 UGC

### 2.4.1 模板表 `templates`

| 字段              | 类型       | 说明                                        |
|-------------------|------------|---------------------------------------------|
| `id`              | UUID PK    | 模板 ID                                     |
| `creator_id`      | UUID FK    | 创作者 ID                                  |
| `title`           | VARCHAR    | 标题                                        |
| `slug`            | VARCHAR    | URL 标识（唯一）                            |
| `description`     | TEXT       | 简短描述                                    |
| `long_description`| TEXT       | 详细描述（Markdown）                        |
| `category`        | VARCHAR    | 分类                                        |
| `tags`            | VARCHAR[]  | 标签                                        |
| `pricing_type`    | VARCHAR    | `free` `tip` `paid` `subscription`         |
| `price`           | DECIMAL    | 价格                                        |
| `currency`        | VARCHAR    | 货币，如 `USD`                              |
| `workflow_json`   | JSONB      | 模板工作流 JSON（含 inputs / outputs）    |
| `workflow_version`| INT        | 模板内部版本                               |
| `input_schema`    | JSONB      | 模板实例化所需参数定义                     |
| `preview_image_url`| VARCHAR   | 预览图                                      |
| `demo_video_url`  | VARCHAR    | 演示视频                                    |
| `downloads`       | INT        | 下载次数                                    |
| `views`           | INT        | 浏览次数                                    |
| `favorites`       | INT        | 收藏次数                                    |
| `rating_avg`      | DECIMAL    | 平均评分                                    |
| `rating_count`    | INT        | 评分数                                      |
| `status`          | VARCHAR    | `draft` `pending_review` `published` 等    |
| `visibility`      | VARCHAR    | `public` `unlisted` `private`              |
| `license_type`    | VARCHAR    | 授权类型 `personal` `commercial` 等       |
| `allow_fork`      | BOOLEAN    | 是否允许 Fork                              |
| `is_featured`     | BOOLEAN    | 是否精选                                    |
| `created_at`      | TIMESTAMP  |                                            |
| `updated_at`      | TIMESTAMP  |                                            |
| `published_at`    | TIMESTAMP  |                                            |

### 2.4.2 模板版本表 `template_versions`

- 记录每次发布前的旧版本，便于回滚 / 查看更新日志。

| 字段            | 类型      | 说明                 |
|-----------------|-----------|----------------------|
| `id`            | UUID PK   |                      |
| `template_id`   | UUID FK   |                      |
| `version`       | INT       |                      |
| `workflow_json` | JSONB     |                      |
| `changelog`     | TEXT      | 更新说明             |
| `created_at`    | TIMESTAMP |                      |

### 2.4.3 交易表 `transactions`

用于记录购买和打赏。

| 字段             | 类型       | 说明                                     |
|------------------|------------|------------------------------------------|
| `id`             | UUID PK    |                                          |
| `template_id`    | UUID FK    | 对应模板                                 |
| `buyer_id`       | UUID FK    | 购买者                                   |
| `creator_id`     | UUID FK    | 创作者                                   |
| `type`           | VARCHAR    | `purchase` `tip` `subscription` `refund`|
| `amount`         | DECIMAL    | 总金额                                   |
| `platform_fee`   | DECIMAL    | 平台抽成                                 |
| `creator_earning`| DECIMAL    | 创作者收入                               |
| `payment_provider`| VARCHAR   | `stripe` `paypal` 等                     |
| `payment_intent_id`| VARCHAR  | 第三方支付唯一标识                       |
| `status`         | VARCHAR    | `pending` `completed` `failed` 等       |
| `created_at`     | TIMESTAMP  |                                          |
| `completed_at`   | TIMESTAMP  |                                          |

### 2.4.4 创作者钱包 `creator_wallets`

| 字段            | 类型       | 说明                   |
|-----------------|------------|------------------------|
| `id`            | UUID PK    |                        |
| `user_id`       | UUID FK    | 创作者                 |
| `balance`       | DECIMAL    | 可提现余额             |
| `pending_balance`| DECIMAL   | 提现中或待结算金额     |
| `total_earned`  | DECIMAL    | 累积收入               |
| `total_withdrawn`| DECIMAL   | 累积提现               |

### 2.4.5 访问记录 `user_template_access`

记录用户对模板的使用权（购买 / 订阅 / 免费）。

| 字段         | 类型       | 说明                 |
|--------------|------------|----------------------|
| `id`         | UUID PK    |                      |
| `user_id`    | UUID FK    |                      |
| `template_id`| UUID FK    |                      |
| `access_type`| VARCHAR    | `purchased` `free` `subscribed` 等 |
| `granted_at` | TIMESTAMP  |                      |
| `expires_at` | TIMESTAMP  | 订阅到期时间（如适用）|
| `times_used` | INT        | 使用次数             |
| `last_used_at`| TIMESTAMP | 最后使用时间         |

### 2.4.6 社交表（简要）

- `reviews`：评分与评价
- `collections`：收藏关系
- `template_forks`：Fork 关系
- `creator_follows`：关注创作者

## 2.5 协作与画布状态

### 2.5.1 画布协作状态 `canvas_states`

用于持久化 Y.Doc 的二进制状态（备份与冷启动），定期从协作服务同步。

| 字段        | 类型      | 说明                      |
|-------------|-----------|---------------------------|
| `workflow_id`| UUID PK  | 对应工作流               |
| `doc_state` | BYTEA     | Y.Doc 编码字节           |
| `updated_at`| TIMESTAMP | 最后同步时间             |

---

# 三、交互与通信协议设计

## 3.1 总体通信模式

- **REST API**
  - 用于：资源 CRUD（工作流、模板、用户）、大部分业务操作、支付回调等
- **WebSocket**
  - 通道 1：`/ws/run/{thread_id}` — 工作流执行事件流（LangGraph → 前端）
  - 通道 2：`/ws/hitl/{thread_id}` — 人在回路交互
  - 通道 3：`/yjs`（由 Hocuspocus/y-websocket 接管）— 画布协作
- **第三方回调**
  - `POST /webhooks/stripe` 等

## 3.2 工作流执行 WebSocket 协议

### 3.2.1 连接流程

1. 前端发起 WebSocket 连接：`ws://api.example.com/ws/run/{thread_id}`
2. 连接建立后，前端可立即收到历史状态同步事件（可选）

### 3.2.2 消息格式

使用统一 envelope：

```json
{
  "type": "event_type",
  "runId": "run-uuid",
  "threadId": "thread-uuid",
  "nodeId": "node-uuid-or-null",
  "payload": { ... }
}
```

#### 事件类型定义

1. **执行生命周期**

```json
{
  "type": "run_started",
  "runId": "run-123",
  "threadId": "thread-abc",
  "payload": {
    "workflowId": "wf-456",
    "inputSummary": "根据以下提纲写一篇文章..."
  }
}
```

```json
{
  "type": "run_completed",
  "runId": "run-123",
  "threadId": "thread-abc",
  "payload": {
    "status": "completed",
    "durationMs": 12345
  }
}
```

2. **节点级状态**

```json
{
  "type": "node_started",
  "runId": "run-123",
  "threadId": "thread-abc",
  "nodeId": "node-1",
  "payload": {
    "label": "Research AI Trends"
  }
}
```

```json
{
  "type": "node_status",
  "runId": "run-123",
  "threadId": "thread-abc",
  "nodeId": "node-1",
  "payload": {
    "status": "executing"  // idle / thinking / executing / completed / error / interrupted
  }
}
```

3. **Token 流**

```json
{
  "type": "token",
  "runId": "run-123",
  "threadId": "thread-abc",
  "nodeId": "node-1",
  "payload": {
    "content": "这",
    "sequence": 1,
    "finished": false
  }
}
```

4. **Tool 调用与生成式 UI**

```json
{
  "type": "tool_call",
  "runId": "run-123",
  "threadId": "thread-abc",
  "nodeId": "node-2",
  "payload": {
    "tool": "render_chart",
    "args": {
      "x": ["Jan", "Feb", "Mar"],
      "y": [10, 20, 15]
    },
    "componentHint": "LineChart"
  }
}
```

前端 `SmartNode` 内部有 `ToolRenderer` 组件，根据 `tool` 名和 `componentHint` 映射到具体 React 组件进行渲染。

5. **错误事件**

```json
{
  "type": "error",
  "runId": "run-123",
  "threadId": "thread-abc",
  "nodeId": "node-1",
  "payload": {
    "message": "OpenAI API quota exceeded",
    "code": "LLM_QUOTA",
    "fatal": false
  }
}
```

## 3.3 人在回路（HITL）协议

### 3.3.1 后端 → 前端：中断通知

```json
{
  "type": "interrupt",
  "runId": "run-123",
  "threadId": "thread-abc",
  "nodeId": "node-review",
  "payload": {
    "inputState": {
      "draft_summary": "当前研究结果摘要...",
      "sources": [
        {"url": "...", "title": "..."}
      ]
    },
    "reason": "manual_review_required"
  }
}
```

### 3.3.2 前端 → 后端：用户修改后恢复

通过 REST 或单独 WebSocket 通道，例如 REST：

`POST /api/v1/workflows/runs/{run_id}/resume`

```json
{
  "nodeId": "node-review",
  "updatedState": {
    "draft_summary": "用户编辑后的摘要...",
    "sources": [
      {"url": "...", "title": "...", "include": true}
    ]
  }
}
```

后端内部：`graph.ainvoke(Command(resume=updatedState), config={...})`。

## 3.4 协作协议（Yjs）

- 使用标准 y-websocket/Hocuspocus 协议：
  - 文档名：`workflow-{workflow_id}`
  - Y.Map:
    - `nodes`: Y.Array（React Flow `nodes` 的序列化）
    - `edges`: Y.Array
    - `viewport`: Y.Map
- Awareness：
  - `user`: `{name, color, avatar}`
  - `cursor`: `{x, y}`
  - `selectedNodeId`: string

前端仅需根据 Yjs 文档变化更新本地 React Flow 状态。

---

# 四、接口设计文档（REST 概览）

> 以下为主要 API 的概要设计，实际项目中可进一步拆分为 Swagger / OpenAPI 文档。

## 4.1 认证与用户

### 4.1.1 登录 / 注册

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/register`
- `GET /api/v1/auth/me`

## 4.2 工作流与画布

### 4.2.1 工作流 CRUD

| 方法 | 路径                                | 说明                 |
|------|-------------------------------------|----------------------|
| GET  | `/api/v1/workflows`                | 列出当前用户的工作流 |
| POST | `/api/v1/workflows`                | 创建新工作流         |
| GET  | `/api/v1/workflows/{workflow_id}`  | 获取工作流详情含画布 |
| PUT  | `/api/v1/workflows/{workflow_id}`  | 更新标题/描述/画布   |
| DELETE | `/api/v1/workflows/{workflow_id}`| 删除工作流           |

**创建示例**

```json
POST /api/v1/workflows
{
  "title": "AI 趋势报告生成器",
  "description": "搜索 → 大纲 → 撰写 的组合工作流",
  "canvasJson": {
    "nodes": [...],
    "edges": [...],
    "viewport": {"x": 0, "y": 0, "zoom": 1}
  },
  "sourceTemplateId": "template-123" 
}
```

### 4.2.2 工作流执行

- `POST /api/v1/workflows/{workflow_id}/run`

请求：

```json
{
  "input": "请根据最近的 AI 大模型新闻生成一份趋势报告",
  "initialState": {
    "user_intent": "ai_trend_report",
    "copilot_context": {...}
  }
}
```

响应：

```json
{
  "runId": "run-uuid",
  "threadId": "thread-uuid",
  "wsUrl": "wss://api.example.com/ws/run/thread-uuid"
}
```

## 4.3 模板市场 API

### 4.3.1 浏览 & 搜索

- `GET /api/v1/marketplace/templates`
- `GET /api/v1/marketplace/templates/{id}`
- `GET /api/v1/marketplace/templates/featured`
- `GET /api/v1/marketplace/templates/categories`

### 4.3.2 创作者发布与管理

- `POST /api/v1/marketplace/templates` — 创建草稿模板
- `PUT /api/v1/marketplace/templates/{id}` — 更新模板
- `POST /api/v1/marketplace/templates/{id}/publish` — 提交审核
- `POST /api/v1/marketplace/templates/{id}/upload-preview` — 上传预览图

### 4.3.3 购买与打赏

- `POST /api/v1/marketplace/templates/{id}/purchase` — 创建支付意图
- `POST /api/v1/marketplace/templates/{id}/tip` — 打赏
- `POST /api/v1/marketplace/webhooks/stripe` — Stripe Webhook

### 4.3.4 使用与 Fork

- `POST /api/v1/marketplace/templates/{id}/use` — 基于模板创建用户工作流
- `POST /api/v1/marketplace/templates/{id}/fork` — Fork 为新模板（草稿）

### 4.3.5 评价与收藏

- `POST /api/v1/marketplace/templates/{id}/reviews`
- `GET /api/v1/marketplace/templates/{id}/reviews`
- `POST /api/v1/marketplace/templates/{id}/collect`（或 `PUT/DELETE` 收藏关系）

## 4.4 创作者中心 API

- `GET /api/v1/creator/dashboard` — 数据总览
- `GET /api/v1/creator/analytics` — 收益/下载/评分分析
- `POST /api/v1/creator/withdraw` — 提现
- `GET /api/v1/creator/templates` — 我发布的模板列表

## 4.5 知识库 API

- `POST /api/v1/kb/documents` — 上传文档或 URL
- `GET /api/v1/kb/documents` — 列表
- `DELETE /api/v1/kb/documents/{id}`
- `POST /api/v1/kb/search` — 向量检索

## 4.6 MCP 与工具 API（内部）

- MCP Server 单独配置与生命周期由后端管理，通常不暴露直接 REST，透过工作流节点/工具来使用。

---

# 五、分阶段详细开发计划（MVP → 生产级）

## 5.1 Phase 0：基础设施与骨架（1–2 周）

**目标**：搭建最小可运行骨架，不含复杂业务。

### 范围

- Next.js + React Flow 工程基础
- FastAPI 项目骨架
- PostgreSQL 初始化（基础表：`users` `workflows`）
- LLM 调用封装（OpenAI/Anthropic SDK）
- 简单鉴权（JWT）

### TODO 列表

- [ ] 搭建 Next.js + TypeScript + Tailwind 工程  
- [ ] 集成 React Flow，渲染静态 demo 画布  
- [ ] 搭建 FastAPI 项目，配置 Uvicorn、CORS  
- [ ] 建立 PostgreSQL 实例，初始化基础表  
- [ ] 实现基础登录/注册 API  
- [ ] 实现前端登录页 + 会话管理  
- [ ] 封装 LLM 客户端（配置模型、超时、错误处理）

---

## 5.2 Phase 1：MVP — 基础画布 + 静态执行（6–8 周）

**目标**：可拖拽搭建简单工作流，执行固定 LangGraph 模板，支持流式输出。

### 范围

- React Flow 画布基础：增加/删除节点、连线
- 简单节点类型：`Research` `Writer` `Reviewer`
- FastAPI + LangGraph 静态图（硬编码流程）
- WebSocket 流式 Token 回传
- 工作流持久化（`workflows` 表）

### 详细任务

#### 前端

- [ ] 实现工作台页面布局（画布 + 属性面板 + 执行面板）  
- [ ] 实现节点拖拽创建、连线、删除  
- [ ] 定义 `AgentNodeData` 类型（label、modelConfig、status 等）  
- [ ] 使用 Zustand 管理 `nodes` `edges` 状态  
- [ ] 实现简单节点状态渲染：idle / running / completed  
- [ ] 接收 WebSocket 事件，更新 `streamingContent`  

#### 后端

- [ ] 定义 `workflows` 表和简单 CRUD  
- [ ] 实现静态 LangGraph 工作流：
  - START → Research → Writer → Reviewer → END  
- [ ] 集成 `astream_events`，桥接到 FastAPI WebSocket  
- [ ] 实现 `/workflows/{id}/run` 启动执行，返回 `threadId`  
- [ ] 实现 WebSocket `/ws/run/{thread_id}`，推送事件  

#### 验收标准

- [ ] 用户能在画布上执行固定流程并看到实时输出  
- [ ] 支持保存和加载工作流画布  
- [ ] 单用户下并发 $10$ 个 Run 正常运行  

---

## 5.3 Phase 2：Enhanced MVP — 动态图 + HITL + RAG + Copilot（8–10 周）

**目标**：具备 Refly 级核心能力：动态图、在途干预、知识库支持、Copilot 编辑画布。

### 范围

- 动态图构建工厂（从前端 `canvas_json` 动态编译 LangGraph）
- 节点类型扩展：LLM、Tool、Router、Map 节点
- HITL 中断机制（节点级人工确认）
- 知识库上传与检索（RAG）
- CopilotKit 集成（读取画布状态+执行前端动作）

### 详细任务

#### 动态图 & 执行

- [ ] 设计前端节点 JSON Schema（type、data、modelConfig、工具配置等）  
- [ ] 开发 `DynamicGraphFactory`：
  - [ ] 遍历节点列表，绑定执行器函数  
  - [ ] 添加普通边和条件边  
  - [ ] 自动添加 START / END 边  
- [ ] 为执行器增加元数据（nodeId 标签），用于事件反查  
- [ ] 支持在执行前重新编译图（支持修改后重跑）  

#### HITL

- [ ] 在节点配置中增加「需要人工确认」选项  
- [ ] 在编译图时，将对应节点加入 `interrupt_before`  
- [ ] 拓展 WebSocket 协议，增加 `interrupt` 事件  
- [ ] 实现前端弹出编辑面板，展示 `inputState` 并允许修改  
- [ ] 开发 `/runs/{run_id}/resume` 恢复接口  

#### RAG

- [ ] 设计并实现 `kb_documents` 表与向量索引  
- [ ] 文件上传接口（PDF/文本/URL -> 抓取内容 -> 分片向量化）  
- [ ] RAG 检索接口 `/kb/search`  
- [ ] 在 LLM 执行器中加入可选参数 `enableRag`，调用 `retrieve_context`  

#### Copilot 集成

- [ ] 前端接入 CopilotKit SDK  
- [ ] `useCopilotReadable` 暴露:
  - 当前画布聚合信息（选中节点、视口内节点）  
- [ ] `useCopilotAction` 定义：
  - `addNode`、`connectNodes`、`renameNode`、`autoLayout`  
- [ ] 实现「一句话生成工作流」功能（Copilot 调用 actions）  
- [ ] 后端在 `/run` 中将 Copilot 上下文注入 LangGraph 初始 State  

#### 验收标准

- [ ] 任意前端画布 JSON 能在后端成功编译为执行图并运行  
- [ ] HITL：在指定节点自动暂停，用户修改后继续  
- [ ] 节点可配置使用知识库，明显提升结果质量  
- [ ] Copilot 能通过自然语言帮助构建和修改工作流  

---

## 5.4 Phase 2.5：模板市场 + UGC（4–6 周）

**目标**：上线模板市场 MVP，让用户可以分享 / 购买 / 打赏工作流模板。

### 范围

- 模板数据模型与 API
- 模板市场前端页面（列表 + 详情）
- 模板发布、使用、Fork 流程
- 支付与打赏流程（Stripe）
- 创作者基础仪表盘

### 详细任务

#### 数据与后端

- [ ] 创建模板相关表：
  - [ ] `templates` `template_versions`  
  - [ ] `transactions` `creator_wallets` `user_template_access`  
  - [ ] `reviews` `collections` `template_forks` `creator_follows`  
- [ ] 实现模板 CRUD 和审核状态流转  
- [ ] 实现 `use_template`（模板 → 用户工作流实例）  
- [ ] 实现 `fork_template`（模板 → 创作者草稿）  
- [ ] Stripe 集成：
  - [ ] `purchase_template` / `tip_creator` 接口  
  - [ ] Webhook 处理完成支付 → 写入 `transactions` → 更新 `creator_wallets` / `user_template_access`  
- [ ] 创作者提现流程（可先人工处理，只实现记录与状态流转接口）

#### 前端

- [ ] 「模板市场」页：
  - [ ] 分类筛选、搜索、排序（热门 / 最新 / 下载 / 评分）  
  - [ ] 模板卡片组件（价格、评分、下载量）  
- [ ] 模板详情页：
  - [ ] 基本信息、长描述、预览图/视频  
  - [ ] 工作流只读预览（缩略画布）  
  - [ ] 用户操作：使用 / 购买 / 打赏 / Fork / 收藏  
- [ ] 模板发布页：
  - [ ] 从现有工作流一键发布为模板  
  - [ ] 编辑价格、描述、分类、输入参数说明  
- [ ] 创作者中心：
  - [ ] 总览卡片（余额、本月收益、下载量）  
  - [ ] 模板列表与表现统计  

#### 验收标准

- [ ] 用户可以从市场浏览 / 搜索模板，并一键实例化为自己的工作流  
- [ ] 用户可以对喜欢的模板打赏，创作者钱包余额相应增加  
- [ ] 创作者可以查看基础收益与下载数据  

---

## 5.5 Phase 3：Production — 企业级稳定化（12–16 周）

**目标**：满足企业级稳定性、安全性、协作与可观测性要求。

### 范围

- 多人协作（Yjs）正式上线
- MCP 深度集成（GitHub / Slack / 自有系统）
- 完整监控 & 报警体系
- 安全与合规（权限、数据保护）

### 详细任务

#### 协作

- [ ] 部署 Yjs WebSocket 服务（Hocuspocus 或自建）  
- [ ] 将 React Flow `nodes`/`edges` 状态迁移到 Y.Doc 管理  
- [ ] 实现光标与选中节点 Awareness  
- [ ] 将 Y.Doc 定期快照存到 `canvas_states` 表  
- [ ] 冲突测试：多人同时移动 / 编辑节点  

#### MCP

- [ ] 设计 `MCPServerManager`，加载配置文件注册 MCP Server  
- [ ] 将 MCP 工具自动包装为 LangChain Tool 并注入 `tool_registry`  
- [ ] 前端节点工具选择器中展示 MCP 工具列表  
- [ ] 实现几个典型集成案例：
  - GitHub：列 PR、创建 Issue  
  - Slack：发送消息/通知  

#### 可观测性与性能

- [ ] 接入 Prometheus 指标：
  - 工作流执行次数 / 时延 / 成功率  
  - 各模型 Token 用量 / 错误率  
- [ ] 接入 OpenTelemetry + Jaeger：
  - 工作流级 Trace  
  - 节点级 Span（便于排查慢点）  
- [ ] 实现熔断和重试：
  - LLM 失败自动重试  
  - 达到错误阈值时熔断，降级为缓存或提示  

#### 安全与合规

- [ ] RBAC 权限模型（区分管理员 / 创作者 / 普通用户）  
- [ ] 工作流共享与访问控制（私有 / 链接分享 / 组织内可见）  
- [ ] 对敏感数据字段加密存储（如支付信息）  
- [ ] 日志审计（关键操作写入审计日志）  

#### 验收标准

- [ ] 支持 $5$ 人以上实时协作编辑同一画布，无明显冲突  
- [ ] P95 API 延迟 < $500$ms，P99 < $2$s  
- [ ] 应用月稳定性 $99.5\%$+  
- [ ] 完整监控看板 + 报警策略上线  

---

## 5.6 Phase 4：高级特性 & 持续演进（持续）

**目标**：差异化能力与持续增长。

### 范围

- 多智能体高级协作模式（Supervisor / Map-Reduce / Debate）
- 自适应工作流优化（基于历史数据推荐重构）
- 行业垂直模板库（金融、教育、游戏、开发运维等）

### TODO 示例

- [ ] 实现 Supervisor 模式节点（自动路由到不同专家子图）  
- [ ] 实现 Map-Reduce 写作模板（自动生成多段并汇总）  
- [ ] 构建「AI 报告生成」「竞品分析」「代码审查」等官方模板集  
- [ ] 收集执行统计，训练推荐模型，给出工作流优化建议  

---
