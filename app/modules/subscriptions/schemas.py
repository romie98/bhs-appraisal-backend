"""Subscription management schemas"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class GrantPremiumRequest(BaseModel):
    """Schema for granting premium access"""
    lifetime: bool = Field(
        default=False,
        description="If True, grants lifetime premium (no expiration). If False, expires in 30 days."
    )
    days: Optional[int] = Field(
        default=30,
        ge=1,
        description="Number of days until expiration (ignored if lifetime=True)"
    )


class SubscriptionUpdateResponse(BaseModel):
    """Schema for subscription update response"""
    id: str
    email: str
    full_name: str
    subscription_plan: str
    subscription_status: str
    subscription_expires_at: Optional[datetime] = None
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AdminGrantPremiumRequest(BaseModel):
    """Schema for admin granting premium access"""
    expires_at: Optional[datetime] = Field(
        default=None,
        description="Optional expiration datetime (ISO format). If omitted, grants indefinitely."
    )


class AdminPremiumResponse(BaseModel):
    """Schema for admin premium management response"""
    model_config = ConfigDict(from_attributes=True)
    
    user_id: str
    effective_premium: bool
    admin_override: bool
    admin_expires_at: Optional[datetime] = None







