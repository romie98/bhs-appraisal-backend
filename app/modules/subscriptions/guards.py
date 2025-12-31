"""Subscription access control guards"""
from datetime import datetime, timezone
from fastapi import HTTPException, status
from app.modules.auth.models import User
from app.modules.auth.constants import SUBSCRIPTION_PLAN_FREE


def has_premium_access(user: User) -> bool:
    """
    Single source of truth for premium access checking.
    
    Checks premium access in this order:
    1. Stripe subscription (if user has stripe_customer_id and status is ACTIVE)
    2. Admin premium override (if admin_premium_override is True and not expired)
    
    Args:
        user: User object to check
        
    Returns:
        bool: True if user has premium access, False otherwise
    """
    # Check Stripe subscription first (source of truth for paying users)
    if user.stripe_customer_id and user.subscription_status == "ACTIVE":
        # Check if subscription has expired
        if user.subscription_expires_at is not None:
            now_utc = datetime.now(timezone.utc)
            expires_at = user.subscription_expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < now_utc:
                # Stripe subscription expired, check admin override
                pass
            else:
                return True
        else:
            # Active Stripe subscription with no expiration
            return True
    
    # Check admin premium override
    if user.admin_premium_override:
        if user.admin_premium_expires_at is None:
            # Admin override granted indefinitely
            return True
        # Check if admin override has expired
        now_utc = datetime.now(timezone.utc)
        expires_at = user.admin_premium_expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at > now_utc:
            return True
    
    return False


def require_premium(user: User) -> None:
    """
    Guard function to ensure user has active premium subscription.
    
    Uses has_premium_access() as the single source of truth for premium checking.
    Admins (user.role == "ADMIN") can bypass premium requirements.
    
    Args:
        user: User object to check
        
    Raises:
        HTTPException: 403 Forbidden if user does not have active premium subscription
    """
    # Admin bypass: Admins can access premium features
    if user.role == "ADMIN":
        return
    
    # Use single source of truth function
    if not has_premium_access(user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required"
        )







