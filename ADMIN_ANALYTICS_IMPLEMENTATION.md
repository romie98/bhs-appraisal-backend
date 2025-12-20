# Admin Analytics Implementation

## ✅ Implementation Complete

### 1. Module Structure Created
**Location:** `app/modules/admin_analytics/`

- ✅ `__init__.py` - Module exports
- ✅ `models.py` - UserActivityLog SQLAlchemy model
- ✅ `helpers.py` - log_user_activity() helper function with metadata sanitization
- ✅ `schemas.py` - Pydantic schemas for API responses
- ✅ `dependencies.py` - Admin access control (ENV + role-based)
- ✅ `routers.py` - Read-only admin analytics endpoints

### 2. Database Model
**File:** `app/modules/admin_analytics/models.py`

- ✅ `UserActivityLog` model with all required fields:
  - `id` (UUID, primary key)
  - `user_id` (UUID, foreign key to users)
  - `action_type` (string, required, indexed)
  - `entity_type` (string, optional)
  - `entity_id` (UUID, optional)
  - `metadata` (JSON, optional, sanitized)
  - `created_at` (timestamp, default now, indexed)

### 3. Helper Function
**File:** `app/modules/admin_analytics/helpers.py`

- ✅ `log_user_activity()` - Lightweight, non-blocking
- ✅ Metadata sanitization removes sensitive data (tokens, passwords, URLs)
- ✅ Never raises exceptions (won't break business logic)

### 4. Activity Logging Integration
**Safe points only - after successful operations:**

- ✅ **Login** (`app/modules/auth/routers.py`):
  - Regular login endpoint
  - JSON login endpoint
  - Google login endpoint

- ✅ **Evidence Upload** (`app/modules/evidence/routers.py`):
  - Logs after successful upload with entity info

- ✅ **Lesson Plan Creation** (`app/modules/lesson_plans/routers.py`):
  - Upload endpoint
  - Create-from-text endpoint

- ⚠️ **Logbook Entry Creation** (`app/modules/logbook/routers.py`):
  - **Note:** Logbook entry creation endpoint does not have user authentication
  - **Note:** LogEntry model does not have user_id/teacher_id field
  - Logging skipped to avoid modifying existing business logic
  - **Recommendation:** Add authentication and user_id to LogEntry model if logging is needed

### 5. Admin Analytics Endpoints
**File:** `app/modules/admin_analytics/routers.py`

- ✅ `GET /admin/analytics/summary`
  - Returns: total_users, total_actions, active_users_last_7_days, active_users_last_30_days

- ✅ `GET /admin/analytics/recent-activity`
  - Returns: Last 50 activity logs with user email, action_type, entity_type, created_at

### 6. Security & Access Control
**File:** `app/modules/admin_analytics/dependencies.py`

- ✅ **ENV Guard:** `ENABLE_ADMIN=true` required (returns 404 if false)
- ✅ **Role-Based:** `ADMIN_EMAILS` env variable (comma-separated emails)
- ✅ **Read-Only:** No mutation endpoints
- ✅ **Data Sanitization:** Sensitive metadata removed

### 7. Router Registration
**File:** `app/main.py`

- ✅ Admin router only included if `ENABLE_ADMIN=true`
- ✅ Router returns 404 if admin features disabled

### 8. Database Migration
**File:** `alembic/versions/add_user_activity_logs_table.py`

- ✅ Creates `user_activity_logs` table
- ✅ Adds indexes for performance
- ✅ Includes downgrade function

**File:** `alembic/env.py`

- ✅ UserActivityLog model imported for migrations

### 9. Environment Configuration
**File:** `.env`

- ✅ `ENABLE_ADMIN=false` (disabled by default)
- ✅ `ADMIN_EMAILS=` (comma-separated admin emails)

## 🚀 Deployment Steps

### Step 1: Run Database Migration

```bash
alembic upgrade head
```

### Step 2: Configure Environment Variables

**For local development:**
```bash
ENABLE_ADMIN=true
ADMIN_EMAILS=admin@example.com,another-admin@example.com
```

**For production:**
- Set `ENABLE_ADMIN=true` in Railway environment variables
- Set `ADMIN_EMAILS` with comma-separated admin email addresses

### Step 3: Verify Setup

```bash
# Check migration ran
alembic current

# Test admin endpoint (should return 404 if ENABLE_ADMIN=false)
curl http://localhost:8000/admin/analytics/summary
```

## 📋 API Endpoints

### GET /admin/analytics/summary

**Requires:**
- `ENABLE_ADMIN=true`
- Admin user (email in `ADMIN_EMAILS`)
- Bearer token authentication

**Response:**
```json
{
    "total_users": 42,
    "total_actions": 1234,
    "active_users_last_7_days": 15,
    "active_users_last_30_days": 28
}
```

### GET /admin/analytics/recent-activity

**Requires:**
- `ENABLE_ADMIN=true`
- Admin user (email in `ADMIN_EMAILS`)
- Bearer token authentication

**Response:**
```json
{
    "activities": [
        {
            "user_email": "teacher@example.com",
            "action_type": "login",
            "entity_type": null,
            "created_at": "2025-01-27T14:00:00Z"
        },
        {
            "user_email": "teacher@example.com",
            "action_type": "evidence_upload",
            "entity_type": "evidence",
            "created_at": "2025-01-27T13:45:00Z"
        }
    ]
}
```

## ✅ Verification Checklist

- [x] Module structure created
- [x] UserActivityLog model created
- [x] log_user_activity() helper function created
- [x] Metadata sanitization implemented
- [x] Admin endpoints created (read-only)
- [x] ENV guard implemented (ENABLE_ADMIN)
- [x] Role-based access implemented (ADMIN_EMAILS)
- [x] Activity logging integrated at safe points
- [x] Router registered in main.py (env-guarded)
- [x] Database migration created
- [x] Environment variables added to .env
- [ ] Migration run on database
- [ ] Admin emails configured
- [ ] Endpoints tested

## 🔒 Security Features

1. **ENV Guard:** Admin features completely disabled if `ENABLE_ADMIN=false`
2. **Role-Based Access:** Only emails in `ADMIN_EMAILS` can access
3. **Read-Only:** No mutation endpoints (GET only)
4. **Data Sanitization:** Sensitive metadata automatically removed
5. **Non-Breaking:** Analytics failures never break business logic

## 📝 Notes

### Logbook Entry Creation
The logbook entry creation endpoint (`POST /logbook/`) does not currently have:
- User authentication dependency
- User ID in the LogEntry model

To enable logging for logbook entries:
1. Add `get_current_user` dependency to the endpoint
2. Add `teacher_id` or `user_id` field to LogEntry model
3. Add activity logging after successful creation

This was skipped to avoid modifying existing business logic.

### Activity Types Logged
- `login` - User login (all methods)
- `evidence_upload` - Evidence file upload
- `lesson_plan_create` - Lesson plan creation (upload or text)

## 🧪 Testing

### Test Admin Endpoints (with ENABLE_ADMIN=true):

```bash
# Get summary
curl -X GET "http://localhost:8000/admin/analytics/summary" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"

# Get recent activity
curl -X GET "http://localhost:8000/admin/analytics/recent-activity" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Test Access Control:

```bash
# Should return 404 if ENABLE_ADMIN=false
curl "http://localhost:8000/admin/analytics/summary"

# Should return 403 if user is not in ADMIN_EMAILS
curl -X GET "http://localhost:8000/admin/analytics/summary" \
  -H "Authorization: Bearer NON_ADMIN_TOKEN"
```

## 📁 Files Created/Modified

### Created:
1. `app/modules/admin_analytics/__init__.py`
2. `app/modules/admin_analytics/models.py`
3. `app/modules/admin_analytics/helpers.py`
4. `app/modules/admin_analytics/schemas.py`
5. `app/modules/admin_analytics/dependencies.py`
6. `app/modules/admin_analytics/routers.py`
7. `alembic/versions/add_user_activity_logs_table.py`
8. `ADMIN_ANALYTICS_IMPLEMENTATION.md` (this file)

### Modified:
1. `app/main.py` - Added admin router (env-guarded)
2. `app/modules/auth/routers.py` - Added activity logging to login endpoints
3. `app/modules/evidence/routers.py` - Added activity logging to upload endpoint
4. `app/modules/lesson_plans/routers.py` - Added activity logging to create endpoints
5. `alembic/env.py` - Added UserActivityLog import
6. `.env` - Added ENABLE_ADMIN and ADMIN_EMAILS variables

## 🎯 Expected Results

After deployment:
- ✅ User activities are logged automatically
- ✅ Admin endpoints return 404 if `ENABLE_ADMIN=false`
- ✅ Only admin users can access analytics
- ✅ Analytics data is sanitized (no sensitive info)
- ✅ Business logic is never broken by analytics failures
- ✅ Read-only access only (no mutations)




