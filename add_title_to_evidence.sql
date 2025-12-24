-- Add title column to evidence table
-- Run this SQL directly on Railway PostgreSQL if migration doesn't work

ALTER TABLE evidence ADD COLUMN IF NOT EXISTS title TEXT;

-- Verify the column was added
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'evidence' AND column_name = 'title';












