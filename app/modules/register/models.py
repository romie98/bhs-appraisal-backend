"""Register models"""
from sqlalchemy import Column, String, Date, ForeignKey, Text, Enum as SQLEnum, Integer, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
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


class HomeroomRegister(Base):
    """Homeroom register model - tracks morning and afternoon attendance by gender"""
    __tablename__ = "homeroom_registers"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    teacher_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    classroom_id = Column(String(36), ForeignKey("classes.id"), nullable=False, index=True)
    
    date = Column(Date, nullable=False, index=True)
    
    morning_boys = Column(Integer, default=0, nullable=False)
    morning_girls = Column(Integer, default=0, nullable=False)
    
    afternoon_boys = Column(Integer, default=0, nullable=False)
    afternoon_girls = Column(Integer, default=0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        UniqueConstraint("classroom_id", "date", name="uq_homeroom_per_day"),
    )
    
    def __repr__(self):
        return f"<HomeroomRegister(id={self.id}, classroom_id={self.classroom_id}, date={self.date})>"

