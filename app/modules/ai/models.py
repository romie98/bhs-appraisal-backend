"""AI module database models"""
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class LessonEvidence(Base):
    """Lesson evidence model for storing AI-extracted evidence"""
    __tablename__ = "lesson_evidence"

    id = Column(String(36), primary_key=True, index=True)
    lesson_id = Column(String(36), nullable=False, index=True)
    gp_number = Column(Integer, nullable=False)  # 1-6 for GP1-GP6
    evidence_text = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<LessonEvidence(id={self.id}, lesson_id={self.lesson_id}, gp_number={self.gp_number})>"


class LogEvidence(Base):
    """Log book evidence model for storing AI-extracted evidence"""
    __tablename__ = "log_evidence"

    id = Column(String(36), primary_key=True, index=True)
    log_entry_id = Column(String(36), nullable=False, index=True)
    gp_number = Column(Integer, nullable=False)  # 3, 4, or 6
    evidence_text = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)  # Stored once per log entry
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<LogEvidence(id={self.id}, log_entry_id={self.log_entry_id}, gp_number={self.gp_number})>"


class RegisterEvidence(Base):
    """Register/attendance evidence model for storing AI-extracted evidence"""
    __tablename__ = "register_evidence"

    id = Column(String(36), primary_key=True, index=True)
    register_period_id = Column(String(36), nullable=False, index=True)  # e.g., "week-2025-01-15" or "month-2025-01"
    gp_number = Column(Integer, nullable=False)  # 3 or 6
    evidence_text = Column(Text, nullable=False)
    evidence_type = Column(String(50), nullable=True)  # 'evidence', 'pattern', 'intervention'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<RegisterEvidence(id={self.id}, register_period_id={self.register_period_id}, gp_number={self.gp_number})>"


class AssessmentEvidence(Base):
    """Assessment evidence model for storing AI-extracted evidence"""
    __tablename__ = "assessment_evidence"

    id = Column(String(36), primary_key=True, index=True)
    assessment_id = Column(String(36), nullable=False, index=True)
    gp_number = Column(Integer, nullable=False)  # 2 or 3
    evidence_text = Column(Text, nullable=False)
    evidence_type = Column(String(50), nullable=True)  # 'evidence', 'performance', 'action'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<AssessmentEvidence(id={self.id}, assessment_id={self.assessment_id}, gp_number={self.gp_number})>"


class PortfolioCache(Base):
    """Portfolio cache model for storing built portfolios"""
    __tablename__ = "portfolio_cache"

    id = Column(String(36), primary_key=True, index=True)
    portfolio_data = Column(Text, nullable=False)  # JSON string of portfolio
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<PortfolioCache(id={self.id}, created_at={self.created_at})>"


class AppraisalReport(Base):
    """Appraisal report model for storing generated reports"""
    __tablename__ = "appraisal_report"

    id = Column(String(36), primary_key=True, index=True)
    report_data = Column(Text, nullable=False)  # JSON string of report
    html_report = Column(Text, nullable=True)  # HTML formatted report
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<AppraisalReport(id={self.id}, created_at={self.created_at})>"
