-- Migration: Add full_name column to users table
-- This SQL can be run manually in Railway PostgreSQL if Alembic migration is not used
-- Run this BEFORE deploying the updated backend code

-- Step 1: Add column as nullable
ALTER TABLE users ADD COLUMN full_name VARCHAR(255);

-- Step 2: Update existing rows with default values
UPDATE users 
SET full_name = COALESCE(
    SPLIT_PART(email, '@', 1),
    'User'
)
WHERE full_name IS NULL;

-- Step 3: Make column NOT NULL
ALTER TABLE users ALTER COLUMN full_name SET NOT NULL;
