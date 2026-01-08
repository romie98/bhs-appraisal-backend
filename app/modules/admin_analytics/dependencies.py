"""Admin access dependencies"""
import os
from fastapi import Depends, HTTPException, status
from app.modules.auth.models import User
from app.services.auth_dependency import get_current_user

# Check if admin features are enabled
ENABLE_ADMIN = os.getenv("ENABLE_ADMIN", "false").lower() == "true"


def require_admin_enabled():
    """
    Dependency to check if admin features are enabled.
    Returns 404 if ENABLE_ADMIN is not true.
    """
    if not ENABLE_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin features are disabled"
        )


def require_admin_role(
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_admin_enabled)
) -> User:
    """
    Dependency to ensure current user has ADMIN role.
    Requires ENABLE_ADMIN=true and current_user.role == "ADMIN".
    
    Args:
        current_user: Authenticated user from get_current_user
        
    Returns:
        User object if admin
        
    Raises:
        HTTPException: If user is not an admin (403) or admin features disabled (404)
    """
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    return current_user
















