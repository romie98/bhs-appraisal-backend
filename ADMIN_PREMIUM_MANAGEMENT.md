# Admin Premium Management Endpoints

## Overview
Admin-only endpoints to grant and revoke premium access to users. These endpoints allow administrators to manually manage user subscriptions without Stripe integration.

## Security
- **ADMIN role required**: Uses `require_admin_role` dependency
- **ENV guarded**: Only available when `ENABLE_ADMIN=true`
- **Activity logging**: All actions are logged to admin activity feed

## Endpoints

### POST /admin/users/{user_id}/grant-premium

Grants premium access to a user.

**Authentication:** Bearer token with ADMIN role

**Request Body (optional):**
```json
{
    "lifetime": false,  // If true, grants lifetime premium (no expiration)
    "days": 30          // Number of days until expiration (ignored if lifetime=true)
}
```

**Default behavior:** If no request body is provided, grants 30-day premium access.

**Actions:**
- Sets `subscription_plan = "PREMIUM"`
- Sets `subscription_status = "ACTIVE"`
- Sets `subscription_expires_at = now + days` (or `NULL` if lifetime=true)

**Response:**
```json
{
    "id": "user-uuid",
    "email": "user@example.com",
    "full_name": "User Name",
    "subscription_plan": "PREMIUM",
    "subscription_status": "ACTIVE",
    "subscription_expires_at": "2025-01-20T12:00:00Z",  // or null for lifetime
    "updated_at": "2024-12-21T12:00:00Z"
}
```

**Example Requests:**

Grant 30-day premium (default):
```bash
curl -X POST "http://localhost:8000/admin/users/{user_id}/grant-premium" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json"
```

Grant 90-day premium:
```bash
curl -X POST "http://localhost:8000/admin/users/{user_id}/grant-premium" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"days": 90}'
```

Grant lifetime premium:
```bash
curl -X POST "http://localhost:8000/admin/users/{user_id}/grant-premium" \
  -H "Authorization: Bearer ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"lifetime": true}'
```

---

### POST /admin/users/{user_id}/revoke-premium

Revokes premium access from a user.

**Authentication:** Bearer token with ADMIN role

**Request Body:** None required

**Actions:**
- Sets `subscription_plan = "FREE"`
- Sets `subscription_status = "INACTIVE"`
- Sets `subscription_expires_at = NULL`

**Response:**
```json
{
    "id": "user-uuid",
    "email": "user@example.com",
    "full_name": "User Name",
    "subscription_plan": "FREE",
    "subscription_status": "INACTIVE",
    "subscription_expires_at": null,
    "updated_at": "2024-12-21T12:00:00Z"
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/admin/users/{user_id}/revoke-premium" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

## Error Responses

### 404 Not Found
```json
{
    "detail": "User with id {user_id} not found"
}
```

### 400 Bad Request
```json
{
    "detail": "Days must be at least 1 if not lifetime"
}
```

### 403 Forbidden
```json
{
    "detail": "Admin access required"
}
```
(Returned if user is not an admin)

### 404 Not Found (Admin features disabled)
```json
{
    "detail": "Admin features are disabled"
}
```
(Returned if `ENABLE_ADMIN=false`)

## Implementation Details

### Files Created/Modified

1. **`app/modules/subscriptions/schemas.py`**
   - `GrantPremiumRequest`: Schema for grant request (not currently used, but available)
   - `SubscriptionUpdateResponse`: Schema for response (not currently used, but available)

2. **`app/modules/subscriptions/services.py`**
   - `grant_premium_access()`: Service function to grant premium
   - `revoke_premium_access()`: Service function to revoke premium

3. **`app/modules/admin_analytics/routers.py`**
   - Added two new endpoints to existing admin router
   - Uses `require_admin_role` for security
   - Logs actions to admin activity feed

4. **`app/modules/auth/constants.py`**
   - Added `SUBSCRIPTION_PLAN_PREMIUM = "PREMIUM"` constant
   - Added PREMIUM to `VALID_SUBSCRIPTION_PLANS` list

### Database Compatibility

- **SQLite**: Fully compatible
- **PostgreSQL**: Fully compatible
- Uses standard SQLAlchemy operations that work across databases

### Activity Logging

Both endpoints log admin actions to the admin activity feed:

**Grant Premium:**
- Action: `"GRANT_PREMIUM"`
- Resource: `"user:{user_id}"`
- Metadata: `{"granted_by": admin_email, "lifetime": bool, "days": int, "expires_at": datetime}`

**Revoke Premium:**
- Action: `"REVOKE_PREMIUM"`
- Resource: `"user:{user_id}"`
- Metadata: `{"revoked_by": admin_email, "previous_plan": str, "previous_status": str}`

Logging failures are caught and logged as warnings, but do not break the endpoint.

## Testing

### Prerequisites
1. Set `ENABLE_ADMIN=true` in environment
2. Create a user with `role = "ADMIN"`
3. Get admin JWT token

### Test Grant Premium
```bash
# Get user ID first
USER_ID="some-user-uuid"

# Grant 30-day premium (default)
curl -X POST "http://localhost:8000/admin/users/$USER_ID/grant-premium" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json"

# Grant lifetime premium
curl -X POST "http://localhost:8000/admin/users/$USER_ID/grant-premium" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"lifetime": true}'
```

### Test Revoke Premium
```bash
curl -X POST "http://localhost:8000/admin/users/$USER_ID/revoke-premium" \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

### Verify Changes
Check the user's subscription status:
```bash
curl "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer $USER_TOKEN"
```

## Notes

- **No Stripe integration**: These endpoints work independently of Stripe
- **No breaking changes**: Login and other functionality remain unchanged
- **Admin-only**: Regular users cannot access these endpoints
- **Activity logged**: All actions are tracked in admin activity feed
- **Timezone aware**: All datetime operations use UTC









