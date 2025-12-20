"""FastAPI application entry point"""

import logging
import os
from dotenv import load_dotenv

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.core.database import Base, engine, get_db

# Routers
from app.modules.auth.routers import router as auth_router
from app.modules.students.routers import router as students_router
from app.modules.register.routers import router as register_router
from app.modules.assessments.routers import router as assessments_router
from app.modules.export.routers import router as export_router
from app.modules.classes.routers import router as classes_router
from app.modules.logbook.routers import router as logbook_router
from app.modules.ai.routers import router as ai_router
from app.modules.lesson_plans.routers import router as lesson_plans_router
from app.modules.photo_library.routers import router as photo_library_router
from app.modules.evidence.routers import router as evidence_router

# Load environment variables
load_dotenv()

# --------------------------------------------------
# Create FastAPI app FIRST
# --------------------------------------------------
app = FastAPI(
    title="Mark Book & Register API",
    description="API for managing students, attendance register, and assessments",
    version="1.0.0",
)

# --------------------------------------------------
# CORS (SINGLE, CORRECT CONFIG)
# --------------------------------------------------
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allowed_origins = [
    FRONTEND_URL,
    "https://www.mytportfolio.com",
    "https://mytportfolio.com",
],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --------------------------------------------------
# Logging
# --------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# Database
# --------------------------------------------------
Base.metadata.create_all(bind=engine)

# --------------------------------------------------
# Routers
# --------------------------------------------------
app.include_router(auth_router)  # already has /auth
app.include_router(students_router, prefix="/students", tags=["Students"])
app.include_router(register_router, prefix="/register", tags=["Register"])
app.include_router(assessments_router, prefix="/assessments", tags=["Assessments"])
app.include_router(export_router, prefix="/export", tags=["Export"])
app.include_router(classes_router, prefix="/classes", tags=["Classes"])
app.include_router(logbook_router, prefix="/logbook", tags=["Log Book"])
app.include_router(ai_router, prefix="/ai", tags=["AI"])
app.include_router(lesson_plans_router, prefix="/lesson-plans", tags=["Lesson Plans"])
app.include_router(photo_library_router, prefix="/photo-library", tags=["Photo Library"])
app.include_router(evidence_router, tags=["Evidence"])

# --------------------------------------------------
# Account management
# --------------------------------------------------
from app.modules.account.routers import router as account_router
app.include_router(account_router)

# --------------------------------------------------
# Admin analytics (ENV-GUARDED)
# --------------------------------------------------
if os.getenv("ENABLE_ADMIN", "false").lower() == "true":
    from app.modules.admin_analytics.routers import router as admin_analytics_router
    app.include_router(admin_analytics_router, prefix="/admin", tags=["Admin"])

# --------------------------------------------------
# Static uploads
# --------------------------------------------------
if os.path.exists("uploads"):
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# --------------------------------------------------
# Utility endpoints
# --------------------------------------------------
@app.get("/")
async def root():
    return {"message": "Mark Book & Register API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/ping")
async def ping():
    return {"status": "ok"}

# --------------------------------------------------
# Helper endpoint for markbook classes
# --------------------------------------------------
@app.get("/markbook/classes")
async def get_markbook_classes(db: Session = Depends(get_db)):
    from app.modules.classes.models import Class, class_students
    from app.modules.classes.schemas import ClassResponse
    from sqlalchemy import func

    classes = db.query(Class).order_by(Class.created_at.desc()).all()

    result = []
    for cls in classes:
        student_count = (
            db.query(func.count(class_students.c.student_id))
            .filter(class_students.c.class_id == cls.id)
            .scalar()
            or 0
        )

        result.append(
            ClassResponse(
                id=cls.id,
                name=cls.name,
                academic_year=cls.academic_year,
                created_at=cls.created_at,
                student_count=student_count,
            )
        )

    return result
