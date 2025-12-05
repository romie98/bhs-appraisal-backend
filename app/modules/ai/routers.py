"""AI API router"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, List, Optional
from app.core.database import get_db
from app.services.ai_service import (
    send_to_ai, extract_lesson_evidence, extract_log_evidence, 
    extract_register_evidence, extract_assessment_evidence, build_portfolio,
    generate_appraisal_report
)
from app.modules.ai.schemas import (
    LessonEvidenceRequest, LessonEvidenceResponse, AITestRequest, AITestResponse,
    LogEvidenceRequest, LogEvidenceResponse, RegisterEvidenceRequest, RegisterEvidenceResponse,
    AssessmentEvidenceRequest, AssessmentEvidenceResponse,
    PortfolioEvidenceRequest, PortfolioResponse, GPSection,
    AppraisalReportRequest, AppraisalReportResponse
)
from app.modules.ai.models import (
    LessonEvidence, LogEvidence, RegisterEvidence, 
    AssessmentEvidence, PortfolioCache, AppraisalReport
)
from fastapi.responses import HTMLResponse, StreamingResponse
import uuid
import json

router = APIRouter()


@router.post("/test", response_model=AITestResponse)
async def test_ai(request: AITestRequest):
    """
    Test endpoint for AI service.
    Sends "Hello AI" (or custom prompt) to OpenAI and returns the response.
    """
    try:
        prompt = request.prompt if request.prompt else "Hello AI"
        response = send_to_ai(prompt)
        return AITestResponse(response=response, success=True)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI service error: {str(e)}"
        )


@router.post("/extract-lesson-evidence", response_model=LessonEvidenceResponse)
async def extract_lesson_evidence_endpoint(
    request: LessonEvidenceRequest,
    db: Session = Depends(get_db)
):
    """
    Extract evidence from a lesson plan using AI analysis.
    Analyzes the lesson plan according to Jamaica Teacher Appraisal GP1-GP6.
    Stores evidence in the database and returns the extracted evidence.
    """
    try:
        # Extract evidence using AI
        evidence_data = extract_lesson_evidence(request.lesson_text)
        
        # Generate a lesson_id if not provided
        lesson_id = request.lesson_id if request.lesson_id else str(uuid.uuid4())
        
        # Store evidence in database
        stored_evidence = {}
        for gp_number in range(1, 7):
            gp_key = f"gp{gp_number}"
            evidence_items = evidence_data.get(gp_key, [])
            
            stored_items = []
            for evidence_text in evidence_items:
                db_evidence = LessonEvidence(
                    id=str(uuid.uuid4()),
                    lesson_id=lesson_id,
                    gp_number=gp_number,
                    evidence_text=evidence_text
                )
                db.add(db_evidence)
                stored_items.append(evidence_text)
            
            stored_evidence[gp_key] = stored_items
        
        # Store strengths and weaknesses
        stored_evidence["strengths"] = evidence_data.get("strengths", [])
        stored_evidence["weaknesses"] = evidence_data.get("weaknesses", [])
        
        db.commit()
        
        return LessonEvidenceResponse(
            lesson_id=lesson_id,
            **stored_evidence
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting lesson evidence: {str(e)}"
        )


@router.get("/lesson-evidence/{lesson_id}", response_model=LessonEvidenceResponse)
async def get_lesson_evidence(
    lesson_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve stored evidence for a specific lesson.
    """
    evidence_records = db.query(LessonEvidence).filter(
        LessonEvidence.lesson_id == lesson_id
    ).all()
    
    # Organize evidence by GP
    evidence_data = {
        "gp1": [],
        "gp2": [],
        "gp3": [],
        "gp4": [],
        "gp5": [],
        "gp6": [],
        "strengths": [],
        "weaknesses": []
    }
    
    for record in evidence_records:
        gp_key = f"gp{record.gp_number}"
        if gp_key in evidence_data:
            evidence_data[gp_key].append(record.evidence_text)
    
    return LessonEvidenceResponse(
        lesson_id=lesson_id,
        **evidence_data
    )


@router.post("/extract-log-evidence", response_model=LogEvidenceResponse)
async def extract_log_evidence_endpoint(
    request: LogEvidenceRequest,
    db: Session = Depends(get_db)
):
    """
    Extract evidence from a log book entry using AI analysis.
    Analyzes the entry according to Jamaica Teacher Appraisal GP3, GP4, GP6.
    Stores evidence in the database and returns the extracted evidence.
    """
    try:
        # Extract evidence using AI
        evidence_data = extract_log_evidence(request.entry_text)
        
        # Generate a log_entry_id if not provided
        log_entry_id = request.log_entry_id if request.log_entry_id else str(uuid.uuid4())
        
        # Store evidence in database
        mapped_gp = []
        summary = evidence_data.get("summary", "")
        
        for gp_item in evidence_data.get("mappedGP", []):
            gp_number = gp_item.get("gp")
            evidence_text = gp_item.get("evidence")
            
            if gp_number in [3, 4, 6] and evidence_text:
                db_evidence = LogEvidence(
                    id=str(uuid.uuid4()),
                    log_entry_id=log_entry_id,
                    gp_number=gp_number,
                    evidence_text=evidence_text,
                    summary=summary if not mapped_gp else None  # Store summary only once
                )
                db.add(db_evidence)
                mapped_gp.append({"gp": gp_number, "evidence": evidence_text})
        
        db.commit()
        
        return LogEvidenceResponse(
            log_entry_id=log_entry_id,
            mappedGP=mapped_gp,
            summary=summary
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting log evidence: {str(e)}"
        )


@router.get("/log-evidence/{log_entry_id}", response_model=LogEvidenceResponse)
async def get_log_evidence(
    log_entry_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve stored evidence for a specific log entry.
    """
    evidence_records = db.query(LogEvidence).filter(
        LogEvidence.log_entry_id == log_entry_id
    ).all()
    
    mapped_gp = []
    summary = ""
    
    for record in evidence_records:
        if record.summary:
            summary = record.summary
        mapped_gp.append({
            "gp": record.gp_number,
            "evidence": record.evidence_text
        })
    
    return LogEvidenceResponse(
        log_entry_id=log_entry_id,
        mappedGP=mapped_gp,
        summary=summary
    )


@router.post("/extract-register-evidence", response_model=RegisterEvidenceResponse)
async def extract_register_evidence_endpoint(
    request: RegisterEvidenceRequest,
    db: Session = Depends(get_db)
):
    """
    Extract evidence from register/attendance data using AI analysis.
    Analyzes the data according to Jamaica Teacher Appraisal GP3 and GP6.
    Stores evidence in the database and returns the extracted evidence.
    """
    try:
        # Prepare register data for AI
        register_data = {
            "attendance_percentage": request.attendance_percentage,
            "punctuality_percentage": request.punctuality_percentage,
            "notes": request.notes,
            "follow_ups": request.follow_ups,
            "date_range": request.date_range or "N/A"
        }
        
        # Extract evidence using AI
        evidence_data = extract_register_evidence(register_data)
        
        # Generate a register_period_id if not provided
        register_period_id = request.register_period_id if request.register_period_id else str(uuid.uuid4())
        
        # Store evidence in database
        # Store GP3 evidence
        for evidence_text in evidence_data.get("gp3", []):
            db_evidence = RegisterEvidence(
                id=str(uuid.uuid4()),
                register_period_id=register_period_id,
                gp_number=3,
                evidence_text=evidence_text,
                evidence_type="evidence"
            )
            db.add(db_evidence)
        
        # Store GP6 evidence
        for evidence_text in evidence_data.get("gp6", []):
            db_evidence = RegisterEvidence(
                id=str(uuid.uuid4()),
                register_period_id=register_period_id,
                gp_number=6,
                evidence_text=evidence_text,
                evidence_type="evidence"
            )
            db.add(db_evidence)
        
        # Store patterns
        for pattern in evidence_data.get("patternsDetected", []):
            db_evidence = RegisterEvidence(
                id=str(uuid.uuid4()),
                register_period_id=register_period_id,
                gp_number=3,  # Patterns typically relate to GP3
                evidence_text=pattern,
                evidence_type="pattern"
            )
            db.add(db_evidence)
        
        # Store interventions
        for intervention in evidence_data.get("recommendedInterventions", []):
            db_evidence = RegisterEvidence(
                id=str(uuid.uuid4()),
                register_period_id=register_period_id,
                gp_number=3,  # Interventions typically relate to GP3
                evidence_text=intervention,
                evidence_type="intervention"
            )
            db.add(db_evidence)
        
        db.commit()
        
        return RegisterEvidenceResponse(
            register_period_id=register_period_id,
            gp3=evidence_data.get("gp3", []),
            gp6=evidence_data.get("gp6", []),
            patternsDetected=evidence_data.get("patternsDetected", []),
            recommendedInterventions=evidence_data.get("recommendedInterventions", [])
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting register evidence: {str(e)}"
        )


@router.get("/register-evidence/{register_period_id}", response_model=RegisterEvidenceResponse)
async def get_register_evidence(
    register_period_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve stored evidence for a specific register period.
    """
    evidence_records = db.query(RegisterEvidence).filter(
        RegisterEvidence.register_period_id == register_period_id
    ).all()
    
    gp3 = []
    gp6 = []
    patterns = []
    interventions = []
    
    for record in evidence_records:
        if record.gp_number == 3:
            if record.evidence_type == "pattern":
                patterns.append(record.evidence_text)
            elif record.evidence_type == "intervention":
                interventions.append(record.evidence_text)
            else:
                gp3.append(record.evidence_text)
        elif record.gp_number == 6:
            gp6.append(record.evidence_text)
    
    return RegisterEvidenceResponse(
        register_period_id=register_period_id,
        gp3=gp3,
        gp6=gp6,
        patternsDetected=patterns,
        recommendedInterventions=interventions
    )


@router.post("/extract-assessment-evidence", response_model=AssessmentEvidenceResponse)
async def extract_assessment_evidence_endpoint(
    request: AssessmentEvidenceRequest,
    db: Session = Depends(get_db)
):
    """
    Extract evidence from assessment data using AI analysis.
    Analyzes the assessment according to Jamaica Teacher Appraisal GP2 and GP3.
    Stores evidence in the database and returns the extracted evidence.
    """
    try:
        # Prepare assessment data for AI
        assessment_data = {
            "description": request.description,
            "grade_distribution": request.grade_distribution or {},
            "diagnostic_results": request.diagnostic_results or []
        }
        
        # Extract evidence using AI
        evidence_data = extract_assessment_evidence(assessment_data)
        
        # Generate an assessment_id if not provided
        assessment_id = request.assessment_id if request.assessment_id else str(uuid.uuid4())
        
        # Store evidence in database
        # Store GP2 evidence
        for evidence_text in evidence_data.get("gp2", []):
            db_evidence = AssessmentEvidence(
                id=str(uuid.uuid4()),
                assessment_id=assessment_id,
                gp_number=2,
                evidence_text=evidence_text,
                evidence_type="evidence"
            )
            db.add(db_evidence)
        
        # Store GP3 evidence
        for evidence_text in evidence_data.get("gp3", []):
            db_evidence = AssessmentEvidence(
                id=str(uuid.uuid4()),
                assessment_id=assessment_id,
                gp_number=3,
                evidence_text=evidence_text,
                evidence_type="evidence"
            )
            db.add(db_evidence)
        
        # Store performance breakdown as JSON in a special record
        if evidence_data.get("performanceBreakdown"):
            pb_text = json.dumps(evidence_data["performanceBreakdown"])
            db_evidence = AssessmentEvidence(
                id=str(uuid.uuid4()),
                assessment_id=assessment_id,
                gp_number=2,  # Performance breakdown relates to GP2
                evidence_text=pb_text,
                evidence_type="performance"
            )
            db.add(db_evidence)
        
        # Store recommended actions
        for action in evidence_data.get("recommendedActions", []):
            action_text = json.dumps(action)
            db_evidence = AssessmentEvidence(
                id=str(uuid.uuid4()),
                assessment_id=assessment_id,
                gp_number=3,  # Actions relate to GP3
                evidence_text=action_text,
                evidence_type="action"
            )
            db.add(db_evidence)
        
        db.commit()
        
        return AssessmentEvidenceResponse(
            assessment_id=assessment_id,
            gp2=evidence_data.get("gp2", []),
            gp3=evidence_data.get("gp3", []),
            performanceBreakdown=evidence_data.get("performanceBreakdown", {}),
            recommendedActions=evidence_data.get("recommendedActions", [])
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting assessment evidence: {str(e)}"
        )


@router.get("/assessment-evidence/{assessment_id}", response_model=AssessmentEvidenceResponse)
async def get_assessment_evidence(
    assessment_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve stored evidence for a specific assessment.
    """
    evidence_records = db.query(AssessmentEvidence).filter(
        AssessmentEvidence.assessment_id == assessment_id
    ).all()
    
    gp2 = []
    gp3 = []
    performance_breakdown = {}
    recommended_actions = []
    
    for record in evidence_records:
        if record.evidence_type == "performance":
            try:
                performance_breakdown = json.loads(record.evidence_text)
            except:
                pass
        elif record.evidence_type == "action":
            try:
                action = json.loads(record.evidence_text)
                recommended_actions.append(action)
            except:
                pass
        elif record.gp_number == 2:
            gp2.append(record.evidence_text)
        elif record.gp_number == 3:
            gp3.append(record.evidence_text)
    
    return AssessmentEvidenceResponse(
        assessment_id=assessment_id,
        gp2=gp2,
        gp3=gp3,
        performanceBreakdown=performance_breakdown,
        recommendedActions=recommended_actions
    )


@router.post("/build-portfolio", response_model=PortfolioResponse)
async def build_portfolio_endpoint(
    request: PortfolioEvidenceRequest,
    db: Session = Depends(get_db)
):
    """
    Build a comprehensive portfolio from all evidence sources.
    Organizes evidence into GP1-GP6 sections with summaries.
    
    This endpoint:
    - Aggregates evidence from all sources (lessons, logs, assessments, register, uploads)
    - Sends structured evidence to AI for organization
    - Handles JSON parsing errors gracefully
    - Returns safe fallback structure if AI fails
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Prepare all evidence data - ensure all fields are lists
        all_evidence = {
            "lesson_evidence": request.lesson_evidence if request.lesson_evidence else [],
            "log_evidence": request.log_evidence if request.log_evidence else [],
            "assessment_evidence": request.assessment_evidence if request.assessment_evidence else [],
            "register_evidence": request.register_evidence if request.register_evidence else [],
            "external_uploads": request.external_uploads if request.external_uploads else []
        }
        
        # Auto-fetch evidence from database if requested or if all arrays are empty
        if request.auto_fetch_all or (
            not all_evidence["lesson_evidence"] and
            not all_evidence["log_evidence"] and
            not all_evidence["assessment_evidence"] and
            not all_evidence["register_evidence"] and
            not all_evidence["external_uploads"]
        ):
            logger.info("Auto-fetching evidence from database...")
            
            # Fetch lesson evidence
            lesson_query = db.query(LessonEvidence)
            if request.teacher_id:
                # Filter by teacher_id if we can link lessons to teachers
                # For now, fetch all lesson evidence
                pass
            lesson_records = lesson_query.all()
            # Group by lesson_id to create proper structure
            lesson_groups = {}
            for r in lesson_records:
                if r.lesson_id not in lesson_groups:
                    lesson_groups[r.lesson_id] = {f"gp{i}": [] for i in range(1, 7)}
                gp_key = f"gp{r.gp_number}"
                if gp_key in lesson_groups[r.lesson_id]:
                    lesson_groups[r.lesson_id][gp_key].append(r.evidence_text)
            all_evidence["lesson_evidence"] = list(lesson_groups.values())
            
            # Fetch log evidence
            log_query = db.query(LogEvidence)
            log_records = log_query.all()
            # Group by log_entry_id
            log_groups = {}
            for r in log_records:
                if r.log_entry_id not in log_groups:
                    log_groups[r.log_entry_id] = {"mappedGP": []}
                log_groups[r.log_entry_id]["mappedGP"].append({
                    "gp": r.gp_number,
                    "evidence": r.evidence_text
                })
            all_evidence["log_evidence"] = list(log_groups.values())
            
            # Fetch assessment evidence
            assessment_query = db.query(AssessmentEvidence).filter(
                AssessmentEvidence.evidence_type == "evidence"
            )
            assessment_records = assessment_query.all()
            # Group by assessment_id
            assessment_groups = {}
            for r in assessment_records:
                if r.assessment_id not in assessment_groups:
                    assessment_groups[r.assessment_id] = {f"gp{i}": [] for i in range(1, 7)}
                gp_key = f"gp{r.gp_number}"
                if gp_key in assessment_groups[r.assessment_id]:
                    assessment_groups[r.assessment_id][gp_key].append(r.evidence_text)
            all_evidence["assessment_evidence"] = list(assessment_groups.values())
            
            # Fetch register evidence
            register_query = db.query(RegisterEvidence).filter(
                RegisterEvidence.evidence_type == "evidence"
            )
            register_records = register_query.all()
            # Group by register_period_id
            register_groups = {}
            for r in register_records:
                if r.register_period_id not in register_groups:
                    register_groups[r.register_period_id] = {f"gp{i}": [] for i in range(1, 7)}
                gp_key = f"gp{r.gp_number}"
                if gp_key in register_groups[r.register_period_id]:
                    register_groups[r.register_period_id][gp_key].append(r.evidence_text)
            all_evidence["register_evidence"] = list(register_groups.values())
            
            # Fetch photo evidence and convert to external_uploads format
            from app.modules.photo_library.models import PhotoEvidence
            photo_query = db.query(PhotoEvidence)
            if request.teacher_id:
                photo_query = photo_query.filter(PhotoEvidence.teacher_id == request.teacher_id)
            photo_records = photo_query.all()
            
            for photo in photo_records:
                # Extract GP recommendations from photo
                try:
                    gp_recommendations = json.loads(photo.gp_recommendations) if photo.gp_recommendations else {}
                    
                    # Convert photo evidence to external_uploads format
                    for gp_key in ["GP1", "GP2", "GP3", "GP4", "GP5", "GP6"]:
                        gp_num = int(gp_key.replace("GP", ""))
                        evidence_items = gp_recommendations.get(gp_key, [])
                        
                        for evidence_text in evidence_items:
                            all_evidence["external_uploads"].append({
                                "gp": gp_num,
                                "evidence": evidence_text,
                                "description": f"Photo evidence: {photo.file_path}",
                                "source": "photo_library",
                                "photo_id": photo.id
                            })
                except Exception as e:
                    logger.warning(f"Error processing photo evidence {photo.id}: {e}")
        
        # Log evidence counts for debugging
        logger.info(f"Build portfolio endpoint: Received evidence - "
                   f"Lessons: {len(all_evidence['lesson_evidence'])}, "
                   f"Logs: {len(all_evidence['log_evidence'])}, "
                   f"Assessments: {len(all_evidence['assessment_evidence'])}, "
                   f"Register: {len(all_evidence['register_evidence'])}, "
                   f"Uploads: {len(all_evidence['external_uploads'])}")
        
        # Build portfolio using AI (with built-in error handling)
        portfolio_data = build_portfolio(all_evidence)
        
        # Check if AI returned an error structure
        if "error" in portfolio_data:
            logger.warning(f"Build portfolio endpoint: AI returned error: {portfolio_data.get('error')}")
            # Still return the structure, but log the error
            # The frontend can check for "error" key if needed
        
        # Store portfolio in cache (even if it has errors, for debugging)
        portfolio_json = json.dumps(portfolio_data)
        db_portfolio = PortfolioCache(
            id=str(uuid.uuid4()),
            portfolio_data=portfolio_json
        )
        db.add(db_portfolio)
        db.commit()
        db.refresh(db_portfolio)
        
        # Build response - ensure portfolio_id is included
        response_data = {
            "portfolio_id": db_portfolio.id,
            "gp1": GPSection(
                evidence=portfolio_data.get("gp1", {}).get("evidence", []),
                summary=portfolio_data.get("gp1", {}).get("summary", "")
            ),
            "gp2": GPSection(
                evidence=portfolio_data.get("gp2", {}).get("evidence", []),
                summary=portfolio_data.get("gp2", {}).get("summary", "")
            ),
            "gp3": GPSection(
                evidence=portfolio_data.get("gp3", {}).get("evidence", []),
                summary=portfolio_data.get("gp3", {}).get("summary", "")
            ),
            "gp4": GPSection(
                evidence=portfolio_data.get("gp4", {}).get("evidence", []),
                summary=portfolio_data.get("gp4", {}).get("summary", "")
            ),
            "gp5": GPSection(
                evidence=portfolio_data.get("gp5", {}).get("evidence", []),
                summary=portfolio_data.get("gp5", {}).get("summary", "")
            ),
            "gp6": GPSection(
                evidence=portfolio_data.get("gp6", {}).get("evidence", []),
                summary=portfolio_data.get("gp6", {}).get("summary", "")
            ),
            "overall_summary": portfolio_data.get("overall_summary", "")
        }
        
        return PortfolioResponse(**response_data)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Build portfolio endpoint: Unexpected error: {str(e)}", exc_info=True)
        
        # Return safe fallback structure instead of crashing
        fallback_data = {
            "portfolio_id": str(uuid.uuid4()),
            "gp1": GPSection(evidence=[], summary=""),
            "gp2": GPSection(evidence=[], summary=""),
            "gp3": GPSection(evidence=[], summary=""),
            "gp4": GPSection(evidence=[], summary=""),
            "gp5": GPSection(evidence=[], summary=""),
            "gp6": GPSection(evidence=[], summary=""),
            "overall_summary": f"Error building portfolio: {str(e)}"
        }
        
        # Try to save error state for debugging
        try:
            error_json = json.dumps({"error": str(e), **fallback_data})
            db_portfolio = PortfolioCache(
                id=fallback_data["portfolio_id"],
                portfolio_data=error_json
            )
            db.add(db_portfolio)
            db.commit()
        except:
            pass  # Don't fail if we can't save error state
        
        # Return the fallback structure (HTTP 200 with error in content)
        # This allows frontend to handle gracefully
        return PortfolioResponse(**fallback_data)


@router.get("/portfolio/latest", response_model=PortfolioResponse)
async def get_latest_portfolio(
    db: Session = Depends(get_db)
):
    """
    Retrieve the most recently built portfolio.
    """
    portfolio = db.query(PortfolioCache).order_by(
        PortfolioCache.created_at.desc()
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No portfolio found"
        )
    
    try:
        portfolio_data = json.loads(portfolio.portfolio_data)
        return PortfolioResponse(**portfolio_data)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error parsing portfolio data"
        )


@router.post("/extract-assessment-evidence", response_model=AssessmentEvidenceResponse)
async def extract_assessment_evidence_endpoint(
    request: AssessmentEvidenceRequest,
    db: Session = Depends(get_db)
):
    """
    Extract evidence from assessment data using AI analysis.
    Analyzes the assessment according to Jamaica Teacher Appraisal GP2 and GP3.
    Stores evidence in the database and returns the extracted evidence.
    """
    try:
        # Prepare assessment data for AI
        assessment_data = {
            "description": request.description,
            "grade_distribution": request.grade_distribution or {},
            "diagnostic_results": request.diagnostic_results or [],
            "total_students": request.total_students,
            "average_score": request.average_score
        }
        
        # Extract evidence using AI
        evidence_data = extract_assessment_evidence(assessment_data)
        
        # Generate an assessment_id if not provided
        assessment_id = request.assessment_id if request.assessment_id else str(uuid.uuid4())
        
        # Store evidence in database
        # Store GP2 evidence
        for evidence_text in evidence_data.get("gp2", []):
            db_evidence = AssessmentEvidence(
                id=str(uuid.uuid4()),
                assessment_id=assessment_id,
                gp_number=2,
                evidence_text=evidence_text,
                evidence_type="evidence"
            )
            db.add(db_evidence)
        
        # Store GP3 evidence
        for evidence_text in evidence_data.get("gp3", []):
            db_evidence = AssessmentEvidence(
                id=str(uuid.uuid4()),
                assessment_id=assessment_id,
                gp_number=3,
                evidence_text=evidence_text,
                evidence_type="evidence"
            )
            db.add(db_evidence)
        
        # Store strengths
        for strength in evidence_data.get("performanceBreakdown", {}).get("strengths", []):
            db_evidence = AssessmentEvidence(
                id=str(uuid.uuid4()),
                assessment_id=assessment_id,
                gp_number=2,  # Strengths typically relate to GP2
                evidence_text=strength,
                evidence_type="strength"
            )
            db.add(db_evidence)
        
        # Store areas needing intervention
        for area in evidence_data.get("performanceBreakdown", {}).get("areasNeedingIntervention", []):
            db_evidence = AssessmentEvidence(
                id=str(uuid.uuid4()),
                assessment_id=assessment_id,
                gp_number=3,  # Interventions typically relate to GP3
                evidence_text=area,
                evidence_type="intervention"
            )
            db.add(db_evidence)
        
        # Store recommended student groups
        for group in evidence_data.get("performanceBreakdown", {}).get("recommendedStudentGroups", []):
            db_evidence = AssessmentEvidence(
                id=str(uuid.uuid4()),
                assessment_id=assessment_id,
                gp_number=2,  # Grouping strategies relate to GP2
                evidence_text=group,
                evidence_type="group"
            )
            db.add(db_evidence)
        
        # Store recommended actions
        for action in evidence_data.get("recommendedActions", []):
            db_evidence = AssessmentEvidence(
                id=str(uuid.uuid4()),
                assessment_id=assessment_id,
                gp_number=3,  # Actions typically relate to GP3
                evidence_text=action,
                evidence_type="intervention"
            )
            db.add(db_evidence)
        
        db.commit()
        
        return AssessmentEvidenceResponse(
            assessment_id=assessment_id,
            gp2=evidence_data.get("gp2", []),
            gp3=evidence_data.get("gp3", []),
            performanceBreakdown=evidence_data.get("performanceBreakdown", {
                "strengths": [],
                "areasNeedingIntervention": [],
                "recommendedStudentGroups": []
            }),
            recommendedActions=evidence_data.get("recommendedActions", [])
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting assessment evidence: {str(e)}"
        )


@router.get("/assessment-evidence/{assessment_id}", response_model=AssessmentEvidenceResponse)
async def get_assessment_evidence(
    assessment_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve stored evidence for a specific assessment.
    """
    evidence_records = db.query(AssessmentEvidence).filter(
        AssessmentEvidence.assessment_id == assessment_id
    ).all()
    
    gp2 = []
    gp3 = []
    strengths = []
    areas_needing_intervention = []
    recommended_student_groups = []
    recommended_actions = []
    
    for record in evidence_records:
        if record.gp_number == 2:
            if record.evidence_type == "strength":
                strengths.append(record.evidence_text)
            elif record.evidence_type == "group":
                recommended_student_groups.append(record.evidence_text)
            else:
                gp2.append(record.evidence_text)
        elif record.gp_number == 3:
            if record.evidence_type == "intervention":
                if record.evidence_text not in recommended_actions:
                    # Check if it's an intervention area or action
                    if "intervention" in record.evidence_text.lower() or "support" in record.evidence_text.lower():
                        areas_needing_intervention.append(record.evidence_text)
                    else:
                        recommended_actions.append(record.evidence_text)
            else:
                gp3.append(record.evidence_text)
    
    return AssessmentEvidenceResponse(
        assessment_id=assessment_id,
        gp2=gp2,
        gp3=gp3,
        performanceBreakdown={
            "strengths": strengths,
            "areasNeedingIntervention": areas_needing_intervention,
            "recommendedStudentGroups": recommended_student_groups
        },
        recommendedActions=recommended_actions
    )


@router.get("/portfolio/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve a cached portfolio.
    """
    portfolio = db.query(PortfolioCache).filter(
        PortfolioCache.id == portfolio_id
    ).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio not found"
        )
    
    portfolio_data = json.loads(portfolio.portfolio_data)
    
    return PortfolioResponse(
        portfolio_id=portfolio_id,
        gp1=GPSection(
            evidence=portfolio_data.get("gp1", {}).get("evidence", []),
            summary=portfolio_data.get("gp1", {}).get("summary", "")
        ),
        gp2=GPSection(
            evidence=portfolio_data.get("gp2", {}).get("evidence", []),
            summary=portfolio_data.get("gp2", {}).get("summary", "")
        ),
        gp3=GPSection(
            evidence=portfolio_data.get("gp3", {}).get("evidence", []),
            summary=portfolio_data.get("gp3", {}).get("summary", "")
        ),
        gp4=GPSection(
            evidence=portfolio_data.get("gp4", {}).get("evidence", []),
            summary=portfolio_data.get("gp4", {}).get("summary", "")
        ),
        gp5=GPSection(
            evidence=portfolio_data.get("gp5", {}).get("evidence", []),
            summary=portfolio_data.get("gp5", {}).get("summary", "")
        ),
        gp6=GPSection(
            evidence=portfolio_data.get("gp6", {}).get("evidence", []),
            summary=portfolio_data.get("gp6", {}).get("summary", "")
        ),
        overall_summary=portfolio_data.get("overall_summary", "")
    )


@router.get("/portfolio/latest", response_model=PortfolioResponse)
async def get_latest_portfolio(
    teacher_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get the most recently created portfolio.
    """
    query = db.query(PortfolioCache)
    if teacher_id:
        query = query.filter(PortfolioCache.teacher_id == teacher_id)
    
    portfolio = query.order_by(PortfolioCache.created_at.desc()).first()
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No portfolio found"
        )
    
    portfolio_data = json.loads(portfolio.portfolio_data)
    
    return PortfolioResponse(
        portfolio_id=portfolio.id,
        gp1=GPSection(
            evidence=portfolio_data.get("gp1", {}).get("evidence", []),
            summary=portfolio_data.get("gp1", {}).get("summary", "")
        ),
        gp2=GPSection(
            evidence=portfolio_data.get("gp2", {}).get("evidence", []),
            summary=portfolio_data.get("gp2", {}).get("summary", "")
        ),
        gp3=GPSection(
            evidence=portfolio_data.get("gp3", {}).get("evidence", []),
            summary=portfolio_data.get("gp3", {}).get("summary", "")
        ),
        gp4=GPSection(
            evidence=portfolio_data.get("gp4", {}).get("evidence", []),
            summary=portfolio_data.get("gp4", {}).get("summary", "")
        ),
        gp5=GPSection(
            evidence=portfolio_data.get("gp5", {}).get("evidence", []),    
            summary=portfolio_data.get("gp5", {}).get("summary", "")       
        ),
        gp6=GPSection(
            evidence=portfolio_data.get("gp6", {}).get("evidence", []),    
            summary=portfolio_data.get("gp6", {}).get("summary", "")       
        ),
        overall_summary=portfolio_data.get("overall_summary", "")
    )


@router.post("/generate-appraisal-report", response_model=AppraisalReportResponse)
async def generate_appraisal_report_endpoint(
    request: AppraisalReportRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a comprehensive appraisal report with scoring and categorization.
    """
    # Generate the report using AI
    report_data = generate_appraisal_report({
        "gp_evidence": request.gp_evidence or {},
        "attendance_patterns": request.attendance_patterns or {},
        "professional_development": request.professional_development or [],
        "lesson_plan_quality": request.lesson_plan_quality or {},
        "class_performance_trends": request.class_performance_trends or {}
    })
    
    # Create report ID
    report_id = str(uuid.uuid4())
    
    # Store in database
    report_record = AppraisalReport(
        id=report_id,
        report_data=json.dumps(report_data),
        html_report=report_data.get("html_report", "")
    )
    db.add(report_record)
    db.commit()
    db.refresh(report_record)
    
    # Build response
    return AppraisalReportResponse(
        report_id=report_id,
        scores=report_data.get("scores", {}),
        category=report_data.get("category", ""),
        strengths=report_data.get("strengths", []),
        weaknesses=report_data.get("weaknesses", []),
        recommendations=report_data.get("recommendations", []),
        actionPlan=report_data.get("actionPlan", []),
        html_report=report_data.get("html_report")
    )


@router.get("/appraisal-report/{report_id}", response_model=AppraisalReportResponse)
async def get_appraisal_report(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve a generated appraisal report by ID.
    """
    report = db.query(AppraisalReport).filter(
        AppraisalReport.id == report_id
    ).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appraisal report not found"
        )
    
    report_data = json.loads(report.report_data)
    
    return AppraisalReportResponse(
        report_id=report_id,
        scores=report_data.get("scores", {}),
        category=report_data.get("category", ""),
        strengths=report_data.get("strengths", []),
        weaknesses=report_data.get("weaknesses", []),
        recommendations=report_data.get("recommendations", []),
        actionPlan=report_data.get("actionPlan", []),
        html_report=report.html_report
    )


@router.get("/appraisal-report/latest", response_model=AppraisalReportResponse)
async def get_latest_appraisal_report(
    db: Session = Depends(get_db)
):
    """
    Get the most recently generated appraisal report.
    """
    report = db.query(AppraisalReport).order_by(
        AppraisalReport.created_at.desc()
    ).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No appraisal report found"
        )
    
    report_data = json.loads(report.report_data)
    
    return AppraisalReportResponse(
        report_id=report.id,
        scores=report_data.get("scores", {}),
        category=report_data.get("category", ""),
        strengths=report_data.get("strengths", []),
        weaknesses=report_data.get("weaknesses", []),
        recommendations=report_data.get("recommendations", []),
        actionPlan=report_data.get("actionPlan", []),
        html_report=report.html_report
    )


@router.get("/appraisal-report/{report_id}/pdf")
async def export_appraisal_report_pdf(
    report_id: str,
    db: Session = Depends(get_db)
):
    """
    Export an appraisal report as PDF.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from io import BytesIO
    
    report = db.query(AppraisalReport).filter(
        AppraisalReport.id == report_id
    ).first()
    
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appraisal report not found"
        )
    
    report_data = json.loads(report.report_data)
    
    # Create PDF buffer
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor='#1e40af',
        spaceAfter=12
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor='#1e40af',
        spaceAfter=8
    )
    
    # Build PDF content
    story = []
    
    # Title
    story.append(Paragraph("Teacher Appraisal Report", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Scores
    story.append(Paragraph("GP Scores", heading_style))
    scores = report_data.get("scores", {})
    for gp_num in range(1, 7):
        gp_key = f"gp{gp_num}"
        score = scores.get(gp_key, 0)
        story.append(Paragraph(f"GP {gp_num}: {score}/100", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Category
    story.append(Paragraph(f"Category: {report_data.get('category', 'N/A')}", heading_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Strengths
    story.append(Paragraph("Strengths", heading_style))
    for strength in report_data.get("strengths", []):
        story.append(Paragraph(f"• {strength}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Weaknesses
    story.append(Paragraph("Areas for Improvement", heading_style))
    for weakness in report_data.get("weaknesses", []):
        story.append(Paragraph(f"• {weakness}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Recommendations
    story.append(Paragraph("Recommendations", heading_style))
    for rec in report_data.get("recommendations", []):
        story.append(Paragraph(f"• {rec}", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    
    # Action Plan
    story.append(Paragraph("Action Plan", heading_style))
    for item in report_data.get("actionPlan", []):
        if isinstance(item, dict):
            priority = item.get("priority", "")
            action = item.get("action", "")
            timeline = item.get("timeline", "")
            story.append(Paragraph(f"• [{priority}] {action} - {timeline}", styles['Normal']))
        else:
            story.append(Paragraph(f"• {item}", styles['Normal']))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    
    # Return as streaming response
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=appraisal_report_{report_id}.pdf"
        }
    )

