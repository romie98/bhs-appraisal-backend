"""Subscription management services"""
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.modules.auth.models import User
from app.modules.auth.constants import (
    SUBSCRIPTION_PLAN_FREE,
    SUBSCRIPTION_PLAN_PREMIUM,
    SUBSCRIPTION_STATUS_ACTIVE,
    SUBSCRIPTION_STATUS_INACTIVE
)

logger = logging.getLogger(__name__)


def grant_premium_access(
    db: Session,
    user: User,
    lifetime: bool = False,
    days: int = 30
) -> User:
    """
    Grant premium access to a user.
    
    Sets:
    - subscription_plan = "PREMIUM"
    - subscription_status = "ACTIVE"
    - subscription_expires_at = now + days (or NULL if lifetime)
    
    Args:
        db: Database session
        user: User to grant premium access to
        lifetime: If True, grants lifetime premium (expires_at = NULL)
        days: Number of days until expiration (ignored if lifetime=True)
        
    Returns:
        Updated User object
        
    Raises:
        ValueError: If days is less than 1
    """
    if not lifetime and days < 1:
        raise ValueError("Days must be at least 1")
    
    # Set premium plan and active status
    user.subscription_plan = SUBSCRIPTION_PLAN_PREMIUM
    user.subscription_status = SUBSCRIPTION_STATUS_ACTIVE
    
    # Set expiration date
    if lifetime:
        user.subscription_expires_at = None
    else:
        user.subscription_expires_at = datetime.now(timezone.utc) + timedelta(days=days)
    
    # Update updated_at timestamp
    user.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"Granted premium access to user {user.id} ({user.email}) - lifetime: {lifetime}, expires: {user.subscription_expires_at}")
    
    return user


def revoke_premium_access(db: Session, user: User) -> User:
    """
    Revoke premium access from a user.
    
    Sets:
    - subscription_plan = "FREE"
    - subscription_status = "INACTIVE"
    - subscription_expires_at = NULL
    
    Args:
        db: Database session
        user: User to revoke premium access from
        
    Returns:
        Updated User object
    """
    # Set free plan and inactive status
    user.subscription_plan = SUBSCRIPTION_PLAN_FREE
    user.subscription_status = SUBSCRIPTION_STATUS_INACTIVE
    user.subscription_expires_at = None
    
    # Update updated_at timestamp
    user.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"Revoked premium access from user {user.id} ({user.email})")
    
    return user




