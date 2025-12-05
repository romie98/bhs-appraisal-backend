"""Assessments API router"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import List, Optional
from uuid import UUID
from app.core.database import get_db
from app.modules.assessments.models import Assessment, AssessmentScore
from app.modules.students.models import Student
from app.modules.classes.models import class_students
from app.modules.assessments.schemas import (
    AssessmentCreate,
    AssessmentUpdate,
    AssessmentResponse,
    AssessmentScoreCreate,
    AssessmentScoreUpdate,
    AssessmentScoreResponse,
    BulkScoreCreate,
    BulkScoreImportRequest,
    BulkScoreImportResponse,
    StudentWithScore
)

router = APIRouter()


# Assessment endpoints
@router.post("/", response_model=AssessmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    assessment: AssessmentCreate,
    db: Session = Depends(get_db)
):
    """Create a new assessment"""
    from app.modules.classes.models import class_students
    
    assessment_dict = assessment.model_dump(exclude={'class_id'})
    
    # If class_id is provided, get the grade from the class students
    if assessment.class_id:
        class_students_list = db.query(class_students).filter(
            class_students.c.class_id == str(assessment.class_id)
        ).all()
        student_ids = [row.student_id for row in class_students_list]
        
        if student_ids:
            students = db.query(Student).filter(Student.id.in_(student_ids)).limit(1).all()
            if students:
                assessment_dict['grade'] = students[0].grade
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Class has no students. Cannot create assessment."
                )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Class has no students. Cannot create assessment."
            )
    elif not assessment_dict.get('grade'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either class_id or grade must be provided"
        )
    
    db_assessment = Assessment(**assessment_dict)
    db.add(db_assessment)
    db.commit()
    db.refresh(db_assessment)
    return db_assessment


@router.get("/", response_model=List[AssessmentResponse])
async def get_assessments(
    grade: Optional[str] = Query(None, description="Filter by grade (deprecated, use class_id)"),
    class_id: Optional[UUID] = Query(None, description="Filter by class ID"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all assessments, optionally filtered by grade or class_id"""
    
    query = db.query(Assessment)
    
    if class_id:
        # Get students in the class
        class_students_list = db.query(class_students).filter(
            class_students.c.class_id == str(class_id)
        ).all()
        student_ids = [row.student_id for row in class_students_list]
        
        if student_ids:
            # Get assessments for students in this class
            # We need to get the grade from the students, then filter assessments
            students = db.query(Student).filter(Student.id.in_(student_ids)).all()
            grades = set([s.grade for s in students])
            if grades:
                query = query.filter(Assessment.grade.in_(grades))
            else:
                # No students in class, return empty
                return []
        else:
            # No students in class, return empty
            return []
    elif grade:
        # Legacy support for grade filtering
        query = query.filter(Assessment.grade == grade)
    
    assessments = query.offset(skip).limit(limit).all()
    return assessments


@router.get("/{id}", response_model=AssessmentResponse)
async def get_assessment(id: UUID, db: Session = Depends(get_db)):
    """Get an assessment by ID"""
    assessment = db.query(Assessment).filter(Assessment.id == str(id)).first()
    
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    return assessment


@router.put("/{id}", response_model=AssessmentResponse)
async def update_assessment(
    id: UUID,
    assessment_update: AssessmentUpdate,
    db: Session = Depends(get_db)
):
    """Update an assessment"""
    db_assessment = db.query(Assessment).filter(Assessment.id == str(id)).first()
    
    if not db_assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    # Update only provided fields
    update_data = assessment_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_assessment, field, value)
    
    db.commit()
    db.refresh(db_assessment)
    return db_assessment


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assessment(id: UUID, db: Session = Depends(get_db)):
    """Delete an assessment"""
    db_assessment = db.query(Assessment).filter(Assessment.id == str(id)).first()
    
    if not db_assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    db.delete(db_assessment)
    db.commit()
    return None


# Assessment Score endpoints
@router.post("/scores/bulk", response_model=List[AssessmentScoreResponse], status_code=status.HTTP_201_CREATED)
async def create_bulk_scores(
    bulk_data: BulkScoreCreate,
    db: Session = Depends(get_db)
):
    """Add scores for an entire class"""
    assessment_id_str = str(bulk_data.assessment_id)
    # Validate assessment exists
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id_str).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    created_scores = []
    
    for score_data in bulk_data.scores:
        student_id_str = str(score_data.student_id)
        # Validate student exists
        student = db.query(Student).filter(Student.id == student_id_str).first()
        if not student:
            continue
        
        # Check if score already exists
        existing = db.query(AssessmentScore).filter(
            and_(
                AssessmentScore.assessment_id == assessment_id_str,
                AssessmentScore.student_id == student_id_str
            )
        ).first()
        
        if existing:
            # Update existing score
            existing.score = score_data.score
            existing.comment = score_data.comment
            created_scores.append(existing)
        else:
            # Create new score
            db_score = AssessmentScore(
                assessment_id=assessment_id_str,
                student_id=student_id_str,
                score=score_data.score,
                comment=score_data.comment
            )
            db.add(db_score)
            created_scores.append(db_score)
    
    db.commit()
    
    # Refresh all scores
    for score in created_scores:
        db.refresh(score)
    
    return created_scores


@router.get("/scores/by-assessment/{assessment_id}", response_model=List[AssessmentScoreResponse])
async def get_scores_by_assessment(
    assessment_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all scores for a specific assessment"""
    assessment_id_str = str(assessment_id)
    # Validate assessment exists
    assessment = db.query(Assessment).filter(Assessment.id == assessment_id_str).first()
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment not found"
        )
    
    scores = db.query(AssessmentScore).filter(
        AssessmentScore.assessment_id == assessment_id_str
    ).all()
    
    return scores


@router.get("/scores/by-student/{student_id}", response_model=List[AssessmentScoreResponse])
async def get_scores_by_student(
    student_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all scores for a specific student"""
    student_id_str = str(student_id)
    # Validate student exists
    student = db.query(Student).filter(Student.id == student_id_str).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    scores = db.query(AssessmentScore).filter(
        AssessmentScore.student_id == student_id_str
    ).all()
    
    return scores


@router.put("/scores/{id}", response_model=AssessmentScoreResponse)
async def update_score(
    id: UUID,
    score_update: AssessmentScoreUpdate,
    db: Session = Depends(get_db)
):
    """Update an assessment score"""
    db_score = db.query(AssessmentScore).filter(AssessmentScore.id == str(id)).first()
    
    if not db_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment score not found"
        )
    
    # Update only provided fields
    update_data = score_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_score, field, value)
    
    db.commit()
    db.refresh(db_score)
    return db_score


@router.delete("/scores/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_score(id: UUID, db: Session = Depends(get_db)):
    """Delete an assessment score"""
    db_score = db.query(AssessmentScore).filter(AssessmentScore.id == str(id)).first()
    
    if not db_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment score not found"
        )
    
    db.delete(db_score)
    db.commit()
    return None

