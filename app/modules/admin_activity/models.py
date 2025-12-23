"""Admin activity log models"""
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime


class AdminActivityLog(Base):
    """Admin activity log model for tracking system events"""
    __tablename__ = "admin_activity_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(36), index=True, nullable=True)
    user_email = Column(String(255), index=True, nullable=True)
    action = Column(String(100), index=True, nullable=False)
    resource = Column(String(500), nullable=True)
    metadata_json = Column("metadata", JSON, nullable=True)  # Column name is "metadata", attribute is "metadata_json"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    def __repr__(self):
        return f"<AdminActivityLog(id={self.id}, user_email={self.user_email}, action={self.action})>"






