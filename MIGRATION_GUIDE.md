# Database Migration Guide: Fix /auth/register 500 Error

## Problem
The `/auth/register` endpoint returns a 500 Internal Server Error due to a database schema mismatch between the SQLAlchemy User model and the PostgreSQL `users` table in Railway.

## Solution
Add missing columns to the `users` table to match the SQLAlchemy model.

---

## Step 1: Check Current Database Structure

Run this SQL in Railway PostgreSQL console to see current columns:

```sql
-- File: check_users_table_structure.sql
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'users'
ORDER BY ordinal_position;
```

---

## Step 2: Apply Migration

### Option A: Use Alembic (Recommended)

```bash
alembic upgrade head
```

### Option B: Run SQL Manually in Railway

Execute the SQL from `migration_add_full_name.sql` in Railway PostgreSQL console.

---

## Required Columns (SQLAlchemy Model)

The `users` table must have these columns:

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | VARCHAR(36) | PRIMARY KEY | UUID string |
| `full_name` | VARCHAR(255) | NOT NULL | User's full name |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | User email |
| `password_hash` | VARCHAR(255) | NULLABLE | Hashed password (null for Google-only users) |
| `google_id` | VARCHAR(255) | UNIQUE, NULLABLE | Google OAuth ID |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Update timestamp |

---

## Migration Details

The migration safely:

1. ✅ Adds `full_name` column if missing
2. ✅ Adds `password_hash` column if missing
3. ✅ Adds `google_id` column with unique index if missing
4. ✅ Drops old `password` column if it exists (migrated to `password_hash`)
5. ✅ Updates existing rows with default `full_name` values
6. ✅ Makes `full_name` NOT NULL after updating existing data

**Safe to run multiple times** - uses `IF NOT EXISTS` checks.

---

## Verification Checklist

After running the migration:

- [ ] Run `check_users_table_structure.sql` to confirm all columns exist
- [ ] Test `/auth/register` endpoint - should return 201 (not 500)
- [ ] Test `/auth/login` endpoint - should work with hashed passwords
- [ ] Test `/auth/google` endpoint - should work with Google OAuth
- [ ] Verify new users are created successfully

---

## Files Updated

1. **`alembic/versions/add_full_name_to_users.py`** - Alembic migration
2. **`migration_add_full_name.sql`** - Manual SQL migration
3. **`check_users_table_structure.sql`** - Database structure checker

---

## Model Verification

✅ **User Model** (`app/modules/auth/models.py`):
- `full_name = Column(String(255), nullable=False)` ✓
- `password_hash = Column(String(255), nullable=True)` ✓
- `google_id = Column(String(255), unique=True, nullable=True)` ✓

✅ **Register Endpoint** (`app/modules/auth/routers.py`):
- Creates user with `full_name`, `email`, `password_hash` ✓

---

## After Migration

Once the migration is applied:

- ✅ `/auth/register` will no longer return 500 errors
- ✅ New users will be created successfully
- ✅ Login will work with hashed passwords
- ✅ Google OAuth will work correctly

---

## Troubleshooting

### If migration fails:

1. Check if columns already exist:
   ```sql
   SELECT column_name FROM information_schema.columns WHERE table_name = 'users';
   ```

2. If `full_name` exists but is NULL, run:
   ```sql
   UPDATE users SET full_name = COALESCE(SPLIT_PART(email, '@', 1), 'User') WHERE full_name IS NULL;
   ALTER TABLE users ALTER COLUMN full_name SET NOT NULL;
   ```

3. If unique constraint fails on `google_id`, check for duplicates:
   ```sql
   SELECT google_id, COUNT(*) FROM users WHERE google_id IS NOT NULL GROUP BY google_id HAVING COUNT(*) > 1;
   ```

---

## Cleanup Suggestions

For future migrations:

1. Always use `IF NOT EXISTS` for adding columns
2. Check column existence before altering constraints
3. Update existing rows before making columns NOT NULL
4. Test migrations on a staging database first
5. Keep migration files in version control
