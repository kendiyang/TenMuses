"""LLM Provider (供应商) database model."""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base
from app.core.encryption import encryption_manager


class LLMProvider(Base):
    """
    LLM供应商配置表 - 存储供应商级别的配置信息
    
    每个供应商（如OpenAI、Anthropic）对应一条记录，
    包含该供应商的API密钥和base_url等配置。
    一个供应商可以有多个模型。
    """
    __tablename__ = "llm_providers"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 供应商标识: "openai", "anthropic", "azure", "custom" 等
    name = Column(String(100), unique=True, nullable=False, index=True)
    
    # 显示名称
    display_name = Column(String(200), nullable=False)
    
    # 加密的API密钥
    api_key_encrypted = Column(Text, nullable=False)
    
    # 自定义base URL（可选，用于代理、本地服务器等）
    base_url = Column(String(500), nullable=True)
    
    # SSL验证配置（true=验证，false=禁用验证，用于自签名证书的代理）
    verify_ssl = Column(Boolean, default=True, nullable=False)
    
    # 是否激活
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # 优先级（用于排序，数值越小优先级越高）
    priority = Column(Integer, default=100, nullable=False)
    
    # 描述信息
    description = Column(Text, nullable=True)
    
    # 供应商图标URL（可选）
    icon_url = Column(String(500), nullable=True)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系：一个供应商有多个模型
    models = relationship(
        "LLMModel",
        back_populates="provider",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    
    def set_api_key(self, plaintext_key: str) -> None:
        """加密并存储API密钥"""
        self.api_key_encrypted = encryption_manager.encrypt(plaintext_key)
    
    def get_api_key(self) -> str:
        """解密并返回API密钥"""
        return encryption_manager.decrypt(self.api_key_encrypted)
    
    def to_dict(self, include_api_key: bool = False) -> dict:
        """
        转换为字典
        
        Args:
            include_api_key: 是否包含解密后的API密钥（敏感信息，默认不包含）
        
        Returns:
            字典表示
        """
        data = {
            "id": str(self.id),
            "name": self.name,
            "display_name": self.display_name,
            "base_url": self.base_url,
            "verify_ssl": self.verify_ssl,
            "is_active": self.is_active,
            "priority": self.priority,
            "description": self.description,
            "icon_url": self.icon_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "models_count": len(self.models) if self.models else 0,
        }
        
        if include_api_key:
            data["api_key"] = self.get_api_key()
        
        return data
    
    def __repr__(self):
        return f"<LLMProvider(name='{self.name}', display_name='{self.display_name}', is_active={self.is_active})>"
