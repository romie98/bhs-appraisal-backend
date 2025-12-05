"""FastAPI application entry point"""
import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import Base, engine, get_db
from app.modules.students.routers import router as students_router
from app.modules.register.routers import router as register_router
from app.modules.assessments.routers import router as assessments_router
from app.modules.export.routers import router as export_router
from app.modules.classes.routers import router as classes_router
from app.modules.logbook.routers import router as logbook_router
from app.modules.ai.routers import router as ai_router
from app.modules.lesson_plans.routers import router as lesson_plans_router
from app.modules.photo_library.routers import router as photo_library_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Mark Book & Register API",
    description="API for managing students, attendance register, and assessments",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(students_router, prefix="/students", tags=["Students"])
app.include_router(register_router, prefix="/register", tags=["Register"])
app.include_router(assessments_router, prefix="/assessments", tags=["Assessments"])
app.include_router(export_router, prefix="/export", tags=["Export"])
app.include_router(classes_router, prefix="/classes", tags=["Classes"])
app.include_router(logbook_router, prefix="/logbook", tags=["Log Book"])
app.include_router(ai_router, prefix="/ai", tags=["AI"])
app.include_router(lesson_plans_router, prefix="/lesson-plans", tags=["Lesson Plans"])
app.include_router(photo_library_router, prefix="/photo-library", tags=["Photo Library"])

# Serve uploaded files statically
import os
if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Mark Book & Register API", "version": "1.0.0"}


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# Helper endpoint for markbook classes
@app.get("/markbook/classes")
async def get_markbook_classes(db: Session = Depends(get_db)):
    """Get all classes for markbook/register selection"""
    from app.modules.classes.models import Class
    from app.modules.classes.schemas import ClassResponse
    from sqlalchemy import func
    from app.modules.classes.models import class_students
    
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

