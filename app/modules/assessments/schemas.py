"""Assessment Pydantic schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import date
from app.modules.assessments.models import AssessmentType


class AssessmentBase(BaseModel):
    """Base assessment schema"""
    title: str = Field(..., min_length=1, max_length=200)
    type: AssessmentType
    total_marks: int = Field(..., gt=0)
    date_assigned: date
    date_due: Optional[date] = None
    grade: Optional[str] = Field(None, min_length=1, max_length=10, description="Grade (deprecated, use class_id)")
    class_id: Optional[UUID] = Field(None, description="Class ID")


class AssessmentCreate(AssessmentBase):
    """Schema for creating an assessment"""
    pass


class AssessmentUpdate(BaseModel):
    """Schema for updating an assessment"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    type: Optional[AssessmentType] = None
    total_marks: Optional[int] = Field(None, gt=0)
    date_assigned: Optional[date] = None
    date_due: Optional[date] = None
    grade: Optional[str] = Field(None, min_length=1, max_length=10)


class AssessmentResponse(AssessmentBase):
    """Schema for assessment response"""
    id: UUID
    
    class Config:
        from_attributes = True


class AssessmentScoreBase(BaseModel):
    """Base assessment score schema"""
    assessment_id: UUID
    student_id: UUID
    score: float = Field(..., ge=0)
    comment: Optional[str] = None


class AssessmentScoreCreate(AssessmentScoreBase):
    """Schema for creating an assessment score"""
    pass


class AssessmentScoreUpdate(BaseModel):
    """Schema for updating an assessment score"""
    score: Optional[float] = Field(None, ge=0)
    comment: Optional[str] = None


class AssessmentScoreResponse(AssessmentScoreBase):
    """Schema for assessment score response"""
    id: UUID
    
    class Config:
        from_attributes = True


class BulkScoreCreate(BaseModel):
    """Schema for bulk score creation"""
    assessment_id: UUID
    scores: List[AssessmentScoreBase]


class BulkScoreImportRow(BaseModel):
    """Schema for a single row in bulk import"""
    student_name: str
    student_id: Optional[UUID] = None
    score: float = Field(..., ge=0)
    comment: Optional[str] = None


class BulkScoreImportRequest(BaseModel):
    """Schema for bulk score import from Excel paste"""
    assessment_id: UUID
    rows: List[BulkScoreImportRow]


class BulkScoreImportResponse(BaseModel):
    """Schema for bulk score import response"""
    success: int
    updated: int
    created: int
    conflicts: List[dict] = []


class StudentWithScore(BaseModel):
    """Schema for student with score data"""
    student_id: UUID
    student_name: str
    score: Optional[float] = None
    comment: Optional[str] = None
    score_id: Optional[UUID] = None

