"""Evidence file upload API router"""
import uuid
import json
import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.sql import func

from app.core.database import get_db
from app.modules.auth.models import User
from app.modules.evidence.models import Evidence
from app.services.auth_dependency import get_current_user
from app.services.supabase_service import upload_bytes_to_supabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/evidence", tags=["Evidence"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    file: UploadFile = File(...),
    gp_section: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload evidence file to Supabase Storage.
    
    Args:
        file: The file to upload
        gp_section: Optional GP section (GP1, GP2, etc.)
        description: Optional description of the evidence
        current_user: Authenticated user
        db: Database session
    
    Returns:
        Evidence record with Supabase URL
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        # Read file content
        content = await file.read()
        
        # Determine folder based on GP section
        folder = "evidence"
        if gp_section:
            folder = f"evidence/{gp_section.lower()}"
        
        # Upload to Supabase
        supabase_result = upload_bytes_to_supabase(
            file_bytes=content,
            filename=file.filename,
            folder=folder,
            content_type=file.content_type or "application/octet-stream"
        )
        
        if "error" in supabase_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file to Supabase: {supabase_result.get('error')}"
            )
        
        supabase_path = supabase_result.get("path")
        supabase_url = supabase_result.get("url")
        
        # Create database record
        evidence_record = Evidence(
            id=str(uuid.uuid4()),
            teacher_id=current_user.id,
            gp_section=gp_section,
            description=description,
            filename=file.filename,
            supabase_path=supabase_path,
            supabase_url=supabase_url,
        )
        
        db.add(evidence_record)
        db.commit()
        db.refresh(evidence_record)
        
        logger.info(f"Evidence uploaded: {supabase_path} by user {current_user.id}")
        
        return {
            "id": evidence_record.id,
            "teacher_id": evidence_record.teacher_id,
            "gp_section": evidence_record.gp_section,
            "description": evidence_record.description,
            "filename": evidence_record.filename,
            "supabase_path": evidence_record.supabase_path,
            "supabase_url": evidence_record.supabase_url,
            "uploaded_at": evidence_record.uploaded_at.isoformat(),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading evidence: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload evidence: {str(e)}"
        )


@router.get("/", status_code=status.HTTP_200_OK)
async def list_evidence(
    gp_section: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all evidence files for the current user.
    
    Args:
        gp_section: Optional filter by GP section
        current_user: Authenticated user
        db: Database session
    
    Returns:
        List of evidence records
    """
    try:
        query = db.query(Evidence).filter(Evidence.teacher_id == current_user.id)
        
        if gp_section:
            query = query.filter(Evidence.gp_section == gp_section.upper())
        
        evidence_list = query.order_by(Evidence.uploaded_at.desc()).all()
        
        return [
            {
                "id": record.id,
                "teacher_id": record.teacher_id,
                "gp_section": record.gp_section,
                "description": record.description,
                "filename": record.filename,
                "supabase_path": record.supabase_path,
                "supabase_url": record.supabase_url,
                "uploaded_at": record.uploaded_at.isoformat(),
            }
            for record in evidence_list
        ]
    
    except Exception as e:
        logger.error(f"Error listing evidence: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list evidence: {str(e)}"
        )


@router.get("/{evidence_id}", status_code=status.HTTP_200_OK)
async def get_evidence(
    evidence_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific evidence record.
    
    Args:
        evidence_id: Evidence record ID
        current_user: Authenticated user
        db: Database session
    
    Returns:
        Evidence record
    """
    try:
        record = db.query(Evidence).filter(
            Evidence.id == evidence_id,
            Evidence.teacher_id == current_user.id
        ).first()
        
        if not record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence not found"
            )
        
        return {
            "id": record.id,
            "teacher_id": record.teacher_id,
            "gp_section": record.gp_section,
            "description": record.description,
            "filename": record.filename,
            "supabase_path": record.supabase_path,
            "supabase_url": record.supabase_url,
            "uploaded_at": record.uploaded_at.isoformat(),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting evidence: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get evidence: {str(e)}"
        )




