"""Admin analytics models"""
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class UserActivityLog(Base):
    """User activity log model for admin analytics"""
    __tablename__ = "user_activity_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    action_type = Column(String(100), nullable=False, index=True)  # e.g., "login", "evidence_upload"
    entity_type = Column(String(100), nullable=True)  # e.g., "evidence", "lesson_plan"
    entity_id = Column(String(36), nullable=True)  # ID of the entity involved
    metadata_json = Column("metadata", JSON, nullable=True)  # Additional context (sanitized) - Column name is "metadata", attribute is "metadata_json"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    # Relationship to user
    user = relationship("User", backref="activity_logs")

    def __repr__(self):
        return f"<UserActivityLog(id={self.id}, user_id={self.user_id}, action_type={self.action_type})>"










