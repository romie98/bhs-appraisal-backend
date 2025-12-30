# Backend Photo Upload Fix Summary

## Changes Made

### 1. Database Model Updates

**File:** `app/modules/photo_library/models.py`

**Changes:**
- Added `filename` column (String(500), NOT NULL) - stores original filename
- Added `supabase_path` column (String(500), nullable) - stores Supabase storage path
- Made `file_path` nullable (now only used for local storage fallback)
- Kept `supabase_url` (String(1000), nullable) - stores public URL

**Before:**
```python
file_path = Column(String(500), nullable=False)  # Supabase path or local path
supabase_url = Column(String(1000), nullable=True)
```

**After:**
```python
filename = Column(String(500), nullable=False)  # Original filename (required)
file_path = Column(String(500), nullable=True)  # Local path (fallback only)
supabase_path = Column(String(500), nullable=True)  # Supabase storage path
supabase_url = Column(String(1000), nullable=True)  # Public URL from Supabase
```

### 2. Schema Updates

**File:** `app/modules/photo_library/schemas.py`

**Changes:**
- Added `filename` field to `PhotoEvidenceResponse`
- Added `supabase_path` field to `PhotoEvidenceResponse`
- Made `file_path` optional

**Updated Response Schema:**
```python
class PhotoEvidenceResponse(BaseModel):
    id: UUID
    teacher_id: str
    filename: str
    file_path: Optional[str] = None
    supabase_path: Optional[str] = None
    supabase_url: Optional[str] = None
    ocr_text: Optional[str] = None
    gp_recommendations: Dict[str, Any] = {}
    gp_subsections: Dict[str, Any] = {}
    created_at: datetime
```

### 3. Router Updates

**File:** `app/modules/photo_library/routers.py`

**Changes:**
- Updated upload endpoint to store `supabase_path` separately from `file_path`
- Updated to store `filename` separately
- Updated all response serialization to include new fields
- Router already uses `upload_bytes_to_supabase()` correctly (like `/evidence/upload`)

**Key Changes:**
1. **Upload Endpoint (`/upload`):**
   - Extracts `supabase_path` from Supabase upload result
   - Stores `filename` from uploaded file
   - Only sets `file_path` if local storage fallback is used
   - Returns all fields in response

2. **List Endpoint (`/`):**
   - Updated to include `filename` and `supabase_path` in response

3. **Get Endpoint (`/{id}`):**
   - Updated to include `filename` and `supabase_path` in response

### 4. Database Migration

**File:** `alembic/versions/add_supabase_url_columns.py`

**Changes:**
- Added migration to add `supabase_path` column to `photo_evidence` table
- Added migration to add `filename` column to `photo_evidence` table
- Made `file_path` nullable
- Populates `filename` from existing `file_path` values for backward compatibility
- Ensures `supabase_url` column exists (already in migration)

**Migration SQL:**
```sql
-- Add supabase_path column
ALTER TABLE photo_evidence ADD COLUMN IF NOT EXISTS supabase_path VARCHAR(500);

-- Add filename column
ALTER TABLE photo_evidence ADD COLUMN IF NOT EXISTS filename VARCHAR(500);
UPDATE photo_evidence SET filename = SUBSTRING(file_path FROM '[^/\\]+$') WHERE filename IS NULL;
ALTER TABLE photo_evidence ALTER COLUMN filename SET NOT NULL;

-- Make file_path nullable
ALTER TABLE photo_evidence ALTER COLUMN file_path DROP NOT NULL;

-- Ensure supabase_url exists
ALTER TABLE photo_evidence ADD COLUMN IF NOT EXISTS supabase_url VARCHAR(1000);
```

## Database Schema

### photo_evidence Table (Updated)

**Columns:**
- `id` VARCHAR(36) PRIMARY KEY
- `teacher_id` VARCHAR(36) NOT NULL
- `filename` VARCHAR(500) NOT NULL ⭐ **NEW**
- `file_path` VARCHAR(500) NULLABLE ⭐ **NOW NULLABLE**
- `supabase_path` VARCHAR(500) NULLABLE ⭐ **NEW**
- `supabase_url` VARCHAR(1000) NULLABLE
- `ocr_text` TEXT NULLABLE
- `gp_recommendations` TEXT NULLABLE
- `gp_subsections` TEXT NULLABLE
- `created_at` TIMESTAMPTZ NOT NULL

## API Endpoint

### POST `/photo-library/upload`

**Request:**
- Method: POST
- Headers: `Authorization: Bearer <token>`
- Body: `multipart/form-data` with `file` field

**Response:**
```json
{
    "id": "uuid",
    "teacher_id": "uuid",
    "filename": "photo.jpg",
    "file_path": null,  // Only set if local storage fallback used
    "supabase_path": "evidence/uuid.jpg",
    "supabase_url": "https://...supabase.co/storage/v1/object/public/uploads/evidence/uuid.jpg",
    "ocr_text": "extracted text...",
    "gp_recommendations": {...},
    "gp_subsections": {...},
    "created_at": "2025-01-27T14:00:00Z"
}
```

## Deployment Steps

1. **Run Migration:**
   ```bash
   alembic upgrade head
   ```

2. **Verify Database:**
   ```sql
   SELECT column_name, data_type, is_nullable
   FROM information_schema.columns
   WHERE table_name = 'photo_evidence'
   ORDER BY ordinal_position;
   ```

3. **Test Upload:**
   ```bash
   curl -X POST https://your-backend/photo-library/upload \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -F "file=@photo.jpg"
   ```

4. **Check Swagger UI:**
   - Navigate to `/docs`
   - Find "Photo Library" section
   - Test `/photo-library/upload` endpoint

## Verification

✅ Model includes `filename`, `supabase_path`, `supabase_url`
✅ Schema includes all new fields
✅ Router stores and returns all fields correctly
✅ Migration adds all required columns
✅ Router uses `upload_bytes_to_supabase()` like `/evidence/upload`
✅ Backward compatibility maintained (existing records get filename populated)

## Next Steps

1. Run migration: `alembic upgrade head`
2. Deploy backend
3. Update frontend (see `FRONTEND_PHOTO_UPLOAD_FIX.md`)
4. Test end-to-end upload flow















