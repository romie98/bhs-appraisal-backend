"""Register API router"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List, Optional
from uuid import UUID
from datetime import date, timedelta
from app.core.database import get_db
from app.modules.auth.models import User
from app.services.auth_dependency import get_current_user
from app.modules.register.models import RegisterRecord, RegisterStatus, HomeroomRegister
from app.modules.students.models import Student
from app.modules.classes.models import class_students, Class
from app.modules.register.schemas import (
    RegisterRecordCreate,
    RegisterRecordUpdate,
    RegisterRecordResponse,
    BulkRegisterCreate,
    RegisterSummaryResponse,
    HomeroomRegisterCreate,
    HomeroomRegisterOut
)

router = APIRouter()


@router.get("/", response_model=List[RegisterRecordResponse])
async def get_register_records(
    current_user: User = Depends(get_current_user),
    grade: Optional[str] = Query(None, description="Filter by grade (deprecated, use class_id)"),
    class_id: Optional[UUID] = Query(None, description="Filter by class ID"),
    date: Optional[date] = Query(None),
    student_id: Optional[UUID] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get register records, optionally filtered by class_id, grade, and/or date"""
    query = db.query(RegisterRecord)
    
    if student_id:
        query = query.filter(RegisterRecord.student_id == str(student_id))
    
    if date:
        query = query.filter(RegisterRecord.date == date)
    
    if class_id:
        # Get students in the class
        class_students_list = db.query(class_students).filter(
            class_students.c.class_id == str(class_id)
        ).all()
        student_ids = [row.student_id for row in class_students_list]
        
        if student_ids:
            query = query.filter(RegisterRecord.student_id.in_(student_ids))
        else:
            # No students in class, return empty
            return []
    elif grade:
        # Legacy support for grade filtering
        query = query.join(Student).filter(Student.grade == grade)
    
    records = query.offset(skip).limit(limit).all()
    return records


@router.post("/", response_model=RegisterRecordResponse, status_code=status.HTTP_201_CREATED)
async def create_register_record(
    record: RegisterRecordCreate,
    db: Session = Depends(get_db)
):
    """Create a new register record"""
    # Validate student exists
    student = db.query(Student).filter(Student.id == str(record.student_id)).first()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    record_dict = record.model_dump()
    record_dict['student_id'] = str(record_dict['student_id'])
    db_record = RegisterRecord(**record_dict)
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


@router.post("/bulk", response_model=List[RegisterRecordResponse], status_code=status.HTTP_201_CREATED)
async def create_bulk_register_records(
    bulk_data: BulkRegisterCreate,
    db: Session = Depends(get_db)
):
    """Create register records for an entire class"""
    # Get all students - support both grade (legacy) and class_id
    if bulk_data.class_id:
        # Get students from class
        class_students_list = db.query(class_students).filter(
            class_students.c.class_id == str(bulk_data.class_id)
        ).all()
        student_ids = [row.student_id for row in class_students_list]
        students = db.query(Student).filter(Student.id.in_(student_ids)).all() if student_ids else []
    elif bulk_data.grade:
        # Legacy: Get all students in the grade
        students = db.query(Student).filter(Student.grade == bulk_data.grade).all()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either class_id or grade must be provided"
        )
    
    if not students:
        error_msg = f"No students found for {'class' if bulk_data.class_id else 'grade'} {bulk_data.class_id or bulk_data.grade}"
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error_msg
        )
    
    created_records = []
    
    # Create records from provided data
    for record_data in bulk_data.records:
        student_id_str = str(record_data.student_id)
        # Validate student exists
        student = db.query(Student).filter(Student.id == student_id_str).first()
        if not student:
            continue
        
        # Use date from record_data if provided, otherwise use bulk_data.date
        record_date = record_data.date if hasattr(record_data, 'date') and record_data.date else bulk_data.date
        
        # Check if record already exists for this student and date
        existing = db.query(RegisterRecord).filter(
            and_(
                RegisterRecord.student_id == student_id_str,
                RegisterRecord.date == record_date
            )
        ).first()
        
        if existing:
            # Update existing record
            existing.status = record_data.status
            existing.comment = record_data.comment if hasattr(record_data, 'comment') else None
            created_records.append(existing)
        else:
            # Create new record
            db_record = RegisterRecord(
                student_id=student_id_str,
                date=record_date,
                status=record_data.status,
                comment=record_data.comment if hasattr(record_data, 'comment') else None
            )
            db.add(db_record)
            created_records.append(db_record)
    
    db.commit()
    
    # Refresh all records
    for record in created_records:
        db.refresh(record)
    
    return created_records


@router.put("/{id}", response_model=RegisterRecordResponse)
async def update_register_record(
    id: UUID,
    record_update: RegisterRecordUpdate,
    db: Session = Depends(get_db)
):
    """Update a register record"""
    db_record = db.query(RegisterRecord).filter(RegisterRecord.id == str(id)).first()
    
    if not db_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Register record not found"
        )
    
    # Update only provided fields
    update_data = record_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_record, field, value)
    
    db.commit()
    db.refresh(db_record)
    return db_record


@router.get("/summary/weekly", response_model=List[RegisterSummaryResponse])
async def get_weekly_summary(
    grade: str = Query(..., description="Grade to filter by (e.g., '10-9')"),
    week_start: Optional[date] = Query(None, description="Start date of week (defaults to current week)"),
    db: Session = Depends(get_db)
):
    """Get weekly attendance summary for a grade"""
    if not week_start:
        # Default to Monday of current week
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
    
    week_end = week_start + timedelta(days=6)
    
    # Get all students in the grade
    students = db.query(Student).filter(Student.grade == grade).all()
    student_ids = [s.id for s in students]
    
    if not student_ids:
        return []
    
    # Get records for the week
    records = db.query(RegisterRecord).filter(
        and_(
            RegisterRecord.student_id.in_(student_ids),
            RegisterRecord.date >= week_start,
            RegisterRecord.date <= week_end
        )
    ).all()
    
    # Group by date
    summary_by_date = {}
    for record in records:
        if record.date not in summary_by_date:
            summary_by_date[record.date] = {
                "date": record.date,
                "total_students": len(students),
                "present": 0,
                "absent": 0,
                "late": 0,
                "excused": 0
            }
        
        summary_by_date[record.date][record.status.value.lower()] += 1
    
    # Calculate attendance rates
    summaries = []
    for date_key, summary in summary_by_date.items():
        total_present = summary["present"] + summary["late"] + summary["excused"]
        summary["attendance_rate"] = (total_present / summary["total_students"] * 100) if summary["total_students"] > 0 else 0
        summaries.append(RegisterSummaryResponse(**summary))
    
    return sorted(summaries, key=lambda x: x.date)


@router.get("/summary/monthly", response_model=List[RegisterSummaryResponse])
async def get_monthly_summary(
    grade: Optional[str] = Query(None, description="Grade to filter by (deprecated, use class_id)"),
    class_id: Optional[UUID] = Query(None, description="Class ID to filter by"),
    year: Optional[int] = Query(None, description="Year (defaults to current year)"),
    month: Optional[int] = Query(None, description="Month (defaults to current month)"),
    db: Session = Depends(get_db)
):
    """Get monthly attendance summary for a class or grade"""
    if not year:
        year = date.today().year
    if not month:
        month = date.today().month
    
    month_start = date(year, month, 1)
    # Get last day of month
    if month == 12:
        month_end = date(year, month, 31)
    else:
        month_end = date(year, month + 1, 1) - timedelta(days=1)
    
    # Get all students in the class or grade
    if class_id:
        class_students_list = db.query(class_students).filter(
            class_students.c.class_id == str(class_id)
        ).all()
        student_ids = [row.student_id for row in class_students_list]
        students = db.query(Student).filter(Student.id.in_(student_ids)).all() if student_ids else []
    elif grade:
        students = db.query(Student).filter(Student.grade == grade).all()
        student_ids = [s.id for s in students]
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either class_id or grade must be provided"
        )
    
    if not student_ids:
        return []
    
    # Get records for the month
    records = db.query(RegisterRecord).filter(
        and_(
            RegisterRecord.student_id.in_(student_ids),
            RegisterRecord.date >= month_start,
            RegisterRecord.date <= month_end
        )
    ).all()
    
    # Group by date
    summary_by_date = {}
    for record in records:
        if record.date not in summary_by_date:
            summary_by_date[record.date] = {
                "date": record.date,
                "total_students": len(students),
                "present": 0,
                "absent": 0,
                "late": 0,
                "excused": 0
            }
        
        summary_by_date[record.date][record.status.value.lower()] += 1
    
    # Calculate attendance rates
    summaries = []
    for date_key, summary in summary_by_date.items():
        total_present = summary["present"] + summary["late"] + summary["excused"]
        summary["attendance_rate"] = (total_present / summary["total_students"] * 100) if summary["total_students"] > 0 else 0
        summaries.append(RegisterSummaryResponse(**summary))
    
    return sorted(summaries, key=lambda x: x.date)


# --------------------------------------------------
# Homeroom Register Endpoints
# --------------------------------------------------

def serialize_homeroom_register(r: HomeroomRegister) -> dict:
    """Serialize homeroom register with computed totals"""
    return {
        "id": r.id,
        "date": r.date,
        "morning_boys": r.morning_boys,
        "morning_girls": r.morning_girls,
        "morning_total": r.morning_boys + r.morning_girls,
        "afternoon_boys": r.afternoon_boys,
        "afternoon_girls": r.afternoon_girls,
        "afternoon_total": r.afternoon_boys + r.afternoon_girls,
    }


@router.post("/homeroom", response_model=HomeroomRegisterOut, status_code=status.HTTP_200_OK)
async def create_or_update_homeroom(
    payload: HomeroomRegisterCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create or update a homeroom register entry.
    
    Ensures the classroom is marked as homeroom.
    If a register already exists for the date, it will be updated.
    """
    # Ensure classroom exists and is marked as homeroom
    classroom = db.query(Class).filter(
        Class.id == str(payload.classroom_id),
        Class.is_homeroom == True
    ).first()
    
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Classroom is not marked as a homeroom"
        )
    
    # Check if register already exists for this date
    register = db.query(HomeroomRegister).filter(
        HomeroomRegister.classroom_id == str(payload.classroom_id),
        HomeroomRegister.date == payload.date
    ).first()
    
    if not register:
        # Create new register
        register = HomeroomRegister(
            teacher_id=current_user.id,
            classroom_id=str(payload.classroom_id),
            date=payload.date,
            morning_boys=payload.morning_boys,
            morning_girls=payload.morning_girls,
            afternoon_boys=payload.afternoon_boys,
            afternoon_girls=payload.afternoon_girls,
        )
        db.add(register)
    else:
        # Update existing register
        register.morning_boys = payload.morning_boys
        register.morning_girls = payload.morning_girls
        register.afternoon_boys = payload.afternoon_boys
        register.afternoon_girls = payload.afternoon_girls
    
    db.commit()
    db.refresh(register)
    
    return serialize_homeroom_register(register)


@router.get("/homeroom/{classroom_id}", response_model=List[HomeroomRegisterOut])
async def list_homeroom_registers(
    classroom_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List all homeroom register entries for a specific classroom.
    
    Only returns registers for classrooms that are marked as homeroom.
    """
    # Verify classroom exists and is homeroom
    classroom = db.query(Class).filter(
        Class.id == str(classroom_id),
        Class.is_homeroom == True
    ).first()
    
    if not classroom:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Homeroom classroom not found"
        )
    
    # Get all registers for this classroom
    registers = db.query(HomeroomRegister).filter(
        HomeroomRegister.classroom_id == str(classroom_id),
        HomeroomRegister.teacher_id == current_user.id
    ).order_by(HomeroomRegister.date.desc()).all()
    
    return [serialize_homeroom_register(r) for r in registers]
