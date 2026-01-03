"""LLM Configuration database model."""
from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from app.core.database import Base
from app.core.encryption import encryption_manager

class LLMConfig(Base):
    """
    Stores LLM provider configurations.
    API keys are encrypted at rest.
    """
    __tablename__ = "llm_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Provider: "openai", "anthropic", etc.
    provider = Column(String, nullable=False, index=True)
    
    # Model name: "gpt-4-turbo-preview", "claude-3-sonnet-20240229", etc.
    model_name = Column(String, nullable=False)
    
    # Encrypted API key - stored as encrypted string
    api_key_encrypted = Column(String, nullable=False)
    
    # Optional custom base URL (e.g., for proxies, local servers)
    base_url = Column(String, nullable=True)
    
    # Display name for UI
    display_name = Column(String, nullable=False)
    
    # Whether this config is active/available for use
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Priority/order for display (lower = higher priority)
    priority = Column(Integer, default=100, nullable=False)
    
    # Metadata/description
    description = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def set_api_key(self, plaintext_key: str) -> None:
        """Encrypt and store API key."""
        self.api_key_encrypted = encryption_manager.encrypt(plaintext_key)
    
    def get_api_key(self) -> str:
        """Decrypt and retrieve API key."""
        return encryption_manager.decrypt(self.api_key_encrypted)
    
    def to_dict(self, include_api_key: bool = False) -> dict:
        """Convert to dict, optionally including decrypted API key."""
        data = {
            "id": str(self.id),
            "provider": self.provider,
            "model_name": self.model_name,
            "display_name": self.display_name,
            "base_url": self.base_url,
            "is_active": self.is_active,
            "priority": self.priority,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_api_key:
            data["api_key"] = self.get_api_key()
        return data
