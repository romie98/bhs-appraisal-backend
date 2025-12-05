"""Lesson Plans module database models"""
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class LessonPlan(Base):
    """Lesson Plan model for storing uploaded lesson plans"""
    __tablename__ = "lesson_plans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    teacher_id = Column(String(36), nullable=False, index=True)  # UUID of teacher
    title = Column(String(255), nullable=False)
    content_text = Column(Text, nullable=False)  # Extracted text from file or pasted text
    file_path = Column(String(500), nullable=True)  # Path to uploaded file (if file was uploaded)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<LessonPlan(id={self.id}, title={self.title}, teacher_id={self.teacher_id})>"




