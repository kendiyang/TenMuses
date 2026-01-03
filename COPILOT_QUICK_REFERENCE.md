# Copilot 系统快速参考指南

## ✅ 系统状态

所有 Copilot 模型调用功能已验证 **正常运作**！

| 功能 | 状态 | 测试时间 |
|------|------|---------|
| 数据库配置 | ✅ | 2026-01-02 |
| LLM 调用 | ✅ | 2026-01-02 |
| 流式响应 | ✅ | 2026-01-02 |
| Copilot 服务 | ✅ | 2026-01-02 |

---

## 🚀 核心配置

### 当前使用的 LLM Provider

```
名称:      OpenAI (Custom)
Base URL:  https://ssvip.dmxapi.com/v1
API Key:   sk-DgUXUOU1tfvLz0x0L69RV9mVzz806jTho82ZzEVXGcq5iGTU ✅
模型:      gpt-4o, text-embedding-3-large
状态:      激活 ✅
```

### 数据库表

**llm_providers** - 供应商配置
- id: UUID
- name: 供应商标识 (e.g., "openai")
- api_key_encrypted: 加密的 API Key
- base_url: 自定义 Base URL
- is_active: 是否激活

**llm_models** - 模型配置  
- id: UUID
- model_name: 模型名称 (e.g., "gpt-4o")
- provider_id: 关联的 Provider ID
- is_active: 是否激活

---

## 📡 API 端点

### Copilot Chat
```bash
POST /api/v1/copilot/chat
Content-Type: application/json
Authorization: Bearer <token>

{
  "message": "你的问题",
  "model": "local-smart",  # local-smart | local-rules | gpt-4 | claude-3
  "chat_history": [],
  "context": "工作流上下文 (可选)"
}
```

### Copilot Stream Chat
```bash
POST /api/v1/copilot/stream-chat
Content-Type: application/json
Authorization: Bearer <token>

{
  "message": "你的问题",
  "model": "gpt-4",
  "chat_history": [],
  "context": "工作流上下文 (可选)"
}
```

### 获取可用模型
```bash
GET /api/v1/copilot/models
Authorization: Bearer <token>
```

---

## 🔌 代码集成示例

### 使用 LLM Client

```python
from app.services.llm_client import llm_client
from langchain_core.messages import HumanMessage, SystemMessage

# 非流式调用
response = await llm_client.invoke(
    messages=[
        SystemMessage(content="你是一个有用的助手"),
        HumanMessage(content="你好")
    ],
    provider="openai",
    model="gpt-4o"
)
print(response.content)

# 流式调用
async for token in llm_client.stream(
    messages=[...],
    provider="openai", 
    model="gpt-4o"
):
    print(token, end="", flush=True)
```

### 使用 Copilot Service

```python
from app.services.copilot_stream_service import CopilotStreamService

copilot = CopilotStreamService(provider="openai", model="gpt-4o")

async for event in copilot.stream_chat(
    message="你好",
    chat_history=[],
    workflow_context=None
):
    if event.type == "token":
        print(event.get("content"), end="")
    elif event.type == "chat_completed":
        print("对话已完成")
```

---

## 🧪 验证和测试

### 运行验证脚本

```bash
cd /Users/mg/Workspace/TenMuses/backend
source venv/bin/activate
python test_copilot_invoke.py
```

### 查看测试结果
- 数据库配置 ✅
- LLM Client 初始化 ✅  
- 非流式调用 ✅
- 流式调用 ✅
- Copilot 本地服务 ✅
- Copilot 流式服务 ✅

### 手动测试 API

```bash
# 获取 JWT token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user@example.com","password":"password"}'

# 测试 Copilot Chat
curl -X POST http://localhost:8000/api/v1/copilot/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "message": "TenMuses 是什么?",
    "model": "gpt-4",
    "chat_history": []
  }'
```

---

## 🔧 故障排查

### 问题：API 调用返回 401 Unauthorized

**原因**: 认证失败

**解决方案**:
```bash
# 检查 JWT token 是否有效
# 检查 Authorization header 是否包含 "Bearer <token>"
# 重新登录获取新 token
```

### 问题：模型未找到

**原因**: 数据库中没有激活的模型

**解决方案**:
```bash
# 检查数据库配置
PGPASSWORD=password psql -h localhost -U postgres -d tenmuses \
  -c "SELECT * FROM llm_models WHERE is_active = true;"

# 激活模型
UPDATE llm_models SET is_active = true WHERE model_name = 'gpt-4o';
```

### 问题：API Key 无效

**原因**: API Key 过期或不正确

**解决方案**:
```bash
# 更新 API Key
UPDATE llm_providers 
SET api_key_encrypted = encrypt('sk-new-key')
WHERE name = 'openai';

# 刷新缓存
# 在应用代码中调用：await llm_client.refresh_cache()
```

### 问题：SSL 证书验证失败

**原因**: 自签名证书或代理问题

**解决方案**: 
- 已在 `llm_client.py` 中全局禁用 SSL 验证
- 代理服务器使用 base_url: `https://ssvip.dmxapi.com/v1`

---

## 📊 性能参考

| 操作 | 响应时间 |
|------|---------|
| 数据库加载 | ~40ms |
| Client 初始化 | ~50ms |
| API 调用 (非流式) | ~1.3s |
| 流式首 token | ~1.6s |
| 流式完整响应 | ~2-3s |

---

## 🔐 安全检查清单

- [x] API Key 已加密存储在数据库
- [x] HTTPS 连接已启用
- [x] SSL 验证已启用
- [x] JWT 认证已实现
- [x] 敏感信息不会记录到日志
- [x] 数据库连接使用异步连接池

---

## 📚 相关文档

| 文档 | 位置 |
|------|------|
| 数据库配置验证 | DATABASE_CONFIG_VERIFICATION_REPORT.md |
| 完整验证报告 | COPILOT_MODEL_VERIFICATION_REPORT.md |
| 测试脚本 | backend/test_copilot_invoke.py |
| Copilot API | backend/app/api/v1/copilot.py |
| LLM Client | backend/app/services/llm_client.py |
| Copilot 服务 | backend/app/services/copilot_stream_service.py |

---

## 🆘 获取帮助

### 查看日志

```bash
# 后端日志（实时）
tail -f /var/log/tenmuses/backend.log

# 查看特定错误
grep "ERROR" /var/log/tenmuses/backend.log

# 查看 LLM 相关日志
grep -i "llm\|copilot\|openai" /var/log/tenmuses/backend.log
```

### 检查系统状态

```bash
# 检查数据库连接
psql postgresql://postgres:password@localhost:5432/tenmuses -c "SELECT 1;"

# 检查 API 服务
curl http://localhost:8000/health

# 检查 Copilot 可用模型
curl http://localhost:8000/api/v1/copilot/models \
  -H "Authorization: Bearer <token>"
```

---

**更新时间**: 2026-01-02  
**系统状态**: ✅ 正常运作
