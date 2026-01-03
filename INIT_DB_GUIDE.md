# 数据库供应商和模型初始化脚本使用指南

## 📋 脚本说明

`init_db_providers_models.py` 是一个用于初始化 TenMuses 数据库中 LLM 供应商和模型配置的脚本。

### 功能特性

✅ 自动创建或更新供应商配置（支持幂等操作）  
✅ 自动创建或更新模型配置  
✅ API 密钥自动加密存储  
✅ 详细的日志输出  
✅ 配置验证和摘要显示

---

## 🚀 快速开始

### 1. 确保环境准备就绪

```bash
# 确保数据库已启动
# 确保 .env 文件中已配置 DATABASE_URL 和 JWT_SECRET_KEY

# 示例 .env 配置：
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/tenmuses
JWT_SECRET_KEY=your-secret-key-here
```

### 2. 运行初始化脚本

```bash
# 方法 1: 直接运行
python init_db_providers_models.py

# 方法 2: 作为可执行文件运行
./init_db_providers_models.py
```

---

## 📊 脚本配置的数据

### 供应商配置

| 字段 | 值 |
|------|-----|
| 名称 | `openai` |
| 显示名称 | `OpenAI (Custom)` |
| API Key | `sk-wvbHvCfLHCvCf0kHEB8xTOInLVfZtDe4rNB0FiHQxgbQ0OhY` |
| Base URL | `https://chrisapius.top/v1` |
| 优先级 | 10 |
| 状态 | 激活 ✅ |

### 模型配置

#### 1. GPT-4o (聊天模型)

| 字段 | 值 |
|------|-----|
| 模型名称 | `gpt-4o` |
| 显示名称 | `GPT-4o` |
| 模型系列 | `gpt-4` |
| 上下文窗口 | 128,000 tokens |
| 支持流式 | ✅ |
| 支持函数调用 | ✅ |
| 支持视觉 | ✅ |
| 支持 JSON 模式 | ✅ |
| 输入成本 | $0.005 / 1K tokens |
| 输出成本 | $0.015 / 1K tokens |

#### 2. text-embedding-3-large (向量模型)

| 字段 | 值 |
|------|-----|
| 模型名称 | `text-embedding-3-large` |
| 显示名称 | `Text Embedding 3 Large` |
| 模型系列 | `embedding` |
| 上下文窗口 | 8,191 tokens |
| 输出维度 | 3,072 |
| 支持流式 | ✗ |
| 输入成本 | $0.00013 / 1K tokens |

---

## 📝 输出示例

```
======================================================================
TenMuses - 数据库供应商和模型初始化脚本
======================================================================

步骤 1: 初始化供应商配置
----------------------------------------------------------------------
创建新供应商 'openai'...
✓ 供应商 'openai' 已创建

步骤 2: 初始化模型配置
----------------------------------------------------------------------
  创建新模型 'gpt-4o'...
  ✓ 模型 'gpt-4o' 已创建
  创建新模型 'text-embedding-3-large'...
  ✓ 模型 'text-embedding-3-large' 已创建

步骤 3: 保存到数据库
----------------------------------------------------------------------
✓ 所有配置已成功写入数据库

======================================================================
初始化完成摘要
======================================================================
供应商名称: openai
供应商显示名: OpenAI (Custom)
Base URL: https://chrisapius.top/v1
API Key: sk-wvbHvCfLHCvCf0kH... (已加密存储)
供应商 ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
激活状态: ✓ 是

已配置模型数: 2
  1. GPT-4o (gpt-4o)
     - 模型系列: gpt-4
     - 上下文窗口: 128000 tokens
     - 支持流式: ✓
     - 支持函数调用: ✓
     - 支持视觉: ✓
     - 模型 ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

  2. Text Embedding 3 Large (text-embedding-3-large)
     - 模型系列: embedding
     - 上下文窗口: 8191 tokens
     - 支持流式: ✗
     - 支持函数调用: ✗
     - 支持视觉: ✗
     - 模型 ID: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

======================================================================
✓ 初始化成功！现在可以使用这些配置进行测试。
======================================================================
```

---

## 🔄 重复运行

脚本支持**幂等操作**：

- ✅ 如果供应商已存在，会更新配置
- ✅ 如果模型已存在，会更新配置
- ✅ 可以安全地多次运行

---

## 🛠️ 自定义配置

如需修改配置，编辑脚本中的以下部分：

```python
# 供应商配置
PROVIDER_CONFIG = {
    "name": "openai",  # 修改供应商名称
    "api_key": "your-api-key",  # 修改 API Key
    "base_url": "https://your-url.com/v1",  # 修改 Base URL
    # ...
}

# 模型配置
MODELS_CONFIG = [
    {
        "model_name": "gpt-4o",  # 修改模型名称
        "display_name": "GPT-4o",  # 修改显示名称
        # ...
    },
    # 添加更多模型...
]
```

---

## 🔍 验证配置

初始化完成后，脚本会自动列出所有配置。你也可以：

### 方法 1: 查看数据库

```sql
-- 查看供应商
SELECT id, name, display_name, base_url, is_active FROM llm_providers;

-- 查看模型
SELECT id, provider_id, model_name, display_name, is_active FROM llm_models;
```

### 方法 2: 使用 API

```bash
# 启动后端服务
cd backend
uvicorn app.main:app --reload

# 访问 API 文档
# http://localhost:8000/docs

# 查看供应商列表
curl http://localhost:8000/api/v1/llm-config/providers

# 查看模型列表
curl http://localhost:8000/api/v1/llm-config/models
```

---

## 🧪 测试配置

### 测试 LLM 调用

```python
from app.services.llm_client import llm_client
from langchain_core.messages import HumanMessage

# 使用 gpt-4o
result = await llm_client.invoke(
    messages=[HumanMessage(content="Hello!")],
    provider="openai",
    model="gpt-4o"
)
print(result)
```

### 测试 Embedding

```python
from app.services.embedding_service import EmbeddingService

# 使用 text-embedding-3-large
service = EmbeddingService(
    provider="openai",
    model="text-embedding-3-large"
)
embeddings = await service.embed_documents(["Hello world"])
print(f"向量维度: {len(embeddings[0])}")  # 应该是 3072
```

---

## ⚠️ 常见问题

### 问题 1: `ModuleNotFoundError: No module named 'app'`

**解决方案**: 确保从项目根目录运行脚本

```bash
cd /Users/mg/Workspace/TenMuses
python init_db_providers_models.py
```

### 问题 2: 数据库连接失败

**解决方案**: 检查 `.env` 文件中的 `DATABASE_URL` 配置

```bash
# 确保数据库正在运行
pg_isready -h localhost -p 5432

# 测试连接
psql postgresql://postgres:password@localhost:5432/tenmuses
```

### 问题 3: 加密失败

**解决方案**: 确保 `.env` 文件中已设置 `JWT_SECRET_KEY`

```bash
# .env
JWT_SECRET_KEY=your-secret-key-here
```

### 问题 4: 表不存在

**解决方案**: 先启动后端服务以自动创建表

```bash
cd backend
uvicorn app.main:app --reload
# 表会自动创建，然后停止服务并运行初始化脚本
```

---

## 📚 相关文档

- [LLM_ARCHITECTURE_QUICK_REFERENCE.md](./LLM_ARCHITECTURE_QUICK_REFERENCE.md) - LLM 架构快速参考
- [LLM_MIGRATION_COMPLETE_REPORT.md](./LLM_MIGRATION_COMPLETE_REPORT.md) - 完整迁移报告
- [backend/app/models/llm_provider.py](./backend/app/models/llm_provider.py) - 供应商模型定义
- [backend/app/models/llm_model.py](./backend/app/models/llm_model.py) - 模型定义

---

## 🎯 下一步

初始化完成后，你可以：

1. ✅ 启动后端服务测试 API
2. ✅ 使用 Postman/curl 测试端点
3. ✅ 运行集成测试
4. ✅ 在应用中调用 LLM 和 Embedding 服务

---

**脚本创建日期**: 2026-01-01  
**版本**: 1.0.0  
**作者**: GitHub Copilot
