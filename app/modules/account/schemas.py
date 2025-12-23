"""Account subscription schemas"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SubscriptionPlanResponse(BaseModel):
    """Response schema for subscription plan information"""
    subscription_plan: str
    subscription_status: str
    subscription_expires_at: Optional[datetime] = None
    is_premium: bool
    
    class Config:
        from_attributes = True


class UpgradeRequest(BaseModel):
    """Request schema for subscription upgrade"""
    plan: str = Field(..., description="Subscription plan to upgrade to (e.g., 'PREMIUM')")


class UpgradeResponse(BaseModel):
    """Response schema for subscription upgrade"""
    message: str
    subscription_plan: Optional[str] = None


class CancelResponse(BaseModel):
    """Response schema for subscription cancellation"""
    message: str






