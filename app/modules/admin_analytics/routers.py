"""Admin analytics API router"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Body
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
    RecentActivityResponse,
    AdminUserListItem
)
from app.modules.subscriptions.schemas import AdminPremiumResponse
from app.modules.subscriptions.guards import has_premium_access

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


# --------------------------------------------------
# User Management Endpoints
# --------------------------------------------------

@router.get("/users", response_model=List[AdminUserListItem])
async def list_users(
    admin_user: User = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """
    List all users for admin dashboard.
    
    Requires ADMIN role and ENABLE_ADMIN=true.
    
    Returns a list of users with subscription and admin override information.
    Does NOT return sensitive data like password hashes.
    
    Returns:
        List of AdminUserListItem with user information
        
    Raises:
        HTTPException: 403 if user is not admin
    """
    try:
        # Query all users, ordered by created_at DESC
        users = db.query(User).order_by(User.created_at.desc()).all()
        
        # Return only the specified fields
        return [
            AdminUserListItem(
                id=str(user.id),  # Convert UUID to string if needed
                full_name=user.full_name,
                email=user.email,
                role=user.role,
                subscription_plan=user.subscription_plan,
                subscription_status=user.subscription_status,
                stripe_customer_id=user.stripe_customer_id,
                admin_premium_override=bool(user.admin_premium_override),  # Ensure boolean
                admin_premium_expires_at=user.admin_premium_expires_at,
                created_at=user.created_at
            )
            for user in users
        ]
    except Exception as e:
        logger.error(f"Error listing users: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


# --------------------------------------------------
# Subscription Management Endpoints
# --------------------------------------------------

@router.post("/users/{user_id}/grant-premium", response_model=AdminPremiumResponse)
async def grant_premium_access(
    user_id: str,
    request: Optional[dict] = Body(default=None),
    admin_user: User = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """
    Grant premium access to a user via admin override.
    
    Requires ADMIN role and ENABLE_ADMIN=true.
    
    IMPORTANT: Cannot modify users with Stripe subscriptions.
    Only sets admin_premium_override fields, does NOT touch:
    - subscription_plan
    - subscription_status
    - subscription_expires_at
    - stripe_customer_id
    
    Request body (optional):
    {
        "expires_at": "2024-12-31T23:59:59Z"  // Optional ISO datetime. If omitted, grants indefinitely.
    }
    
    Args:
        user_id: ID of the user to grant premium access to
        request: Optional dict with "expires_at" (ISO datetime string)
        admin_user: Admin user (from require_admin_role dependency)
        db: Database session
        
    Returns:
        AdminPremiumResponse with premium status
        
    Raises:
        HTTPException: 404 if user not found, 400 if user has Stripe subscription
    """
    
    # Find user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    # SECURITY: Reject if user has Stripe subscription
    if user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe subscriptions cannot be modified by admin"
        )
    
    # Parse request body
    expires_at = None
    if request and "expires_at" in request:
        try:
            expires_at_str = request["expires_at"]
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid expires_at format: {str(e)}"
            )
    
    # Grant admin premium override
    try:
        user.admin_premium_override = True
        user.admin_premium_expires_at = expires_at
        user.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(user)
        
        # Log admin action
        try:
            from app.modules.admin_activity.services import log_activity
            log_activity(
                db=db,
                user=user,
                action="GRANT_ADMIN_PREMIUM",
                resource=f"user:{user_id}",
                metadata={
                    "granted_by": admin_user.email,
                    "expires_at": expires_at.isoformat() if expires_at else None
                }
            )
        except Exception as e:
            logger.warning(f"Failed to log admin activity: {e}")
        
        # Return response
        return AdminPremiumResponse(
            user_id=user.id,
            effective_premium=has_premium_access(user),
            admin_override=user.admin_premium_override,
            admin_expires_at=user.admin_premium_expires_at
        )
    except Exception as e:
        logger.error(f"Error granting admin premium access: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to grant premium access"
        )


@router.post("/users/{user_id}/revoke-premium", response_model=AdminPremiumResponse)
async def revoke_premium_access(
    user_id: str,
    admin_user: User = Depends(require_admin_role),
    db: Session = Depends(get_db)
):
    """
    Revoke admin premium override from a user.
    
    Requires ADMIN role and ENABLE_ADMIN=true.
    
    IMPORTANT: Cannot modify users with Stripe subscriptions.
    Only clears admin_premium_override fields, does NOT touch:
    - subscription_plan
    - subscription_status
    - subscription_expires_at
    - stripe_customer_id
    
    Args:
        user_id: ID of the user to revoke premium access from
        admin_user: Admin user (from require_admin_role dependency)
        db: Database session
        
    Returns:
        AdminPremiumResponse with premium status
        
    Raises:
        HTTPException: 404 if user not found, 400 if user has Stripe subscription
    """
    
    # Find user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {user_id} not found"
        )
    
    # SECURITY: Reject if user has Stripe subscription
    if user.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe subscriptions cannot be modified by admin"
        )
    
    # Revoke admin premium override
    try:
        user.admin_premium_override = False
        user.admin_premium_expires_at = None
        user.updated_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(user)
        
        # Log admin action
        try:
            from app.modules.admin_activity.services import log_activity
            log_activity(
                db=db,
                user=user,
                action="REVOKE_ADMIN_PREMIUM",
                resource=f"user:{user_id}",
                metadata={
                    "revoked_by": admin_user.email
                }
            )
        except Exception as e:
            logger.warning(f"Failed to log admin activity: {e}")
        
        # Return response
        return AdminPremiumResponse(
            user_id=user.id,
            effective_premium=has_premium_access(user),
            admin_override=user.admin_premium_override,
            admin_expires_at=user.admin_premium_expires_at
        )
    except Exception as e:
        logger.error(f"Error revoking admin premium access: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke premium access"
        )














