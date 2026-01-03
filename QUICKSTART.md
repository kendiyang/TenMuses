# TenMuses 快速启动指南

## 🚀 5分钟快速开始

### 前置条件检查

确保你已安装：
- ✅ Node.js 18+ (`node --version`)
- ✅ Python 3.11+ (`python3 --version`)
- ✅ PostgreSQL 14+ (`psql --version`)

### 步骤 1: 克隆并设置项目

```bash
# 进入项目目录
cd TenMuses

# 运行自动设置脚本
./scripts/setup.sh
```

### 步骤 2: 配置环境变量

#### 后端配置 (`backend/.env`)

```bash
cd backend
cp .env.example .env
```

编辑 `backend/.env`，至少配置以下内容：

```env
# 数据库连接
DATABASE_URL=postgresql+asyncpg://postgres:your_password@localhost:5432/tenmuses

# JWT 密钥（生产环境请使用强密钥）
JWT_SECRET_KEY=your-super-secret-key-change-this-in-production

# OpenAI API Key（至少配置一个）
OPENAI_API_KEY=sk-your-openai-api-key

# 或者使用 Anthropic
# ANTHROPIC_API_KEY=your-anthropic-api-key
```

#### 前端配置 (`frontend/.env.local`)

```bash
cd frontend
cp .env.local.example .env.local
```

通常不需要修改，默认配置即可：

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### 步骤 3: 创建数据库

```bash
# 使用 PostgreSQL 创建数据库
createdb tenmuses

# 或者使用 psql
psql -U postgres -c "CREATE DATABASE tenmuses;"
```

### 步骤 4: 启动服务

#### 方式 1: 使用启动脚本（推荐）

```bash
# 在项目根目录
./scripts/dev.sh
```

这会同时启动前端和后端服务。

#### 方式 2: 分别启动

**启动后端：**

```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python -m app.main
```

**启动前端（新终端）：**

```bash
cd frontend
npm run dev
```

### 步骤 5: 访问应用

- 🌐 **前端应用**: http://localhost:3000
- 🔌 **后端 API**: http://localhost:8000
- 📚 **API 文档**: http://localhost:8000/docs

## 🧪 测试 API

### 1. 注册用户

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "password123"
  }'
```

### 2. 登录获取 Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

保存返回的 `access_token`。

### 3. 创建工作流

```bash
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "我的第一个工作流",
    "description": "测试工作流",
    "is_public": false
  }'
```

### 4. 列出工作流

```bash
curl -X GET http://localhost:8000/api/v1/workflows \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🔧 常见问题

### 问题 1: 数据库连接失败

**错误**: `could not connect to server`

**解决**:
1. 确保 PostgreSQL 正在运行：`pg_ctl status`
2. 检查数据库连接字符串是否正确
3. 确认数据库已创建：`psql -l | grep tenmuses`

### 问题 2: Python 依赖安装失败

**错误**: `error: Microsoft Visual C++ 14.0 is required` (Windows)

**解决**:
- Windows: 安装 [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- macOS: `xcode-select --install`
- Linux: `sudo apt-get install python3-dev`

### 问题 3: 端口已被占用

**错误**: `Address already in use`

**解决**:
```bash
# 查找占用端口的进程
lsof -i :8000  # 后端
lsof -i :3000  # 前端

# 杀死进程
kill -9 <PID>
```

### 问题 4: OpenAI API 配额不足

**错误**: `You exceeded your current quota`

**解决**:
1. 检查 OpenAI 账户余额
2. 或切换到 Anthropic：在 `.env` 中配置 `ANTHROPIC_API_KEY`

## 📖 下一步

现在你已经成功启动了 TenMuses！接下来可以：

1. 📚 阅读[详细设计文档](docs/design.md)了解系统架构
2. 🎨 查看[实施状态](docs/implementation-status.md)了解当前进度
3. 💻 开始开发 Phase 1 功能
4. 🧪 编写测试用例

## 🆘 获取帮助

- 查看 [README.md](README.md) 了解更多信息
- 查看 API 文档：http://localhost:8000/docs
- 提交 Issue 报告问题

---

**祝你使用愉快！** 🎉
