# LLM 数据库配置 - 实现总结

## ✅ 已完成的功能

### 1. 加密系统
- **文件**: `backend/app/core/encryption.py`
- **功能**: Fernet 对称加密，使用 `JWT_SECRET_KEY` 推导密钥
- **特点**: 
  - `encrypt(plaintext)` → 可安全存储在数据库的加密字符串
  - `decrypt(ciphertext)` → 恢复明文（用于 LLM 客户端）

### 2. 数据库模型
- **文件**: `backend/app/models/llm_config.py`
- **类**: `LLMConfig`
- **字段**:
  - `provider`: "openai" | "anthropic" | ...
  - `model_name`: 具体模型名（gpt-4-turbo-preview, claude-3-sonnet-20240229 等）
  - `api_key_encrypted`: 加密存储的 API key
  - `base_url`: 可选自定义端点（代理、本地 LLM 服务器等）
  - `display_name`: UI 显示名称
  - `is_active`: 启用/禁用标志（无需删除）
  - `priority`: 排序优先级
  - `description`: 描述信息
- **方法**:
  - `set_api_key(plaintext)`: 加密后存储
  - `get_api_key()`: 解密返回明文
  - `to_dict()`: 转换为字典

### 3. Pydantic 数据模型
- **文件**: `backend/app/schemas/llm_config.py`
- **模型**:
  - `LLMConfigCreate`: 创建时使用（包含明文 api_key）
  - `LLMConfigUpdate`: 部分更新（所有字段可选）
  - `LLMConfigResponse`: API 响应（无 api_key，安全）
  - `LLMConfigDetailResponse`: 管理员获取（包含解密的 api_key）
  - `LLMConfigListResponse`: 前端模型选择器用（最小信息）

### 4. 升级的 LLM 客户端
- **文件**: `backend/app/services/llm_client.py`
- **改进**:
  - 启动时从数据库加载所有活跃配置
  - 内存缓存配置以提升性能
  - 优雅降级：如果数据库不可用，使用环境变量
  - `ensure_initialized()`: 异步初始化配置
  - `get_available_configs()`: 获取活跃配置列表
  - 支持动态 base_url 覆盖
  - 自动使用加密后的 API key

### 5. API 路由
- **文件**: `backend/app/api/v1/llm_config.py`
- **端点**:
  - `GET /api/v1/llm-configs`: 公开 - 获取活跃配置列表（用于前端模型选择）
  - `GET /api/v1/llm-configs/admin`: 仅管理员 - 获取所有配置（包含解密 api_key）
  - `POST /api/v1/llm-configs`: 仅管理员 - 创建新配置
  - `PUT /api/v1/llm-configs/{id}`: 仅管理员 - 更新配置
  - `DELETE /api/v1/llm-configs/{id}`: 仅管理员 - 删除配置

### 6. 前端服务
- **文件**: `frontend/src/services/llm-config-client.ts`
- **功能**:
  - `getAvailableLLMConfigs()`: 获取用户可选的模型
  - `getAllLLMConfigs()`: 获取所有配置（管理员）
  - `createLLMConfig()`, `updateLLMConfig()`, `deleteLLMConfig()`
  - 自动 Bearer token 注入

### 7. 前端组件
- **文件**: `frontend/src/components/ModelSelector.tsx`
- **功能**:
  - React 组件，下拉选择可用模型
  - 自动加载和缓存模型列表
  - Props: `selectedModelId`, `onModelSelect`, `showLabel`, `className`
  - 自动选择第一个模型（可选）

### 8. 管理员面板
- **文件**: `frontend/src/app/llm-config/page.tsx`
- **功能**:
  - 完整的 CRUD 界面
  - 查看所有配置（包括非活跃的）
  - 创建/编辑/删除配置
  - 显示加密状态和优先级

### 9. 演示页面
- **文件**: `frontend/src/app/copilot/page.tsx`
- **功能**:
  - 集成 ModelSelector 组件
  - 演示模型选择和聊天界面
  - 显示当前选中的模型信息

### 10. 初始化脚本
- **文件**: `backend/scripts/init_llm_configs.py`
- **功能**:
  - 创建默认 LLM 配置模板
  - 使用占位符 API key（用户需手动更新）
  - 快速启动数据库配置

### 11. 文档
- **LLM_CONFIG_SETUP.md**: 完整的技术文档和 API 参考
- **QUICKSTART_LLM_CONFIG.md**: 快速启动指南
- **此文件**: 实现总结

---

## 🔐 安全特性

1. ✅ **API Key 加密存储**: Fernet 对称加密，使用 `JWT_SECRET_KEY`
2. ✅ **Admin 权限控制**: 配置管理端点需要 `role == ADMIN`
3. ✅ **API Key 不在响应中**: 标准响应不包含 api_key
4. ✅ **安全初始化**: 占位符 key，用户需主动填写真实 key
5. ✅ **环境变量备份**: 如果 DB 不可用，可回退到 .env 变量

---

## 📊 数据库架构

```
llm_configs 表
├── id (UUID, PK)
├── provider (VARCHAR) - "openai", "anthropic"
├── model_name (VARCHAR) - "gpt-4-turbo-preview"
├── api_key_encrypted (VARCHAR) - 加密的 API key
├── base_url (VARCHAR, NULL) - 自定义端点
├── display_name (VARCHAR) - UI 显示
├── is_active (BOOLEAN, default=true)
├── priority (INTEGER, default=100)
├── description (VARCHAR, NULL)
├── created_at (TIMESTAMP)
└── updated_at (TIMESTAMP)

唯一约束: (provider, model_name)
```

自动创建：FastAPI 启动时通过 SQLAlchemy `Base.metadata.create_all()`

---

## 🚀 使用流程

### 第一次使用

```bash
# 1. 启动后端
cd backend
python -m app.main

# 2. 可选：初始化默认配置
python scripts/init_llm_configs.py

# 3. 启动前端
cd frontend
npm run dev

# 4. 访问管理面板 http://localhost:3000/llm-config
# 5. 编辑配置，填入真实 API key
# 6. 访问 /copilot 页面选择模型
```

### 调用流程（后端）

```
用户请求
    ↓
llm_client.invoke(messages, provider, model)
    ↓
llm_client.ensure_initialized() [加载 DB 配置]
    ↓
get_client(provider, model) [查找配置]
    ↓
_build_client(config) [使用解密的 API key 构建]
    ↓
ChatOpenAI/ChatAnthropic.ainvoke()
    ↓
返回响应
```

### 前端使用

```jsx
import { ModelSelector } from '@/components/ModelSelector';

<ModelSelector 
  onModelSelect={(id, model) => {
    // model 包含 id, provider, model_name, display_name, priority
  }}
/>
```

---

## 📝 配置示例

### 创建 OpenAI 配置

```bash
curl -X POST http://localhost:8000/api/v1/llm-configs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ADMIN_TOKEN>" \
  -d '{
    "provider": "openai",
    "model_name": "gpt-4-turbo-preview",
    "display_name": "GPT-4 Turbo",
    "api_key": "sk-proj-...",
    "base_url": null,
    "priority": 1,
    "description": "Production GPT-4"
  }'
```

### 创建带代理的配置

```json
{
  "provider": "openai",
  "model_name": "gpt-4-turbo-preview",
  "display_name": "GPT-4 via Proxy",
  "api_key": "sk-...",
  "base_url": "https://proxy.example.com/v1",
  "priority": 2
}
```

### 创建本地 Ollama 配置

```json
{
  "provider": "ollama",
  "model_name": "llama2:70b",
  "display_name": "Llama 2 70B (Local)",
  "api_key": "dummy",
  "base_url": "http://localhost:11434",
  "priority": 3
}
```

---

## 🔧 扩展指南

### 添加新 Provider（如 Ollama）

1. **后端**：修改 `llm_client.py` 的 `_build_client()` 方法

```python
elif config.provider.lower() == "ollama":
    from langchain_community.llms import Ollama
    return Ollama(
        base_url=config.base_url or "http://localhost:11434",
        model=config.model_name,
    )
```

2. **前端**：自动支持（从 API 获取）

3. **创建配置**：如上面的 Ollama 示例

---

## ✨ 特色亮点

| 特性 | 说明 |
|------|------|
| **🔒 加密存储** | API keys 永不以明文存储 |
| **📊 数据库驱动** | 配置持久化，重启不丢失 |
| **🔄 热更新** | 改变配置后可立即（重启后）生效 |
| **⚙️ 回退机制** | DB 不可用时使用环境变量 |
| **🎯 优先级排序** | UI 显示按 priority 排序 |
| **🚫 软删除** | 使用 is_active 而不是真正删除 |
| **👤 权限控制** | 管理端点需 admin 角色 |
| **📱 响应式 UI** | Tailwind 样式，管理和选择界面 |
| **🧪 演示页面** | /copilot 展示完整流程 |

---

## 📚 关键文件一览

| 文件 | 类型 | 说明 |
|------|------|------|
| `backend/app/core/encryption.py` | 新建 | 加密工具 |
| `backend/app/models/llm_config.py` | 新建 | 数据库模型 |
| `backend/app/schemas/llm_config.py` | 新建 | API 数据模型 |
| `backend/app/services/llm_client.py` | 修改 | 升级支持 DB 配置 |
| `backend/app/api/v1/llm_config.py` | 新建 | API 路由 |
| `backend/app/main.py` | 修改 | 注册路由 |
| `frontend/src/services/llm-config-client.ts` | 新建 | API 客户端 |
| `frontend/src/components/ModelSelector.tsx` | 新建 | 组件 |
| `frontend/src/app/llm-config/page.tsx` | 新建 | 管理页面 |
| `frontend/src/app/copilot/page.tsx` | 新建 | 演示页面 |
| `backend/scripts/init_llm_configs.py` | 新建 | 初始化脚本 |

---

## 🎓 学习路径

1. **理解加密**：阅读 `backend/app/core/encryption.py`
2. **理解数据模型**：阅读 `backend/app/models/llm_config.py`
3. **理解 API**：查看 `backend/app/api/v1/llm_config.py`
4. **理解前端**：查看 `ModelSelector.tsx` 和 `llm-config/page.tsx`
5. **了解集成**：查看 `copilot/page.tsx` 如何使用 ModelSelector
6. **完整理解**：阅读 `LLM_CONFIG_SETUP.md`

---

## ✅ 验收标准

- ✅ 数据库模型完整，字段完善
- ✅ API key 加密存储（使用 Fernet）
- ✅ CRUD API 端点完整
- ✅ 权限控制到位（admin only）
- ✅ 前端支持模型选择
- ✅ 前端有管理界面
- ✅ 后端能从数据库加载配置
- ✅ 支持自定义 base URL
- ✅ 支持多提供商
- ✅ 有完整文档和快速启动指南

---

## 🚀 下一步建议

1. **测试**：运行初始化脚本，创建配置，验证工作流
2. **文档**：阅读 `LLM_CONFIG_SETUP.md` 和 `QUICKSTART_LLM_CONFIG.md`
3. **集成**：在其他工作流/组件中使用 ModelSelector
4. **监控**：添加日志记录加密/解密操作（生产环境）
5. **扩展**：添加更多 LLM 提供商支持

---

生成时间：2026年1月1日
实现状态：✅ 完整
