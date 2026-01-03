# LLM Configuration Management

## Overview

This system allows administrators to manage multiple LLM provider configurations (OpenAI, Anthropic, etc.) through a database-driven approach with encrypted API key storage. Users can then select which model to use through the UI.

## Features

- ✅ **Encrypted API Key Storage**: Uses Fernet (symmetric encryption) to safely store API keys
- ✅ **Multiple Provider Support**: OpenAI, Anthropic, and extensible for others
- ✅ **Custom Base URLs**: Support for proxy/custom endpoints (e.g., for local LLM servers)
- ✅ **Model Selection UI**: Frontend component for users to choose models
- ✅ **Admin Management Panel**: Full CRUD operations for managing configurations
- ✅ **Database-Driven**: All configs stored in PostgreSQL, survives restarts
- ✅ **Fallback to Environment Variables**: If database is unavailable, falls back to env vars

## Architecture

### Backend

#### Encryption (`backend/app/core/encryption.py`)
- Implements Fernet symmetric encryption using JWT_SECRET_KEY
- `encrypt(plaintext)` → encrypted string suitable for DB storage
- `decrypt(ciphertext)` → plaintext API key

#### Database Model (`backend/app/models/llm_config.py`)
- `LLMConfig` SQLAlchemy model with fields:
  - `provider`: "openai", "anthropic", etc.
  - `model_name`: "gpt-4-turbo-preview", "claude-3-sonnet-20240229"
  - `api_key_encrypted`: Encrypted API key (stored in DB)
  - `base_url`: Optional custom endpoint
  - `display_name`: UI-friendly name
  - `is_active`: Enable/disable without deletion
  - `priority`: Sort order for UI listing
  - Methods: `set_api_key()`, `get_api_key()`, `to_dict()`

#### Pydantic Schemas (`backend/app/schemas/llm_config.py`)
- `LLMConfigCreate`: For creation (includes plaintext api_key)
- `LLMConfigUpdate`: For updates (optional fields)
- `LLMConfigResponse`: For API responses (no api_key)
- `LLMConfigDetailResponse`: Admin responses (includes decrypted api_key)
- `LLMConfigListResponse`: For client model picker (minimal info)

#### LLM Client Service (`backend/app/services/llm_client.py`)
- Enhanced to load configs from database on startup
- Caches configs in memory for performance
- Fallback to environment variables if DB unavailable
- Methods:
  - `ensure_initialized()`: Load configs from DB
  - `get_client(provider, model)`: Get configured LLM client
  - `invoke()`: Call LLM
  - `stream()`: Stream LLM responses
  - `get_available_configs()`: Get list of active configs

#### API Routes (`backend/app/api/v1/llm_config.py`)
- `GET /api/v1/llm-configs`: Public endpoint - list active configs for UI picker
- `GET /api/v1/llm-configs/admin`: Admin only - all configs with decrypted keys
- `POST /api/v1/llm-configs`: Admin only - create new config
- `PUT /api/v1/llm-configs/{config_id}`: Admin only - update config
- `DELETE /api/v1/llm-configs/{config_id}`: Admin only - delete config

### Frontend

#### LLM Config Client (`frontend/src/services/llm-config-client.ts`)
- Service functions for API communication
- `getAvailableLLMConfigs()`: Fetch active models for user
- `getAllLLMConfigs()`: Fetch all configs (admin)
- `createLLMConfig()`, `updateLLMConfig()`, `deleteLLMConfig()`

#### Model Selector Component (`frontend/src/components/ModelSelector.tsx`)
- React component for model selection
- Loads available configs on mount
- Props: `selectedModelId`, `onModelSelect`, `showLabel`, `className`
- Auto-selects first model if none provided

#### LLM Config Management Page (`frontend/src/app/llm-config/page.tsx`)
- Admin panel for managing LLM configurations
- Create, read, update, delete operations
- Form for entering provider, model name, API key, base URL
- Visual indicators for active/inactive configs

#### Copilot Demo Page (`frontend/src/app/copilot/page.tsx`)
- Example page demonstrating model selection
- Chat interface with message history
- Shows selected model info

## Usage

### 1. Initial Setup (Backend)

The system is backward compatible with environment variables:

```bash
# .env (optional - used as fallback)
OPENAI_API_KEY=sk-xxx
ANTHROPIC_API_KEY=sk-ant-xxx
JWT_SECRET_KEY=your-secret-key  # Used for encrypting API keys
```

### 2. Create First Config via API

```bash
# Create OpenAI config
curl -X POST http://localhost:8000/api/v1/llm-configs \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_token>" \
  -d '{
    "provider": "openai",
    "model_name": "gpt-4-turbo-preview",
    "display_name": "GPT-4 Turbo",
    "api_key": "sk-...",
    "base_url": null,
    "priority": 1,
    "description": "Production GPT-4 Turbo"
  }'
```

### 3. Access Admin Panel

Navigate to `/llm-config` (admin-only page) to:
- View all configurations
- Create new ones
- Edit existing configs
- Delete configs (with confirmation)

### 4. Use in Frontend

```typescript
import { ModelSelector } from '@/components/ModelSelector';

function MyComponent() {
  const [selectedModel, setSelectedModel] = useState<LLMConfig | null>(null);

  return (
    <div>
      <ModelSelector
        selectedModelId={selectedModel?.id}
        onModelSelect={(id, model) => setSelectedModel(model)}
      />
      {selectedModel && <p>Using: {selectedModel.display_name}</p>}
    </div>
  );
}
```

### 5. Use in Backend

```python
from app.services.llm_client import llm_client

# Get available configs
configs = await llm_client.get_available_configs()

# Use a specific config
messages = [HumanMessage(content="Hello")]
response = await llm_client.invoke(
    messages,
    provider="openai",
    model="gpt-4-turbo-preview"
)

# Stream response
async for token in llm_client.stream(messages, provider="openai"):
    print(token, end='', flush=True)
```

## Security Considerations

1. **API Key Encryption**: All API keys are encrypted using Fernet before storage
2. **Admin-Only Access**: Configuration management requires admin role
3. **JWT Secret**: Encryption key is derived from `JWT_SECRET_KEY`
4. **Never Log API Keys**: Encrypted keys are safe to log, plaintext keys are only in memory
5. **HTTPS in Production**: Always use HTTPS in production to prevent token interception

## Database Schema

```sql
CREATE TABLE llm_configs (
  id UUID PRIMARY KEY,
  provider VARCHAR NOT NULL,
  model_name VARCHAR NOT NULL,
  api_key_encrypted VARCHAR NOT NULL,
  base_url VARCHAR,
  display_name VARCHAR NOT NULL,
  is_active BOOLEAN DEFAULT TRUE,
  priority INTEGER DEFAULT 100,
  description VARCHAR,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(provider, model_name)
);

-- Created automatically by SQLAlchemy on startup
```

## Adding New Providers

1. Update `backend/app/models/llm_config.py`:
   - Add provider name to validation

2. Update `backend/app/services/llm_client.py`:
   - Add new provider case in `_build_client()` method
   - Import necessary LangChain integration

3. Update frontend schema:
   - Add provider option in `LLMConfigCreate` form

Example:
```python
# In llm_client.py
elif config.provider.lower() == "new_provider":
    from langchain_new_provider import ChatNewProvider
    return ChatNewProvider(
        api_key=api_key,
        model=config.model_name,
        **kwargs
    )
```

## Troubleshooting

### "API key not configured" Error
- Ensure a config exists in database with `is_active=true`
- Or set env vars: `OPENAI_API_KEY=...`

### Config changes not reflected
- LLM client caches configs on first initialization
- Restart backend after making DB changes
- Or call `llm_client.ensure_initialized()` to reload

### Encryption errors
- Ensure `JWT_SECRET_KEY` is consistent across restarts
- Changing JWT_SECRET_KEY will invalidate existing encrypted keys
- Back up database before changing secret

## API Response Examples

### Get Available Configs
```json
GET /api/v1/llm-configs

[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "provider": "openai",
    "model_name": "gpt-4-turbo-preview",
    "display_name": "GPT-4 Turbo",
    "priority": 1
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "provider": "anthropic",
    "model_name": "claude-3-sonnet-20240229",
    "display_name": "Claude 3 Sonnet",
    "priority": 2
  }
]
```

### Get All Configs (Admin)
```json
GET /api/v1/llm-configs/admin
Authorization: Bearer <admin_token>

[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "provider": "openai",
    "model_name": "gpt-4-turbo-preview",
    "display_name": "GPT-4 Turbo",
    "base_url": null,
    "is_active": true,
    "priority": 1,
    "description": "Production model",
    "api_key": "sk-...",
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-01-01T00:00:00"
  }
]
```

## Files Modified/Created

### Backend
- ✅ `backend/app/core/encryption.py` - NEW: Encryption utilities
- ✅ `backend/app/core/config.py` - MODIFIED: Added `OPENAI_BASE_URL`, `ANTHROPIC_BASE_URL`
- ✅ `backend/app/models/llm_config.py` - NEW: LLMConfig model
- ✅ `backend/app/schemas/llm_config.py` - NEW: Pydantic schemas
- ✅ `backend/app/services/llm_client.py` - MODIFIED: Database-driven config loading
- ✅ `backend/app/api/v1/llm_config.py` - NEW: API routes
- ✅ `backend/app/main.py` - MODIFIED: Added llm_config router

### Frontend
- ✅ `frontend/src/services/llm-config-client.ts` - NEW: API client service
- ✅ `frontend/src/components/ModelSelector.tsx` - NEW: Model selection component
- ✅ `frontend/src/app/llm-config/page.tsx` - NEW: Admin management page
- ✅ `frontend/src/app/copilot/page.tsx` - NEW: Demo Copilot page with model selection
