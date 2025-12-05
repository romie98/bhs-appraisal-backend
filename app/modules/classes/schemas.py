"""Class Pydantic schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class ClassBase(BaseModel):
    """Base class schema"""
    name: str = Field(..., min_length=1, max_length=200)
    academic_year: str = Field(..., min_length=1, max_length=50)


class ClassCreate(ClassBase):
    """Schema for creating a class"""
    pass


class ClassUpdate(BaseModel):
    """Schema for updating a class"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    academic_year: Optional[str] = Field(None, min_length=1, max_length=50)


class ClassResponse(ClassBase):
    """Schema for class response"""
    id: UUID
    created_at: datetime
    student_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class StudentAddRequest(BaseModel):
    """Schema for adding a single student to a class"""
    student_id: UUID


class BulkStudentAddRequest(BaseModel):
    """Schema for bulk adding students"""
    students: List[str] = Field(..., description="List of student names or formatted strings (e.g., 'John Brown, M, 10-9' or just 'John Brown')")
    default_grade: Optional[str] = Field(None, description="Default grade if not specified in student string")
    default_gender: Optional[str] = Field(None, description="Default gender if not specified in student string")


class StudentInClassResponse(BaseModel):
    """Schema for student in class response"""
    id: UUID
    first_name: str
    last_name: str
    grade: str
    gender: Optional[str]
    parent_contact: Optional[str]
    
    class Config:
        from_attributes = True





