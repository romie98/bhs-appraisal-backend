"""Admin analytics schemas"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any, List
from datetime import datetime


class AdminStatsResponse(BaseModel):
    """System-wide statistics for admin dashboard"""
    total_users: int
    active_users_7d: int
    total_evidence: int
    ai_requests: int
    storage_used_mb: int
    errors_24h: int


class AdminHealthResponse(BaseModel):
    """System health status"""
    api: str
    database: str
    storage: str


class AdminActivityResponse(BaseModel):
    """Activity events response (placeholder for future use)"""
    events: List[Dict[str, Any]] = []


# Legacy schemas (kept for backward compatibility)
class ActivitySummaryResponse(BaseModel):
    """Summary statistics for admin analytics"""
    total_users: int
    total_actions: int
    active_users_last_7_days: int
    active_users_last_30_days: int


class RecentActivityItem(BaseModel):
    """Single activity log item for admin view"""
    user_email: str
    action_type: str
    entity_type: Optional[str]
    created_at: datetime


class RecentActivityResponse(BaseModel):
    """Recent activity logs response"""
    activities: list[RecentActivityItem]


class AdminUserListItem(BaseModel):
    """User information for admin user list"""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    full_name: str
    email: str
    role: str
    subscription_plan: str
    subscription_status: str
    stripe_customer_id: Optional[str] = None
    admin_premium_override: bool
    admin_premium_expires_at: Optional[datetime] = None
    created_at: datetime
















