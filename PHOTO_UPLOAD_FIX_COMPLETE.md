# Photo Upload Fix - Complete Summary

## ✅ Backend Fixes Completed

### 1. Database Schema Updates
- ✅ Added `filename` column (VARCHAR(500), NOT NULL) to `photo_evidence` table
- ✅ Added `supabase_path` column (VARCHAR(500), nullable) to `photo_evidence` table
- ✅ Made `file_path` nullable (now only for local storage fallback)
- ✅ Ensured `supabase_url` column exists (VARCHAR(1000), nullable)

### 2. Model Updates
- ✅ Updated `PhotoEvidence` model in `app/modules/photo_library/models.py`
- ✅ Added `filename`, `supabase_path` fields
- ✅ Made `file_path` nullable

### 3. Schema Updates
- ✅ Updated `PhotoEvidenceResponse` schema to include all new fields
- ✅ Updated `PhotoEvidenceListItem` schema

### 4. Router Updates
- ✅ Updated `/photo-library/upload` endpoint to store `supabase_path` separately
- ✅ Updated to store `filename` separately
- ✅ Already uses `upload_bytes_to_supabase()` correctly (like `/evidence/upload`)
- ✅ Updated all response serialization (upload, list, get endpoints)

### 5. Migration
- ✅ Updated migration `add_supabase_url_columns.py` to add all required columns
- ✅ Handles backward compatibility (populates filename from existing file_path)
- ✅ Makes file_path nullable safely

## 📋 Frontend Fixes Required

See `FRONTEND_PHOTO_UPLOAD_FIX.md` for detailed instructions.

**Key Points:**
1. Replace all relative URLs (`/photo-library/upload`) with absolute URLs using `apiUrl`
2. Create/update API service to export `apiUrl` constant
3. Set `window.__APP_API_URL__` in `index.html`
4. Add environment variables for API URL
5. Add logging to verify correct URL usage

## 🚀 Deployment Steps

### Backend:
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
   
   Should show:
   - `filename` VARCHAR(500) NOT NULL
   - `file_path` VARCHAR(500) NULLABLE
   - `supabase_path` VARCHAR(500) NULLABLE
   - `supabase_url` VARCHAR(1000) NULLABLE

3. **Deploy Backend:**
   - Commit and push changes
   - Deploy to Railway
   - Verify `/photo-library/upload` endpoint in Swagger UI (`/docs`)

### Frontend:
1. **Apply Changes:**
   - Follow `FRONTEND_PHOTO_UPLOAD_FIX.md`
   - Replace all relative URLs
   - Set API URL configuration

2. **Test:**
   - Open browser DevTools → Network tab
   - Upload a photo
   - Verify request goes to Railway backend, not Vercel
   - Check console for correct API URL

## ✅ Verification Checklist

### Backend:
- [x] Model includes `filename`, `supabase_path`, `supabase_url`
- [x] Schema includes all new fields
- [x] Router stores and returns all fields correctly
- [x] Migration adds all required columns
- [x] Router uses `upload_bytes_to_supabase()` correctly
- [ ] Migration run on production database
- [ ] Backend deployed and tested

### Frontend:
- [ ] All `/photo-library/upload` calls use `${apiUrl}/photo-library/upload`
- [ ] `window.__APP_API_URL__` is set in `index.html`
- [ ] API service exports `apiUrl` correctly
- [ ] Environment variables configured
- [ ] Console logs show correct API URL
- [ ] Network tab shows requests to Railway, not Vercel

## 📝 Files Changed

### Backend:
1. `app/modules/photo_library/models.py` - Added fields
2. `app/modules/photo_library/schemas.py` - Updated response schema
3. `app/modules/photo_library/routers.py` - Updated upload/list/get endpoints
4. `alembic/versions/add_supabase_url_columns.py` - Updated migration

### Documentation:
1. `BACKEND_PHOTO_UPLOAD_FIX_SUMMARY.md` - Backend changes details
2. `FRONTEND_PHOTO_UPLOAD_FIX.md` - Frontend fix instructions
3. `PHOTO_UPLOAD_FIX_COMPLETE.md` - This summary

## 🎯 Expected Results

After all fixes:
- ✅ Photo uploads save correctly to backend database
- ✅ `supabase_path` and `supabase_url` are stored in database
- ✅ Frontend sends requests to Railway backend API
- ✅ No more "column supabase_url does not exist" errors
- ✅ No requests go to Vercel frontend domain
- ✅ All uploads use Supabase storage

## 🔍 Testing

### Backend Test:
```bash
curl -X POST https://your-railway-backend.up.railway.app/photo-library/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test-photo.jpg"
```

Expected response:
```json
{
    "id": "uuid",
    "teacher_id": "uuid",
    "filename": "test-photo.jpg",
    "file_path": null,
    "supabase_path": "evidence/uuid.jpg",
    "supabase_url": "https://...supabase.co/storage/v1/object/public/uploads/evidence/uuid.jpg",
    ...
}
```

### Frontend Test:
1. Open browser DevTools
2. Go to Network tab
3. Upload a photo
4. Verify:
   - Request URL: `https://your-railway-backend.up.railway.app/photo-library/upload`
   - NOT: `bhs-appraisal-frontend.vercel.app/photo-library/upload`
   - Status: 201 Created
   - Response includes `supabase_url`

## 📞 Support

If issues persist:
1. Check backend logs for errors
2. Verify database schema matches model
3. Check frontend console for API URL
4. Verify environment variables are set
5. Check Network tab for actual request URLs
