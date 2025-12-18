"""Photo Evidence Library API router"""
import uuid
import json
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.auth.models import User
from app.services.auth_dependency import get_current_user
from app.core.features import require_feature
from app.modules.photo_library.models import PhotoEvidence
from app.modules.photo_library.schemas import PhotoEvidenceResponse, PhotoEvidenceListItem
from app.modules.photo_library.services import save_photo_file, extract_text_from_image, get_image_extension
from app.services.ai_service import analyze_photo_evidence
from app.services.supabase_service import upload_file_to_supabase, get_public_url

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=PhotoEvidenceResponse, status_code=status.HTTP_201_CREATED)
async def upload_photo_evidence(
    file: UploadFile = File(...),
    current_user: User = Depends(require_feature("AI_OCR")),
    db: Session = Depends(get_db),
):
    """Upload a photo, run OCR + AI, and store GP recommendations. Requires AI_OCR feature (PRO or SCHOOL plan)."""
    try:
        ext = get_image_extension(file.filename)
        allowed = [".jpg", ".jpeg", ".png", ".heic"]
        if ext not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Allowed types: {', '.join(allowed)}",
            )

        # Read file content
        content = await file.read()
        
        # Run OCR on the content before uploading (works with bytes)
        ocr_text = ""
        try:
            # Save temporarily for OCR, then delete
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                tmp_file.write(content)
                tmp_path = tmp_file.name
            
            try:
                ocr_text = extract_text_from_image(tmp_path)
                
                # Log AI OCR activity if successful
                if ocr_text and ocr_text.strip():
                    try:
                        from app.modules.admin_activity.services import log_activity
                        log_activity(
                            db,
                            user=current_user,
                            action="AI_OCR",
                            resource=file.filename,
                            metadata={"text_length": len(ocr_text)}
                        )
                    except Exception:
                        pass  # Don't break upload if activity logging fails
            finally:
                # Clean up temp file
                import os
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
        except Exception as e:
            # Log but don't fail upload; allow manual evidence later
            logger.warning(f"OCR failed: {e}")
        
        # Upload to Supabase Storage
        from app.services.supabase_service import upload_bytes_to_supabase
        supabase_result = upload_bytes_to_supabase(
            file_bytes=content,
            filename=file.filename,
            folder="evidence",
            content_type=file.content_type or "image/jpeg"
        )
        supabase_url = None
        supabase_path = None
        file_path = None
        
        if "error" not in supabase_result:
            supabase_path = supabase_result.get("path")
            supabase_url = supabase_result.get("url")
            logger.info(f"File uploaded to Supabase: {supabase_path}, URL: {supabase_url}")
        else:
            # Fallback to local storage
            logger.warning(f"Supabase upload failed, using local storage: {supabase_result.get('error')}")
            file_path = save_photo_file(content, file.filename, current_user.id)

        # Run AI analysis if we have some text
        gp_recommendations = {}
        gp_subsections = {}
        if ocr_text and ocr_text.strip():
            try:
                ai_result = analyze_photo_evidence(ocr_text)
                # Extract subsections structure
                gp_subsections = {}
                for gp_key in ["GP1", "GP2", "GP3", "GP4", "GP5", "GP6"]:
                    gp_data = ai_result.get(gp_key, {})
                    if isinstance(gp_data, dict):
                        subsections = gp_data.get("subsections", [])
                        justifications = gp_data.get("justifications", {})
                        gp_subsections[gp_key] = {
                            "subsections": subsections,
                            "justifications": justifications
                        }
                    else:
                        gp_subsections[gp_key] = {
                            "subsections": [],
                            "justifications": {}
                        }
                # Keep backward compatibility: extract simple GP recommendations
                gp_recommendations = {}
                for gp_key in ["GP1", "GP2", "GP3", "GP4", "GP5", "GP6"]:
                    gp_data = ai_result.get(gp_key, {})
                    if isinstance(gp_data, dict):
                        justifications = gp_data.get("justifications", {})
                        # Convert justifications to list for backward compatibility
                        gp_recommendations[gp_key] = list(justifications.values()) if justifications else []
                    else:
                        gp_recommendations[gp_key] = []
            except Exception as e:
                logger.error(f"AI analysis failed for photo {file_path}: {e}", exc_info=True)
                gp_recommendations = {f"GP{i}": [] for i in range(1, 7)}
                gp_subsections = {f"GP{i}": {"subsections": [], "justifications": {}} for i in range(1, 7)}

        # Store in DB (JSON columns accept dicts directly)
        record = PhotoEvidence(
            id=str(uuid.uuid4()),
            teacher_id=current_user.id,
            filename=file.filename,
            file_path=file_path,  # Only set if local storage fallback
            supabase_path=supabase_path,  # Supabase storage path
            supabase_url=supabase_url,
            ocr_text=ocr_text,
            gp_recommendations=gp_recommendations or {},  # JSON column accepts dict
            gp_subsections=gp_subsections or {},  # JSON column accepts dict
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        return PhotoEvidenceResponse(
            id=record.id,
            teacher_id=record.teacher_id,
            filename=record.filename,
            file_path=record.file_path,
            supabase_path=record.supabase_path,
            supabase_url=record.supabase_url,
            ocr_text=record.ocr_text,
            gp_recommendations=gp_recommendations,
            gp_subsections=gp_subsections,
            created_at=record.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"UPLOAD ERROR: {e}")
        db.rollback()
        logger.error(f"Error uploading photo evidence: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.get("/", response_model=List[PhotoEvidenceListItem])
async def list_photo_evidence(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return list of photo evidence with OCR + GP recommendations for the current user."""
    try:
        query = db.query(PhotoEvidence).filter(PhotoEvidence.teacher_id == current_user.id)
        items = query.order_by(PhotoEvidence.created_at.desc()).all()

        result: List[PhotoEvidenceListItem] = []
        for rec in items:
            # Handle JSON columns (returns dict) or legacy Text columns (returns string)
            if isinstance(rec.gp_recommendations, dict):
                gp = rec.gp_recommendations
            elif isinstance(rec.gp_recommendations, str):
                try:
                    gp = json.loads(rec.gp_recommendations) if rec.gp_recommendations else {}
                except json.JSONDecodeError:
                    gp = {}
            else:
                gp = {}
            
            if isinstance(rec.gp_subsections, dict):
                subsections = rec.gp_subsections
            elif isinstance(rec.gp_subsections, str):
                try:
                    subsections = json.loads(rec.gp_subsections) if rec.gp_subsections else {}
                except json.JSONDecodeError:
                    subsections = {}
            else:
                subsections = {}
            result.append(
                PhotoEvidenceListItem(
                    id=rec.id,
                    teacher_id=rec.teacher_id,
                    filename=rec.filename,
                    file_path=rec.file_path,
                    supabase_path=rec.supabase_path,
                    supabase_url=rec.supabase_url,
                    ocr_text=rec.ocr_text,
                    gp_recommendations=gp,
                    gp_subsections=subsections,
                    created_at=rec.created_at,
                )
            )
        return result
    except Exception as e:
        logger.error(f"Error listing photo evidence: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing photo evidence: {e}",
        )


@router.get("/{id}", response_model=PhotoEvidenceResponse)
async def get_photo_evidence(
    id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Return single photo evidence entry. Only returns evidence belonging to the current user."""
    try:
        rec = db.query(PhotoEvidence).filter(
            PhotoEvidence.id == str(id),
            PhotoEvidence.teacher_id == current_user.id
        ).first()
        if not rec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo evidence not found",
            )

        # Handle JSON columns (returns dict) or legacy Text columns (returns string)
        if isinstance(rec.gp_recommendations, dict):
            gp = rec.gp_recommendations
        elif isinstance(rec.gp_recommendations, str):
            try:
                gp = json.loads(rec.gp_recommendations) if rec.gp_recommendations else {}
            except json.JSONDecodeError:
                gp = {}
        else:
            gp = {}
        
        if isinstance(rec.gp_subsections, dict):
            subsections = rec.gp_subsections
        elif isinstance(rec.gp_subsections, str):
            try:
                subsections = json.loads(rec.gp_subsections) if rec.gp_subsections else {}
            except json.JSONDecodeError:
                subsections = {}
        else:
            subsections = {}

        return PhotoEvidenceResponse(
            id=rec.id,
            teacher_id=rec.teacher_id,
            filename=rec.filename,
            file_path=rec.file_path,
            supabase_path=rec.supabase_path,
            supabase_url=rec.supabase_url,
            ocr_text=rec.ocr_text,
            gp_recommendations=gp,
            gp_subsections=subsections,
            created_at=rec.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting photo evidence: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting photo evidence: {e}",
        )