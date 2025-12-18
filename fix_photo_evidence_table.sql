-- Fix photo_evidence table schema
-- Run this SQL directly on Railway PostgreSQL if migration doesn't work

-- Add filename column
ALTER TABLE photo_evidence ADD COLUMN IF NOT EXISTS filename TEXT;

-- Populate filename from file_path for existing records
UPDATE photo_evidence 
SET filename = SUBSTRING(file_path FROM '[^/\\]+$') 
WHERE filename IS NULL AND file_path IS NOT NULL;

-- Set default for any remaining NULL values
UPDATE photo_evidence SET filename = 'unknown' WHERE filename IS NULL;

-- Make filename NOT NULL
ALTER TABLE photo_evidence ALTER COLUMN filename SET NOT NULL;

-- Add file_path column if missing (make it nullable)
ALTER TABLE photo_evidence ADD COLUMN IF NOT EXISTS file_path TEXT;

-- Make file_path nullable if it exists
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'photo_evidence' 
        AND column_name = 'file_path' 
        AND is_nullable = 'NO'
    ) THEN
        ALTER TABLE photo_evidence ALTER COLUMN file_path DROP NOT NULL;
    END IF;
END $$;

-- Add supabase_path column
ALTER TABLE photo_evidence ADD COLUMN IF NOT EXISTS supabase_path TEXT;

-- Add supabase_url column
ALTER TABLE photo_evidence ADD COLUMN IF NOT EXISTS supabase_url TEXT;

-- Add ocr_text column
ALTER TABLE photo_evidence ADD COLUMN IF NOT EXISTS ocr_text TEXT;

-- Add gp_recommendations as JSONB
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'photo_evidence' AND column_name = 'gp_recommendations'
    ) THEN
        ALTER TABLE photo_evidence ADD COLUMN gp_recommendations JSONB;
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'photo_evidence' 
        AND column_name = 'gp_recommendations' 
        AND data_type = 'text'
    ) THEN
        -- Convert TEXT to JSONB
        ALTER TABLE photo_evidence ALTER COLUMN gp_recommendations TYPE JSONB USING gp_recommendations::jsonb;
    END IF;
END $$;

-- Add gp_subsections as JSONB
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'photo_evidence' AND column_name = 'gp_subsections'
    ) THEN
        ALTER TABLE photo_evidence ADD COLUMN gp_subsections JSONB;
    ELSIF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'photo_evidence' 
        AND column_name = 'gp_subsections' 
        AND data_type = 'text'
    ) THEN
        -- Convert TEXT to JSONB
        ALTER TABLE photo_evidence ALTER COLUMN gp_subsections TYPE JSONB USING gp_subsections::jsonb;
    END IF;
END $$;

-- Add created_at column if missing
ALTER TABLE photo_evidence ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();

-- Verify the schema
SELECT 
    column_name, 
    data_type, 
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'photo_evidence'
ORDER BY ordinal_position;





