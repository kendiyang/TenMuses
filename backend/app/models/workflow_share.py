from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timedelta
import uuid
import enum
import secrets

from app.core.database import Base


class SharePermission(str, enum.Enum):
    VIEW = "view"
    EDIT = "edit"
    EXECUTE = "execute"


class WorkflowShare(Base):
    """Workflow sharing model for public/shareable links"""
    __tablename__ = "workflow_shares"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Share token and metadata
    share_token = Column(String, nullable=False, unique=True, default=lambda: secrets.token_urlsafe(32))
    share_url = Column(String, nullable=True)  # Full URL if provided
    
    # Permissions
    permission = Column(Enum(SharePermission), default=SharePermission.VIEW, nullable=False)
    
    # Access control
    is_public = Column(Boolean, default=False, nullable=False)
    max_uses = Column(String, nullable=True)  # Unlimited if null
    current_uses = Column(String, default="0", nullable=False)
    
    # Expiration
    expires_at = Column(DateTime, nullable=True)
    
    # Metadata
    description = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def is_expired(self) -> bool:
        """Check if share link is expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def is_usage_exceeded(self) -> bool:
        """Check if share link usage limit exceeded"""
        if self.max_uses:
            try:
                return int(self.current_uses) >= int(self.max_uses)
            except (ValueError, TypeError):
                return False
        return False
    
    def is_valid(self) -> bool:
        """Check if share link is still valid"""
        return not self.is_expired() and not self.is_usage_exceeded()


class WorkflowShareAccess(Base):
    """Track access to shared workflows"""
    __tablename__ = "workflow_share_access"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    share_id = Column(UUID(as_uuid=True), ForeignKey("workflow_shares.id", ondelete="CASCADE"), nullable=False)
    access_token = Column(String, nullable=True, unique=True)  # For anonymous access
    accessed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Access info
    accessed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
