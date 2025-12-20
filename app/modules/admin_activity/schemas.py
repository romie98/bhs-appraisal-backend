"""Admin activity schemas"""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class AdminActivityItem(BaseModel):
    """Single activity log item"""
    id: int
    user_email: str
    action: str
    resource: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AdminActivityResponse(BaseModel):
    """Activity feed response"""
    events: List[AdminActivityItem]



