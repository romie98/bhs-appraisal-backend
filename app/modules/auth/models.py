"""User authentication model"""
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.sql import func
from app.core.database import Base
from app.modules.auth.constants import (
    SUBSCRIPTION_PLAN_FREE,
    SUBSCRIPTION_STATUS_ACTIVE
)
import uuid


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Nullable for Google-only users
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    role = Column(String, nullable=False, default="TEACHER")
    subscription_plan = Column(String(50), nullable=False, default=SUBSCRIPTION_PLAN_FREE)
    subscription_status = Column(String(50), nullable=False, default=SUBSCRIPTION_STATUS_ACTIVE)
    subscription_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"


