"""Lesson Plans Pydantic schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class LessonPlanBase(BaseModel):
    """Base lesson plan schema"""
    title: str = Field(..., min_length=1, max_length=255)
    content_text: str = Field(..., min_length=1)


class LessonPlanCreate(LessonPlanBase):
    """Schema for creating a lesson plan from text"""
    teacher_id: str = Field(..., description="UUID of the teacher")


class LessonPlanUpdate(BaseModel):
    """Schema for updating a lesson plan"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content_text: Optional[str] = Field(None, min_length=1)


class LessonPlanResponse(LessonPlanBase):
    """Schema for lesson plan response"""
    id: UUID
    teacher_id: str
    file_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LessonPlanWithEvidence(LessonPlanResponse):
    """Schema for lesson plan with extracted evidence"""
    evidence: Optional[dict] = None  # Contains gp1-gp6, strengths, weaknesses

    class Config:
        from_attributes = True




