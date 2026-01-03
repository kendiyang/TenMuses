# LLM 配置系统架构图

## 系统整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                         前端应用                                     │
│                    (Next.js + React)                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────┐      ┌──────────────────────┐            │
│  │   ModelSelector      │      │   LLM Config Panel   │            │
│  │   (组件)            │      │   (/llm-config)      │            │
│  │                     │      │   Admin 管理页面     │            │
│  │ ┌────────────────┐ │      │                      │            │
│  │ │  下拉菜单      │ │      │ ┌────────────────┐   │            │
│  │ │  + 模型列表    │ │      │ │ 创建/编辑/删除 │   │            │
│  │ │  + 选择回调    │ │      │ │ 配置表单       │   │            │
│  │ └────────────────┘ │      │ │ 配置列表       │   │            │
│  └──────────────────────┘      │ └────────────────┘   │            │
│           ↓                     │        ↓             │            │
│  ┌──────────────────────┐      │ ┌──────────────────┐ │            │
│  │ llm-config-client.ts │      │ │ llm-config-     │ │            │
│  │ (API 客户端)        │      │ │ client.ts       │ │            │
│  │                     │      │ │ (API 客户端)    │ │            │
│  │ - get/set models    │      │ │                │ │            │
│  │ - create/update/del │      │ │                │ │            │
│  └──────────────────────┘      │ └──────────────────┘ │            │
│           │                    │        │             │            │
└───────────┼────────────────────┼────────┼─────────────┘            │
            │                    │        │                          │
            └────────┬───────────┴────────┘                          │
                     │                                                │
                HTTP │ /api/v1/llm-configs*                         │
                     │ Authorization: Bearer <token>                 │
                     ↓                                                │
┌─────────────────────────────────────────────────────────────────────┐
│                     后端 API                                         │
│                  (FastAPI)                                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────────────────────────────────┐               │
│  │   API 路由层                                     │               │
│  │   (app/api/v1/llm_config.py)                    │               │
│  │                                                  │               │
│  │  GET /llm-configs              [公开]          │               │
│  │  GET /llm-configs/admin        [Admin]         │               │
│  │  POST /llm-configs             [Admin]         │               │
│  │  PUT /llm-configs/{id}         [Admin]         │               │
│  │  DELETE /llm-configs/{id}      [Admin]         │               │
│  └──────────────────────┬──────────────────────────┘               │
│                         ↓                                           │
│  ┌─────────────────────────────────────────────────┐               │
│  │   业务逻辑层                                     │               │
│  │                                                  │               │
│  │  ├─ 权限检查 (get_current_user)               │               │
│  │  ├─ CRUD 操作                                 │               │
│  │  ├─ API Key 加密/解密                        │               │
│  │  └─ 缓存更新 (llm_client.ensure_initialized) │               │
│  └──────────────────────┬──────────────────────────┘               │
│                         ↓                                           │
│  ┌─────────────────────────────────────────────────┐               │
│  │   数据访问层                                     │               │
│  │   (SQLAlchemy ORM)                              │               │
│  └──────────────────────┬──────────────────────────┘               │
│                         ↓                                           │
│  ┌─────────────────────────────────────────────────┐               │
│  │   LLM 客户端服务                                 │               │
│  │   (app/services/llm_client.py)                 │               │
│  │                                                  │               │
│  │  初始化:                                        │               │
│  │  ├─ 加载环境变量备份配置                       │               │
│  │  └─ 准备缓存                                    │               │
│  │                                                  │               │
│  │  运行时:                                        │               │
│  │  ├─ ensure_initialized()  [DB 加载]          │               │
│  │  ├─ get_client()         [获取客户端]         │               │
│  │  ├─ invoke() / stream()  [调用 LLM]           │               │
│  │  └─ get_available_configs() [列表]           │               │
│  └──────────────────────┬──────────────────────────┘               │
│                         ↓                                           │
└─────────────────────────────────────────────────────────────────────┘
                         │
            ┌────────────┬────────────┐
            ↓            ↓            ↓
       ┌─────────┐  ┌─────────┐  ┌──────────────┐
       │ OpenAI  │  │Anthropic│  │ 其他Provider │
       │         │  │         │  │ (扩展支持)   │
       │ API     │  │ API     │  │              │
       └─────────┘  └─────────┘  └──────────────┘
```

---

## 数据流向详解

### 1️⃣ 模型选择流程

```
用户访问 /copilot
    ↓
React mount ModelSelector 组件
    ↓
component.useEffect() 调用
    ↓
llm-config-client.getAvailableLLMConfigs()
    ↓
axios.get('/api/v1/llm-configs')  [无需认证]
    ↓
后端 @router.get("/llm-configs")
    ↓
查询数据库: SELECT * FROM llm_configs WHERE is_active=true
    ↓
返回 JSON [LLMConfigListResponse, ...]
    ↓
前端渲染下拉菜单 <select>
    ↓
用户选择模型
    ↓
onModelSelect(modelId, modelObj) 回调
    ↓
应用保存选中的 model 到 state
```

### 2️⃣ 配置创建/更新流程

```
Admin 用户访问 /llm-config
    ↓
页面加载，认证检查
    ↓
点击 "Add Configuration" 按钮
    ↓
填写表单：
  ├─ provider: "openai"
  ├─ model_name: "gpt-4-turbo-preview"
  ├─ display_name: "GPT-4 Turbo"
  ├─ api_key: "sk-xxx"  [明文输入]
  ├─ base_url: "https://..."
  └─ priority: 1
    ↓
点击 Submit
    ↓
llm-config-client.createLLMConfig(formData)
    ↓
axios.post('/api/v1/llm-configs', formData, {
  headers: { Authorization: `Bearer ${token}` }
})
    ↓
后端 @router.post("/llm-configs")
    ↓
检查权限: user.role == "admin" ?
    ↓ 否
返回 403 Forbidden
    ↓ 是
验证数据 (LLMConfigCreate schema)
    ↓
创建 LLMConfig 实例
    ↓
config.set_api_key(formData.api_key)
    ├─ 调用 encryption_manager.encrypt()
    ├─ Fernet 加密明文密钥
    └─ 密文存储到 config.api_key_encrypted
    ↓
db.add(config)
db.commit()
    ↓
更新 llm_client 缓存
    ├─ await llm_client.ensure_initialized()
    └─ 从 DB 重新加载配置
    ↓
返回 LLMConfigResponse (无 api_key 字段)
    ↓
前端收到响应
    ↓
前端刷新配置列表
    ↓
显示成功消息
```

### 3️⃣ LLM 调用流程

```
后端其他服务需要调用 LLM
    例如：copilot.py 的聊天端点
    ↓
llm_client.invoke(
    messages=[HumanMessage(...)],
    provider="openai",
    model="gpt-4-turbo-preview"
)
    ↓
llm_client.ensure_initialized()  [第一次调用时]
    ├─ 检查 self._initialized 标志
    ├─ 如果未初始化：
    │  ├─ 连接数据库 AsyncSessionLocal()
    │  ├─ 查询: SELECT * FROM llm_configs WHERE is_active=true
    │  ├─ 迭代结果，创建缓存键: f"{provider}_{model_name}"
    │  └─ 存入 self.configs_cache
    └─ 标记 _initialized = true
    ↓
llm_client.get_client("openai", "gpt-4-turbo-preview")
    ├─ 查找缓存键: "openai_gpt-4-turbo-preview"
    ├─ 找到 LLMConfig 对象
    └─ 调用 _build_client(config)
    ↓
_build_client(config)
    ├─ 取出 config.provider  →  "openai"
    ├─ 调用 config.get_api_key()
    │  ├─ encryption_manager.decrypt(config.api_key_encrypted)
    │  └─ 返回明文密钥 "sk-xxx"
    ├─ 使用 base_url（如有）
    └─ return ChatOpenAI(api_key="sk-xxx", ...)
    ↓
client.ainvoke(messages)
    ↓
OpenAI API
    ↓
返回响应
    ↓
应用继续处理响应
```

---

## 数据库架构

```
┌─────────────────────────────────────┐
│         llm_configs 表               │
├─────────────────────────────────────┤
│ 列名               │ 类型      │ 说明 │
├─────────────────────┼──────────┼──────┤
│ id                 │ UUID(PK) │      │
│ provider           │ VARCHAR  │ "openai" │
│ model_name         │ VARCHAR  │ "gpt-4-turbo-preview" │
│ api_key_encrypted  │ VARCHAR  │ 密文   │
│ base_url           │ VARCHAR  │ nullable │
│ display_name       │ VARCHAR  │ "GPT-4 Turbo" │
│ is_active          │ BOOLEAN  │ default=true │
│ priority           │ INTEGER  │ default=100 │
│ description        │ VARCHAR  │ nullable │
│ created_at         │ TIMESTAMP│      │
│ updated_at         │ TIMESTAMP│      │
├─────────────────────┴──────────┴──────┤
│ 约束：UNIQUE(provider, model_name)    │
└─────────────────────────────────────┘

示例数据：
┌────┬──────────┬──────────────────────┬─────────────────────┬──────────────┐
│ id │ provider │ model_name          │ api_key_encrypted   │ display_name │
├────┼──────────┼──────────────────────┼─────────────────────┼──────────────┤
│ 1  │ openai   │ gpt-4-turbo-preview │ gAAAAABl...（密文） │ GPT-4 Turbo  │
│ 2  │ openai   │ gpt-3.5-turbo       │ gAAAAABl...（密文） │ GPT-3.5      │
│ 3  │anthropic │ claude-3-sonnet-... │ gAAAAABl...（密文） │ Claude 3     │
└────┴──────────┴──────────────────────┴─────────────────────┴──────────────┘
```

---

## 加密解密流程

```
┌────────────────────────────────────────────────────────┐
│               Encryption/Decryption Flow                │
└────────────────────────────────────────────────────────┘

初始化时：
  JWT_SECRET_KEY (来自 .env)
      ↓
  SHA256 哈希
      ↓
  32 字节密钥
      ↓
  Fernet 对象初始化
      ↓
  encryption_manager (全局单例)

创建配置时：
  明文 API Key (例如: "sk-proj-xxx")
      ↓
  config.set_api_key(plaintext)
      ↓
  encryption_manager.encrypt(plaintext)
      ↓
  Fernet 加密
      ↓
  Base64 编码
      ↓
  密文 (例如: "gAAAAABl5Kq...")
      ↓
  保存到数据库 llm_configs.api_key_encrypted

使用配置时：
  从数据库读取密文
      ↓
  config.get_api_key()
      ↓
  encryption_manager.decrypt(ciphertext)
      ↓
  Base64 解码
      ↓
  Fernet 解密
      ↓
  明文 API Key (恢复)
      ↓
  传给 LLM 客户端

关键点：
  ✅ 密钥来自 JWT_SECRET_KEY（服务器秘密）
  ✅ 加密后的数据即使被盗也无法解密（无密钥）
  ✅ 解密仅在内存中进行（创建 LLM 客户端时）
  ✅ API 响应中永不包含明文或密文
```

---

## 缓存策略

```
┌──────────────────────────────────────────┐
│      LLM Client Cache Flow                │
└──────────────────────────────────────────┘

应用启动：
  llm_client = LLMClient()
      ├─ 加载环境变量备份配置到 clients_cache
      ├─ _initialized = False
      └─ configs_cache = {}

第一次 invoke() 调用：
  ensure_initialized()
      ├─ 检查 _initialized
      ├─ 如果 False：
      │  ├─ 连接数据库
      │  ├─ 查询活跃配置
      │  ├─ 填充 configs_cache
      │  └─ _initialized = true
      └─ 返回

后续 invoke() 调用：
  ensure_initialized()  [跳过，已初始化]
      ↓
  get_client(provider, model)
      ├─ 组合缓存键: f"{provider}_{model}"
      ├─ 在 configs_cache 中查找
      ├─ 找到 → _build_client(config)
      ├─ 未找到 → 使用环境变量备份
      └─ 返回客户端

缓存更新：
  Admin 创建/编辑/删除配置
      ↓
  API 更新数据库
      ↓
  调用 llm_client.ensure_initialized()
      ├─ 强制从数据库重新加载
      └─ 更新缓存

性能优化：
  ✅ 第一次加载后，所有后续查询都在内存中
  ✅ 避免了每次调用都查数据库
  ✅ 配置更改时主动刷新缓存
```

---

## 权限控制流程

```
┌──────────────────────────────────────────┐
│          Permission Control Flow           │
└──────────────────────────────────────────┘

API 请求到达：
  GET /api/v1/llm-configs
      └─ 无需认证，直接返回

  GET /api/v1/llm-configs/admin
      ↓
      get_current_user(token)  [依赖]
      ├─ 验证 Bearer token
      ├─ 解码 JWT
      └─ 返回 User 对象
      ↓
      检查 user.role == UserRole.ADMIN
      ├─ True → 返回所有配置 + 解密后的 api_key
      └─ False → 403 Forbidden

  POST /api/v1/llm-configs
      ↓
      权限检查（同上）
      ↓
      验证请求数据 (LLMConfigCreate schema)
      ├─ provider 是否有效
      ├─ api_key 是否提供
      └─ model_name 是否唯一
      ↓
      创建配置

数据库中的权限：
  users 表
  ├─ id
  ├─ email
  ├─ username
  ├─ password_hash
  ├─ role: enum('user' | 'admin')  ← 关键
  └─ ...

检查逻辑：
  if current_user.role != UserRole.ADMIN:
      raise HTTPException(
          status_code=403,
          detail="Admin access required"
      )
```

---

## 部署架构

```
┌─────────────────────────────────────────────────────────┐
│                    生产环境部署                          │
└─────────────────────────────────────────────────────────┘

互联网
    ↓
┌─────────────────────────┐
│   Nginx / Reverse       │
│   Proxy                 │
│   (SSL/TLS)             │
└──────────┬──────────────┘
           ↓
    ┌──────┴──────┐
    ↓             ↓
┌─────────┐   ┌─────────┐
│Frontend │   │ Backend │
│Container│   │Container│
│(Next.js)│   │(FastAPI)│
│:3000   │   │:8000   │
└────┬────┘   └────┬────┘
     │            │
     │  Internal Network
     │            │
     │       ┌────┴────┐
     │       ↓         ↓
     │    ┌───────────────┐
     │    │  PostgreSQL   │
     │    │  Container    │
     │    │  :5432        │
     │    │               │
     │    │ ┌───────────┐ │
     │    │ │llm_configs│ │
     │    │ │(encrypted)│ │
     │    │ └───────────┘ │
     │    └───────────────┘
     │
  显示于浏览器
  - http://domain.com/copilot
  - http://domain.com/llm-config (admin)

环境变量注入：
  Backend Container:
  - DATABASE_URL=postgresql://...
  - JWT_SECRET_KEY=<secure-random>
  - OPENAI_API_KEY=<备份，可选>
  - ANTHROPIC_API_KEY=<备份，可选>
  
  Frontend Container:
  - NEXT_PUBLIC_API_URL=https://domain.com
  - NEXT_PUBLIC_WS_URL=wss://domain.com
```

---

## 错误处理流程

```
┌─────────────────────────────────────┐
│      Error Handling Flow              │
└─────────────────────────────────────┘

数据库错误：
  连接失败 → 降级到环境变量配置
  查询错误 → 返回 500 Internal Server Error

认证错误：
  缺少 token → 返回 401 Unauthorized
  token 无效 → 返回 401 Unauthorized
  权限不足 → 返回 403 Forbidden

验证错误：
  请求格式错误 → 返回 422 Unprocessable Entity
  缺少必填字段 → 返回 422 + 详细信息

加密错误：
  解密失败（密钥错误） → 日志警告 + 异常
  加密失败 → 返回 500

业务逻辑错误：
  重复配置 → 返回 400 Bad Request
  配置不存在 → 返回 404 Not Found

前端错误处理：
  API 请求失败 → 显示错误提示
  模型加载失败 → 显示备用 UI
  表单验证失败 → 显示字段错误
```

---

## 扩展点（Extensibility）

```
┌────────────────────────────────────────────────┐
│         How to Extend the System                │
└────────────────────────────────────────────────┘

添加新 Provider：

1. 后端代码修改：
   backend/app/services/llm_client.py
   
   def _build_client(self, config):
       ...
       elif config.provider.lower() == "new_provider":
           from langchain_new_provider import ChatNewProvider
           return ChatNewProvider(
               api_key=config.get_api_key(),
               model=config.model_name,
               base_url=config.base_url,
               **kwargs
           )

2. 创建配置：
   curl -X POST /api/v1/llm-configs \
     -d '{
       "provider": "new_provider",
       "model_name": "model-v1",
       "display_name": "New Model",
       "api_key": "key-xxx"
     }'

3. 前端无需修改
   （自动通过 API 获取）

添加新字段：

1. 数据库模型
   backend/app/models/llm_config.py
   
   new_field = Column(String, nullable=True)

2. Pydantic 模型
   backend/app/schemas/llm_config.py
   
   new_field: Optional[str] = None

3. 迁移脚本（如果用 Alembic）
   alembic revision --autogenerate

4. 前端自动支持

添加新 API 端点：

1. backend/app/api/v1/llm_config.py
   
   @router.custom_endpoint("/endpoint")
   async def custom_endpoint(...):
       ...

2. 前端 llm-config-client.ts
   
   export async function customEndpoint() {
       const response = await axios.get("/endpoint");
       return response.data;
   }

3. 在组件中使用
   const data = await customEndpoint();
```

---

这个架构图展现了整个系统从前端到后端再到数据库的完整数据流，以及各个层次之间的交互方式。
