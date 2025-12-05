"""Register models"""
from sqlalchemy import Column, String, Date, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
import uuid
import enum
from app.core.database import Base


class RegisterStatus(str, enum.Enum):
    """Register status enum"""
    PRESENT = "Present"
    ABSENT = "Absent"
    LATE = "Late"
    EXCUSED = "Excused"


class RegisterRecord(Base):
    """Register record model"""
    __tablename__ = "register_records"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    status = Column(SQLEnum(RegisterStatus), nullable=False, default=RegisterStatus.PRESENT)
    comment = Column(Text, nullable=True)
    
    # Relationships
    student = relationship("Student", back_populates="register_records")
    
    def __repr__(self):
        return f"<RegisterRecord(id={self.id}, student_id={self.student_id}, date={self.date}, status={self.status})>"

