"""
Example: Using LLMClient with database-driven configuration

This demonstrates how to use the new unified LLMClient architecture
to access LLM models with configuration stored in database.

New Architecture Benefits:
- Unified interface for OpenAI and Anthropic
- Automatic credential loading from database
- Support for model_id to fetch config from database
- Proper async handling with asyncio.to_thread for sync operations
- LangChain integration for embeddings and other tools
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.llm_client import llm_client
from langchain_core.messages import HumanMessage, SystemMessage


class LLMClientWithDatabaseConfig:
    """
    Example: Using LLMClient with database configuration.
    
    The new LLMClient architecture automatically handles:
    1. Reading provider and model from database
    2. Fetching credentials from environment or database
    3. Creating appropriate client (OpenAI/Anthropic)
    4. Handling async operations safely
    """
    
    def __init__(self, db_session: AsyncSession):
        """Initialize with database session (if needed for advanced config)."""
        self.db_session = db_session
    
    async def invoke_by_model_id(self, model_id: str, messages: list):
        """
        Invoke LLM using a model_id from database.
        
        Args:
            model_id: UUID of model stored in database
            messages: List of message dicts with 'role' and 'content'
        """
        # LLMClient automatically loads provider and model from database
        response = await llm_client.invoke(
            messages=messages,
            model_id=model_id,
            temperature=0.7,
            max_tokens=1000,
        )
        return response
    
    async def invoke_by_provider(
        self,
        provider: str,
        model: str,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ):
        """
        Invoke LLM using provider and model name.
        
        Args:
            provider: "openai" or "anthropic"
            model: Model name (e.g., "gpt-4-turbo-preview", "claude-3-sonnet-20240229")
            messages: List of message dicts with 'role' and 'content'
            temperature: LLM temperature
            max_tokens: Maximum tokens to generate
        """
        response = await llm_client.invoke(
            messages=messages,
            provider=provider,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response
    
    async def stream_by_model_id(self, model_id: str, messages: list):
        """
        Stream response using model_id from database.
        
        Usage:
            async for token in await llm_client.stream(...):
                yield token  # Update UI incrementally
        """
        # Note: stream() returns a sync iterator, use asyncio.to_thread if needed
        stream_result = await llm_client.stream(
            messages=messages,
            model_id=model_id,
            temperature=0.7,
            max_tokens=1000,
        )
        return stream_result
    
    async def get_embeddings(
        self,
        text: str,
        provider: str = "openai",
        model: str = "text-embedding-3-small",
        model_id: Optional[str] = None,
    ):
        """
        Get embeddings for text using LLMClient infrastructure.
        
        Args:
            text: Text to embed
            provider: "openai" or "anthropic"
            model: Embedding model name
            model_id: Optional database model ID
        """
        from app.services.embedding_service import EmbeddingService
        
        service = EmbeddingService(
            provider=provider,
            model=model,
            model_id=model_id,
        )
        
        embedding = await service.embed_text(text)
        return embedding


# ============================================================================
# Usage Examples in FastAPI Routes
# ============================================================================

"""
Example 1: Simple Chat using model_id from database
-----------------------------------------------------

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from langchain_core.messages import HumanMessage

router = APIRouter()

@router.post("/api/chat")
async def chat_with_database_model(
    request: Request,
    message: str,
    model_id: str,  # UUID from database
    db: AsyncSession = Depends(get_db)
):
    client = LLMClientWithDatabaseConfig(db)
    
    # LLMClient automatically loads provider/model from database
    response = await client.invoke_by_model_id(
        model_id=model_id,
        messages=[HumanMessage(content=message)]
    )
    
    return {"response": response.content}


Example 2: Chat using provider and model name
----------------------------------------------

@router.post("/api/chat/openai")
async def chat_with_openai(
    message: str,
    db: AsyncSession = Depends(get_db)
):
    client = LLMClientWithDatabaseConfig(db)
    
    response = await client.invoke_by_provider(
        provider="openai",
        model="gpt-4-turbo-preview",
        messages=[HumanMessage(content=message)]
    )
    
    return {"response": response.content}


Example 3: Streaming response
------------------------------

from fastapi.responses import StreamingResponse
import asyncio

@router.get("/api/chat/stream")
async def chat_stream(
    message: str,
    model_id: str,
    db: AsyncSession = Depends(get_db)
):
    client = LLMClientWithDatabaseConfig(db)
    
    async def generate():
        stream = await client.stream_by_model_id(
            model_id=model_id,
            messages=[HumanMessage(content=message)]
        )
        
        # stream returns a sync iterator, wrap with asyncio.to_thread if needed
        for token in stream:
            yield f"data: {token}\\n\\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


Example 4: Get embeddings
---------------------------

@router.post("/api/embed")
async def get_embeddings(
    text: str,
    model_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    client = LLMClientWithDatabaseConfig(db)
    
    embeddings = await client.get_embeddings(
        text=text,
        model_id=model_id  # Optional: load from database
    )
    
    return {"embeddings": embeddings}
"""

# ============================================================================
# Migration Guide: From Old to New Architecture
# ============================================================================

"""
OLD PATTERN (DO NOT USE):
------------------------

# ❌ DANGEROUS: Hardcoded API key and direct imports
# from openai import AsyncOpenAI
# from anthropic import AsyncAnthropic
# client = AsyncOpenAI(api_key="sk-...")
# response = await client.chat.completions.create(...)


NEW PATTERN (USE THIS):
----------------------

from app.services.llm_client import llm_client

# ✅ SAFE: Credentials from environment/database
response = await llm_client.invoke(
    messages=[HumanMessage(content="...")],
    provider="openai",
    model="gpt-4-turbo-preview"
)

# Or load from database:
response = await llm_client.invoke(
    messages=[...],
    model_id="<uuid-from-database>"
)


Key Differences:
1. llm_client handles provider initialization
2. No hardcoded credentials
3. Unified interface for both providers
4. LangChain integration built-in
5. Automatic error handling and retries
"""

