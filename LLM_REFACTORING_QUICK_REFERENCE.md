# LLM Refactoring - Developer Quick Reference

## 🎯 Quick Summary
The LLM configuration system was refactored from a single table (`llm_configs`) to a proper relational design:
- **llm_providers** table: Stores API keys and base URLs (one per supplier)
- **llm_models** table: Stores model configurations linked to providers

✅ **Status**: Complete, all tests passing, backward compatible

---

## 📖 How to Use the New LLMClient

### Option 1: NEW WAY - By Model ID (Recommended)
```python
from app.services.llm_client import llm_client

# Get a model ID from the database
model_id = "uuid-xxx"  # Get from UI or API

messages = [HumanMessage(content="Hello")]
response = await llm_client.invoke(
    messages,
    model_id=model_id,  # NEW: Use model UUID
    temperature=0.7
)
```

### Option 2: LEGACY WAY - By Provider + Model Name (Still Works)
```python
from app.services.llm_client import llm_client

messages = [HumanMessage(content="Hello")]
response = await llm_client.invoke(
    messages,
    provider="openai",           # OLD: Use provider name
    model="gpt-4-turbo-preview",  # OLD: Use model name
    temperature=0.7
)
```

Both ways work. The second is backward compatible with existing code.

---

## 📊 Database Schema

### llm_providers Table
Stores supplier-level configuration (no model-specific data)
```sql
SELECT * FROM llm_providers;

id | name       | display_name | api_key_encrypted | base_url | is_active | priority
---|------------|--------------|------------------|----------|-----------|----------
.. | openai     | GPT          | [encrypted]      | NULL     | true      | 1
.. | anthropic  | Anthropic    | [encrypted]      | NULL     | true      | 2
```

**Key Columns**:
- `id`: UUID primary key
- `name`: Unique identifier ("openai", "anthropic")
- `api_key_encrypted`: API key stored securely
- `base_url`: Optional custom endpoint
- `is_active`: Boolean flag
- `priority`: Ordering preference

### llm_models Table
Stores individual model configurations
```sql
SELECT 
  m.id, m.model_name, m.display_name, 
  p.name as provider, m.context_window,
  m.supports_streaming, m.supports_function_calling
FROM llm_models m
JOIN llm_providers p ON m.provider_id = p.id;

id | model_name              | display_name  | provider  | context_window | streaming | functions
...|gpt-4-turbo-preview      | GPT-4 Turbo   | openai    | 128000         | true      | true
...|claude-3-sonnet-20240229 | Claude 3      | anthropic | 200000         | true      | false
```

**Key Columns**:
- `id`: UUID primary key
- `provider_id`: Foreign key to llm_providers
- `model_name`: Model identifier
- `model_family`: Family classification
- `context_window`: Max tokens
- `supports_*`: Capability flags
- `cost_per_1k_*_tokens`: Pricing info
- `default_temperature`, `default_max_tokens`: Defaults

---

## 🔧 Adding New Models/Providers

### Add New Provider
```sql
INSERT INTO llm_providers (id, name, display_name, api_key_encrypted, is_active, priority)
VALUES (gen_random_uuid(), 'claude', 'Anthropic Claude', pgp_sym_encrypt('sk-...', 'secret'), true, 10);
```

### Add New Model to Existing Provider
```sql
INSERT INTO llm_models (
  id, provider_id, model_name, display_name, model_family,
  context_window, supports_streaming, supports_function_calling
)
VALUES (
  gen_random_uuid(),
  (SELECT id FROM llm_providers WHERE name = 'openai'),
  'gpt-4o',
  'GPT-4o',
  'gpt-4',
  128000,
  true,
  true
);
```

✅ No code changes needed - system auto-discovers new models!

---

## 🔍 Querying Available Models

### Via API
```bash
curl -X GET "http://localhost:8000/api/v1/config/llm/available-models" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
{
  "models": [
    {
      "id": "uuid-xxx",
      "model_name": "gpt-4-turbo-preview",
      "display_name": "GPT-4 Turbo",
      "provider_name": "openai",
      "context_window": 128000,
      "supports_streaming": true,
      "supports_function_calling": true,
      "cost_per_1k_input_tokens": 0.01
    },
    ...
  ],
  "count": 5
}
```

### Via Python
```python
from app.services.llm_client import llm_client

models = await llm_client.get_available_models()
for model in models:
    print(f"{model.display_name} ({model.model_name}) - {model.provider.display_name}")
```

---

## 🚀 In Workflow Nodes

Workflows still use inline configuration (backward compatible):
```python
@dataclass
class Node:
    id: str
    type: str
    data: LLMNodeConfig  # Note: Renamed from LLMConfig
    
class LLMNodeConfig(BaseModel):
    provider: Literal["openai", "anthropic"] = "openai"
    model: str = "gpt-4-turbo-preview"
    temperature: float = 0.7
```

When executing nodes, the system resolves provider/model to an LLM client:
```python
client = await llm_client.get_client(provider="openai", model="gpt-4-turbo-preview")
response = await llm_client.invoke(messages, provider=..., model=...)
```

---

## 📋 Files Changed

| File | Status | Change |
|------|--------|--------|
| llm_provider.py | NEW ✅ | Provider model definition |
| llm_model.py | NEW ✅ | Model configuration table |
| llm_client.py | REPLACED ✅ | New dual-API implementation |
| llm_client_old.py | BACKUP ✅ | Original version preserved |
| schemas/node.py | MODIFIED ✅ | Renamed LLMConfig → LLMNodeConfig |
| executor_library.py | MODIFIED ✅ | Updated invoke() calls |
| dynamic_graph_factory.py | MODIFIED ✅ | Updated invoke() calls |
| api/v1/config.py | MODIFIED ✅ | Added /available-models endpoint |

---

## 🧪 Testing

Run LLM-specific tests:
```bash
cd backend
python -m pytest tests/test_phase2_comprehensive.py -v  # 21/21 passed ✅
python -m pytest tests/test_langgraph_service.py -v     # 8/8 passed ✅
python -m pytest tests/test_copilot_service.py -v       # 22/22 passed ✅
```

---

## ⚠️ Migration Notes

### What Happened
1. Old `llm_configs` table was read
2. New `llm_providers` and `llm_models` tables were created
3. Data was migrated: 5 configs → 2 providers + 5 models
4. Old table was **NOT deleted** (safe rollback possible)

### Rollback (If Needed)
```sql
-- The old llm_configs table still exists with all original data
-- Just revert the code to use old LLMClient
-- No data recovery needed
```

---

## 🔐 API Key Security

API keys are:
- ✅ Encrypted at rest in database (using encryption_manager)
- ✅ Never logged or exposed in responses
- ✅ Only decrypted when needed to create LLM clients
- ✅ Cached in memory for performance (with TTL refresh)

---

## 💡 Key Improvements

| Aspect | Before | After |
|--------|--------|-------|
| **Credential Duplication** | API key duplicated per model | Stored once per provider ✅ |
| **Model Discovery** | Hardcoded in code | Dynamic from database ✅ |
| **Model Metadata** | Limited fields | Rich metadata (streaming, vision, costs) ✅ |
| **API Design** | Single provider endpoint | Multiple suppliers supported ✅ |
| **Scalability** | Add model = update code | Add model = insert row ✅ |
| **Type Safety** | Loose typing | Full SQLAlchemy + Pydantic ✅ |

---

## ❓ FAQ

**Q: Do I need to update my code?**
A: No! Old code still works. `llm_client.invoke(messages, provider=..., model=...)` works unchanged.

**Q: How do I use the new model_id API?**
A: Get the model ID from the database or the `/available-models` API, then call `llm_client.invoke(messages, model_id=...)`.

**Q: What if my API key stops working?**
A: Update the `api_key_encrypted` field in the `llm_providers` table. No code changes needed.

**Q: Can I rollback the migration?**
A: Yes! The old `llm_configs` table still exists with all original data. Just revert the code to the old LLMClient.

**Q: How do I add a new model?**
A: Add a row to `llm_models` table with foreign key to the provider. No code changes needed.

**Q: Does this break existing workflows?**
A: No! Workflows still use inline provider/model configuration. The new architecture is transparent to workflows.

---

## 📞 Support

For issues or questions about the refactoring:
1. Check the migration execution logs: `PHASE_2_5_LLM_REFACTORING_COMPLETE.md`
2. Run validation tests: `pytest tests/test_phase2_comprehensive.py -v`
3. Review the code: `backend/app/services/llm_client.py`
4. Check database: `SELECT * FROM llm_providers; SELECT * FROM llm_models;`

---

**Status**: ✅ Production Ready
**Last Updated**: 2024-01-01
**Backward Compatible**: Yes ✅

