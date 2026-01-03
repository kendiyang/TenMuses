# LLM架构重构实施报告

**实施日期**: 2026年1月1日  
**状态**: ✅ 核心重构已完成  
**下一步**: 需要更新引用代码并进行测试

---

## 📋 已完成的改进

### ✅ P1: 修复命名冲突（已完成）

**问题**: `LLMConfig` 在两个文件中重复定义导致命名冲突

**解决方案**:
- 将 `backend/app/schemas/node.py` 中的 `LLMConfig` 重命名为 `LLMNodeConfig`
- 更新了3处引用：类定义、RouterConfig、NodeData

**文件变更**:
- ✅ `backend/app/schemas/node.py` - 重命名完成

**影响**:
- 避免了与数据库模型 `models/llm_config.py` 的命名冲突
- 代码更清晰：NodeConfig用于节点配置，LLMConfig用于数据库模型

---

### ✅ P0: 创建新的数据库架构（已完成）

**问题**: 
- 旧架构：单表存储，provider和model_name在同一张表
- API key和base_url需要为每个模型重复存储
- 无法表达"模型与供应商的关联关系"

**解决方案**: 拆分为两张表

#### 1. 供应商表 (`llm_providers`)

**文件**: `backend/app/models/llm_provider.py` ✅

**字段**:
```python
- id: UUID (主键)
- name: String (供应商标识，唯一) - "openai", "anthropic"
- display_name: String - "OpenAI", "Anthropic"
- api_key_encrypted: Text - 加密的API密钥
- base_url: String (可选) - 自定义base URL
- is_active: Boolean - 是否激活
- priority: Integer - 优先级
- description: Text - 描述
- icon_url: String (可选) - 图标URL
- created_at, updated_at: DateTime
```

**方法**:
- `set_api_key(plaintext_key)` - 加密并存储
- `get_api_key()` - 解密并返回
- `to_dict(include_api_key=False)` - 转换为字典

**关系**:
- `models` - 一对多关系，指向 LLMModel

---

#### 2. 模型表 (`llm_models`)

**文件**: `backend/app/models/llm_model.py` ✅

**字段**:
```python
- id: UUID (主键)
- provider_id: UUID (外键 -> llm_providers.id)
- model_name: String - "gpt-4-turbo-preview"
- display_name: String - "GPT-4 Turbo Preview"
- model_family: String - "gpt-4", "claude-3"
- version: String - 版本号

# 默认参数
- default_temperature: Float (0.7)
- default_max_tokens: Integer
- default_top_p: Float (1.0)
- context_window: Integer - 上下文窗口大小

# 功能支持
- supports_streaming: Boolean (True)
- supports_function_calling: Boolean (False)
- supports_vision: Boolean (False)
- supports_json_mode: Boolean (False)

# 成本信息
- cost_per_1k_input_tokens: Float
- cost_per_1k_output_tokens: Float

# 其他
- is_active: Boolean
- priority: Integer
- description: Text
- usage_notes: Text
- tags: String (逗号分隔)
- created_at, updated_at: DateTime
```

**索引**:
- 唯一索引：`(provider_id, model_name)` - 同一供应商下模型名唯一
- 普通索引：`is_active`, `model_family`

**关系**:
- `provider` - 多对一关系，指向 LLMProvider

**方法**:
- `to_dict(include_provider=False)` - 转换为字典
- `get_full_name()` - 获取完整名称（供应商 + 模型）

---

#### 3. 数据库初始化更新

**文件**: `backend/app/models/__init__.py` ✅

**变更**:
```python
# 新增导入
from app.models.llm_provider import LLMProvider
from app.models.llm_model import LLMModel

# 保留旧模型（向后兼容）
from app.models.llm_config import LLMConfig

__all__ = [
    # ...existing...
    "LLMConfig",    # 旧模型（待迁移后废弃）
    "LLMProvider",  # 新：供应商表
    "LLMModel",     # 新：模型表
]
```

---

#### 4. 数据迁移脚本

**文件**: `backend/app/scripts/migrate_llm_config_to_provider_model.py` ✅

**功能**:
1. 创建新表 `llm_providers` 和 `llm_models`
2. 从旧表 `llm_configs` 读取数据
3. 按供应商分组，创建供应商记录
4. 为每个配置创建模型记录
5. 验证迁移结果
6. 保留旧表（验证后手动删除）

**运行方式**:
```bash
cd backend
python -m app.scripts.migrate_llm_config_to_provider_model
```

**迁移逻辑**:
```
llm_configs 表 (旧):
├── provider: "openai", model_name: "gpt-4-turbo"
├── provider: "openai", model_name: "gpt-4o"
└── provider: "anthropic", model_name: "claude-3-sonnet"

            ↓ 迁移

llm_providers 表 (新):
├── name: "openai", api_key: "...", base_url: "..."
└── name: "anthropic", api_key: "...", base_url: "..."

llm_models 表 (新):
├── provider_id: (openai), model_name: "gpt-4-turbo"
├── provider_id: (openai), model_name: "gpt-4o"
└── provider_id: (anthropic), model_name: "claude-3-sonnet"
```

---

### ✅ P2: 重构LLMClient服务（已完成）

**问题**:
- 旧代码逻辑重复，在 `get_client()` 中重复创建客户端
- 缺少配置验证
- 缓存机制不明确

**解决方案**: 全新重构

**文件**: `backend/app/services/llm_client_v2.py` ✅

**主要改进**:

#### 1. 双缓存机制
```python
# 新架构缓存：model_id -> (Model, Provider)
self.model_cache: Dict[str, Tuple[LLMModel, LLMProvider]] = {}

# 旧架构缓存：(provider_name, model_name) -> (Model, Provider)
self.legacy_cache: Dict[Tuple[str, str], Tuple[LLMModel, LLMProvider]] = {}
```

#### 2. 支持两种调用方式

**方式1: 通过model_id（新架构，推荐）**
```python
await llm_client.invoke(
    messages,
    model_id="uuid-xxx",  # 直接使用数据库中的模型ID
    temperature=0.8
)
```

**方式2: 通过provider + model（旧架构，向后兼容）**
```python
await llm_client.invoke(
    messages,
    provider="openai",
    model="gpt-4-turbo-preview",
    temperature=0.8
)
```

#### 3. 核心方法

**`get_client_by_model_id(model_id, **kwargs)`** - 新方法
- 通过模型ID获取客户端
- 从缓存或数据库加载配置
- 自动读取供应商的API key和base_url
- 合并模型默认参数和覆盖参数

**`get_client(provider, model, **kwargs)`** - 兼容方法
- 保持向后兼容
- 优先使用数据库配置
- 回退到环境变量

**`_build_client(provider, model, **kwargs)`** - 统一构建
- 单一职责：只负责构建客户端
- 支持参数覆盖：temperature, max_tokens, top_p
- 根据供应商创建对应的LangChain客户端

#### 4. 缓存管理

**自动刷新**:
```python
cache_ttl = 300  # 5分钟自动过期
```

**手动刷新**:
```python
await llm_client.refresh_cache()  # 强制刷新
```

#### 5. 辅助方法

**`get_available_models()`** - 获取所有可用模型
```python
models = await llm_client.get_available_models()
# 返回: [
#   {
#     "model_id": "uuid-xxx",
#     "model_name": "gpt-4-turbo-preview",
#     "display_name": "GPT-4 Turbo Preview",
#     "provider_name": "openai",
#     "supports_streaming": true,
#     ...
#   }
# ]
```

#### 6. 错误处理

- 模型不存在：抛出 `ValueError` 并给出清晰错误信息
- 数据库加载失败：自动回退到环境变量配置
- 重试机制：使用 `tenacity` 库，最多重试3次

---

## 🔄 架构对比

### 旧架构（单表）
```
llm_configs 表:
├── id: UUID
├── provider: String         ← 每个模型都要重复
├── model_name: String
├── api_key_encrypted: Text  ← 每个模型都要重复
├── base_url: String         ← 每个模型都要重复
├── display_name: String
├── is_active: Boolean
└── priority: Integer

问题:
- ❌ API key重复存储
- ❌ base_url重复存储
- ❌ 无法独立管理供应商
- ❌ 修改API key需要更新多条记录
```

### 新架构（双表）
```
llm_providers 表 (供应商):
├── id: UUID
├── name: String (唯一)
├── api_key_encrypted: Text  ← 只存储一次
├── base_url: String         ← 只存储一次
└── ...

        ↓ 一对多关系

llm_models 表 (模型):
├── id: UUID
├── provider_id: UUID → llm_providers.id
├── model_name: String
├── default_temperature: Float
├── supports_streaming: Boolean
└── ...

优点:
- ✅ API key只存储一次
- ✅ base_url只存储一次
- ✅ 可独立管理供应商
- ✅ 修改API key只需更新一条记录
- ✅ 支持更丰富的模型元数据
```

---

## 📊 数据流对比

### 旧流程
```
前端发送: { provider: "openai", model: "gpt-4" }
    ↓
LLMClient.get_client(provider, model)
    ↓
查询: WHERE provider='openai' AND model_name='gpt-4'
    ↓
返回: LLMConfig (包含重复的api_key和base_url)
```

### 新流程（推荐）
```
前端发送: { model_id: "uuid-xxx" }
    ↓
LLMClient.get_client_by_model_id(model_id)
    ↓
查询: JOIN llm_models和llm_providers ON provider_id
    ↓
返回: (Model配置, Provider配置)
    ↓
使用Provider的api_key和base_url + Model的默认参数
```

---

## ⚠️ 待完成的任务

### 🔴 高优先级

#### 1. 运行数据库迁移
```bash
cd backend
python -m app.scripts.migrate_llm_config_to_provider_model
```

#### 2. 替换旧的LLMClient
```bash
# 备份旧文件
mv app/services/llm_client.py app/services/llm_client_old.py

# 使用新文件
mv app/services/llm_client_v2.py app/services/llm_client.py
```

#### 3. 更新所有引用 `LLMNodeConfig` 的代码

**需要更新的文件**:
- `backend/app/services/executor_library.py`
- `backend/app/services/dynamic_graph_factory.py`
- 其他使用 `llm_config` 的地方

**更新示例**:
```python
# 旧代码
from app.schemas.node import LLMConfig  # ❌ 不存在了

config.llm_config.provider  # ❌ 这是旧的内联配置
config.llm_config.model

# 新代码
from app.schemas.node import LLMNodeConfig  # ✅ 新名称

# 方案A: 如果前端传model_id
await llm_client.invoke(
    messages,
    model_id=config.llm_config.model_id,  # 前端需要传model_id
    temperature=config.llm_config.temperature
)

# 方案B: 保持向后兼容（前端仍传provider+model）
await llm_client.invoke(
    messages,
    provider=config.llm_config.provider,
    model=config.llm_config.model,
    temperature=config.llm_config.temperature
)
```

#### 4. 更新API端点和Schema

**需要更新**:
- `backend/app/api/v1/config.py` - 修改API端点逻辑
- 创建新的Response Schema for Provider和Model

**新的API设计建议**:
```python
# 供应商管理
GET  /api/v1/providers          # 列出所有供应商
POST /api/v1/providers          # 创建供应商
GET  /api/v1/providers/{id}     # 获取供应商详情
PUT  /api/v1/providers/{id}     # 更新供应商
DELETE /api/v1/providers/{id}   # 删除供应商

# 模型管理
GET  /api/v1/models             # 列出所有模型
POST /api/v1/models             # 创建模型
GET  /api/v1/models/{id}        # 获取模型详情
PUT  /api/v1/models/{id}        # 更新模型
DELETE /api/v1/models/{id}      # 删除模型

# 获取可用模型（用于前端下拉选择）
GET  /api/v1/models/available   # 返回所有激活的模型列表
```

---

### 🟡 中优先级

#### 5. 更新Schema定义

在 `backend/app/schemas/node.py` 中更新 `LLMNodeConfig`:
```python
class LLMNodeConfig(BaseModel):
    """LLM节点运行时配置"""
    
    # 新架构：优先使用model_id
    model_id: Optional[str] = Field(
        None,
        description="数据库中的模型ID（推荐）"
    )
    
    # 旧架构：向后兼容
    provider: Optional[Literal["openai", "anthropic"]] = Field(
        None,
        description="供应商名称（已废弃，请使用model_id）"
    )
    model: Optional[str] = Field(
        None,
        description="模型名称（已废弃，请使用model_id）"
    )
    
    # 运行时参数覆盖
    temperature: Optional[float] = Field(None, ge=0, le=1)
    max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    
    # RAG配置（保持不变）
    enable_rag: bool = False
    # ...
```

#### 6. 创建初始化脚本

创建 `backend/app/scripts/init_default_llm_configs.py`:
- 自动创建常用的供应商和模型配置
- 用于新安装时的初始化

---

### 🟢 低优先级

#### 7. 前端适配

- 更新前端类型定义，添加 `model_id` 字段
- 创建模型选择UI组件
- 从 `/api/v1/models/available` 获取可用模型列表

#### 8. 文档更新

- 更新API文档
- 更新开发者指南
- 添加迁移指南

#### 9. 测试

- 单元测试：测试新的LLMClient方法
- 集成测试：测试完整流程
- 性能测试：测试缓存机制

---

## ✅ 当前状态总结

| 任务 | 状态 | 文件 |
|------|------|------|
| P1: 修复命名冲突 | ✅ 完成 | `schemas/node.py` |
| P0: 创建供应商表模型 | ✅ 完成 | `models/llm_provider.py` |
| P0: 创建模型表 | ✅ 完成 | `models/llm_model.py` |
| P0: 更新模型导入 | ✅ 完成 | `models/__init__.py` |
| P0: 创建迁移脚本 | ✅ 完成 | `scripts/migrate_...py` |
| P2: 重构LLMClient | ✅ 完成 | `services/llm_client_v2.py` |
| 运行数据库迁移 | ⏳ 待执行 | - |
| 替换旧LLMClient | ⏳ 待执行 | - |
| 更新代码引用 | ⏳ 待执行 | 多个文件 |
| 更新API端点 | ⏳ 待执行 | `api/v1/config.py` |
| 集成测试 | ⏳ 待执行 | - |

---

## 🚀 下一步行动计划

### 阶段1: 数据迁移（今天）
1. 备份数据库
2. 运行迁移脚本
3. 验证数据

### 阶段2: 代码更新（明天）
1. 替换LLMClient文件
2. 更新executor_library.py等文件中的引用
3. 更新API端点

### 阶段3: 测试（后天）
1. 运行集成测试
2. 手动测试主要功能
3. 修复发现的问题

### 阶段4: 清理（完成后）
1. 删除旧的llm_configs表
2. 删除llm_client_old.py备份
3. 更新文档

---

**准备好开始阶段1（数据迁移）了吗？**
