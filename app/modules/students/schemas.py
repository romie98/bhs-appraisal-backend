"""Student Pydantic schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import date


class StudentBase(BaseModel):
    """Base student schema"""
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    grade: str = Field(..., min_length=1, max_length=10)
    gender: Optional[str] = Field(None, max_length=20)
    parent_contact: Optional[str] = Field(None, max_length=100)


class StudentCreate(StudentBase):
    """Schema for creating a student"""
    pass


class StudentUpdate(BaseModel):
    """Schema for updating a student"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    grade: Optional[str] = Field(None, min_length=1, max_length=10)
    gender: Optional[str] = Field(None, max_length=20)
    parent_contact: Optional[str] = Field(None, max_length=100)


class StudentResponse(StudentBase):
    """Schema for student response"""
    id: UUID
    
    class Config:
        from_attributes = True

