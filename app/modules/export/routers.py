"""Export API router"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from .services import PDFExportService

router = APIRouter()
pdf_service = PDFExportService()


@router.get("/markbook/{grade}")
async def export_markbook(
    grade: str,
    db: Session = Depends(get_db)
):
    """
    Export Mark Book Summary PDF for a grade
    
    - **grade**: Grade identifier (e.g., "10-9", "11-1")
    """
    try:
        pdf_buffer = pdf_service.generate_markbook_summary(db, grade)
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="markbook_grade_{grade}_{pdf_service.TEACHER_NAME.replace(" ", "_")}.pdf"'
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating PDF: {str(e)}"
        )


@router.get("/attendance/{grade}")
async def export_attendance(
    grade: str,
    db: Session = Depends(get_db)
):
    """
    Export Attendance Summary PDF for a grade
    
    - **grade**: Grade identifier (e.g., "10-9", "11-1")
    """
    try:
        pdf_buffer = pdf_service.generate_attendance_summary(db, grade)
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="attendance_grade_{grade}_{pdf_service.TEACHER_NAME.replace(" ", "_")}.pdf"'
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating PDF: {str(e)}"
        )


@router.get("/student/{student_id}")
async def export_student_progress(
    student_id: str,
    db: Session = Depends(get_db)
):
    """
    Export Student Progress Report PDF
    
    - **student_id**: UUID of the student
    """
    try:
        pdf_buffer = pdf_service.generate_student_progress_report(db, student_id)
        
        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="student_progress_{student_id}.pdf"'
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating PDF: {str(e)}"
        )





