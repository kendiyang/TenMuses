"""LLM Model (模型) database model."""
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Float, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from app.core.database import Base


class LLMModel(Base):
    """
    LLM模型配置表 - 存储具体的模型信息
    
    每个模型（如gpt-4-turbo-preview、claude-3-sonnet等）对应一条记录。
    模型通过外键关联到供应商表，继承供应商的API密钥和base_url。
    """
    __tablename__ = "llm_models"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 关联的供应商ID（外键）
    provider_id = Column(
        UUID(as_uuid=True),
        ForeignKey("llm_providers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # 模型名称: "gpt-4-turbo-preview", "claude-3-sonnet-20240229" 等
    model_name = Column(String(200), nullable=False)
    
    # 显示名称
    display_name = Column(String(300), nullable=False)
    
    # 模型类型/系列: "gpt-4", "gpt-3.5", "claude-3", "claude-2" 等
    model_family = Column(String(100), nullable=True, index=True)
    
    # 模型版本
    version = Column(String(100), nullable=True)
    
    # 默认参数
    default_temperature = Column(Float, default=0.7, nullable=False)
    default_max_tokens = Column(Integer, nullable=True)
    default_top_p = Column(Float, default=1.0, nullable=True)
    
    # 上下文窗口大小
    context_window = Column(Integer, nullable=True, comment="上下文窗口token数")
    
    # 支持的功能标志
    supports_streaming = Column(Boolean, default=True, nullable=False)
    supports_function_calling = Column(Boolean, default=False, nullable=False)
    supports_vision = Column(Boolean, default=False, nullable=False)
    supports_json_mode = Column(Boolean, default=False, nullable=False)
    
    # 成本信息（每1000 tokens的价格，美元）
    cost_per_1k_input_tokens = Column(Float, nullable=True, comment="输入token价格（美元/1k）")
    cost_per_1k_output_tokens = Column(Float, nullable=True, comment="输出token价格（美元/1k）")
    
    # 是否激活
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    # 优先级（用于排序，数值越小优先级越高）
    priority = Column(Integer, default=100, nullable=False)
    
    # 描述信息
    description = Column(Text, nullable=True)
    
    # 使用说明
    usage_notes = Column(Text, nullable=True)
    
    # 标签（用于分类和搜索）
    tags = Column(String(500), nullable=True, comment="逗号分隔的标签")
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # 关系：多个模型对应一个供应商
    provider = relationship("LLMProvider", back_populates="models")
    
    # 复合唯一索引：同一供应商下的模型名称必须唯一
    __table_args__ = (
        Index("idx_provider_model_unique", "provider_id", "model_name", unique=True),
        Index("idx_model_active", "is_active"),
        Index("idx_model_family", "model_family"),
    )
    
    def to_dict(self, include_provider: bool = False) -> dict:
        """
        转换为字典
        
        Args:
            include_provider: 是否包含完整的供应商信息
        
        Returns:
            字典表示
        """
        data = {
            "id": str(self.id),
            "provider_id": str(self.provider_id),
            "model_name": self.model_name,
            "display_name": self.display_name,
            "model_family": self.model_family,
            "version": self.version,
            "default_temperature": self.default_temperature,
            "default_max_tokens": self.default_max_tokens,
            "default_top_p": self.default_top_p,
            "context_window": self.context_window,
            "supports_streaming": self.supports_streaming,
            "supports_function_calling": self.supports_function_calling,
            "supports_vision": self.supports_vision,
            "supports_json_mode": self.supports_json_mode,
            "cost_per_1k_input_tokens": self.cost_per_1k_input_tokens,
            "cost_per_1k_output_tokens": self.cost_per_1k_output_tokens,
            "is_active": self.is_active,
            "priority": self.priority,
            "description": self.description,
            "usage_notes": self.usage_notes,
            "tags": self.tags.split(",") if self.tags else [],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        
        if include_provider and self.provider:
            data["provider"] = self.provider.to_dict(include_api_key=False)
        else:
            # 只包含基本的供应商信息
            if self.provider:
                data["provider_name"] = self.provider.name
                data["provider_display_name"] = self.provider.display_name
        
        return data
    
    def get_full_name(self) -> str:
        """获取完整的模型名称（供应商 + 模型）"""
        if self.provider:
            return f"{self.provider.display_name} - {self.display_name}"
        return self.display_name
    
    def __repr__(self):
        return f"<LLMModel(model_name='{self.model_name}', provider='{self.provider.name if self.provider else 'N/A'}', is_active={self.is_active})>"
