"""Register Pydantic schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import date
from app.modules.register.models import RegisterStatus


class RegisterRecordBase(BaseModel):
    """Base register record schema"""
    student_id: UUID
    date: date
    status: RegisterStatus = RegisterStatus.PRESENT
    comment: Optional[str] = None


class RegisterRecordCreate(RegisterRecordBase):
    """Schema for creating a register record"""
    pass


class RegisterRecordUpdate(BaseModel):
    """Schema for updating a register record"""
    status: Optional[RegisterStatus] = None
    comment: Optional[str] = None


class RegisterRecordResponse(RegisterRecordBase):
    """Schema for register record response"""
    id: UUID
    
    class Config:
        from_attributes = True


class BulkRegisterCreate(BaseModel):
    """Schema for bulk register creation"""
    grade: Optional[str] = Field(None, min_length=1, max_length=10, description="Grade (deprecated, use class_id)")
    class_id: Optional[UUID] = Field(None, description="Class ID")
    date: date
    records: List[RegisterRecordBase]
    
    @classmethod
    def model_validate(cls, obj, *, strict=None, from_attributes=None, context=None):
        """Validate and convert class_id from string if needed"""
        if isinstance(obj, dict) and 'class_id' in obj and isinstance(obj['class_id'], str):
            try:
                from uuid import UUID
                obj['class_id'] = UUID(obj['class_id'])
            except (ValueError, TypeError):
                pass
        return super().model_validate(obj, strict=strict, from_attributes=from_attributes, context=context)


class RegisterSummaryResponse(BaseModel):
    """Schema for register summary response"""
    date: date
    total_students: int
    present: int
    absent: int
    late: int
    excused: int
    attendance_rate: float


class HomeroomRegisterCreate(BaseModel):
    """Schema for creating/updating a homeroom register"""
    classroom_id: UUID
    date: date
    morning_boys: int = Field(ge=0, description="Number of boys present in morning")
    morning_girls: int = Field(ge=0, description="Number of girls present in morning")
    afternoon_boys: int = Field(ge=0, description="Number of boys present in afternoon")
    afternoon_girls: int = Field(ge=0, description="Number of girls present in afternoon")


class HomeroomRegisterOut(BaseModel):
    """Schema for homeroom register response"""
    id: UUID
    date: date
    
    morning_boys: int
    morning_girls: int
    morning_total: int
    
    afternoon_boys: int
    afternoon_girls: int
    afternoon_total: int
    
    class Config:
        from_attributes = True

