"""AI module Pydantic schemas"""
from pydantic import BaseModel
from typing import List, Optional, Dict


class AITestRequest(BaseModel):
    """Schema for AI test request"""
    prompt: Optional[str] = None


class AITestResponse(BaseModel):
    """Schema for AI test response"""
    response: str
    success: bool


class LessonEvidenceRequest(BaseModel):
    """Schema for lesson evidence extraction request"""
    lesson_text: str
    lesson_id: Optional[str] = None


class LessonEvidenceResponse(BaseModel):
    """Schema for lesson evidence response"""
    lesson_id: str
    gp1: List[str] = []
    gp2: List[str] = []
    gp3: List[str] = []
    gp4: List[str] = []
    gp5: List[str] = []
    gp6: List[str] = []
    strengths: List[str] = []
    weaknesses: List[str] = []


class GPEvidenceItem(BaseModel):
    """Schema for a single GP evidence item"""
    gp: int
    evidence: str


class LogEvidenceRequest(BaseModel):
    """Schema for log evidence extraction request"""
    entry_text: str
    log_entry_id: Optional[str] = None


class LogEvidenceResponse(BaseModel):
    """Schema for log evidence response"""
    log_entry_id: str
    mappedGP: List[GPEvidenceItem] = []
    summary: str = ""


class RegisterEvidenceRequest(BaseModel):
    """Schema for register evidence extraction request"""
    attendance_percentage: Optional[float] = None
    punctuality_percentage: Optional[float] = None
    date_range: Optional[str] = None
    notes: List[str] = []
    follow_ups: List[str] = []
    register_period_id: Optional[str] = None


class RegisterEvidenceResponse(BaseModel):
    """Schema for register evidence response"""
    register_period_id: str
    gp3: List[str] = []
    gp6: List[str] = []
    patternsDetected: List[str] = []
    recommendedInterventions: List[str] = []


class PerformanceBreakdown(BaseModel):
    """Schema for performance breakdown"""
    excellent: List[str] = []
    proficient: List[str] = []
    developing: List[str] = []
    needsSupport: List[str] = []
    commonGaps: List[str] = []


class RecommendedAction(BaseModel):
    """Schema for recommended action"""
    action: str
    targetGroup: str
    priority: str  # "high", "medium", "low"


class AssessmentEvidenceRequest(BaseModel):
    """Schema for assessment evidence extraction request"""
    description: str
    grade_distribution: Optional[Dict[str, int]] = {}
    diagnostic_results: Optional[List[str]] = []
    assessment_id: Optional[str] = None


class AssessmentEvidenceResponse(BaseModel):
    """Schema for assessment evidence response"""
    assessment_id: str
    gp2: List[str] = []
    gp3: List[str] = []
    performanceBreakdown: PerformanceBreakdown = PerformanceBreakdown()
    recommendedActions: List[RecommendedAction] = []


class PortfolioEvidenceRequest(BaseModel):
    """Schema for portfolio build request"""
    lesson_evidence: Optional[List[Dict]] = []
    log_evidence: Optional[List[Dict]] = []
    assessment_evidence: Optional[List[Dict]] = []
    register_evidence: Optional[List[Dict]] = []
    external_uploads: Optional[List[Dict]] = []
    # Optional flags to auto-fetch all evidence from database
    auto_fetch_all: Optional[bool] = False
    teacher_id: Optional[str] = None  # For filtering by teacher


class GPSection(BaseModel):
    """Schema for a GP section in portfolio"""
    evidence: List[str] = []
    summary: str = ""


class PortfolioResponse(BaseModel):
    """Schema for portfolio response"""
    portfolio_id: Optional[str] = None
    gp1: GPSection = GPSection()
    gp2: GPSection = GPSection()
    gp3: GPSection = GPSection()
    gp4: GPSection = GPSection()
    gp5: GPSection = GPSection()
    gp6: GPSection = GPSection()
    overall_summary: str = ""


class ActionPlanItem(BaseModel):
    """Schema for action plan item"""
    priority: str  # "high", "medium", "low"
    action: str
    timeline: str


class AppraisalReportRequest(BaseModel):
    """Schema for appraisal report generation request"""
    gp_evidence: Optional[Dict[str, List[str]]] = {}
    attendance_patterns: Optional[Dict] = {}
    professional_development: Optional[List[Dict]] = []
    lesson_plan_quality: Optional[Dict] = {}
    class_performance_trends: Optional[Dict] = {}


class AppraisalReportResponse(BaseModel):
    """Schema for appraisal report response"""
    report_id: str
    scores: Dict[str, int] = {}
    category: str = ""
    strengths: List[str] = []
    weaknesses: List[str] = []
    recommendations: List[str] = []
    actionPlan: List[ActionPlanItem] = []
    html_report: Optional[str] = None
