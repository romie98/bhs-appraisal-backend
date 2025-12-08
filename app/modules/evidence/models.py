"""Evidence models"""
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Evidence(Base):
    """Evidence model for storing uploaded files with GP sections"""
    __tablename__ = "evidence"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    teacher_id = Column(String(36), nullable=False, index=True)
    gp_section = Column(String(10), nullable=True)  # GP1, GP2, etc.
    description = Column(Text, nullable=True)
    filename = Column(String(500), nullable=False)
    supabase_path = Column(String(500), nullable=False)
    supabase_url = Column(String(1000), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<Evidence(id={self.id}, teacher_id={self.teacher_id}, gp_section={self.gp_section})>"




