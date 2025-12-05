"""Photo Evidence Library models"""
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class PhotoEvidence(Base):
    """Photo evidence model for storing uploaded photos and AI GP recommendations"""
    __tablename__ = "photo_evidence"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    teacher_id = Column(String(36), nullable=False, index=True)
    file_path = Column(String(500), nullable=False)
    ocr_text = Column(Text, nullable=True)
    gp_recommendations = Column(Text, nullable=True)  # JSON string of GP1-GP6 recommendations
    gp_subsections = Column(Text, nullable=True)  # JSON string of GP subsections mapping
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<PhotoEvidence(id={self.id}, teacher_id={self.teacher_id}, file_path={self.file_path})>"