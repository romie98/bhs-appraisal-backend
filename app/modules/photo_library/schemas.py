"""Photo Evidence Library Pydantic schemas"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class PhotoEvidenceBase(BaseModel):
    """Base schema for photo evidence"""
    teacher_id: str = Field(..., description="UUID of the teacher")


class PhotoEvidenceCreate(PhotoEvidenceBase):
    """Schema for creating photo evidence (metadata only, file handled separately)"""
    pass


class PhotoEvidenceResponse(BaseModel):
    """Schema for photo evidence response"""
    id: UUID
    teacher_id: str
    file_path: str
    ocr_text: Optional[str] = None
    gp_recommendations: Dict[str, Any] = {}
    gp_subsections: Dict[str, Any] = {}
    created_at: datetime

    class Config:
        from_attributes = True


class PhotoEvidenceListItem(PhotoEvidenceResponse):
    """Schema for listing photo evidence"""
    pass