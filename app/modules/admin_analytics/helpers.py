"""Helper functions for admin analytics"""
import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.modules.admin_analytics.models import UserActivityLog

logger = logging.getLogger(__name__)


def log_user_activity(
    db: Session,
    user_id: str,
    action_type: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log user activity for admin analytics.
    
    This function is lightweight and should be called after successful operations only.
    It does not raise exceptions to avoid breaking business logic.
    
    Args:
        db: Database session
        user_id: ID of the user performing the action
        action_type: Type of action (e.g., "login", "evidence_upload", "lesson_plan_create")
        entity_type: Optional type of entity involved (e.g., "evidence", "lesson_plan")
        entity_id: Optional ID of the entity involved
        metadata: Optional additional context (will be sanitized to remove sensitive data)
    """
    try:
        # Sanitize metadata to remove sensitive information
        sanitized_metadata = _sanitize_metadata(metadata) if metadata else None
        
        activity_log = UserActivityLog(
            user_id=user_id,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_json=sanitized_metadata
        )
        
        db.add(activity_log)
        db.commit()
    except Exception as e:
        # Log error but don't raise - analytics should never break business logic
        logger.warning(f"Failed to log user activity: {str(e)}")
        db.rollback()


def _sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove sensitive information from metadata.
    
    Args:
        metadata: Original metadata dictionary
        
    Returns:
        Sanitized metadata dictionary
    """
    if not isinstance(metadata, dict):
        return {}
    
    sanitized = {}
    sensitive_keys = [
        "password", "token", "secret", "key", "authorization",
        "access_token", "refresh_token", "api_key", "supabase_url"
    ]
    
    for key, value in metadata.items():
        key_lower = key.lower()
        # Skip sensitive keys
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            continue
        
        # Recursively sanitize nested dictionaries
        if isinstance(value, dict):
            sanitized[key] = _sanitize_metadata(value)
        else:
            sanitized[key] = value
    
    return sanitized















