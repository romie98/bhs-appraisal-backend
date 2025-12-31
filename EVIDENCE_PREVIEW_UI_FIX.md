# Evidence Preview UI Fix Guide

> **Note:** For the latest modal overlay and preview fixes, see `EVIDENCE_MODAL_PATCH.md`

## Backend Changes (Completed)

### 1. Database Schema
- ✅ Added `title` column (TEXT, nullable) to `evidence` table
- ✅ Migration created: `alembic/versions/add_title_to_evidence.py`
- ✅ SQL script available: `add_title_to_evidence.sql`

### 2. API Endpoints Updated
- ✅ `/evidence/upload` now accepts `title` parameter
- ✅ All endpoints (`/upload`, `/`, `/{evidence_id}`) return `title` in response

**Example API Response:**
```json
{
    "id": "uuid",
    "teacher_id": "uuid",
    "gp_section": "GP1",
    "title": "My Evidence Title",
    "description": "Evidence description",
    "filename": "evidence.pdf",
    "supabase_path": "evidence/gp1/uuid.pdf",
    "supabase_url": "https://...supabase.co/storage/v1/object/public/uploads/evidence/gp1/uuid.pdf",
    "uploaded_at": "2025-01-27T14:00:00Z"
}
```

## Frontend Changes Required

### 1. Update Evidence Upload Form

**Find the evidence upload component** (likely `EvidenceUpload.jsx`, `UploadEvidence.jsx`, or similar)

**BEFORE:**
```javascript
const formData = new FormData();
formData.append('file', file);
formData.append('gp_section', gpSection || '');
formData.append('description', description);
```

**AFTER:**
```javascript
const [title, setTitle] = useState('');

// In the form:
<input
    type="text"
    placeholder="Evidence Title"
    value={title}
    onChange={(e) => setTitle(e.target.value)}
/>

// In the upload function:
const formData = new FormData();
formData.append('file', file);
formData.append('gp_section', gpSection || '');
formData.append('title', title);  // Add this
formData.append('description', description);
```

### 2. Fix Evidence Preview Modal

**Find the evidence preview modal component** (likely `EvidencePreview.jsx`, `EvidenceModal.jsx`, or similar)

**Add CSS class and styles:**

```css
/* Add to your CSS file or styled component */
.evidence-preview-modal {
    max-width: 900px;
    max-height: 80vh;
    overflow-y: auto;
    z-index: 9999;
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    padding: 24px;
}

.evidence-preview-image {
    width: 100%;
    max-height: 400px;
    object-fit: contain;
    margin: 16px 0;
}

.evidence-preview-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 9998;
}
```

**Update the modal component:**

```jsx
function EvidencePreview({ evidence, onClose }) {
    if (!evidence) return null;

    const isImage = /\.(jpg|jpeg|png|gif|webp)$/i.test(evidence.filename);
    const isPDF = /\.pdf$/i.test(evidence.filename);
    const isVideo = /\.(mp4|webm|ogg)$/i.test(evidence.filename);

    // Format date
    const uploadedDate = evidence.uploaded_at 
        ? new Date(evidence.uploaded_at).toLocaleDateString()
        : 'Unknown';

    // Get title or fallback
    const displayTitle = evidence.title || 'Untitled Evidence';

    return (
        <>
            {/* Overlay */}
            <div 
                className="evidence-preview-overlay"
                onClick={onClose}
            />
            
            {/* Modal */}
            <div className="evidence-preview-modal">
                {/* Close button */}
                <button 
                    onClick={onClose}
                    style={{
                        position: 'absolute',
                        top: '16px',
                        right: '16px',
                        background: 'none',
                        border: 'none',
                        fontSize: '24px',
                        cursor: 'pointer',
                        zIndex: 10000
                    }}
                >
                    ×
                </button>

                {/* Title */}
                <h2 style={{ marginTop: 0, marginBottom: '8px' }}>
                    {displayTitle}
                </h2>

                {/* Date */}
                <p style={{ color: '#666', fontSize: '14px', marginBottom: '16px' }}>
                    Uploaded: {uploadedDate}
                </p>

                {/* Description */}
                {evidence.description && (
                    <p style={{ marginBottom: '16px' }}>
                        {evidence.description}
                    </p>
                )}

                {/* File preview */}
                {isImage && (
                    <img 
                        src={evidence.supabase_url} 
                        alt={displayTitle}
                        className="evidence-preview-image"
                    />
                )}

                {isPDF && (
                    <iframe 
                        src={evidence.supabase_url} 
                        width="100%" 
                        height="600px"
                        title={displayTitle}
                        style={{ border: 'none', marginTop: '16px' }}
                    />
                )}

                {isVideo && (
                    <video 
                        controls 
                        src={evidence.supabase_url}
                        className="evidence-preview-image"
                    >
                        Your browser does not support video.
                    </video>
                )}

                {!isImage && !isPDF && !isVideo && (
                    <div style={{ marginTop: '16px' }}>
                        <a 
                            href={evidence.supabase_url} 
                            download={evidence.filename}
                            style={{
                                display: 'inline-block',
                                padding: '12px 24px',
                                background: '#007bff',
                                color: 'white',
                                textDecoration: 'none',
                                borderRadius: '4px'
                            }}
                        >
                            Download {evidence.filename}
                        </a>
                    </div>
                )}
            </div>
        </>
    );
}
```

### 3. Ensure GP Evidence Filtering

**Find where evidence is listed for GP sections** (likely in GP evidence pages)

**Verify filtering is correct:**

```javascript
// When fetching evidence for a specific GP section
async function fetchEvidenceForGP(gpSection, token) {
    const response = await fetch(
        `${apiUrl}/evidence?gp_section=${gpSection}`,
        {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        }
    );
    
    const evidence = await response.json();
    
    // Double-check filtering on frontend (defense in depth)
    return evidence.filter(item => 
        item.gp_section === gpSection.toUpperCase()
    );
}
```

**Example component:**

```jsx
function GPEvidencePage({ gpSection }) {
    const [evidence, setEvidence] = useState([]);
    const token = getAuthToken(); // Your auth method

    useEffect(() => {
        async function loadEvidence() {
            const data = await fetchEvidenceForGP(gpSection, token);
            setEvidence(data);
        }
        loadEvidence();
    }, [gpSection, token]);

    return (
        <div>
            <h1>Evidence for {gpSection}</h1>
            {evidence.map(item => (
                <EvidenceCard 
                    key={item.id} 
                    evidence={item}
                    onPreview={(item) => setPreviewItem(item)}
                />
            ))}
        </div>
    );
}
```

## Complete Example: Evidence Upload Form

```jsx
import { useState } from 'react';
import { apiUrl } from '../services/api';

function EvidenceUploadForm({ gpSection, token, onUploadSuccess }) {
    const [file, setFile] = useState(null);
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [uploading, setUploading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!file) return;

        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);
        formData.append('gp_section', gpSection || '');
        formData.append('title', title);  // Add title
        formData.append('description', description);

        try {
            const response = await fetch(`${apiUrl}/evidence/upload`, {
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
            onUploadSuccess(data);
            
            // Reset form
            setFile(null);
            setTitle('');
            setDescription('');
        } catch (error) {
            console.error('Upload error:', error);
            alert('Upload failed. Please try again.');
        } finally {
            setUploading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit}>
            <div>
                <label>File:</label>
                <input 
                    type="file" 
                    onChange={(e) => setFile(e.target.files[0])}
                    required
                />
            </div>

            <div>
                <label>Title:</label>
                <input
                    type="text"
                    placeholder="Evidence Title"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                />
            </div>

            <div>
                <label>Description:</label>
                <textarea
                    placeholder="Evidence Description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                />
            </div>

            <button type="submit" disabled={uploading || !file}>
                {uploading ? 'Uploading...' : 'Upload Evidence'}
            </button>
        </form>
    );
}
```

## Verification Checklist

### Backend:
- [x] Model includes `title` column
- [x] Upload endpoint accepts `title`
- [x] All endpoints return `title`
- [ ] Migration run on production database

### Frontend:
- [ ] Upload form includes title field
- [ ] Title is sent in formData
- [ ] Preview modal has `.evidence-preview-modal` class
- [ ] Modal has max-width: 900px, max-height: 80vh, overflow-y: auto
- [ ] Modal has z-index: 9999
- [ ] Images use `.evidence-preview-image` class with object-fit: contain
- [ ] Title displays instead of "Untitled Evidence"
- [ ] Date uses `new Date(uploaded_at).toLocaleDateString()`
- [ ] GP evidence pages only show evidence for that GP section

## Testing

1. **Upload with title:**
   - Fill in title field
   - Upload file
   - Verify title appears in response

2. **Preview modal:**
   - Click on evidence item
   - Verify modal doesn't overlap page elements
   - Verify image doesn't stretch
   - Verify title and date display correctly

3. **GP filtering:**
   - Navigate to GP1 evidence page
   - Verify only GP1 evidence shows
   - Navigate to GP2 evidence page
   - Verify only GP2 evidence shows

## Notes

- The backend now supports `title` in all evidence operations
- Migration must be run: `alembic upgrade head` or use SQL script
- Frontend should always use absolute API URLs (not relative)
- Modal z-index should be higher than other page elements
- Image object-fit: contain prevents stretching while maintaining aspect ratio














