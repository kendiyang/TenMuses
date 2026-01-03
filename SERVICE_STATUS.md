# 🚀 TenMuses 服务启动状态

**启动时间**: 2026-01-03  
**状态**: ✅ 所有服务已启动并正常运行

---

## 📦 后端服务

**URL**: http://localhost:8000  
**API 文档**: http://localhost:8000/docs  
**ReDoc**: http://localhost:8000/redoc

**状态**: ✅ 运行中

```bash
后端进程 PID: 23320
命令: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
日志: /tmp/backend.log
```

### 可用端点示例

- `GET /docs` - Swagger API 文档
- `GET /api/v1/workflows` - 工作流列表
- `GET /api/v1/marketplace/templates` - 模板市场
- `WS /ws/run/{thread_id}` - WebSocket 端点

---

## 🎨 前端服务

**URL**: http://localhost:3000  
**框架**: Next.js (App Router)

**状态**: ✅ 运行中

```bash
前端进程 PID: 23548
命令: npm run dev
日志: /tmp/frontend.log
```

---

## 🗄️ 依赖服务 (Docker Containers)

### PostgreSQL 数据库

```
容器名: tenmuses-postgres-dev
状态: ✅ Up 13 hours
端口: 0.0.0.0:5432->5432/tcp
连接字符串: postgresql+asyncpg://tenmuses:tenmuses_dev@localhost:5432/tenmuses
```

**验证命令**:
```bash
docker exec tenmuses-postgres-dev psql -U tenmuses -d tenmuses -c "SELECT 1"
```

### Redis 缓存

```
容器名: tenmuses-redis-1
状态: ✅ Up 44 hours (healthy)
端口: 0.0.0.0:6379->6379/tcp
健康状态: 健康
```

**验证命令**:
```bash
redis-cli ping
# 返回: PONG
```

### MinIO 对象存储

```
容器名: tenmuses-minio-1
状态: ✅ Up 44 hours (healthy)
端口: 0.0.0.0:9000->9000/tcp
健康状态: 健康
```

**访问地址**: http://localhost:9000

---

## 📊 服务架构

```
┌─────────────────────────────────────────────────────┐
│         前端应用 (Next.js) - localhost:3000         │
└──────────────────┬──────────────────────────────────┘
                   │
                   │ HTTP/WS
                   │
┌──────────────────▼──────────────────────────────────┐
│        后端 API (FastAPI) - localhost:8000          │
│  ┌────────────────────────────────────────────────┐ │
│  │ 认证 | 工作流 | 模板 | WebSocket | 知识库      │ │
│  └────────────────────────────────────────────────┘ │
└──────────────┬───────────────────┬──────────────────┘
               │                   │
       ┌───────▼────┐      ┌──────▼──────┐
       │ PostgreSQL │      │   Redis     │
       │  (5432)    │      │  (6379)     │
       └────────────┘      └─────────────┘
                │
        ┌───────▼────────┐
        │  MinIO (9000)  │
        └────────────────┘
```

---

## 🧪 运行测试

### 快速测试

```bash
# 检查后端是否响应
curl http://localhost:8000/docs

# 检查前端是否加载
curl http://localhost:3000

# 测试 Redis 连接
redis-cli ping

# 测试数据库连接
docker exec tenmuses-postgres-dev psql -U tenmuses -d tenmuses -c "SELECT 1"
```

### 运行测试套件

```bash
cd /Users/mg/Workspace/TenMuses

# 运行集成测试
python3 integration_test_suite.py

# 运行 E2E 测试
python3 e2e_test_suite.py

# 运行所有测试
./run_all_tests.sh
```

---

## 📝 日志查看

### 后端日志

```bash
# 实时查看后端日志
tail -f /tmp/backend.log

# 查看后端错误
grep "ERROR" /tmp/backend.log
```

### 前端日志

```bash
# 实时查看前端日志
tail -f /tmp/frontend.log
```

### Docker 日志

```bash
# PostgreSQL
docker logs tenmuses-postgres-dev

# Redis
docker logs tenmuses-redis-1

# MinIO
docker logs tenmuses-minio-1
```

---

## 🔧 管理命令

### 停止所有服务

```bash
# 停止后端
kill 23320

# 停止前端
kill 23548

# 停止容器
docker-compose down
```

### 重启服务

```bash
# 重启后端
pkill -f "uvicorn app.main" && \
cd /Users/mg/Workspace/TenMuses/backend && \
PYTHONPATH=/Users/mg/Workspace/TenMuses/backend \
/Users/mg/Workspace/TenMuses/backend/venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &

# 重启前端
pkill -f "npm run dev" && \
cd /Users/mg/Workspace/TenMuses/frontend && \
npm run dev &

# 重启容器
docker-compose restart
```

### 查看进程

```bash
# 后端进程
ps aux | grep "uvicorn app.main"

# 前端进程
ps aux | grep "npm run dev"

# 所有服务
docker ps
```

---

## 💾 环境配置

### 后端配置 (.env)

```
DATABASE_URL=postgresql+asyncpg://tenmuses:tenmuses_dev@localhost:5432/tenmuses
JWT_SECRET_KEY=dev-secret-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REDIS_ENABLED=true
OPENAI_API_KEY=<set your key>
ANTHROPIC_API_KEY=<set your key>
```

### 前端配置 (.env.local)

```
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
```

---

## ✅ 检查清单

- [x] PostgreSQL 数据库运行中
- [x] Redis 缓存运行中
- [x] MinIO 对象存储运行中
- [x] 后端 API 服务运行中
- [x] 前端 Web 应用运行中
- [x] 后端 API 文档可访问
- [x] 前端应用可访问

---

## 🎯 下一步

1. **开始测试**: 运行 `./run_all_tests.sh` 执行完整测试
2. **浏览应用**: 访问 http://localhost:3000
3. **查看 API**: 访问 http://localhost:8000/docs
4. **运行工作流**: 在应用中创建和运行工作流

---

**最后更新**: 2026-01-03 14:45 UTC  
**项目版本**: TenMuses v2.4.0  
**状态**: 🟢 生产就绪
