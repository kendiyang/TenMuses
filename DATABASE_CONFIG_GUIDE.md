# 数据库配置管理指南

## 概述

TenMuses 现在支持在数据库中存储 LLM 配置（API 密钥、Base URL 等），而不是仅依赖环境变量。这提供了更灵活的配置管理和运行时更新。

## 功能特点

✅ **加密存储** - API 密钥在数据库中被加密存储
✅ **动态配置** - 无需重启应用即可更新配置
✅ **多提供商支持** - OpenAI、Anthropic 等
✅ **优先级管理** - 在有多个配置时选择优先级最高的
✅ **回退机制** - 如果数据库无配置，自动回退到环境变量

## 数据库模型

### LLMConfig 表

```
llm_configs (
    id: UUID,                    # 配置唯一ID
    provider: VARCHAR,           # 提供商名称: openai, anthropic
    model_name: VARCHAR,         # 模型名称: gpt-4-turbo-preview
    api_key_encrypted: VARCHAR,  # 加密的API密钥
    base_url: VARCHAR (nullable),# 自定义Base URL（可选）
    display_name: VARCHAR,       # UI显示名称
    is_active: BOOLEAN,          # 是否激活
    priority: INTEGER,           # 优先级（数字越小优先级越高）
    description: VARCHAR,        # 配置描述
    created_at: TIMESTAMP,       # 创建时间
    updated_at: TIMESTAMP        # 更新时间
)
```

## API 端点

### 1. 列出所有 LLM 提供商

```bash
GET /api/v1/config/llm/providers?active_only=true

# 响应
[
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "provider": "openai",
        "model_name": "gpt-4-turbo-preview",
        "display_name": "OpenAI GPT-4 Turbo",
        "base_url": "https://api.openai.com/v1",
        "is_active": true,
        "priority": 10,
        "description": "OpenAI's GPT-4 Turbo model",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }
]
```

### 2. 获取特定提供商配置

```bash
GET /api/v1/config/llm/providers/openai

# 响应（同上）
```

### 3. 创建或更新提供商配置

```bash
POST /api/v1/config/llm/providers

# 请求体
{
    "provider": "openai",
    "model_name": "gpt-4-turbo-preview",
    "api_key": "sk-...",
    "base_url": "https://api.openai.com/v1",
    "display_name": "OpenAI GPT-4 Turbo",
    "description": "My OpenAI configuration",
    "priority": 10
}

# 响应（同列出响应格式）
```

### 4. 激活/停用提供商

```bash
PATCH /api/v1/config/llm/providers/openai/toggle?is_active=true

# 响应（同列出响应格式）
```

### 5. 获取 OpenAI 配置（不显示密钥）

```bash
GET /api/v1/config/llm/openai

# 响应
{
    "provider": "openai",
    "has_api_key": true,
    "base_url": "https://api.openai.com/v1"
}
```

### 6. 获取 Anthropic 配置（不显示密钥）

```bash
GET /api/v1/config/llm/anthropic

# 响应
{
    "provider": "anthropic",
    "has_api_key": true,
    "base_url": "https://api.anthropic.com"
}
```

## 使用方式

### 方式 1: 初始化脚本（推荐用于第一次设置）

```bash
# 方法 A: 使用交互式脚本
bash setup-llm-config.sh

# 方法 B: 使用 Python 脚本
OPENAI_API_KEY=sk-... python init-llm-config.py
```

### 方式 2: API 调用

```bash
# 使用 curl 保存 OpenAI 配置
curl -X POST http://localhost:8000/api/v1/config/llm/providers \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "model_name": "gpt-4-turbo-preview",
    "api_key": "sk-...",
    "display_name": "OpenAI GPT-4 Turbo",
    "priority": 10
  }'
```

### 方式 3: 在代码中读取配置

#### 获取 OpenAI 客户端

```python
from app.services.config_service import ConfigService
from openai import AsyncOpenAI

async def get_openai():
    config = await ConfigService.get_openai_config(db_session)
    
    client = AsyncOpenAI(
        api_key=config["api_key"],
        base_url=config["base_url"],
    )
    return client
```

#### 获取特定提供商配置

```python
from app.services.config_service import ConfigService

async def get_provider_info():
    # 从数据库获取
    config = await ConfigService.get_provider_config(db_session, "openai")
    
    if config:
        print(f"Model: {config.model_name}")
        print(f"API Key: {config.get_api_key()}")
        print(f"Base URL: {config.base_url}")
```

#### 列出所有活跃的提供商

```python
async def list_providers():
    providers = await ConfigService.list_providers(db_session, active_only=True)
    
    for provider in providers:
        print(f"{provider.provider}: {provider.model_name}")
```

#### 保存新配置

```python
async def save_openai_config():
    config = await ConfigService.save_provider_config(
        db_session,
        provider="openai",
        model_name="gpt-4-turbo-preview",
        api_key="sk-...",
        base_url=None,
        display_name="My OpenAI Config",
        priority=10,
    )
    await db_session.commit()
    return config
```

## 优先级系统

当有多个相同提供商的配置时，优先级最高的（数字最小的）会被使用：

```
Priority 5  - OpenAI Config A  ← 最优先使用
Priority 10 - OpenAI Config B
Priority 20 - OpenAI Config C
```

## 回退机制

如果数据库中没有配置，系统会自动回退到环境变量：

```
1. 查询数据库 → 找到？ 使用数据库配置
2. 找不到？ → 检查环境变量 → 找到？ 使用环境变量
3. 都找不到？ → 错误
```

可以通过 `use_env_fallback=False` 参数禁用回退：

```python
config = await ConfigService.get_openai_config(db_session, use_env_fallback=False)
# 如果数据库没有配置，会返回 {api_key: None, base_url: None}
```

## 加密机制

所有 API 密钥在数据库中被加密存储。加密由 `app/core/encryption.py` 管理：

```python
# 加密
config.set_api_key("sk-...")  # 自动加密

# 解密
plaintext_key = config.get_api_key()  # 自动解密
```

## 安全建议

1. **环境变量** - 不要在代码中硬编码密钥，使用环境变量
2. **数据库加密** - 确保数据库连接使用 SSL/TLS
3. **API 认证** - 所有配置管理 API 都需要有效的 JWT token
4. **权限控制** - 考虑为不同用户分配不同的配置管理权限

## 故障排除

### 问题: "OpenAI configuration not found"

**原因**: 数据库中没有 OpenAI 配置，且环境变量未设置

**解决方案**:
```bash
# 方案 1: 使用 setup 脚本
bash setup-llm-config.sh

# 方案 2: 设置环境变量后重启
export OPENAI_API_KEY=sk-...
```

### 问题: "Error loading config from database"

**原因**: 数据库连接问题或加密密钥不匹配

**解决方案**:
1. 检查数据库是否运行
2. 检查 `ENCRYPTION_KEY` 环境变量是否设置
3. 查看服务器日志获取详细错误信息

### 问题: API Key 显示为已存储但无法使用

**原因**: 加密/解密失败（通常是加密密钥不同）

**解决方案**:
1. 确保所有实例使用相同的 `ENCRYPTION_KEY`
2. 重新保存配置

## 示例工作流

### 第一次部署

```bash
# 1. 启动后端
cd backend && uvicorn app.main:app --reload &

# 2. 初始化配置
bash setup-llm-config.sh

# 3. 验证配置
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/config/llm/providers

# 4. 现在可以使用 Copilot 功能了
```

### 更新配置（无需重启）

```bash
# 使用 API 更新
curl -X POST http://localhost:8000/api/v1/config/llm/providers \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "model_name": "gpt-4-turbo-preview",
    "api_key": "new-api-key",
    "priority": 5
  }'

# 应用立即使用新配置，无需重启
```

## 完全迁移到数据库配置

如果要完全停止使用环境变量，只用数据库配置：

```python
# 在 config_service.py 中
config = await ConfigService.get_openai_config(
    db_session,
    use_env_fallback=False  # 禁用环保变量回退
)

if not config["api_key"]:
    raise RuntimeError("OpenAI not configured in database")
```

## 相关文件

- **模型**: `backend/app/models/llm_config.py`
- **服务**: `backend/app/services/config_service.py`
- **API**: `backend/app/api/v1/config.py`
- **示例**: `backend/app/examples/database_config_example.py`
- **初始化**: `init-llm-config.py`
- **设置脚本**: `setup-llm-config.sh`
