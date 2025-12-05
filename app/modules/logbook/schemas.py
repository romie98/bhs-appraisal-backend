"""Log Book Pydantic schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date
from uuid import UUID


class LogEntryBase(BaseModel):
    """Base log entry schema"""
    title: Optional[str] = None
    content: str
    entry_type: str
    date: datetime
    student_id: Optional[UUID] = None
    class_id: Optional[UUID] = None


class LogEntryCreate(LogEntryBase):
    """Schema for creating a log entry"""
    pass


class LogEntryUpdate(BaseModel):
    """Schema for updating a log entry"""
    title: Optional[str] = None
    content: Optional[str] = None
    entry_type: Optional[str] = None
    date: Optional[datetime] = None
    student_id: Optional[UUID] = None
    class_id: Optional[UUID] = None


class StudentInfo(BaseModel):
    """Student info for log entry response"""
    id: UUID
    first_name: str
    last_name: str

    class Config:
        from_attributes = True


class ClassInfo(BaseModel):
    """Class info for log entry response"""
    id: UUID
    name: str
    academic_year: str

    class Config:
        from_attributes = True


class LogEntryResponse(LogEntryBase):
    """Schema for log entry response"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    student: Optional[StudentInfo] = None
    class_obj: Optional[ClassInfo] = None

    class Config:
        from_attributes = True

