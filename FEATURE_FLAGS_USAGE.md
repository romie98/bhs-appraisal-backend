# Feature Flags Usage Guide

## Overview

The feature flag system allows you to restrict access to features based on subscription plans without hardcoding plan checks in routers.

## Feature Registry

Features are defined in `app/core/features.py`:

```python
FEATURE_REGISTRY = {
    "AI_OCR": {
        "name": "AI OCR",
        "description": "Extract text from images using AI",
        "allowed_plans": ["PRO", "SCHOOL"]
    },
    "ADVANCED_ANALYTICS": {
        "name": "Advanced Analytics",
        "description": "Access to detailed analytics and insights",
        "allowed_plans": ["PRO", "SCHOOL"]
    },
    "EXPORT_REPORTS": {
        "name": "Export Reports",
        "description": "Export reports in various formats",
        "allowed_plans": ["PRO", "SCHOOL"]
    },
    "UNLIMITED_EVIDENCE": {
        "name": "Unlimited Evidence",
        "description": "Upload unlimited evidence files",
        "allowed_plans": ["PRO", "SCHOOL"]
    }
}
```

## Usage Examples

### 1. Using `require_feature` Dependency

Protect an endpoint with a feature requirement:

```python
from fastapi import APIRouter, Depends
from app.core.features import require_feature
from app.modules.auth.models import User

router = APIRouter()

@router.post("/photo-library/upload")
async def upload_photo(
    user: User = Depends(require_feature("AI_OCR")),
    # ... other parameters
):
    """
    Upload photo with AI OCR.
    Requires AI_OCR feature (PRO or SCHOOL plan).
    """
    # Endpoint logic here
    pass
```

### 2. Using `has_feature` Helper

Check feature access in business logic:

```python
from app.core.features import has_feature

def some_function(user: User):
    if has_feature(user, "UNLIMITED_EVIDENCE"):
        # Allow unlimited uploads
        max_uploads = None
    else:
        # Limit to 10 for FREE plan
        max_uploads = 10
    
    # Continue with logic
```

### 3. Conditional Feature Access

```python
from app.core.features import has_feature

@router.get("/analytics/advanced")
async def get_advanced_analytics(
    user: User = Depends(get_current_user)
):
    """
    Get advanced analytics (if available).
    """
    if not has_feature(user, "ADVANCED_ANALYTICS"):
        # Return basic analytics instead
        return {"message": "Upgrade to PRO for advanced analytics"}
    
    # Return advanced analytics
    return {"advanced_data": "..."}
```

## HTTP Response

When a user without the required feature tries to access a protected endpoint:

**Status Code:** `402 Payment Required`

**Response:**
```json
{
    "detail": "Feature 'AI OCR' is not available with your current subscription plan. Please upgrade to access this feature."
}
```

## Adding New Features

1. Add the feature to `FEATURE_REGISTRY` in `app/core/features.py`:

```python
FEATURE_REGISTRY["NEW_FEATURE"] = {
    "name": "New Feature",
    "description": "Description of the feature",
    "allowed_plans": [SUBSCRIPTION_PLAN_PRO, SUBSCRIPTION_PLAN_SCHOOL]
}
```

2. Use it in your endpoints:

```python
@router.post("/new-endpoint")
async def new_endpoint(
    user: User = Depends(require_feature("NEW_FEATURE"))
):
    # Feature-protected logic
    pass
```

## Plan Hierarchy

- **FREE**: Basic features only
- **PRO**: All features except school-specific ones
- **SCHOOL**: All features

## Best Practices

1. **Don't hardcode plan checks** - Use `require_feature()` or `has_feature()`
2. **Centralize feature definitions** - All features in `FEATURE_REGISTRY`
3. **Clear error messages** - Users know which feature they need
4. **Graceful degradation** - Use `has_feature()` for optional features

## Example: Photo Upload with Feature Check

```python
from app.core.features import require_feature, has_feature

@router.post("/photo-library/upload")
async def upload_photo(
    file: UploadFile = File(...),
    user: User = Depends(require_feature("AI_OCR")),
    db: Session = Depends(get_db)
):
    """
    Upload photo with optional AI OCR.
    Requires AI_OCR feature for OCR functionality.
    """
    # OCR is available (guaranteed by require_feature)
    ocr_text = extract_text_from_image(file)
    
    # Check for additional features
    if has_feature(user, "UNLIMITED_EVIDENCE"):
        # No upload limit
        pass
    else:
        # Check upload count for FREE users
        upload_count = db.query(PhotoEvidence).filter_by(teacher_id=user.id).count()
        if upload_count >= 10:
            raise HTTPException(400, "Upload limit reached. Upgrade for unlimited uploads.")
    
    # Continue with upload
    ...
```









