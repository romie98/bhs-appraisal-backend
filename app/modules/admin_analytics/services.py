"""Admin analytics services"""
import logging
import os
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.modules.auth.models import User
from app.modules.evidence.models import Evidence

logger = logging.getLogger(__name__)


def get_system_stats(db: Session) -> dict:
    """
    Get system-wide statistics for admin dashboard.
    Safely handles missing tables by returning 0.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with system statistics
    """
    stats = {
        "total_users": 0,
        "active_users_7d": 0,
        "total_evidence": 0,
        "ai_requests": 0,
        "storage_used_mb": 0,
        "errors_24h": 0
    }
    
    try:
        # Total users
        stats["total_users"] = db.query(func.count(User.id)).scalar() or 0
    except Exception as e:
        logger.warning(f"Error counting users: {e}")
    
    try:
        # Active users last 7 days (using activity logs if available)
        from app.modules.admin_analytics.models import UserActivityLog
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        stats["active_users_7d"] = db.query(
            func.count(func.distinct(UserActivityLog.user_id))
        ).filter(
            UserActivityLog.created_at >= seven_days_ago
        ).scalar() or 0
    except Exception as e:
        logger.warning(f"Error counting active users: {e}")
        # If last_login doesn't exist or activity logs don't exist, return 0
    
    try:
        # Total evidence
        stats["total_evidence"] = db.query(func.count(Evidence.id)).scalar() or 0
    except Exception as e:
        logger.warning(f"Error counting evidence: {e}")
    
    try:
        # AI requests - count from AI evidence tables
        from app.modules.ai.models import (
            LessonEvidence, LogEvidence, RegisterEvidence, AssessmentEvidence
        )
        ai_count = (
            (db.query(func.count(LessonEvidence.id)).scalar() or 0) +
            (db.query(func.count(LogEvidence.id)).scalar() or 0) +
            (db.query(func.count(RegisterEvidence.id)).scalar() or 0) +
            (db.query(func.count(AssessmentEvidence.id)).scalar() or 0)
        )
        stats["ai_requests"] = ai_count
    except Exception as e:
        logger.warning(f"Error counting AI requests: {e}")
        # Table might not exist, return 0
    
    try:
        # Storage used - estimate from file counts (actual size not stored)
        # For now, return 0 as we don't track file sizes
        stats["storage_used_mb"] = 0
    except Exception as e:
        logger.warning(f"Error calculating storage: {e}")
    
    try:
        # Errors in last 24 hours - check if error log table exists
        # For now, return 0 as we don't have an error log table
        stats["errors_24h"] = 0
    except Exception as e:
        logger.warning(f"Error counting errors: {e}")
    
    return stats


def check_database_health(db: Session) -> str:
    """
    Check database connectivity.
    
    Args:
        db: Database session
        
    Returns:
        "ok" if database is accessible, "error" otherwise
    """
    try:
        db.execute(text("SELECT 1"))
        return "ok"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return "error"


def check_storage_health() -> str:
    """
    Check storage availability.
    
    Returns:
        "ok" if uploads directory exists, "error" otherwise
    """
    try:
        uploads_dir = "uploads"
        if os.path.exists(uploads_dir) and os.path.isdir(uploads_dir):
            return "ok"
        return "error"
    except Exception as e:
        logger.error(f"Storage health check failed: {e}")
        return "error"


def get_system_health(db: Session) -> dict:
    """
    Get system health status.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with health status for api, database, and storage
    """
    return {
        "api": "ok",
        "database": check_database_health(db),
        "storage": check_storage_health()
    }









