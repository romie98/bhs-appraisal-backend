"""Lesson Plans API router"""
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.modules.lesson_plans.models import LessonPlan
from app.modules.lesson_plans.schemas import (
    LessonPlanCreate,
    LessonPlanUpdate,
    LessonPlanResponse,
    LessonPlanWithEvidence
)
from app.modules.lesson_plans.services import (
    extract_text_from_file,
    save_uploaded_file,
    get_file_extension
)
from app.services.ai_service import extract_lesson_evidence
from app.modules.ai.models import LessonEvidence

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=LessonPlanResponse, status_code=status.HTTP_201_CREATED)
async def upload_lesson_plan(
    file: UploadFile = File(...),
    title: str = Form(...),
    teacher_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Upload a lesson plan file (PDF, DOCX, or TXT).
    Extracts text from the file and saves it to the database.
    """
    try:
        # Validate file type
        file_ext = get_file_extension(file.filename)
        allowed_extensions = ['.pdf', '.docx', '.txt']
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Allowed types: {', '.join(allowed_extensions)}"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Save file to disk
        file_path = save_uploaded_file(file_content, file.filename, teacher_id)
        
        # Extract text from file
        content_text = extract_text_from_file(file_path, file_ext)
        
        if not content_text or not content_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not extract text from file. File may be empty or corrupted."
            )
        
        # Create lesson plan record
        db_lesson_plan = LessonPlan(
            id=str(uuid.uuid4()),
            teacher_id=teacher_id,
            title=title,
            content_text=content_text,
            file_path=file_path
        )
        
        db.add(db_lesson_plan)
        db.commit()
        db.refresh(db_lesson_plan)
        
        logger.info(f"Lesson plan uploaded: {db_lesson_plan.id} by teacher {teacher_id}")
        
        return db_lesson_plan
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading lesson plan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading lesson plan: {str(e)}"
        )


@router.post("/create-text", response_model=LessonPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson_plan_from_text(
    lesson_plan: LessonPlanCreate,
    db: Session = Depends(get_db)
):
    """
    Create a lesson plan from pasted text.
    No file upload, just text content.
    """
    try:
        db_lesson_plan = LessonPlan(
            id=str(uuid.uuid4()),
            teacher_id=lesson_plan.teacher_id,
            title=lesson_plan.title,
            content_text=lesson_plan.content_text,
            file_path=None
        )
        
        db.add(db_lesson_plan)
        db.commit()
        db.refresh(db_lesson_plan)
        
        logger.info(f"Lesson plan created from text: {db_lesson_plan.id} by teacher {lesson_plan.teacher_id}")
        
        return db_lesson_plan
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating lesson plan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating lesson plan: {str(e)}"
        )


@router.get("/", response_model=List[LessonPlanResponse])
async def list_lesson_plans(
    teacher_id: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    List lesson plans, optionally filtered by teacher_id.
    If teacher_id is not provided, returns all lesson plans.
    """
    try:
        query = db.query(LessonPlan)
        
        if teacher_id:
            query = query.filter(LessonPlan.teacher_id == teacher_id)
        
        lesson_plans = query.order_by(LessonPlan.created_at.desc()).offset(skip).limit(limit).all()
        
        return lesson_plans
    
    except Exception as e:
        logger.error(f"Error listing lesson plans: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing lesson plans: {str(e)}"
        )


@router.get("/{id}", response_model=LessonPlanWithEvidence)
async def get_lesson_plan(
    id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a lesson plan by ID with any existing extracted evidence.
    """
    try:
        lesson_plan = db.query(LessonPlan).filter(LessonPlan.id == str(id)).first()
        
        if not lesson_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson plan not found"
            )
        
        # Get existing evidence from lesson_evidence table
        evidence_records = db.query(LessonEvidence).filter(
            LessonEvidence.lesson_id == str(id)
        ).all()
        
        # Organize evidence by GP
        evidence_dict = {
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
            if gp_key in evidence_dict:
                evidence_dict[gp_key].append(record.evidence_text)
        
        # Build response
        response_data = {
            **lesson_plan.__dict__,
            "evidence": evidence_dict
        }
        
        return LessonPlanWithEvidence(**response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting lesson plan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting lesson plan: {str(e)}"
        )


@router.post("/{id}/extract-evidence", response_model=LessonPlanWithEvidence)
async def extract_evidence_from_lesson_plan(
    id: UUID,
    db: Session = Depends(get_db)
):
    """
    Extract evidence from a lesson plan using AI analysis.
    Uses the existing AI Evidence Engine to analyze the lesson plan
    and save evidence to the lesson_evidence table.
    """
    try:
        # Get lesson plan
        lesson_plan = db.query(LessonPlan).filter(LessonPlan.id == str(id)).first()
        
        if not lesson_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson plan not found"
            )
        
        # Extract evidence using AI
        logger.info(f"Extracting evidence from lesson plan {id}")
        evidence_data = extract_lesson_evidence(lesson_plan.content_text)
        
        # Delete existing evidence for this lesson plan (to avoid duplicates)
        db.query(LessonEvidence).filter(LessonEvidence.lesson_id == str(id)).delete()
        
        # Store new evidence in database
        for gp_number in range(1, 7):
            gp_key = f"gp{gp_number}"
            evidence_items = evidence_data.get(gp_key, [])
            
            for evidence_text in evidence_items:
                db_evidence = LessonEvidence(
                    id=str(uuid.uuid4()),
                    lesson_id=str(id),
                    gp_number=gp_number,
                    evidence_text=evidence_text
                )
                db.add(db_evidence)
        
        db.commit()
        
        logger.info(f"Evidence extracted and saved for lesson plan {id}")
        
        # Return updated lesson plan with evidence
        return await get_lesson_plan(id, db)
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error extracting evidence: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting evidence: {str(e)}"
        )


@router.put("/{id}", response_model=LessonPlanResponse)
async def update_lesson_plan(
    id: UUID,
    lesson_plan_update: LessonPlanUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a lesson plan.
    """
    try:
        db_lesson_plan = db.query(LessonPlan).filter(LessonPlan.id == str(id)).first()
        
        if not db_lesson_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson plan not found"
            )
        
        # Update only provided fields
        update_data = lesson_plan_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_lesson_plan, field, value)
        
        db.commit()
        db.refresh(db_lesson_plan)
        
        return db_lesson_plan
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating lesson plan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating lesson plan: {str(e)}"
        )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_lesson_plan(
    id: UUID,
    db: Session = Depends(get_db)
):
    """
    Delete a lesson plan and its associated evidence.
    """
    try:
        db_lesson_plan = db.query(LessonPlan).filter(LessonPlan.id == str(id)).first()
        
        if not db_lesson_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson plan not found"
            )
        
        # Delete associated evidence
        db.query(LessonEvidence).filter(LessonEvidence.lesson_id == str(id)).delete()
        
        # Delete lesson plan
        db.delete(db_lesson_plan)
        db.commit()
        
        logger.info(f"Lesson plan deleted: {id}")
        
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting lesson plan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting lesson plan: {str(e)}"
        )




