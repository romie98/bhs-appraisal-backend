# Frontend Photo Upload Fix Guide

## Problem
The frontend is sending photo upload requests to relative URLs (`/photo-library/upload`), which causes requests to go to the Vercel frontend domain instead of the Railway backend API.

**CRITICAL:** All photo upload requests must use absolute URLs pointing to the Railway backend, not relative URLs.

## Required Changes

### 1. Find All Photo Library Upload Calls

Search the entire frontend codebase for:
- `"/photo-library/upload"`
- `"/photo-library"`
- `fetch("/photo-library`
- `axios.post("/photo-library`
- Any other HTTP client calls to photo-library endpoints

### 2. Create/Update API Service

**File:** `src/services/api.js` (or `src/utils/api.js` or similar)

```javascript
// Get API URL from window global (set in index.html) or environment variable
export const apiUrl =
    window.__APP_API_URL__ ||
    import.meta.env.VITE_API_URL ||
    "http://localhost:8000";

// Helper function to build full API URL
export const getApiUrl = (endpoint) => {
    // Remove leading slash if present to avoid double slashes
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
    return `${apiUrl}/${cleanEndpoint}`;
};

// Export default API configuration
export default {
    baseURL: apiUrl,
    timeout: 30000, // 30 seconds for file uploads
};
```

### 3. Update index.html

**File:** `index.html` (or `public/index.html`)

Add this script tag in the `<head>` section (before other scripts):

```html
<script>
    // Set API URL from environment or use default
    window.__APP_API_URL__ = import.meta.env.VITE_API_URL || 'https://your-railway-backend-url.up.railway.app';
</script>
```

**OR** if using a build-time environment variable:

```html
<script>
    window.__APP_API_URL__ = '%VITE_API_URL%' || 'https://your-railway-backend-url.up.railway.app';
</script>
```

### 4. Fix Photo Upload Component

**Find the file that handles photo uploads** (likely `PhotoAnalyzer.jsx`, `PhotoUpload.jsx`, or similar)

**BEFORE (WRONG):**
```javascript
const formData = new FormData();
formData.append('file', file);

const response = await fetch("/photo-library/upload", {
    method: "POST",
    headers: {
        "Authorization": `Bearer ${token}`
    },
    body: formData
});
```

**AFTER (CORRECT):**
```javascript
import { apiUrl } from "../services/api"; // Adjust import path as needed

const formData = new FormData();
formData.append('file', file);

// Log for debugging
console.log("UPLOAD URL:", `${apiUrl}/photo-library/upload`);

const response = await fetch(`${apiUrl}/photo-library/upload`, {
    method: "POST",
    headers: {
        "Authorization": `Bearer ${token}`
    },
    body: formData
});
```

### 5. Fix All Photo Library API Calls

Search and replace ALL instances of:

**Pattern 1:**
```javascript
// OLD
fetch("/photo-library/...")

// NEW
import { apiUrl } from "../services/api";
fetch(`${apiUrl}/photo-library/...`)
```

**Pattern 2:**
```javascript
// OLD
axios.get("/photo-library/...")
axios.post("/photo-library/...")

// NEW
import { apiUrl } from "../services/api";
axios.get(`${apiUrl}/photo-library/...`)
axios.post(`${apiUrl}/photo-library/...`)
```

**Pattern 3:**
```javascript
// OLD
const response = await fetch("/photo-library", {
    headers: {
        Authorization: `Bearer ${token}`
    }
});

// NEW
import { apiUrl } from "../services/api";
const response = await fetch(`${apiUrl}/photo-library`, {
    headers: {
        Authorization: `Bearer ${token}`
    }
});
```

### 6. Environment Variables

**File:** `.env` or `.env.production`

Add:
```
VITE_API_URL=https://your-railway-backend-url.up.railway.app
```

**File:** `.env.local` (for local development)

Add:
```
VITE_API_URL=http://localhost:8000
```

### 7. Verification Checklist

After making changes:

- [ ] All `/photo-library/upload` calls use `${apiUrl}/photo-library/upload`
- [ ] All `/photo-library` calls use `${apiUrl}/photo-library`
- [ ] `window.__APP_API_URL__` is set in `index.html`
- [ ] API service file exports `apiUrl` correctly
- [ ] Environment variables are set for production and development
- [ ] Console logs show correct API URL when uploading
- [ ] Network tab shows requests going to Railway backend, not Vercel

### 8. Testing

1. Open browser DevTools → Network tab
2. Upload a photo
3. Verify the request URL is: `https://your-railway-backend.up.railway.app/photo-library/upload`
4. Verify the request is NOT going to: `bhs-appraisal-frontend.vercel.app/photo-library/upload`
5. Check console for: `UPLOAD URL: https://your-railway-backend.up.railway.app/photo-library/upload`

## Example Complete Fix

**File:** `src/components/PhotoAnalyzer.jsx` (example)

```javascript
import { useState } from 'react';
import { apiUrl } from '../services/api';

export default function PhotoAnalyzer() {
    const [uploading, setUploading] = useState(false);
    
    const handleUpload = async (file, token) => {
        setUploading(true);
        
        try {
            const formData = new FormData();
            formData.append('file', file);
            
            const uploadUrl = `${apiUrl}/photo-library/upload`;
            console.log("UPLOAD URL:", uploadUrl);
            
            const response = await fetch(uploadUrl, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`
                },
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`Upload failed: ${response.statusText}`);
            }
            
            const data = await response.json();
            console.log("Upload successful:", data);
            return data;
        } catch (error) {
            console.error("Upload error:", error);
            throw error;
        } finally {
            setUploading(false);
        }
    };
    
    // ... rest of component
}
```

## Notes

- The backend API URL should be your Railway deployment URL
- Never use relative URLs for API calls in production
- Always use the `apiUrl` constant from the service file
- Test in both development and production environments

