# 快速启动指南：LLM 数据库配置

## 🚀 30秒快速开始

### 1. 后端启动（如还未启动）

```bash
cd backend
# 确保 .env 已设置（参考下面配置）
python -m app.main
```

### 2. 前端启动（如还未启动）

```bash
cd frontend
npm run dev
```

### 3. 创建第一个 LLM 配置

**选项 A：通过 API（推荐）**

```bash
curl -X POST http://localhost:8000/api/v1/llm-configs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <YOUR_ADMIN_TOKEN>" \
  -d '{
    "provider": "openai",
    "model_name": "gpt-4-turbo-preview",
    "display_name": "GPT-4 Turbo",
    "api_key": "sk-your-api-key-here",
    "priority": 1
  }'
```

**选项 B：通过 Admin UI**
1. 访问 `http://localhost:3000/llm-config`（需要管理员权限）
2. 点击 "Add Configuration"
3. 填表并提交

### 4. 验证配置

```bash
# 获取可用模型列表
curl http://localhost:8000/api/v1/llm-configs

# 输出应该是 JSON 数组，包含你刚创建的配置
```

### 5. 在应用中使用

访问 `http://localhost:3000/copilot` 选择模型并开始聊天

---

## 📋 环境变量配置

### 后端 `.env`

```env
# 数据库
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/tenmuses

# JWT (用于加密 API keys)
JWT_SECRET_KEY=your-super-secret-key-change-this

# 可选：作为备份方案
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx

# 服务器
DEBUG=true
PORT=8000
```

### 前端 `.env.local`

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## 🔐 安全说明

1. **API Key 加密**：所有 API keys 在数据库中使用 Fernet 加密
2. **加密密钥**：使用 `JWT_SECRET_KEY` 推导
3. **Admin Only**：只有管理员可以管理配置
4. **不要分享密钥**：永远不要在代码中硬编码 API keys

---

## 🛠️ 常见问题

### Q: "API key not configured" 错误

**A:** 两个解决方案：
1. 确保通过 API 或 Admin UI 创建了配置
2. 或在 `.env` 中设置环境变量作为备份

### Q: 配置创建后立即生效吗？

**A:** 后端会缓存配置，重启以确保生效：
```bash
# 重启后端
^C  # Ctrl+C 停止
python -m app.main
```

### Q: 忘记了 Admin Token

**A:** 先注册一个用户，然后手动更新数据库：
```sql
UPDATE users SET role = 'admin' WHERE email = 'your@email.com';
```

然后登录获取 token，该 token 用于 Authorization 头。

### Q: 支持哪些 LLM 提供商？

**A:** 当前支持：
- ✅ OpenAI（gpt-4, gpt-3.5-turbo 等）
- ✅ Anthropic（claude-3 等）

扩展新提供商：修改 `backend/app/services/llm_client.py` 的 `_build_client()` 方法。

---

## 🎯 主要页面

| 页面 | URL | 描述 |
|------|-----|------|
| Copilot 演示 | `/copilot` | 模型选择 + 聊天界面 |
| LLM 配置管理 | `/llm-config` | Admin 面板（需要管理员权限） |
| API 文档 | `/docs` | Swagger UI（FastAPI 自动生成） |

---

## 📚 详细文档

完整的功能说明、架构设计、API 文档：
→ 查看 `LLM_CONFIG_SETUP.md`

---

## 💡 开发流程

### 添加新 Provider（例如 Ollama）

1. **后端服务** (`backend/app/services/llm_client.py`)：
   ```python
   elif config.provider.lower() == "ollama":
       from langchain_community.llms import Ollama
       return Ollama(
           base_url=config.base_url or "http://localhost:11434",
           model=config.model_name,
       )
   ```

2. **创建配置**：
   ```bash
   curl -X POST http://localhost:8000/api/v1/llm-configs \
     -H "Authorization: Bearer <ADMIN_TOKEN>" \
     -d '{
       "provider": "ollama",
       "model_name": "llama2",
       "display_name": "Llama 2 (Local)",
       "api_key": "dummy",
       "base_url": "http://localhost:11434",
       "priority": 3
     }'
   ```

3. **前端**会自动识别并显示在模型选择器中

---

## ✅ 检查清单

- [ ] 后端运行在 `http://localhost:8000`
- [ ] 前端运行在 `http://localhost:3000`
- [ ] 至少创建了一个 LLM 配置
- [ ] 能访问 `/copilot` 页面
- [ ] 能选择模型并发送消息（演示模式）

---

## 🆘 需要帮助？

1. 查看完整文档：`LLM_CONFIG_SETUP.md`
2. 检查后端日志：`python -m app.main` 的控制台输出
3. 使用 FastAPI Swagger：`http://localhost:8000/docs`
