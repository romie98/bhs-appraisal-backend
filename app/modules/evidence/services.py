"""Evidence service functions"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.modules.auth.models import User
from app.modules.auth.constants import SUBSCRIPTION_PLAN_FREE
from app.modules.evidence.models import Evidence


def can_upload_evidence(user: User, gp_section: str, db: Session) -> bool:
    """
    Check if a user can upload evidence for a given GP section.
    
    FREE users are limited to 3 uploads per GP subsection.
    PREMIUM users (PRO, SCHOOL) have unlimited uploads.
    
    Args:
        user: User object with subscription_plan attribute
        gp_section: GP section identifier (e.g., "GP1", "GP2", etc.)
        db: Database session
        
    Returns:
        True if user can upload, False if limit exceeded
    """
    # Premium users have unlimited uploads
    if user.subscription_plan != SUBSCRIPTION_PLAN_FREE:
        return True
    
    # For FREE users, check upload count for this GP section
    count = db.query(func.count(Evidence.id)).filter(
        Evidence.teacher_id == user.id,
        Evidence.gp_section == gp_section
    ).scalar() or 0
    
    # FREE users can upload up to 3 items per GP subsection
    return count < 3














