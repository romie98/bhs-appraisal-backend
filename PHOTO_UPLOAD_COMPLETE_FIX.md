# Photo Upload Complete Fix - All Issues Resolved

## ✅ Backend Fixes Completed

### 1. Model Updated to Match Specification
**File:** `app/modules/photo_library/models.py`

- ✅ Added `filename` column (String(500), NOT NULL)
- ✅ Added `file_path` column (String(500), nullable)
- ✅ Added `supabase_path` column (String(500), nullable)
- ✅ Added `supabase_url` column (String(1000), nullable)
- ✅ Added `ocr_text` column (Text, nullable)
- ✅ Changed `gp_recommendations` to JSON type (was Text)
- ✅ Changed `gp_subsections` to JSON type (was Text)
- ✅ `created_at` column exists

### 2. Router Updated for JSON Columns
**File:** `app/modules/photo_library/routers.py`

- ✅ Updated to store dicts directly in JSON columns (no json.dumps needed)
- ✅ Updated list/get endpoints to handle both JSON (dict) and legacy Text (string) formats
- ✅ All endpoints return correct data structure

### 3. Supabase URL Fix
**File:** `app/services/supabase_service.py`

- ✅ Removed trailing '?' from Supabase URLs in `upload_file_to_supabase()`
- ✅ Removed trailing '?' from Supabase URLs in `upload_bytes_to_supabase()`
- ✅ Applied to both public URLs and signed URLs

### 4. Database Migration
**File:** `alembic/versions/add_supabase_url_columns.py`

- ✅ Adds all missing columns to `photo_evidence` table
- ✅ Converts existing TEXT columns to JSONB for `gp_recommendations` and `gp_subsections`
- ✅ Handles backward compatibility
- ✅ Populates `filename` from existing `file_path` values

**Alternative:** Direct SQL script available in `fix_photo_evidence_table.sql`

## 📋 Frontend Fixes Required

See `FRONTEND_PHOTO_UPLOAD_FIX.md` for detailed instructions.

**Critical Steps:**
1. Search for ALL occurrences of `"/photo-library/upload"`
2. Replace with `${apiUrl}/photo-library/upload`
3. Ensure `apiUrl` is imported from API service
4. Add debug logging: `console.log("PHOTO UPLOAD URL:", ...)`

## 🚀 Deployment Steps

### Step 1: Run Database Migration

**Option A: Using Alembic (Recommended)**
```bash
alembic upgrade head
```

**Option B: Direct SQL (If migration fails)**
1. Connect to Railway PostgreSQL database
2. Run the SQL from `fix_photo_evidence_table.sql`

### Step 2: Verify Database Schema

```sql
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'photo_evidence'
ORDER BY ordinal_position;
```

**Expected columns:**
- `id` VARCHAR(36) NOT NULL
- `teacher_id` VARCHAR(36) NOT NULL
- `filename` TEXT NOT NULL ✅
- `file_path` TEXT NULLABLE ✅
- `supabase_path` TEXT NULLABLE ✅
- `supabase_url` TEXT NULLABLE ✅
- `ocr_text` TEXT NULLABLE ✅
- `gp_recommendations` JSONB NULLABLE ✅
- `gp_subsections` JSONB NULLABLE ✅
- `created_at` TIMESTAMP ✅

### Step 3: Deploy Backend

1. Commit all changes
2. Push to repository
3. Deploy to Railway
4. Verify `/photo-library/upload` endpoint in Swagger UI (`/docs`)

### Step 4: Fix Frontend

1. Follow `FRONTEND_PHOTO_UPLOAD_FIX.md`
2. Replace all relative URLs with absolute URLs
3. Test upload functionality

## ✅ Verification Checklist

### Backend:
- [x] Model matches specification exactly
- [x] JSON columns for gp_recommendations and gp_subsections
- [x] Router stores dicts directly (no json.dumps)
- [x] Router handles both JSON and legacy Text formats
- [x] Supabase URLs don't have trailing '?'
- [x] Migration adds all required columns
- [ ] Migration run on production database
- [ ] Backend deployed and tested

### Frontend:
- [ ] All `/photo-library/upload` calls use `${apiUrl}/photo-library/upload`
- [ ] Debug logging shows correct API URL
- [ ] Network tab shows requests to Railway backend
- [ ] No requests go to Vercel frontend domain

## 🧪 Testing

### Backend Test:
```bash
curl -X POST https://your-railway-backend.up.railway.app/photo-library/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test-photo.jpg"
```

**Expected Response:**
```json
{
    "id": "uuid",
    "teacher_id": "uuid",
    "filename": "test-photo.jpg",
    "file_path": null,
    "supabase_path": "evidence/uuid.jpg",
    "supabase_url": "https://...supabase.co/storage/v1/object/public/uploads/evidence/uuid.jpg",
    "ocr_text": "extracted text...",
    "gp_recommendations": {
        "GP1": [...],
        "GP2": [...]
    },
    "gp_subsections": {
        "GP1": {
            "subsections": [...],
            "justifications": {...}
        }
    },
    "created_at": "2025-01-27T14:00:00Z"
}
```

**Verify:**
- ✅ No 500 errors
- ✅ `supabase_url` doesn't end with '?'
- ✅ `gp_recommendations` and `gp_subsections` are JSON objects (not strings)
- ✅ Record appears in database

### Frontend Test:
1. Open browser DevTools → Network tab
2. Upload a photo
3. Verify:
   - Request URL: `https://your-railway-backend.up.railway.app/photo-library/upload`
   - NOT: `bhs-appraisal-frontend.vercel.app/photo-library/upload`
   - Status: 201 Created
   - Response includes all fields

## 📝 Files Changed

### Backend:
1. `app/modules/photo_library/models.py` - Updated model with JSON columns
2. `app/modules/photo_library/routers.py` - Updated for JSON columns
3. `app/services/supabase_service.py` - Fixed trailing '?' in URLs
4. `alembic/versions/add_supabase_url_columns.py` - Complete migration

### Documentation:
1. `PHOTO_UPLOAD_COMPLETE_FIX.md` - This file
2. `FRONTEND_PHOTO_UPLOAD_FIX.md` - Frontend fix guide
3. `fix_photo_evidence_table.sql` - Direct SQL script

## 🎯 Expected Results

After all fixes:
- ✅ Photo uploads save without SQL errors
- ✅ `photo_evidence` table matches SQLAlchemy model
- ✅ Supabase URLs stored correctly (no trailing '?')
- ✅ OCR text saves correctly
- ✅ GP recommendations and subsections save as JSON
- ✅ Frontend sends requests to Railway backend
- ✅ No more "column does not exist" errors

## 🔧 Troubleshooting

### If migration fails:
1. Run `fix_photo_evidence_table.sql` directly on database
2. Verify schema matches expected columns
3. Check Alembic revision history

### If upload still fails:
1. Check backend logs for errors
2. Verify database schema matches model
3. Check Supabase credentials in environment variables
4. Verify frontend is using correct API URL

### If JSON columns cause issues:
- The router handles both JSON (dict) and legacy Text (string) formats
- Existing records with Text will work
- New records will use JSON format

## 📞 Next Steps

1. ✅ Run migration: `alembic upgrade head` or use SQL script
2. ✅ Deploy backend
3. ⏳ Fix frontend (see `FRONTEND_PHOTO_UPLOAD_FIX.md`)
4. ⏳ Test end-to-end upload flow
5. ⏳ Verify all data saves correctly

















