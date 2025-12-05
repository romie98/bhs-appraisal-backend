"""Student model"""
from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base


class Student(Base):
    """Student model"""
    __tablename__ = "students"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    grade = Column(String(10), nullable=False)  # e.g., "10-9", "11-1"
    gender = Column(String(20), nullable=True)
    parent_contact = Column(String(100), nullable=True)
    
    # Relationships
    register_records = relationship("RegisterRecord", back_populates="student", cascade="all, delete-orphan")
    assessment_scores = relationship("AssessmentScore", back_populates="student", cascade="all, delete-orphan")
    classes = relationship("Class", secondary="class_students", back_populates="students")
    
    def __repr__(self):
        return f"<Student(id={self.id}, name={self.first_name} {self.last_name}, grade={self.grade})>"

