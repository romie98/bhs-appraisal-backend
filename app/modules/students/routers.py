"""Students API router"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.core.database import get_db
from app.modules.students.models import Student
from app.modules.students.schemas import (
    StudentCreate,
    StudentUpdate,
    StudentResponse
)

router = APIRouter()


@router.get("/", response_model=List[StudentResponse])
async def get_students(
    grade: str = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all students, optionally filtered by grade"""
    query = db.query(Student)
    
    if grade:
        query = query.filter(Student.grade == grade)
    
    students = query.offset(skip).limit(limit).all()
    return students


@router.get("/{id}", response_model=StudentResponse)
async def get_student(id: UUID, db: Session = Depends(get_db)):
    """Get a student by ID"""
    student = db.query(Student).filter(Student.id == str(id)).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    return student


@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db)
):
    """Create a new student"""
    db_student = Student(**student.model_dump())
    db.add(db_student)
    db.commit()
    db.refresh(db_student)
    return db_student


@router.put("/{id}", response_model=StudentResponse)
async def update_student(
    id: UUID,
    student_update: StudentUpdate,
    db: Session = Depends(get_db)
):
    """Update a student"""
    db_student = db.query(Student).filter(Student.id == str(id)).first()
    
    if not db_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Update only provided fields
    update_data = student_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_student, field, value)
    
    db.commit()
    db.refresh(db_student)
    return db_student


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(id: UUID, db: Session = Depends(get_db)):
    """Delete a student"""
    db_student = db.query(Student).filter(Student.id == str(id)).first()
    
    if not db_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    db.delete(db_student)
    db.commit()
    return None

