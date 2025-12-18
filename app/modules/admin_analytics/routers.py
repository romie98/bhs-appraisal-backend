"""Admin analytics API router"""
import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from app.core.database import get_db
from app.modules.auth.models import User
from app.modules.admin_analytics.models import UserActivityLog
from app.modules.admin_analytics.dependencies import require_admin_role
from app.modules.admin_analytics.services import get_system_stats, get_system_health
from app.core.features import require_feature
from app.modules.admin_analytics.schemas import (
    AdminStatsResponse,
    AdminHealthResponse,
    AdminActivityResponse,
    ActivitySummaryResponse,
    RecentActivityItem,
    RecentActivityResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Admin"])


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    admin_user: User = Depends(require_admin_role),
    _: User = Depends(require_feature("ADVANCED_ANALYTICS")),
    db: Session = Depends(get_db)
):
    """
    Get system-wide statistics for admin dashboard.
    Requires ADMIN role, ENABLE_ADMIN=true, and ADVANCED_ANALYTICS feature (PRO or SCHOOL plan).
    """
    try:
        stats = get_system_stats(db)
        return AdminStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting admin stats: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system statistics"
        )


@router.get("/health", response_model=AdminHealthResponse)
async def get_admin_health(
    admin_user: User = Depends(require_admin_role),
    _: User = Depends(require_feature("ADVANCED_ANALYTICS")),
    db: Session = Depends(get_db)
):
    """
    Get system health status.
    Requires ADMIN role, ENABLE_ADMIN=true, and ADVANCED_ANALYTICS feature (PRO or SCHOOL plan).
    """
    try:
        health = get_system_health(db)
        return AdminHealthResponse(**health)
    except Exception as e:
        logger.error(f"Error getting system health: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system health"
        )


@router.get("/activity", response_model=AdminActivityResponse)
async def get_admin_activity(
    admin_user: User = Depends(require_admin_role),
    _: User = Depends(require_feature("ADVANCED_ANALYTICS")),
    db: Session = Depends(get_db)
):
    """
    Get activity events from admin activity feed.
    Requires ADMIN role, ENABLE_ADMIN=true, and ADVANCED_ANALYTICS feature (PRO or SCHOOL plan).
    """
    try:
        from app.modules.admin_activity.services import get_recent_activity
        from app.modules.admin_activity.schemas import AdminActivityItem
        
        activities = get_recent_activity(db, limit=25)
        
        events = [
            AdminActivityItem(
                id=activity.id,
                user_email=activity.user_email or "Unknown",
                action=activity.action,
                resource=activity.resource,
                metadata=activity.metadata_json,
                created_at=activity.created_at
            )
            for activity in activities
        ]
        
        return AdminActivityResponse(events=events)
    except Exception as e:
        logger.error(f"Error getting admin activity: {e}", exc_info=True)
        # Return empty list on error
        return AdminActivityResponse(events=[])


# Legacy endpoints (kept for backward compatibility)
@router.get("/analytics/summary", response_model=ActivitySummaryResponse)
async def get_activity_summary(
    admin_user: User = Depends(require_admin_role),
    _: User = Depends(require_feature("ADVANCED_ANALYTICS")),
    db: Session = Depends(get_db)
):
    """
    Get summary statistics for admin analytics (legacy endpoint).
    Read-only endpoint, requires admin access, ENABLE_ADMIN=true, and ADVANCED_ANALYTICS feature (PRO or SCHOOL plan).
    """
    try:
        # Total users
        total_users = db.query(func.count(User.id)).scalar() or 0
        
        # Total actions
        total_actions = db.query(func.count(UserActivityLog.id)).scalar() or 0
        
        # Active users last 7 days
        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        active_users_7d = db.query(
            func.count(distinct(UserActivityLog.user_id))
        ).filter(
            UserActivityLog.created_at >= seven_days_ago
        ).scalar() or 0
        
        # Active users last 30 days
        thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
        active_users_30d = db.query(
            func.count(distinct(UserActivityLog.user_id))
        ).filter(
            UserActivityLog.created_at >= thirty_days_ago
        ).scalar() or 0
        
        return ActivitySummaryResponse(
            total_users=total_users,
            total_actions=total_actions,
            active_users_last_7_days=active_users_7d,
            active_users_last_30_days=active_users_30d
        )
    except Exception as e:
        logger.error(f"Error getting activity summary: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve activity summary"
        )


@router.get("/analytics/recent-activity", response_model=RecentActivityResponse)
async def get_recent_activity(
    admin_user: User = Depends(require_admin_role),
    _: User = Depends(require_feature("ADVANCED_ANALYTICS")),
    db: Session = Depends(get_db)
):
    """
    Get recent activity logs (last 50).
    Read-only endpoint, requires admin access, ENABLE_ADMIN=true, and ADVANCED_ANALYTICS feature (PRO or SCHOOL plan).
    Returns user email, action_type, entity_type, and created_at.
    """
    try:
        # Get last 50 activity logs with user email
        logs = db.query(
            UserActivityLog,
            User.email
        ).join(
            User, UserActivityLog.user_id == User.id
        ).order_by(
            UserActivityLog.created_at.desc()
        ).limit(50).all()
        
        activities = [
            RecentActivityItem(
                user_email=email,
                action_type=log.action_type,
                entity_type=log.entity_type,
                created_at=log.created_at
            )
            for log, email in logs
        ]
        
        return RecentActivityResponse(activities=activities)
    except Exception as e:
        logger.error(f"Error getting recent activity: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent activity"
        )


