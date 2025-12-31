# Subscription Hardening Implementation Summary

## Overview
This implementation hardens subscription defaults and access control to ensure **ONLY Stripe webhooks can grant premium access**. All new users and existing FREE users are set to INACTIVE status by default.

## Changes Made

### 1. User Model Updates (`app/modules/auth/models.py`)

**Updated Defaults:**
- `subscription_plan`: `"FREE"` (unchanged)
- `subscription_status`: `"INACTIVE"` (changed from `"ACTIVE"`)
- `subscription_expires_at`: `NULL` (unchanged)
- `stripe_customer_id`: `NULL` (new column)

**New Column:**
- `stripe_customer_id`: `String(255)`, nullable, unique, indexed
  - Tracks which Stripe customer is associated with each user
  - Allows webhook handlers to identify users by Stripe customer ID

### 2. Constants Update (`app/modules/auth/constants.py`)

Added `SUBSCRIPTION_STATUS_INACTIVE = "INACTIVE"` to the valid statuses list.

### 3. Guard Function (`app/modules/subscriptions/guards.py`)

Created `require_premium(user: User)` function that:
- Checks if user has premium plan (any plan that is not FREE)
- Verifies subscription status is "ACTIVE"
- Validates subscription hasn't expired (if `subscription_expires_at` is set)
- **Admin Bypass**: Users with `role == "ADMIN"` can bypass premium requirements

**Usage:**
```python
from app.modules.subscriptions.guards import require_premium

# In a route handler:
@router.get("/premium-feature")
def premium_feature(user: User = Depends(get_current_user)):
    require_premium(user)  # Raises 403 if not premium
    # ... premium feature code
```

### 4. Database Migration (`f77415747eee_harden_subscription_defaults_add_stripe_.py`)

**Actions:**
1. Adds `stripe_customer_id` column (nullable, unique, indexed)
2. Updates existing FREE users with ACTIVE status to INACTIVE
   - Ensures existing users do NOT automatically have premium access
3. New users will default to `subscription_status="INACTIVE"` via model `server_default`

**SQLite Compatibility:**
- Migration is fully SQLite-compatible
- Uses standard Alembic operations that work across databases

## Security Implications

### Before
- New users defaulted to `subscription_status="ACTIVE"`
- Existing FREE users could have ACTIVE status
- No way to track Stripe customer associations

### After
- New users default to `subscription_status="INACTIVE"`
- Existing FREE users with ACTIVE status are set to INACTIVE
- Only Stripe webhooks can grant premium access by:
  1. Setting `subscription_plan` to a premium plan (PRO, SCHOOL, etc.)
  2. Setting `subscription_status` to "ACTIVE"
  3. Optionally setting `subscription_expires_at`
  4. Setting `stripe_customer_id` to link the user to Stripe

## Default Values Summary

| Field | Default | Notes |
|-------|---------|-------|
| `subscription_plan` | `"FREE"` | Enforced at model level |
| `subscription_status` | `"INACTIVE"` | Changed from "ACTIVE" |
| `subscription_expires_at` | `NULL` | Enforced at model level |
| `stripe_customer_id` | `NULL` | New column, unique when set |

## Migration Steps

1. **Merge existing migration heads:**
   ```bash
   python -m alembic upgrade head
   ```
   This will:
   - Merge the two migration heads (role and activity logs)
   - Add `stripe_customer_id` column
   - Update existing FREE users to INACTIVE status

2. **Verify migration:**
   ```bash
   python -m alembic current
   python -m alembic history
   ```

## Guard Function Details

The `require_premium()` guard function enforces:

1. **Plan Check**: `subscription_plan != "FREE"`
2. **Status Check**: `subscription_status == "ACTIVE"`
3. **Expiration Check**: `subscription_expires_at` is NULL or in the future
4. **Admin Bypass**: `role == "ADMIN"` allows access

**Error Responses:**
- `403 Forbidden` - "Premium subscription required"
- `403 Forbidden` - "Premium subscription inactive"
- `403 Forbidden` - "Premium subscription expired"

## Next Steps for Stripe Integration

When implementing Stripe webhooks, ensure they:

1. **On subscription creation/update:**
   - Set `subscription_plan` to premium plan (PRO, SCHOOL, etc.)
   - Set `subscription_status` to "ACTIVE"
   - Set `stripe_customer_id` to Stripe customer ID
   - Optionally set `subscription_expires_at`

2. **On subscription cancellation:**
   - Set `subscription_status` to "CANCELED" or "INACTIVE"
   - Keep `stripe_customer_id` for reference

3. **On subscription expiration:**
   - Set `subscription_status` to "INACTIVE"
   - Update `subscription_expires_at` if needed

## Testing

To test the guard function:

```python
from app.modules.subscriptions.guards import require_premium

# Test with FREE user (should raise 403)
user_free = User(subscription_plan="FREE", subscription_status="INACTIVE")
require_premium(user_free)  # Raises HTTPException

# Test with premium user (should pass)
user_premium = User(
    subscription_plan="PRO",
    subscription_status="ACTIVE",
    subscription_expires_at=None
)
require_premium(user_premium)  # Passes

# Test with admin (should bypass)
user_admin = User(role="ADMIN", subscription_plan="FREE")
require_premium(user_admin)  # Passes (admin bypass)
```

## Notes

- **No breaking changes**: Login functionality is preserved
- **No column removals**: All existing columns remain
- **SQLite compatible**: All migrations work with SQLite
- **Production safe**: Uses server_defaults and proper constraints
- **Guard not yet attached**: The guard function is ready but not yet used in routes (as requested)







