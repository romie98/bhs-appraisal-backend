"""Class management models"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

# Many-to-many relationship table
class_students = Table(
    'class_students',
    Base.metadata,
    Column('id', String(36), primary_key=True, default=lambda: str(uuid.uuid4())),
    Column('class_id', String(36), ForeignKey('classes.id', ondelete='CASCADE'), nullable=False, index=True),
    Column('student_id', String(36), ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True),
)


class Class(Base):
    """Class model"""
    __tablename__ = "classes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    name = Column(String(200), nullable=False)
    academic_year = Column(String(50), nullable=False)  # e.g., "2024-2025"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    students = relationship(
        "Student",
        secondary=class_students,
        back_populates="classes"
    )
    
    def __repr__(self):
        return f"<Class(id={self.id}, name={self.name}, academic_year={self.academic_year})>"





