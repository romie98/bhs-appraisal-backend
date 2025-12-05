"""Classes API router"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from typing import List
from uuid import UUID
from app.core.database import get_db
from app.modules.classes.models import Class, class_students
from app.modules.students.models import Student
from app.modules.classes.schemas import (
    ClassCreate,
    ClassUpdate,
    ClassResponse,
    StudentAddRequest,
    BulkStudentAddRequest,
    StudentInClassResponse
)

router = APIRouter()


@router.post("/", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    class_data: ClassCreate,
    db: Session = Depends(get_db)
):
    """Create a new class"""
    # Check if class with same name and year already exists
    existing = db.query(Class).filter(
        Class.name == class_data.name,
        Class.academic_year == class_data.academic_year
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A class with this name and academic year already exists"
        )
    
    db_class = Class(**class_data.model_dump())
    db.add(db_class)
    db.commit()
    db.refresh(db_class)
    
    # Get student count
    student_count = db.query(func.count(class_students.c.student_id)).filter(
        class_students.c.class_id == db_class.id
    ).scalar() or 0
    
    response = ClassResponse(
        id=db_class.id,
        name=db_class.name,
        academic_year=db_class.academic_year,
        created_at=db_class.created_at,
        student_count=student_count
    )
    return response


@router.get("/", response_model=List[ClassResponse])
async def list_classes(
    db: Session = Depends(get_db)
):
    """List all classes"""
    classes = db.query(Class).order_by(Class.created_at.desc()).all()
    
    result = []
    for cls in classes:
        student_count = db.query(func.count(class_students.c.student_id)).filter(
            class_students.c.class_id == cls.id
        ).scalar() or 0
        
        result.append(ClassResponse(
            id=cls.id,
            name=cls.name,
            academic_year=cls.academic_year,
            created_at=cls.created_at,
            student_count=student_count
        ))
    
    return result


@router.get("/{id}", response_model=ClassResponse)
async def get_class(
    id: UUID,
    db: Session = Depends(get_db)
):
    """Get class details"""
    db_class = db.query(Class).filter(Class.id == str(id)).first()
    
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    student_count = db.query(func.count(class_students.c.student_id)).filter(
        class_students.c.class_id == db_class.id
    ).scalar() or 0
    
    return ClassResponse(
        id=db_class.id,
        name=db_class.name,
        academic_year=db_class.academic_year,
        created_at=db_class.created_at,
        student_count=student_count
    )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class(
    id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a class"""
    db_class = db.query(Class).filter(Class.id == str(id)).first()
    
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    db.delete(db_class)
    db.commit()
    return None


@router.get("/{id}/students", response_model=List[StudentInClassResponse])
async def list_class_students(
    id: UUID,
    db: Session = Depends(get_db)
):
    """List all students in a class"""
    db_class = db.query(Class).filter(Class.id == str(id)).first()
    
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Get student IDs from class_students junction table
    class_students_list = db.query(class_students).filter(
        class_students.c.class_id == str(id)
    ).all()
    
    if not class_students_list:
        return []
    
    student_ids = [row.student_id for row in class_students_list]
    
    # Get students by IDs
    students = db.query(Student).filter(
        Student.id.in_(student_ids)
    ).order_by(Student.last_name, Student.first_name).all()
    
    return students


@router.post("/{id}/students", response_model=StudentInClassResponse, status_code=status.HTTP_201_CREATED)
async def add_student_to_class(
    id: UUID,
    request: StudentAddRequest,
    db: Session = Depends(get_db)
):
    """Add a single student to a class"""
    db_class = db.query(Class).filter(Class.id == str(id)).first()
    
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    student = db.query(Student).filter(Student.id == str(request.student_id)).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    # Check if student is already in class
    existing = db.execute(
        select(class_students).where(
            class_students.c.class_id == str(id),
            class_students.c.student_id == str(request.student_id)
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is already in this class"
        )
    
    # Add student to class
    db.execute(
        class_students.insert().values(
            class_id=str(id),
            student_id=str(request.student_id)
        )
    )
    db.commit()
    
    return student


@router.post("/{id}/students/bulk", response_model=List[StudentInClassResponse], status_code=status.HTTP_201_CREATED)
async def bulk_add_students_to_class(
    id: UUID,
    request: BulkStudentAddRequest,
    db: Session = Depends(get_db)
):
    """Bulk add students to a class"""
    db_class = db.query(Class).filter(Class.id == str(id)).first()
    
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    created_students = []
    
    for student_string in request.students:
        student_string = student_string.strip()
        if not student_string:
            continue
        
        # Parse student string
        # Format 1: "John Brown, M, 10-9"
        # Format 2: "John Brown"
        parts = [p.strip() for p in student_string.split(',')]
        
        if len(parts) >= 1:
            name = parts[0]
            name_parts = name.split()
            
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = ' '.join(name_parts[1:])
            else:
                first_name = name
                last_name = ""
            
            # Extract grade
            grade = request.default_grade
            if len(parts) >= 3:
                grade = parts[2] if parts[2] else request.default_grade
            elif len(parts) >= 2 and parts[1] and parts[1] not in ['M', 'F', 'Male', 'Female']:
                # If second part is not a gender, it might be grade
                if '-' in parts[1]:
                    grade = parts[1]
            
            # Extract gender
            gender = request.default_gender
            if len(parts) >= 2:
                gender_part = parts[1].upper()
                if gender_part in ['M', 'MALE']:
                    gender = 'Male'
                elif gender_part in ['F', 'FEMALE']:
                    gender = 'Female'
            
            # Check if student already exists
            existing_student = db.query(Student).filter(
                Student.first_name == first_name,
                Student.last_name == last_name,
                Student.grade == grade
            ).first()
            
            if existing_student:
                student = existing_student
            else:
                # Create new student
                student = Student(
                    first_name=first_name,
                    last_name=last_name,
                    grade=grade or "Unknown",
                    gender=gender
                )
                db.add(student)
                db.flush()  # Get the ID without committing
            
            # Check if student is already in class
            existing_link = db.execute(
                select(class_students).where(
                    class_students.c.class_id == str(id),
                    class_students.c.student_id == student.id
                )
            ).first()
            
            if not existing_link:
                # Add student to class
                db.execute(
                    class_students.insert().values(
                        class_id=str(id),
                        student_id=student.id
                    )
                )
                created_students.append(student)
    
    db.commit()
    
    # Refresh all students
    for student in created_students:
        db.refresh(student)
    
    return created_students


@router.delete("/{id}/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_student_from_class(
    id: UUID,
    student_id: UUID,
    db: Session = Depends(get_db)
):
    """Remove a student from a class"""
    db_class = db.query(Class).filter(Class.id == str(id)).first()
    
    if not db_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Check if student is in class
    from sqlalchemy import select
    existing = db.execute(
        select(class_students).where(
            class_students.c.class_id == str(id),
            class_students.c.student_id == str(student_id)
        )
    ).first()
    
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student is not in this class"
        )
    
    # Remove student from class
    db.execute(
        class_students.delete().where(
            class_students.c.class_id == str(id),
            class_students.c.student_id == str(student_id)
        )
    )
    db.commit()
    return None

