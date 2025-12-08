# Supabase File Upload Fixes - Complete Summary

## ✅ All Fixes Applied

### 1. Supabase Client ✅
**File:** `app/services/supabase_service.py`

- ✅ Uses `from supabase import create_client, Client`
- ✅ Initializes with `create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)`
- ✅ Proper error handling and logging

### 2. File Upload Path Format ✅
**File:** `app/services/supabase_service.py`

- ✅ Correct format: `storage.from(BUCKET).upload(f"{folder}/{uuid}.{extension}", file_bytes)`
- ✅ Folder organization: `evidence`, `evidence/gp1`, `evidence/gp2`, etc.
- ✅ UUID-based filenames prevent conflicts
- ✅ Proper file extension detection

### 3. Public URL Return ✅
**File:** `app/services/supabase_service.py`

- ✅ After upload, gets public URL: `get_public_url(full_path)`
- ✅ Falls back to signed URL if public URL fails
- ✅ Returns URL in response: `{"path": "...", "url": "...", ...}`

### 4. Backend Record Creation ✅
**Files:** 
- `app/modules/evidence/routers.py` (new)
- `app/modules/photo_library/routers.py` (updated)

**Stores:**
- ✅ `teacher_id` (from authenticated user)
- ✅ `gp_section` (GP1, GP2, etc.)
- ✅ `description` (evidence description)
- ✅ `filename` (original filename)
- ✅ `supabase_path` (path in Supabase)
- ✅ `supabase_url` (public URL)
- ✅ `uploaded_at` (timestamp)

### 5. New Evidence Upload Route ✅
**File:** `app/modules/evidence/routers.py`

**Endpoint:** `POST /evidence/upload`

**Request:**
```javascript
const formData = new FormData();
formData.append('file', file);
formData.append('gp_section', 'GP1');  // Optional
formData.append('description', 'Evidence description');  // Optional

fetch('/evidence/upload', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`
    // Don't set Content-Type - browser sets it automatically
  },
  body: formData
});
```

**Response:**
```json
{
  "id": "uuid",
  "teacher_id": "uuid",
  "gp_section": "GP1",
  "description": "Evidence description",
  "filename": "original.pdf",
  "supabase_path": "evidence/gp1/uuid.pdf",
  "supabase_url": "https://...supabase.co/storage/v1/object/public/uploads/evidence/gp1/uuid.pdf",
  "uploaded_at": "2025-01-27T14:00:00Z"
}
```

### 6. Photo Evidence Updated ✅
**File:** `app/modules/photo_library/routers.py`

- ✅ Now uploads to Supabase (folder: "evidence")
- ✅ Falls back to local storage if Supabase fails
- ✅ Stores `supabase_url` in database
- ✅ Still runs OCR and AI analysis

### 7. Database Schema Updates ✅

**Migration:** `alembic/versions/add_supabase_url_columns.py`

**Changes:**
1. Adds `supabase_url` column to `photo_evidence` table
2. Creates new `evidence` table

**Run Migration:**
```bash
alembic upgrade head
```

---

## Frontend Integration Guide

### Upload Component Example

```jsx
import { useState } from 'react';

function EvidenceUpload({ token, gpSection }) {
  const [file, setFile] = useState(null);
  const [description, setDescription] = useState('');
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);

  const handleUpload = async () => {
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('gp_section', gpSection || '');
    formData.append('description', description);

    try {
      const response = await fetch('https://api.example.com/evidence/upload', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: formData
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Upload error:', error);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div>
      <input type="file" onChange={(e) => setFile(e.target.files[0])} />
      <textarea 
        placeholder="Description"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />
      <button onClick={handleUpload} disabled={uploading || !file}>
        {uploading ? 'Uploading...' : 'Upload'}
      </button>
      {result && (
        <div>
          <p>Uploaded: {result.filename}</p>
          <a href={result.supabase_url} target="_blank" rel="noopener noreferrer">
            View File
          </a>
        </div>
      )}
    </div>
  );
}
```

### Display Component Example

```jsx
function EvidenceDisplay({ evidence }) {
  const { supabase_url, filename, description } = evidence;
  
  // Determine file type
  const isImage = /\.(jpg|jpeg|png|gif|webp)$/i.test(filename);
  const isPDF = /\.pdf$/i.test(filename);
  const isVideo = /\.(mp4|webm|ogg)$/i.test(filename);

  return (
    <div>
      <h3>{description || filename}</h3>
      
      {isImage && (
        <img src={supabase_url} alt={description || filename} style={{ maxWidth: '100%' }} />
      )}
      
      {isPDF && (
        <iframe 
          src={supabase_url} 
          width="100%" 
          height="600px"
          title={filename}
        />
      )}
      
      {isVideo && (
        <video controls src={supabase_url} style={{ maxWidth: '100%' }}>
          Your browser does not support video.
        </video>
      )}
      
      {!isImage && !isPDF && !isVideo && (
        <a href={supabase_url} download={filename}>
          Download {filename}
        </a>
      )}
    </div>
  );
}
```

### List Evidence Example

```jsx
async function listEvidence(token, gpSection = null) {
  const url = gpSection 
    ? `https://api.example.com/evidence?gp_section=${gpSection}`
    : 'https://api.example.com/evidence';
    
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}
```

---

## Environment Variables Required

Set these in Railway (or your deployment platform):

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_BUCKET=uploads
```

**Important:** Use the **Service Role Key**, not the Anon key, for backend uploads.

---

## Supabase Bucket Setup

1. **Create Bucket:**
   - Name: `uploads` (or match `SUPABASE_BUCKET` env var)
   - Public: **Yes** (for public URLs)

2. **Storage Policies:**
   - Allow authenticated users to upload
   - Allow public read access

3. **Test Upload:**
   - Use Supabase Dashboard → Storage
   - Verify files appear in `uploads/evidence/` folder

---

## Files Created/Modified

### Backend Files

1. ✅ `app/services/supabase_service.py` - Updated to return public URLs
2. ✅ `app/modules/evidence/models.py` - New Evidence model
3. ✅ `app/modules/evidence/routers.py` - New evidence upload route
4. ✅ `app/modules/evidence/__init__.py` - Module init
5. ✅ `app/modules/photo_library/models.py` - Added supabase_url
6. ✅ `app/modules/photo_library/schemas.py` - Added supabase_url
7. ✅ `app/modules/photo_library/routers.py` - Updated to use Supabase
8. ✅ `app/main.py` - Added evidence router
9. ✅ `alembic/versions/add_supabase_url_columns.py` - Migration
10. ✅ `alembic/env.py` - Added Evidence model import

### Documentation

1. ✅ `SUPABASE_UPLOAD_GUIDE.md` - Complete implementation guide
2. ✅ `SUPABASE_FIXES_SUMMARY.md` - This file

---

## Testing Checklist

- [ ] Run migration: `alembic upgrade head`
- [ ] Set environment variables in Railway
- [ ] Create Supabase bucket and set to public
- [ ] Test `/evidence/upload` endpoint
- [ ] Verify file appears in Supabase Storage
- [ ] Verify public URL works in browser
- [ ] Test `/photo-library/upload` endpoint
- [ ] Verify photo evidence stores supabase_url
- [ ] Test frontend upload component
- [ ] Test frontend display component

---

## Status

✅ **All Backend Fixes Complete**

The backend now:
- ✅ Uploads files to Supabase Storage correctly
- ✅ Returns public URLs for frontend display
- ✅ Organizes files by GP section
- ✅ Stores all required metadata
- ✅ Handles errors gracefully

**Next Steps:**
1. Run migration
2. Set environment variables
3. Configure Supabase bucket
4. Test endpoints
5. Integrate frontend components




