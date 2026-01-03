# LLM 数据库配置修改完成

## 修改内容

已将 `llm_client.py` 修改为**仅使用数据库配置**，完全移除了环境变量回退逻辑。

### 主要变更

#### 1. 移除环境变量相关代码
- ❌ 删除 `_init_fallback_clients()` 方法
- ❌ 删除 `self.fallback_clients` 字典
- ❌ 移除所有从 `settings` 读取环境变量的逻辑

#### 2. 增强错误提示
当 LLM 配置未找到时，现在会返回清晰的错误信息：

```
❌ LLM 配置错误: 未找到 provider='openai', model='gpt-4o' 的配置。
请在数据库中配置 LLM 供应商和模型:
  1. 访问 /api/v1/llm-provider-model/providers 查看供应商
  2. 访问 /api/v1/llm-provider-model/models 查看模型
  3. 确保供应商有有效的 API Key
  4. 确保模型和供应商都是 active 状态
```

#### 3. Copilot 错误处理改进
在 `copilot_local_service.py` 中添加了 `ValueError` 异常捕获，当 LLM 配置错误时：

```python
except ValueError as e:
    # LLM 配置错误
    return (
        "❌ Copilot 当前无法使用，LLM 配置未正确设置。\n\n"
        f"错误详情:\n{error_msg}\n\n"
        "请联系管理员配置 LLM 供应商和模型。"
    )
```

## 如何配置 LLM

### 方法 1: 使用 API 接口

```bash
# 1. 创建供应商（需要 API key）
curl -X POST "http://localhost:8000/api/v1/llm-provider-model/providers" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "openai",
    "display_name": "OpenAI",
    "api_key": "sk-your-api-key-here",
    "is_active": true
  }'

# 2. 创建模型
curl -X POST "http://localhost:8000/api/v1/llm-provider-model/models" \
  -H "Content-Type: application/json" \
  -d '{
    "provider_id": "provider-uuid-from-step-1",
    "model_name": "gpt-4o",
    "display_name": "GPT-4o",
    "is_active": true
  }'
```

### 方法 2: 使用初始化脚本

项目中应该有类似 `init_db_providers_models.py` 的脚本：

```bash
cd backend
python init_db_providers_models.py
```

### 方法 3: 直接操作数据库

```sql
-- 插入 OpenAI provider
INSERT INTO llm_providers (id, name, display_name, api_key_encrypted, is_active)
VALUES (
  gen_random_uuid(),
  'openai',
  'OpenAI',
  'sk-your-api-key-here',  -- 注意：生产环境应加密
  true
);

-- 插入 GPT-4o 模型
INSERT INTO llm_models (
  id, provider_id, model_name, display_name, is_active
)
VALUES (
  gen_random_uuid(),
  (SELECT id FROM llm_providers WHERE name = 'openai'),
  'gpt-4o',
  'GPT-4o',
  true
);
```

## 验证配置

### 检查数据库配置

```bash
cd backend
python -c "
import asyncio
from app.services.llm_client import llm_client

async def check():
    models = await llm_client.get_available_models()
    print(f'可用模型数: {len(models)}')
    for m in models:
        print(f'  - {m[\"display_name\"]} ({m[\"model_name\"]})')

asyncio.run(check())
"
```

### 测试 Copilot

1. 访问前端工作流页面
2. 打开 Copilot 面板
3. 发送消息

**预期行为:**
- ✅ 如果配置正确：返回 LLM 生成的响应
- ❌ 如果配置缺失：返回清晰的错误提示（而不是静默失败）

## 配置状态检查

运行以下命令检查当前配置：

```bash
curl http://localhost:8000/api/v1/llm-provider-model/providers
curl http://localhost:8000/api/v1/llm-provider-model/models
```

## 注意事项

1. **必须配置数据库**: 现在没有环境变量回退，必须在数据库中配置
2. **API Key 必填**: 供应商的 API key 不能为空
3. **Active 状态**: 供应商和模型都必须是 `is_active = true`
4. **清晰错误**: 配置错误时会有详细的错误信息指导修复

---

**修改时间**: 2026-01-02  
**影响范围**: 所有使用 `llm_client` 的功能（Copilot、工作流运行等）
