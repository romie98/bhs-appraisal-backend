-- Migration: Add missing columns to users table
-- This SQL can be run manually in Railway PostgreSQL if Alembic migration is not used
-- Run this BEFORE deploying the updated backend code
-- Safe to run multiple times (uses IF NOT EXISTS)

-- Step 1: Add full_name column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'full_name'
    ) THEN
        ALTER TABLE users ADD COLUMN full_name VARCHAR(255);
    END IF;
END $$;

-- Step 2: Add password_hash column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'password_hash'
    ) THEN
        ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);
    END IF;
END $$;

-- Step 3: Add google_id column if it doesn't exist (with unique constraint)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'google_id'
    ) THEN
        ALTER TABLE users ADD COLUMN google_id VARCHAR(255);
        CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_id ON users(google_id) WHERE google_id IS NOT NULL;
    END IF;
END $$;

-- Step 4: Drop old 'password' column if it exists (migrated to password_hash)
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'password'
    ) THEN
        ALTER TABLE users DROP COLUMN password;
    END IF;
END $$;

-- Step 5: Update existing rows with default full_name values
UPDATE users 
SET full_name = COALESCE(
    SPLIT_PART(email, '@', 1),
    'User'
)
WHERE full_name IS NULL;

-- Step 6: Make full_name NOT NULL (only if it's currently nullable)
DO $$ 
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'full_name' 
        AND is_nullable = 'YES'
    ) THEN
        ALTER TABLE users ALTER COLUMN full_name SET NOT NULL;
    END IF;
END $$;












