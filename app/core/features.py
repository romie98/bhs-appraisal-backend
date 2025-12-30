"""Feature flags based on subscription plans"""
from typing import Dict, List, Any
from fastapi import Depends, HTTPException, status
from app.modules.auth.models import User
from app.modules.auth.constants import SUBSCRIPTION_PLAN_FREE
from app.services.auth_dependency import get_current_user


# Plan categories
PLAN_FREE = "FREE"
PLAN_PREMIUM = "PREMIUM"  # Any plan that is not FREE (PRO, SCHOOL, etc.)


# Feature registry: maps feature keys to feature definitions
FEATURE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "AI_OCR": {
        "name": "AI OCR",
        "description": "Extract text from images using AI",
        "allowed_plans": [PLAN_PREMIUM]
    },
    "ADVANCED_ANALYTICS": {
        "name": "Advanced Analytics",
        "description": "Access to detailed analytics and insights",
        "allowed_plans": [PLAN_PREMIUM]
    },
    "EXPORT_REPORTS": {
        "name": "Export Reports",
        "description": "Export reports in various formats",
        "allowed_plans": [PLAN_PREMIUM]
    },
    "UNLIMITED_UPLOADS": {
        "name": "Unlimited Uploads",
        "description": "Upload unlimited files without restrictions",
        "allowed_plans": [PLAN_PREMIUM]
    }
}


def has_feature(user: User, feature_key: str) -> bool:
    """
    Check if a user has access to a feature based on their subscription plan.
    
    Plan categories:
    - FREE: Limited access, default for all users
    - PREMIUM: Any plan that is not FREE (PRO, SCHOOL, etc.)
    
    Args:
        user: User object with subscription_plan attribute
        feature_key: Key from FEATURE_REGISTRY
        
    Returns:
        True if user's plan allows the feature, False otherwise.
        FREE users default to limited access (False for PREMIUM features).
        
    Raises:
        KeyError: If feature_key is not in FEATURE_REGISTRY
    """
    if feature_key not in FEATURE_REGISTRY:
        raise KeyError(f"Feature '{feature_key}' not found in FEATURE_REGISTRY")
    
    feature = FEATURE_REGISTRY[feature_key]
    allowed_plans = feature.get("allowed_plans", [])
    
    # Map user's subscription_plan to plan category
    user_plan_category = PLAN_FREE if user.subscription_plan == SUBSCRIPTION_PLAN_FREE else PLAN_PREMIUM
    
    return user_plan_category in allowed_plans


def require_feature(feature_key: str):
    """
    FastAPI dependency to require a specific feature based on subscription plan.
    
    This dependency:
    1. Gets the current authenticated user
    2. Checks if the user's subscription_plan is in the feature's allowed_plans
    3. Raises HTTP 402 (Payment Required) if feature is not available
    
    Usage:
        @router.post("/some-endpoint")
        async def some_endpoint(
            user: User = Depends(require_feature("AI_OCR"))
        ):
            # This endpoint requires AI_OCR feature
            ...
    
    Args:
        feature_key: Key from FEATURE_REGISTRY
        
    Returns:
        FastAPI dependency function that returns the User if feature is available
        
    Raises:
        HTTPException: 402 Payment Required if user's plan doesn't include the feature
        KeyError: If feature_key is not in FEATURE_REGISTRY
    """
    if feature_key not in FEATURE_REGISTRY:
        raise KeyError(f"Feature '{feature_key}' not found in FEATURE_REGISTRY")
    
    feature = FEATURE_REGISTRY[feature_key]
    feature_name = feature.get("name", feature_key)
    
    def feature_dependency(
        current_user: User = Depends(get_current_user)
    ) -> User:
        """
        Internal dependency function that checks feature access.
        """
        if not has_feature(current_user, feature_key):
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Upgrade to Premium to access this feature"
            )
        
        return current_user
    
    return feature_dependency










