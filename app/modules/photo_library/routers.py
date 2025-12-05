"""Photo Evidence Library API router"""
import uuid
import json
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.photo_library.models import PhotoEvidence
from app.modules.photo_library.schemas import PhotoEvidenceResponse, PhotoEvidenceListItem
from app.modules.photo_library.services import save_photo_file, extract_text_from_image, get_image_extension
from app.services.ai_service import analyze_photo_evidence

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=PhotoEvidenceResponse, status_code=status.HTTP_201_CREATED)
async def upload_photo_evidence(
    file: UploadFile = File(...),
    teacher_id: str = Form(...),
    db: Session = Depends(get_db),
):
    """Upload a photo, run OCR + AI, and store GP recommendations."""
    try:
        ext = get_image_extension(file.filename)
        allowed = [".jpg", ".jpeg", ".png", ".heic"]
        if ext not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type. Allowed types: {', '.join(allowed)}",
            )

        # Save file
        content = await file.read()
        file_path = save_photo_file(content, file.filename, teacher_id)

        # Run OCR
        ocr_text = ""
        try:
            ocr_text = extract_text_from_image(file_path)
        except Exception as e:
            # Log but don't fail upload; allow manual evidence later
            logger.warning(f"OCR failed for {file_path}: {e}")

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

        # Store in DB (store recommendations and subsections as JSON strings)
        record = PhotoEvidence(
            id=str(uuid.uuid4()),
            teacher_id=teacher_id,
            file_path=file_path,
            ocr_text=ocr_text,
            gp_recommendations=json.dumps(gp_recommendations or {}),
            gp_subsections=json.dumps(gp_subsections or {}),
        )
        db.add(record)
        db.commit()
        db.refresh(record)

        return PhotoEvidenceResponse(
            id=record.id,
            teacher_id=record.teacher_id,
            file_path=record.file_path,
            ocr_text=record.ocr_text,
            gp_recommendations=gp_recommendations,
            gp_subsections=gp_subsections,
            created_at=record.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading photo evidence: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading photo evidence: {e}",
        )


@router.get("/", response_model=List[PhotoEvidenceListItem])
async def list_photo_evidence(
    teacher_id: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Return list of photo evidence with OCR + GP recommendations."""
    try:
        query = db.query(PhotoEvidence)
        if teacher_id:
            query = query.filter(PhotoEvidence.teacher_id == teacher_id)
        items = query.order_by(PhotoEvidence.created_at.desc()).all()

        result: List[PhotoEvidenceListItem] = []
        for rec in items:
            try:
                gp = json.loads(rec.gp_recommendations) if rec.gp_recommendations else {}
            except json.JSONDecodeError:
                gp = {}
            try:
                subsections = json.loads(rec.gp_subsections) if rec.gp_subsections else {}
            except json.JSONDecodeError:
                subsections = {}
            result.append(
                PhotoEvidenceListItem(
                    id=rec.id,
                    teacher_id=rec.teacher_id,
                    file_path=rec.file_path,
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
async def get_photo_evidence(id: UUID, db: Session = Depends(get_db)):
    """Return single photo evidence entry."""
    try:
        rec = db.query(PhotoEvidence).filter(PhotoEvidence.id == str(id)).first()
        if not rec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Photo evidence not found",
            )

        try:
            gp = json.loads(rec.gp_recommendations) if rec.gp_recommendations else {}
        except json.JSONDecodeError:
            gp = {}
        try:
            subsections = json.loads(rec.gp_subsections) if rec.gp_subsections else {}
        except json.JSONDecodeError:
            subsections = {}

        return PhotoEvidenceResponse(
            id=rec.id,
            teacher_id=rec.teacher_id,
            file_path=rec.file_path,
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