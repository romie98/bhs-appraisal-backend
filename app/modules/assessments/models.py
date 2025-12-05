"""Assessment models"""
from sqlalchemy import Column, String, Integer, Date, ForeignKey, Float, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
import uuid
import enum
from app.core.database import Base


class AssessmentType(str, enum.Enum):
    """Assessment type enum"""
    QUIZ = "Quiz"
    HOMEWORK = "Homework"
    PROJECT = "Project"
    TEST = "Test"
    EXAM = "Exam"


class Assessment(Base):
    """Assessment model"""
    __tablename__ = "assessments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    title = Column(String(200), nullable=False)
    type = Column(SQLEnum(AssessmentType), nullable=False)
    total_marks = Column(Integer, nullable=False)
    date_assigned = Column(Date, nullable=False)
    date_due = Column(Date, nullable=True)
    grade = Column(String(10), nullable=False)  # e.g., "10-9"
    
    # Relationships
    scores = relationship("AssessmentScore", back_populates="assessment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Assessment(id={self.id}, title={self.title}, type={self.type}, grade={self.grade})>"


class AssessmentScore(Base):
    """Assessment score model"""
    __tablename__ = "assessment_scores"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    assessment_id = Column(String(36), ForeignKey("assessments.id"), nullable=False, index=True)
    student_id = Column(String(36), ForeignKey("students.id"), nullable=False, index=True)
    score = Column(Float, nullable=False)
    comment = Column(Text, nullable=True)
    
    # Relationships
    assessment = relationship("Assessment", back_populates="scores")
    student = relationship("Student", back_populates="assessment_scores")
    
    def __repr__(self):
        return f"<AssessmentScore(id={self.id}, assessment_id={self.assessment_id}, student_id={self.student_id}, score={self.score})>"

