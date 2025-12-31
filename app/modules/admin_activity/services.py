"""Admin activity services"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.modules.admin_activity.models import AdminActivityLog
from app.modules.auth.models import User

logger = logging.getLogger(__name__)


def log_activity(
    db: Session,
    user: Optional[User] = None,
    action: str = "",
    resource: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log activity for admin dashboard.
    
    This function is fail-safe and will never raise exceptions to avoid
    breaking main application flows.
    
    Args:
        db: Database session
        user: User object (optional, for user_id and user_email)
        action: Action type (e.g., "LOGIN", "UPLOAD_EVIDENCE", "AI_OCR")
        resource: Resource identifier (e.g., evidence_id, file_path)
        metadata: Optional additional context
    """
    try:
        user_id = user.id if user else None
        user_email = user.email if user else None
        
        activity_log = AdminActivityLog(
            user_id=user_id,
            user_email=user_email,
            action=action,
            resource=resource,
            metadata_json=metadata
        )
        
        db.add(activity_log)
        db.commit()
    except Exception as e:
        # Fail silently - logging must never crash the app
        logger.warning(f"Failed to log admin activity: {e}")
        try:
            db.rollback()
        except Exception:
            pass


def get_recent_activity(db: Session, limit: int = 25) -> list:
    """
    Get recent activity logs for admin dashboard.
    
    Args:
        db: Database session
        limit: Maximum number of records to return (default: 25)
        
    Returns:
        List of AdminActivityLog records ordered by created_at DESC
    """
    try:
        activities = db.query(AdminActivityLog).order_by(
            AdminActivityLog.created_at.desc()
        ).limit(limit).all()
        
        return activities
    except Exception as e:
        logger.error(f"Error fetching admin activity: {e}")
        return []











