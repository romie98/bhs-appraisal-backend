# Evidence Modal Overlay + Preview Issues - Patch Guide

## Files to Edit
- `src/components/EvidenceCard.jsx`

## Changes Required

### 1. Wrap Modal with Fullscreen Overlay

**Replace the current outer modal container with:**

```jsx
<div className="fixed inset-0 z-[9999] bg-black/50 flex items-center justify-center px-4">
  <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6 relative">
    {/* Modal content goes here */}
  </div>
</div>
```

**Notes:**
- `fixed inset-0` ensures full coverage
- `z-[9999]` ensures it sits above everything
- `bg-black/50` gives a soft, dark backdrop
- `max-h-[90vh] overflow-y-auto` ensures long content scrolls properly

### 2. Add Body Scroll Lock

**Add this useEffect hook inside the EvidenceCard component (where `isOpen` state becomes true):**

```jsx
import { useEffect } from 'react';

// Inside your EvidenceCard component
useEffect(() => {
  if (isOpen) {
    document.body.style.overflow = "hidden";
  } else {
    document.body.style.overflow = "auto";
  }
  return () => {
    document.body.style.overflow = "auto";
  };
}, [isOpen]);
```

### 3. Proper Image Detection

**Before rendering preview content, add:**

```jsx
const isImage = /\.(jpg|jpeg|png|gif|webp|svg)$/i.test(evidence.supabase_url);
```

**Note:** Use `supabase_url` for detection, not `filename`, as the URL extension is what matters for rendering.

### 4. Render Image Preview When Possible

**Inside the modal content, replace your preview section with:**

```jsx
{isImage ? (
  <img
    src={evidence.supabase_url}
    alt={evidence.title || "Evidence Preview"}
    className="w-full max-h-[70vh] object-contain rounded-xl"
  />
) : (
  <div className="flex flex-col items-center justify-center py-16 text-gray-500">
    <svg 
      className="w-12 h-12 text-gray-400" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2"
      viewBox="0 0 24 24"
    >
      <path 
        strokeLinecap="round" 
        strokeLinejoin="round"
        d="M9 13h6m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5l2 2h5a2 2 0 012 2v12a2 2 0 01-2 2z" 
      />
    </svg>
    <p className="mt-2">No preview available</p>
    <a
      href={evidence.supabase_url}
      target="_blank"
      rel="noopener noreferrer"
      className="text-blue-600 underline mt-2"
    >
      Open file in new tab
    </a>
  </div>
)}
```

### 5. Keep Action Buttons Below the Preview

**At the bottom of the modal, keep:**

```jsx
<div className="flex justify-between items-center mt-6 border-t pt-4">
  <div className="flex gap-6">
    <button 
      className="flex items-center gap-2 text-gray-700 hover:text-blue-600"
      onClick={() => window.open(evidence.supabase_url, '_blank')}
    >
      👁 View Image
    </button>
    <button 
      className="flex items-center gap-2 text-gray-700 hover:text-blue-600"
      onClick={() => {
        const link = document.createElement('a');
        link.href = evidence.supabase_url;
        link.download = evidence.filename;
        link.click();
      }}
    >
      ⬇ Download
    </button>
  </div>

  <div className="flex gap-6">
    <button 
      className="flex items-center gap-2 text-gray-700 hover:text-yellow-600"
      onClick={handleEdit}
    >
      ✏ Edit
    </button>
    <button 
      className="flex items-center gap-2 text-red-600 hover:text-red-700"
      onClick={handleDelete}
    >
      🗑 Delete
    </button>
  </div>
</div>
```

### 6. Ensure Image Grid Layout Remains Unchanged

**No changes are needed in your 3×3 layout.** The grid should remain as is.

## Complete Example Component Structure

```jsx
import { useState, useEffect } from 'react';

function EvidenceCard({ evidence }) {
  const [isOpen, setIsOpen] = useState(false);

  // Body scroll lock
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "auto";
    }
    return () => {
      document.body.style.overflow = "auto";
    };
  }, [isOpen]);

  // Image detection
  const isImage = /\.(jpg|jpeg|png|gif|webp|svg)$/i.test(evidence.supabase_url);

  const handleEdit = () => {
    // Your edit logic
  };

  const handleDelete = () => {
    // Your delete logic
  };

  return (
    <>
      {/* Your existing grid card */}
      <div onClick={() => setIsOpen(true)}>
        {/* Card content */}
      </div>

      {/* Modal */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-[9999] bg-black/50 flex items-center justify-center px-4"
          onClick={() => setIsOpen(false)}
        >
          <div 
            className="bg-white rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6 relative"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            <button
              onClick={() => setIsOpen(false)}
              className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 text-2xl"
            >
              ×
            </button>

            {/* Title */}
            <h2 className="text-2xl font-bold mb-2 pr-8">
              {evidence.title || 'Untitled Evidence'}
            </h2>

            {/* Date */}
            <p className="text-sm text-gray-500 mb-4">
              Uploaded: {new Date(evidence.uploaded_at).toLocaleDateString()}
            </p>

            {/* Description */}
            {evidence.description && (
              <p className="text-gray-700 mb-6">{evidence.description}</p>
            )}

            {/* Preview */}
            {isImage ? (
              <img
                src={evidence.supabase_url}
                alt={evidence.title || "Evidence Preview"}
                className="w-full max-h-[70vh] object-contain rounded-xl"
              />
            ) : (
              <div className="flex flex-col items-center justify-center py-16 text-gray-500">
                <svg 
                  className="w-12 h-12 text-gray-400" 
                  fill="none" 
                  stroke="currentColor" 
                  strokeWidth="2"
                  viewBox="0 0 24 24"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round"
                    d="M9 13h6m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5l2 2h5a2 2 0 012 2v12a2 2 0 01-2 2z" 
                  />
                </svg>
                <p className="mt-2">No preview available</p>
                <a
                  href={evidence.supabase_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 underline mt-2"
                >
                  Open file in new tab
                </a>
              </div>
            )}

            {/* Action buttons */}
            <div className="flex justify-between items-center mt-6 border-t pt-4">
              <div className="flex gap-6">
                <button 
                  className="flex items-center gap-2 text-gray-700 hover:text-blue-600"
                  onClick={() => window.open(evidence.supabase_url, '_blank')}
                >
                  👁 View Image
                </button>
                <button 
                  className="flex items-center gap-2 text-gray-700 hover:text-blue-600"
                  onClick={() => {
                    const link = document.createElement('a');
                    link.href = evidence.supabase_url;
                    link.download = evidence.filename;
                    link.click();
                  }}
                >
                  ⬇ Download
                </button>
              </div>

              <div className="flex gap-6">
                <button 
                  className="flex items-center gap-2 text-gray-700 hover:text-yellow-600"
                  onClick={handleEdit}
                >
                  ✏ Edit
                </button>
                <button 
                  className="flex items-center gap-2 text-red-600 hover:text-red-700"
                  onClick={handleDelete}
                >
                  🗑 Delete
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default EvidenceCard;
```

## Verification Checklist

After applying changes, verify:

- [x] Modal sits properly centered
- [x] Background does NOT scroll when modal is open
- [x] Image previews appear correctly
- [x] No grey leakage behind modal (overlay covers entire screen)
- [x] Non-image files show "No preview available" block
- [x] Action buttons remain functional
- [x] Grid layout remains unchanged

## Key Points

1. **Fullscreen Overlay:** `fixed inset-0` ensures complete coverage
2. **Scroll Lock:** `document.body.style.overflow = "hidden"` prevents background scrolling
3. **Image Detection:** Use URL extension, not filename
4. **Centered Modal:** `flex items-center justify-center` centers the modal
5. **Responsive Sizing:** `max-w-2xl max-h-[90vh]` ensures proper sizing
6. **Click Outside to Close:** Overlay click closes modal, but modal content click stops propagation

## Troubleshooting

### If modal still allows background scrolling:
- Verify `useEffect` is properly implemented
- Check that `isOpen` state is correctly tracked
- Ensure cleanup function runs on unmount

### If images don't display:
- Verify `supabase_url` is present in evidence object
- Check URL extension matches image pattern
- Verify CORS settings allow image display

### If overlay doesn't cover full screen:
- Ensure parent elements don't have `overflow: hidden`
- Check for conflicting z-index values
- Verify `fixed inset-0` is applied correctly










