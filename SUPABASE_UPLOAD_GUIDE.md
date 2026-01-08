# Supabase File Upload Implementation Guide

## Overview

This guide documents the complete Supabase file upload implementation for evidence files in the backend.

---

## 1. Supabase Client Initialization

**File:** `app/services/supabase_service.py`

✅ **Verified:** Client is correctly initialized using:
```python
from supabase import create_client, Client

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
```

**Environment Variables Required:**
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Service role key (not anon key)
- `SUPABASE_BUCKET` - Bucket name (defaults to "uploads")

---

## 2. File Upload Functions

### `upload_file_to_supabase(file: UploadFile, folder: str = "")`

Uploads a FastAPI UploadFile to Supabase Storage.

**Returns:**
```python
{
    "path": "evidence/uuid.ext",
    "filename": "uuid.ext",
    "url": "https://...supabase.co/storage/v1/object/public/uploads/evidence/uuid.ext",
    "bucket": "uploads"
}
```

### `upload_bytes_to_supabase(file_bytes: bytes, filename: str, folder: str = "", content_type: str = "")`

Uploads file bytes to Supabase Storage.

**Returns:** Same structure as above.

**Key Features:**
- ✅ Generates unique UUID filenames
- ✅ Returns public URL automatically
- ✅ Falls back to signed URL if public URL fails
- ✅ Handles folder organization (e.g., "evidence", "evidence/gp1")

---

## 3. Evidence Upload Route

**Endpoint:** `POST /evidence/upload`

**File:** `app/modules/evidence/routers.py`

**Request:**
- `file`: File to upload (multipart/form-data)
- `gp_section`: Optional GP section (GP1, GP2, etc.)
- `description`: Optional description

**Response:**
```json
{
    "id": "uuid",
    "teacher_id": "uuid",
    "gp_section": "GP1",
    "description": "Evidence description",
    "filename": "original-filename.pdf",
    "supabase_path": "evidence/gp1/uuid.pdf",
    "supabase_url": "https://...supabase.co/storage/v1/object/public/uploads/evidence/gp1/uuid.pdf",
    "uploaded_at": "2025-01-27T14:00:00Z"
}
```

**Features:**
- ✅ Authenticated endpoint (requires Bearer token)
- ✅ Organizes files by GP section in folders
- ✅ Stores metadata in database
- ✅ Returns public URL for frontend display

---

## 4. Photo Evidence Upload

**Endpoint:** `POST /photo-library/upload`

**File:** `app/modules/photo_library/routers.py`

**Updated to:**
- ✅ Upload to Supabase Storage (folder: "evidence")
- ✅ Fallback to local storage if Supabase fails
- ✅ Store `supabase_url` in database
- ✅ Run OCR on uploaded images
- ✅ AI analysis for GP recommendations

---

## 5. Database Schema

### Photo Evidence Table

**New Column:**
- `supabase_url` VARCHAR(1000) - Public URL from Supabase

### Evidence Table (New)

**Columns:**
- `id` VARCHAR(36) PRIMARY KEY
- `teacher_id` VARCHAR(36) NOT NULL
- `gp_section` VARCHAR(10) - GP1, GP2, etc.
- `description` TEXT
- `filename` VARCHAR(500) NOT NULL
- `supabase_path` VARCHAR(500) NOT NULL
- `supabase_url` VARCHAR(1000)
- `uploaded_at` TIMESTAMPTZ NOT NULL

---

## 6. Migration

**File:** `alembic/versions/add_supabase_url_columns.py`

**Run:**
```bash
alembic upgrade head
```

**What it does:**
1. Adds `supabase_url` column to `photo_evidence` table
2. Creates new `evidence` table

---

## 7. Frontend Integration

### Upload Request

```javascript
const formData = new FormData();
formData.append('file', file);
formData.append('gp_section', 'GP1');
formData.append('description', 'Evidence description');

const response = await fetch('https://api.example.com/evidence/upload', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    // Don't set Content-Type - browser will set it with boundary
  },
  body: formData
});

const data = await response.json();
// data.supabase_url contains the public URL
```

### Display File

**For Images:**
```jsx
<img src={evidence.supabase_url} alt={evidence.description} />
```

**For PDFs:**
```jsx
<iframe src={evidence.supabase_url} width="100%" height="600px" />
```

**For Other Files:**
```jsx
<a href={evidence.supabase_url} download={evidence.filename}>
  Download {evidence.filename}
</a>
```

---

## 8. Supabase Bucket Setup

### Required Bucket Configuration

1. **Create Bucket:** `uploads` (or set `SUPABASE_BUCKET` env var)

2. **Bucket Settings:**
   - **Public:** Yes (for public URLs)
   - **File size limit:** Set as needed
   - **Allowed MIME types:** Configure as needed

3. **Storage Policies:**
   - Allow authenticated users to upload
   - Allow public read access (for public URLs)

### Folder Structure

Files are organized as:
```
uploads/
  evidence/
    gp1/
      uuid1.pdf
      uuid2.jpg
    gp2/
      uuid3.pdf
    uuid4.jpg  (no GP section)
```

---

## 9. Error Handling

### Supabase Upload Fails

- **Photo Evidence:** Falls back to local storage
- **Evidence Upload:** Returns 500 error with details

### Public URL Fails

- Automatically falls back to signed URL (1 year expiration)

---

## 10. Testing

### Test Upload

```bash
curl -X POST https://api.example.com/evidence/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.pdf" \
  -F "gp_section=GP1" \
  -F "description=Test evidence"
```

### Verify in Supabase

1. Go to Supabase Dashboard → Storage
2. Check `uploads` bucket
3. Verify file exists in `evidence/gp1/` folder
4. Click file to verify public URL works

---

## 11. Troubleshooting

### "Supabase client not initialized"

- Check environment variables are set
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are correct

### "Failed to upload file"

- Check bucket exists and is public
- Verify service role key has storage permissions
- Check file size limits

### "Public URL not available"

- Ensure bucket is set to public
- Check file path is correct
- Verify Supabase storage policies

---

## 12. Files Modified/Created

### Backend Files

1. ✅ `app/services/supabase_service.py` - Updated to return public URLs
2. ✅ `app/modules/photo_library/models.py` - Added `supabase_url` column
3. ✅ `app/modules/photo_library/schemas.py` - Added `supabase_url` field
4. ✅ `app/modules/photo_library/routers.py` - Updated to use Supabase
5. ✅ `app/modules/evidence/routers.py` - New evidence upload route
6. ✅ `app/main.py` - Added evidence router
7. ✅ `alembic/versions/add_supabase_url_columns.py` - Migration

---

## Status

✅ **Implementation Complete**

All Supabase file upload functionality is now implemented and ready for use. The system:
- Uploads files to Supabase Storage
- Returns public URLs for frontend display
- Organizes files by GP section
- Stores metadata in database
- Handles errors gracefully























