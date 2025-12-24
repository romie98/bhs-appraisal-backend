"""Subscription access control guards"""
from datetime import datetime, timezone
from fastapi import HTTPException, status
from app.modules.auth.models import User
from app.modules.auth.constants import SUBSCRIPTION_PLAN_FREE


def require_premium(user: User) -> None:
    """
    Guard function to ensure user has active premium subscription.
    
    This function enforces that ONLY Stripe webhooks can grant premium access.
    Users must have:
    - subscription_plan != "FREE" (i.e., PREMIUM, PRO, SCHOOL, etc.)
    - subscription_status == "ACTIVE"
    - subscription_expires_at is either NULL or in the future
    
    Admins (user.role == "ADMIN") can bypass premium requirements.
    
    Args:
        user: User object to check
        
    Raises:
        HTTPException: 403 Forbidden if user does not have active premium subscription
    """
    # Admin bypass: Admins can access premium features
    if user.role == "ADMIN":
        return
    
    # Check if user has premium plan (any plan that is not FREE)
    if user.subscription_plan == SUBSCRIPTION_PLAN_FREE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required"
        )
    
    # Check if subscription is active
    if user.subscription_status != "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription inactive"
        )
    
    # Check if subscription has expired
    if user.subscription_expires_at is not None:
        # Use UTC for comparison
        now_utc = datetime.now(timezone.utc)
        # Ensure subscription_expires_at is timezone-aware for comparison
        expires_at = user.subscription_expires_at
        if expires_at.tzinfo is None:
            # If naive datetime, assume UTC
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        if expires_at < now_utc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Premium subscription expired"
            )




