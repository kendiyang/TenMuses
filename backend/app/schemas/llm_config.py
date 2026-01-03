"""Pydantic schemas for LLM configuration."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class LLMConfigBase(BaseModel):
    """Base schema for LLM configuration."""
    provider: str = Field(..., description="Provider: openai, anthropic, etc.")
    model_name: str = Field(..., description="Model name: gpt-4-turbo-preview, claude-3-sonnet-20240229")
    display_name: str = Field(..., description="Display name for UI")
    base_url: Optional[str] = Field(None, description="Optional custom base URL")
    is_active: bool = Field(default=True)
    priority: int = Field(default=100)
    description: Optional[str] = Field(None)

class LLMConfigCreate(LLMConfigBase):
    """Schema for creating LLM configuration."""
    api_key: str = Field(..., description="API key (will be encrypted)")

class LLMConfigUpdate(BaseModel):
    """Schema for updating LLM configuration."""
    model_name: Optional[str] = None
    display_name: Optional[str] = None
    api_key: Optional[str] = None  # If provided, will be re-encrypted
    base_url: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    description: Optional[str] = None

class LLMConfigResponse(LLMConfigBase):
    """Schema for LLM configuration response (no API key)."""
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class LLMConfigDetailResponse(LLMConfigResponse):
    """Detailed response including decrypted API key (admin only)."""
    api_key: Optional[str] = Field(None, description="Decrypted API key - only included when requested by admin")
    
    class Config:
        from_attributes = True

class LLMConfigListResponse(BaseModel):
    """Response with list of active LLM configs for client selection."""
    id: str
    provider: str
    model_name: str
    display_name: str
    priority: int
    
    class Config:
        from_attributes = True
