"""Log Book database models"""
from sqlalchemy import Column, String, Text, Date, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class LogEntryType(str, enum.Enum):
    """Log entry type enumeration"""
    INCIDENT = "Incident"
    REFLECTION = "Reflection"
    PARENT_MEETING = "Parent Meeting"
    BEHAVIOUR = "Behaviour"
    ACHIEVEMENT = "Achievement"
    GENERAL = "General"
    PROFESSIONAL_DEVELOPMENT = "Professional Development"


class LogEntry(Base):
    """Log entry model for teacher journal entries"""
    __tablename__ = "log_entries"

    id = Column(String(36), primary_key=True, index=True)
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    entry_type = Column(SQLEnum(LogEntryType), nullable=False)
    date = Column(DateTime, nullable=False)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=True)
    class_id = Column(String(36), ForeignKey("classes.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    student = relationship("Student", backref="log_entries")
    class_obj = relationship("Class", backref="log_entries")

    def __repr__(self):
        return f"<LogEntry(id={self.id}, title={self.title}, type={self.entry_type})>"





