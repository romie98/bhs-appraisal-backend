# Admin Activity Feed Implementation

## ✅ Implementation Complete

### Overview
A new admin activity feed system has been implemented to track system events for observability. The system logs user actions and makes them available to admins through a read-only API endpoint.

### 1. New Module: `app/modules/admin_activity/`

**Created Files:**
- `__init__.py` - Module exports
- `models.py` - `AdminActivityLog` SQLAlchemy model
- `schemas.py` - Pydantic schemas for API responses
- `services.py` - Logging and fetching functions

**Model Structure:**
```python
class AdminActivityLog(Base):
    __tablename__ = "admin_activity_log"
    
    id: Integer (primary key)
    user_id: String(36) (indexed, nullable)
    user_email: String(255) (indexed, nullable)
    action: String(100) (indexed, required)
    resource: String(500) (nullable)
    metadata: JSON (nullable)
    created_at: DateTime (indexed, auto-set)
```

### 2. Activity Logging Integration

**Logged Events:**

#### A) User Login
**Location:** `app/modules/auth/routers.py`
- All three login endpoints log activity:
  - `/auth/login` (OAuth2 form)
  - `/auth/login/json` (JSON body)
  - `/auth/login/google` (Google OAuth)
- Action: `"LOGIN"`
- Logged after successful authentication

#### B) Evidence Upload
**Location:** `app/modules/evidence/routers.py`
- Endpoint: `/evidence/upload`
- Action: `"UPLOAD_EVIDENCE"`
- Resource: Evidence record ID
- Metadata: `{"filename": ..., "gp_section": ...}`
- Logged after successful upload

#### C) AI OCR Usage
**Location:** `app/modules/photo_library/routers.py`
- Endpoint: `/photo-library/upload`
- Action: `"AI_OCR"`
- Resource: Filename
- Metadata: `{"text_length": ...}`
- Logged after successful OCR extraction

### 3. Service Functions

**`log_activity()`**
- Fail-safe: Never raises exceptions
- Logs activity to `admin_activity_log` table
- Handles missing user gracefully
- Rolls back on error without affecting main flow

**`get_recent_activity()`**
- Fetches recent activity logs
- Default limit: 25 records
- Ordered by `created_at DESC`
- Returns empty list on error

### 4. API Endpoint

**GET `/admin/activity`**
- **Location:** `app/modules/admin_analytics/routers.py` (updated)
- **Access:** ADMIN role required + `ENABLE_ADMIN=true`
- **Response:**
```json
{
  "events": [
    {
      "id": 1,
      "user_email": "teacher@example.com",
      "action": "LOGIN",
      "resource": null,
      "metadata": null,
      "created_at": "2025-01-27T10:30:00Z"
    },
    {
      "id": 2,
      "user_email": "teacher@example.com",
      "action": "UPLOAD_EVIDENCE",
      "resource": "evidence-uuid-123",
      "metadata": {
        "filename": "document.pdf",
        "gp_section": "GP1"
      },
      "created_at": "2025-01-27T10:35:00Z"
    }
  ]
}
```

### 5. Database Migration

**File:** `alembic/versions/501622e712fb_add_admin_activity_log_table.py`

- Creates `admin_activity_log` table
- Adds indexes on: `id`, `user_id`, `user_email`, `action`, `created_at`
- SQLite compatible
- Reversible (downgrade supported)

### 6. Security & Safety

✅ **Fail-Safe Logging:**
- All `log_activity()` calls wrapped in try/except
- Never breaks main application flows
- Silent failures (logged as warnings)

✅ **Role-Based Access:**
- Endpoint requires `ADMIN` role
- Uses `require_admin_role` dependency
- Returns 403 for non-admins
- Returns 404 if `ENABLE_ADMIN=false`

✅ **Read-Only:**
- No mutation endpoints
- Only GET operations
- No data modification

## 📋 Files Created/Modified

### Created:
1. `app/modules/admin_activity/__init__.py`
2. `app/modules/admin_activity/models.py`
3. `app/modules/admin_activity/schemas.py`
4. `app/modules/admin_activity/services.py`
5. `alembic/versions/501622e712fb_add_admin_activity_log_table.py`

### Modified:
1. `app/modules/auth/routers.py` - Added activity logging to all login endpoints
2. `app/modules/evidence/routers.py` - Added activity logging to upload endpoint
3. `app/modules/photo_library/routers.py` - Added activity logging after OCR
4. `app/modules/admin_analytics/routers.py` - Updated `/admin/activity` to use new service
5. `alembic/env.py` - Added `AdminActivityLog` import

## 🧪 Testing

### Run Migration:
```bash
alembic upgrade head
```

### Test Activity Logging:
1. Login as a user → Should log "LOGIN" event
2. Upload evidence → Should log "UPLOAD_EVIDENCE" event
3. Upload photo with OCR → Should log "AI_OCR" event

### Test API Endpoint:
```bash
# Get activity feed (requires ADMIN role)
curl -X GET "http://localhost:8000/admin/activity" \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

### Verify Database:
```sql
SELECT * FROM admin_activity_log ORDER BY created_at DESC LIMIT 25;
```

## ✅ Verification Checklist

- [x] New `admin_activity` module created
- [x] `AdminActivityLog` model defined
- [x] `log_activity()` service function implemented
- [x] `get_recent_activity()` service function implemented
- [x] Login events logged
- [x] Evidence upload events logged
- [x] AI OCR events logged
- [x] `/admin/activity` endpoint updated
- [x] Database migration created
- [x] Fail-safe error handling
- [x] Role-based access control
- [x] SQLite compatible
- [ ] Migration tested
- [ ] Endpoints tested
- [ ] Activity feed verified in frontend

## 🎯 Expected Results

After deployment:
- ✅ Login events appear in activity feed
- ✅ Evidence uploads appear in activity feed
- ✅ AI OCR usage appears in activity feed
- ✅ Admin Dashboard can display real-time activity
- ✅ No impact on main application flows
- ✅ Missing tables/errors don't crash the system

## 📝 Notes

- Activity logging is **non-blocking** - failures are silent
- All events include `user_email` for easy identification
- `resource` field stores entity IDs or file paths
- `metadata` field stores additional context (JSON)
- Default limit is 25 events (can be adjusted in service call)
- Events are ordered by most recent first















