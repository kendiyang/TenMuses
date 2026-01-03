# OPENAI_API_KEY 和 OPENAI_BASE_URL 数据库读取 - 快速指南

## 什么是这个功能？

TenMuses 现在支持从数据库读取 LLM 配置（包括 `OPENAI_API_KEY` 和 `OPENAI_BASE_URL`），而不仅仅依赖环境变量。这样做的好处：

✅ **动态管理** - 无需重启应用即可更新 API 密钥
✅ **加密存储** - 密钥在数据库中被加密存储
✅ **多配置支持** - 可以保存多个提供商的配置
✅ **优先级系统** - 自动选择最优先的配置
✅ **后备机制** - 如果数据库无配置，自动回退到环境变量

## 快速开始

### 1️⃣ 初始化配置（第一次设置）

```bash
# 交互式方式（推荐）
bash setup-llm-config.sh

# 或使用 Python 脚本
python init-llm-config.py
```

### 2️⃣ 验证配置已保存

```bash
# 运行测试
python test-db-config.py

# 输出应该显示所有测试通过 ✓
```

### 3️⃣ 在应用中使用

现在所有 Copilot 服务都会自动从数据库读取配置：

```bash
# 启动后端
cd backend && uvicorn app.main:app --reload

# 现在 Copilot 功能会使用数据库中的 OpenAI 配置
```

## 技术实现

### 新增文件

| 文件 | 目的 |
|------|------|
| `backend/app/services/config_service.py` | 配置管理服务 |
| `backend/app/api/v1/config.py` | 配置管理 API 端点 |
| `backend/app/examples/database_config_example.py` | 使用示例 |
| `init-llm-config.py` | 初始化脚本 |
| `setup-llm-config.sh` | 交互式设置脚本 |
| `test-db-config.py` | 功能测试脚本 |
| `DATABASE_CONFIG_GUIDE.md` | 详细文档 |

### 核心类：ConfigService

```python
from app.services.config_service import ConfigService

# 获取 OpenAI 配置
config = await ConfigService.get_openai_config(db_session)
api_key = config["api_key"]      # 返回：sk-...
base_url = config["base_url"]    # 返回：https://api.openai.com/v1

# 获取 Anthropic 配置
config = await ConfigService.get_anthropic_config(db_session)

# 列出所有提供商
providers = await ConfigService.list_providers(db_session)

# 保存新配置
config = await ConfigService.save_provider_config(
    db_session,
    provider="openai",
    model_name="gpt-4-turbo-preview",
    api_key="sk-...",
)
await db_session.commit()
```

## API 端点

### 获取所有提供商

```bash
GET /api/v1/config/llm/providers
```

### 获取 OpenAI 配置

```bash
GET /api/v1/config/llm/providers/openai
```

### 保存/更新配置

```bash
POST /api/v1/config/llm/providers

{
    "provider": "openai",
    "model_name": "gpt-4-turbo-preview",
    "api_key": "sk-...",
    "base_url": "https://api.openai.com/v1"
}
```

### 激活/停用提供商

```bash
PATCH /api/v1/config/llm/providers/openai/toggle?is_active=true
```

## 数据库架构

```sql
CREATE TABLE llm_configs (
    id UUID PRIMARY KEY,
    provider VARCHAR NOT NULL,           -- 'openai', 'anthropic'
    model_name VARCHAR NOT NULL,         -- 'gpt-4-turbo-preview'
    api_key_encrypted VARCHAR NOT NULL,  -- 加密存储
    base_url VARCHAR,                    -- 可选的自定义 URL
    display_name VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    priority INTEGER DEFAULT 100,
    description VARCHAR,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

## 工作流程

```
应用启动
    ↓
需要 OpenAI API Key
    ↓
1️⃣  查询数据库 (llm_configs 表)
    ↓
2️⃣  找到? → 返回数据库配置
3️⃣  找不到? → 检查环境变量
    ↓
4️⃣  环境变量有? → 使用环境变量
5️⃣  没有? → 错误：API Key 未配置
```

## 常见场景

### 场景 1: 更新 API Key（生产环境）

**问题**: API Key 过期，需要立即更新

**解决方案**:
```bash
# 通过 API 更新（无需重启）
curl -X POST http://api.example.com/api/v1/config/llm/providers \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "provider": "openai",
    "api_key": "sk-new-key-..."
  }'

# 应用立即使用新密钥
```

### 场景 2: 多个 OpenAI 账户

**问题**: 需要在多个 OpenAI 账户之间切换

**解决方案**:
```bash
# 保存两个配置
POST /api/v1/config/llm/providers
{
    "provider": "openai",
    "api_key": "sk-account-1-...",
    "priority": 5    # 最优先
}

POST /api/v1/config/llm/providers
{
    "provider": "openai",
    "api_key": "sk-account-2-...",
    "priority": 10   # 次优先
}

# 切换优先级
PATCH /api/v1/config/llm/providers/openai/toggle?is_active=false  # 禁用第一个
```

### 场景 3: Anthropic 和 OpenAI 共存

```bash
# 保存 OpenAI
POST /api/v1/config/llm/providers
{
    "provider": "openai",
    "api_key": "sk-...",
    "model_name": "gpt-4-turbo-preview"
}

# 保存 Anthropic
POST /api/v1/config/llm/providers
{
    "provider": "anthropic",
    "api_key": "sk-ant-...",
    "model_name": "claude-3-sonnet-20240229"
}

# 都可用，根据服务需求选择
```

## 故障排除

### ❌ "OpenAI configuration not found"

```bash
# 检查是否设置了配置
curl -H "Authorization: Bearer TOKEN" \
  http://localhost:8000/api/v1/config/llm/providers

# 如果列表为空，运行初始化
python init-llm-config.py
```

### ❌ "Error loading config from database"

```bash
# 检查数据库连接
psql $DATABASE_URL -c "SELECT * FROM llm_configs;"

# 检查加密密钥是否设置
echo $ENCRYPTION_KEY  # 应该输出一个密钥

# 重新保存配置
bash setup-llm-config.sh
```

### ❌ API Key 显示已存储但无法使用

```bash
# 可能是加密密钥不匹配
# 确保所有实例使用相同的 ENCRYPTION_KEY

# 重新初始化
python test-db-config.py  # 会显示详细错误
```

## 环境变量配置

```bash
# .env 文件中的相关配置

# 数据库
DATABASE_URL=postgresql://user:pass@localhost/tenmuses

# 加密密钥（用于加密存储的 API 密钥）
ENCRYPTION_KEY=your-32-byte-encryption-key

# 后备用环境变量（如果数据库无配置）
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
ANTHROPIC_API_KEY=sk-ant-...
```

## 集成示例

### 在 LLMClient 中使用

```python
from app.services.config_service import ConfigService
from openai import AsyncOpenAI

async def initialize_openai(db_session):
    # 从数据库读取配置
    config = await ConfigService.get_openai_config(db_session)
    
    # 创建客户端
    client = AsyncOpenAI(
        api_key=config["api_key"],
        base_url=config["base_url"],
    )
    
    return client
```

### 在 Copilot 服务中使用

```python
async def stream_chat(message, db_session):
    # 自动从数据库读取 OpenAI 配置
    client = await initialize_openai(db_session)
    
    # 使用客户端进行 API 调用
    response = await client.chat.completions.create(...)
```

## 安全建议

1. **不要在代码中硬编码密钥** - 总是使用数据库或环境变量
2. **启用数据库加密** - 确保数据库连接使用 SSL/TLS
3. **保护 ENCRYPTION_KEY** - 这是加密 API 密钥的主密钥
4. **定期轮换密钥** - 每月或每季度更新一次 API 密钥
5. **审计配置更改** - 跟踪谁在何时更新了配置

## 详细文档

关于更多信息，请查看 [DATABASE_CONFIG_GUIDE.md](DATABASE_CONFIG_GUIDE.md)

## 总结

| 方式 | 优点 | 缺点 |
|------|------|------|
| **环境变量** | 简单，安全 | 需要重启应用才能更新 |
| **数据库** | 动态管理，无需重启 | 需要额外的加密配置 |
| **混合** | 两者结合 | 配置稍微复杂 |

**推荐**: 生产环境使用数据库 + 加密，开发环境使用环境变量

---

**有问题?** 查看 [DATABASE_CONFIG_GUIDE.md](DATABASE_CONFIG_GUIDE.md) 中的完整 API 文档和示例代码。
