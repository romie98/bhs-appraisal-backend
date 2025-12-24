"""Log Book API router"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional, List
from uuid import UUID
from datetime import datetime, date
from app.core.database import get_db
from app.modules.auth.models import User
from app.services.auth_dependency import get_current_user
from app.modules.subscriptions.guards import require_premium
from app.modules.logbook.models import LogEntry, LogEntryType
from app.modules.logbook.schemas import (
    LogEntryCreate,
    LogEntryUpdate,
    LogEntryResponse
)

router = APIRouter()


@router.get("/", response_model=List[LogEntryResponse])
async def list_log_entries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    require_premium(current_user)

    return (
        db.query(LogEntry)
        .filter(LogEntry.user_id == current_user.id)
        .order_by(LogEntry.created_at.desc())
        .all()
    )


@router.get("/{id}", response_model=LogEntryResponse)
async def get_log_entry(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a single log entry by ID - scoped to current user only"""
    # HARD filter: Only return entry if it belongs to current user
    # No OR conditions, no NULL checks, no joins
    entry = db.query(LogEntry).filter(
        LogEntry.id == str(id),
        LogEntry.user_id == current_user.id
    ).first()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log entry not found"
        )
    
    # Eager load relationships
    if entry.student_id:
        from app.modules.students.models import Student
        entry.student = db.query(Student).filter(Student.id == entry.student_id).first()
    if entry.class_id:
        from app.modules.classes.models import Class
        entry.class_obj = db.query(Class).filter(Class.id == entry.class_id).first()
    
    return entry


@router.post("/", response_model=LogEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_log_entry(
    entry: LogEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new log entry.
    
    Requires premium subscription.
    """
    # Gate behind premium subscription
    require_premium(current_user)
    
    import uuid
    
    # Validate entry type
    try:
        entry_type_enum = LogEntryType(entry.entry_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid entry type: {entry.entry_type}"
        )

    # Validate student exists if provided
    if entry.student_id:
        from app.modules.students.models import Student
        student = db.query(Student).filter(Student.id == str(entry.student_id)).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )

    # Validate class exists if provided
    if entry.class_id:
        from app.modules.classes.models import Class
        class_obj = db.query(Class).filter(Class.id == str(entry.class_id)).first()
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found"
            )

    # Create log entry with user_id for data isolation
    db_entry = LogEntry(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        title=entry.title,
        content=entry.content,
        entry_type=entry_type_enum,
        date=entry.date,
        student_id=str(entry.student_id) if entry.student_id else None,
        class_id=str(entry.class_id) if entry.class_id else None
    )

    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)

    return db_entry


@router.put("/{id}", response_model=LogEntryResponse)
async def update_log_entry(
    id: UUID,
    entry_update: LogEntryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a log entry - scoped to current user only"""
    # HARD filter: Only update entry if it belongs to current user
    db_entry = db.query(LogEntry).filter(
        LogEntry.id == str(id),
        LogEntry.user_id == current_user.id
    ).first()
    
    if not db_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log entry not found"
        )

    # Update only provided fields
    update_data = entry_update.model_dump(exclude_unset=True)
    
    # Validate entry type if provided
    if "entry_type" in update_data:
        try:
            entry_type_enum = LogEntryType(update_data["entry_type"])
            update_data["entry_type"] = entry_type_enum
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid entry type: {update_data['entry_type']}"
            )

    # Validate student exists if provided
    if "student_id" in update_data and update_data["student_id"]:
        from app.modules.students.models import Student
        student = db.query(Student).filter(Student.id == str(update_data["student_id"])).first()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Student not found"
            )
        update_data["student_id"] = str(update_data["student_id"])
    elif "student_id" in update_data and update_data["student_id"] is None:
        update_data["student_id"] = None

    # Validate class exists if provided
    if "class_id" in update_data and update_data["class_id"]:
        from app.modules.classes.models import Class
        class_obj = db.query(Class).filter(Class.id == str(update_data["class_id"])).first()
        if not class_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Class not found"
            )
        update_data["class_id"] = str(update_data["class_id"])
    elif "class_id" in update_data and update_data["class_id"] is None:
        update_data["class_id"] = None

    for field, value in update_data.items():
        setattr(db_entry, field, value)

    db.commit()
    db.refresh(db_entry)

    return db_entry


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_log_entry(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a log entry - scoped to current user only"""
    # HARD filter: Only delete entry if it belongs to current user
    db_entry = db.query(LogEntry).filter(
        LogEntry.id == str(id),
        LogEntry.user_id == current_user.id
    ).first()
    
    if not db_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log entry not found"
        )

    db.delete(db_entry)
    db.commit()
    return None

