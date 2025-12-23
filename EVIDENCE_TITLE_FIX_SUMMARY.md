# Evidence Title and Preview UI Fix - Summary

## ✅ Backend Changes Completed

### 1. Database Model Updated
**File:** `app/modules/evidence/models.py`

- ✅ Added `title` column (Text, nullable) to Evidence model
- ✅ Column is nullable to support existing records

### 2. Upload Endpoint Updated
**File:** `app/modules/evidence/routers.py`

- ✅ Added `title: Optional[str] = Form(None)` parameter
- ✅ Saves title to database record
- ✅ Returns title in API response

### 3. List and Get Endpoints Updated
**File:** `app/modules/evidence/routers.py`

- ✅ `/evidence/` (list) now returns `title` for each record
- ✅ `/evidence/{evidence_id}` (get) now returns `title`

### 4. Database Migration Created
**File:** `alembic/versions/add_title_to_evidence.py`

- ✅ Migration adds `title` column to `evidence` table
- ✅ Handles existing records (column is nullable)
- ✅ Includes downgrade function

**Alternative:** Direct SQL script available in `add_title_to_evidence.sql`

## 📋 Frontend Changes Required

See `EVIDENCE_PREVIEW_UI_FIX.md` for complete frontend guide.

**For latest modal overlay and preview fixes, see `EVIDENCE_MODAL_PATCH.md`**

### Key Frontend Tasks:

1. **Upload Form:**
   - Add title input field
   - Send title via `formData.append("title", value)`

2. **Preview Modal:**
   - Add CSS class `.evidence-preview-modal`
   - Set max-width: 900px, max-height: 80vh, overflow-y: auto
   - Set z-index: 9999
   - Add overlay with z-index: 9998

3. **Image Styling:**
   - Add `.evidence-preview-image` class
   - Set width: 100%, max-height: 400px, object-fit: contain

4. **Display Title and Date:**
   - Show `evidence.title || 'Untitled Evidence'`
   - Format date: `new Date(uploaded_at).toLocaleDateString()`

5. **GP Filtering:**
   - Ensure GP evidence pages filter by `gp_section`
   - Use query parameter: `/evidence?gp_section=GP1`

## 🚀 Deployment Steps

### Step 1: Run Database Migration

**Option A: Using Alembic (Recommended)**
```bash
alembic upgrade head
```

**Option B: Direct SQL (If migration fails)**
1. Connect to Railway PostgreSQL database
2. Run: `ALTER TABLE evidence ADD COLUMN IF NOT EXISTS title TEXT;`
   Or use the SQL from `add_title_to_evidence.sql`

### Step 2: Verify Database Schema

```sql
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'evidence'
ORDER BY ordinal_position;
```

**Expected columns:**
- `id` VARCHAR(36) NOT NULL
- `teacher_id` VARCHAR(36) NOT NULL
- `gp_section` VARCHAR(10) NULLABLE
- `title` TEXT NULLABLE ✅ **NEW**
- `description` TEXT NULLABLE
- `filename` VARCHAR(500) NOT NULL
- `supabase_path` VARCHAR(500) NOT NULL
- `supabase_url` VARCHAR(1000) NULLABLE
- `uploaded_at` TIMESTAMPTZ NOT NULL

### Step 3: Deploy Backend

1. Commit all changes
2. Push to repository
3. Deploy to Railway
4. Verify `/evidence/upload` endpoint in Swagger UI (`/docs`)

### Step 4: Update Frontend

1. Follow `EVIDENCE_PREVIEW_UI_FIX.md`
2. Add title field to upload form
3. Fix preview modal styling
4. Test upload and preview functionality

## ✅ Verification Checklist

### Backend:
- [x] Model includes `title` column
- [x] Upload endpoint accepts `title`
- [x] All endpoints return `title`
- [ ] Migration run on production database
- [ ] Backend deployed and tested

### Frontend:
- [ ] Upload form includes title field
- [ ] Title is sent in formData
- [ ] Preview modal has correct CSS classes
- [ ] Modal doesn't overlap page elements
- [ ] Images don't stretch
- [ ] Title displays correctly
- [ ] Date displays correctly
- [ ] GP filtering works correctly

## 🧪 Testing

### Backend Test:
```bash
curl -X POST https://your-railway-backend.up.railway.app/evidence/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.pdf" \
  -F "gp_section=GP1" \
  -F "title=Test Evidence Title" \
  -F "description=Test description"
```

**Expected Response:**
```json
{
    "id": "uuid",
    "teacher_id": "uuid",
    "gp_section": "GP1",
    "title": "Test Evidence Title",
    "description": "Test description",
    "filename": "test.pdf",
    "supabase_path": "evidence/gp1/uuid.pdf",
    "supabase_url": "https://...supabase.co/storage/v1/object/public/uploads/evidence/gp1/uuid.pdf",
    "uploaded_at": "2025-01-27T14:00:00Z"
}
```

### Frontend Test:
1. Upload evidence with title
2. Verify title appears in list
3. Open preview modal
4. Verify:
   - Modal doesn't overlap elements
   - Image doesn't stretch
   - Title displays correctly
   - Date displays correctly
5. Navigate to GP evidence page
6. Verify only that GP's evidence shows

## 📝 Files Changed

### Backend:
1. `app/modules/evidence/models.py` - Added title column
2. `app/modules/evidence/routers.py` - Updated all endpoints
3. `alembic/versions/add_title_to_evidence.py` - Migration
4. `add_title_to_evidence.sql` - Direct SQL script

### Documentation:
1. `EVIDENCE_PREVIEW_UI_FIX.md` - Complete frontend guide
2. `EVIDENCE_TITLE_FIX_SUMMARY.md` - This file

## 🎯 Expected Results

After all fixes:
- ✅ Evidence uploads can include a title
- ✅ Title displays in evidence list and preview
- ✅ Preview modal doesn't overlap page elements
- ✅ Images display without stretching
- ✅ Date displays in readable format
- ✅ GP evidence pages only show relevant evidence

## 🔧 Troubleshooting

### If migration fails:
1. Run `add_title_to_evidence.sql` directly on database
2. Verify schema matches expected columns
3. Check Alembic revision history

### If title doesn't appear:
1. Check backend response includes `title` field
2. Verify frontend is reading `title` from response
3. Check browser console for errors

### If modal overlaps:
1. Verify CSS classes are applied
2. Check z-index values (modal: 9999, overlay: 9998)
3. Ensure modal is positioned correctly (fixed with transform)

## 📞 Next Steps

1. ✅ Run migration: `alembic upgrade head` or use SQL script
2. ✅ Deploy backend
3. ⏳ Update frontend (see `EVIDENCE_PREVIEW_UI_FIX.md`)
4. ⏳ Test upload with title
5. ⏳ Test preview modal
6. ⏳ Verify GP filtering









