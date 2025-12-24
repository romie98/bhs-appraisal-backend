"""Account subscription API router"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.modules.auth.models import User
from app.services.auth_dependency import get_current_user
from app.modules.account.schemas import (
    SubscriptionPlanResponse,
    UpgradeRequest,
    UpgradeResponse,
    CancelResponse
)
from app.modules.auth.constants import SUBSCRIPTION_PLAN_FREE

router = APIRouter(prefix="/account", tags=["Account"])


@router.get("/plan", response_model=SubscriptionPlanResponse)
async def get_subscription_plan(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's subscription plan information.
    
    Requires authentication.
    
    Returns:
        - subscription_plan: Current plan (FREE, PRO, SCHOOL, etc.)
        - subscription_status: Current status (ACTIVE, CANCELED, TRIAL)
        - subscription_expires_at: When subscription expires (if applicable)
        - is_premium: Boolean indicating if user has premium features
    """
    # Determine if user has premium access
    is_premium = current_user.subscription_plan != SUBSCRIPTION_PLAN_FREE
    
    return SubscriptionPlanResponse(
        subscription_plan=current_user.subscription_plan,
        subscription_status=current_user.subscription_status,
        subscription_expires_at=current_user.subscription_expires_at,
        is_premium=is_premium
    )


@router.post("/upgrade", response_model=UpgradeResponse, status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def upgrade_subscription(
    request: UpgradeRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Upgrade user's subscription plan.
    
    Requires authentication.
    
    Currently returns 501 Not Implemented as billing is not enabled yet.
    
    Args:
        request: Upgrade request containing plan name
        
    Returns:
        Upgrade response (currently returns error)
        
    Raises:
        HTTPException: 501 Not Implemented - Billing not enabled yet
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Billing not enabled yet"
    )


@router.post("/cancel", response_model=CancelResponse, status_code=status.HTTP_501_NOT_IMPLEMENTED)
async def cancel_subscription(
    current_user: User = Depends(get_current_user)
):
    """
    Cancel user's current subscription.
    
    Requires authentication.
    
    Currently returns 501 Not Implemented as billing is not enabled yet.
    
    Returns:
        Cancellation response (currently returns error)
        
    Raises:
        HTTPException: 501 Not Implemented - Billing not enabled yet
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Billing not enabled yet"
    )









