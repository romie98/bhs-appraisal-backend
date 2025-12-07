# Quick Fix: /auth/register 500 Error

## The Problem
The `/auth/register` endpoint returns 500 because the database `users` table is missing required columns that the SQLAlchemy model expects.

## Immediate Solution

### Step 1: Check Current Database State

Run this in Railway PostgreSQL console:

```sql
SELECT column_name FROM information_schema.columns WHERE table_name = 'users';
```

Or run the diagnostic script:
```bash
python diagnose_database.py
```

### Step 2: Apply Migration

**Option A: Use Alembic (Recommended)**
```bash
alembic upgrade head
```

**Option B: Run SQL Manually in Railway**

1. Go to Railway → Your PostgreSQL Service → Query
2. Copy and paste the entire contents of `migration_add_full_name.sql`
3. Execute it

### Step 3: Verify

After migration, check again:
```sql
SELECT column_name FROM information_schema.columns WHERE table_name = 'users';
```

You should see:
- `id`
- `full_name` ✅
- `email`
- `password_hash` ✅
- `google_id` ✅
- `created_at`
- `updated_at`

### Step 4: Test

Try registering a user again. The 500 error should be resolved.

---

## What the Migration Does

1. Adds `full_name VARCHAR(255)` column
2. Adds `password_hash VARCHAR(255)` column  
3. Adds `google_id VARCHAR(255)` column with unique index
4. Drops old `password` column (if exists)
5. Updates existing rows with default `full_name` values
6. Makes `full_name` NOT NULL

**Safe to run multiple times** - won't break if columns already exist.

---

## If Migration Fails

### Check Railway Logs
Look for specific error messages in Railway deployment logs.

### Common Issues

1. **Permission Error**: Make sure database user has ALTER TABLE permissions
2. **Connection Error**: Verify DATABASE_URL is correct
3. **Column Already Exists**: Migration should handle this, but check logs

### Manual Fix

If migration fails, you can manually add columns one by one:

```sql
-- Add full_name
ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(255);

-- Update existing rows
UPDATE users SET full_name = SPLIT_PART(email, '@', 1) WHERE full_name IS NULL;

-- Make NOT NULL
ALTER TABLE users ALTER COLUMN full_name SET NOT NULL;

-- Add password_hash
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);

-- Add google_id
ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR(255);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_google_id ON users(google_id) WHERE google_id IS NOT NULL;
```

---

## After Fix

Once migration is applied:
- ✅ `/auth/register` will work (returns 201, not 500)
- ✅ New users can be created
- ✅ Login will work correctly
- ✅ Google OAuth will work

---

## Need Help?

Check the detailed guide: `MIGRATION_GUIDE.md`
