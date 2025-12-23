"""Add missing columns to users table (full_name, password_hash, google_id)

Revision ID: a1b2c3d4e5f6
Revises: 3cfe11189e3f
Create Date: 2025-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '3cfe11189e3f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if columns exist before adding (safe migration)
    # Add full_name column if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'full_name'
            ) THEN
                ALTER TABLE users ADD COLUMN full_name VARCHAR(255);
            END IF;
        END $$;
    """)
    
    # Add password_hash column if it doesn't exist
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'password_hash'
            ) THEN
                ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);
            END IF;
        END $$;
    """)
    
    # Add google_id column if it doesn't exist (with unique constraint)
    op.execute("""
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
    """)
    
    # Drop old 'password' column if it exists (migrated to password_hash)
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'password'
            ) THEN
                ALTER TABLE users DROP COLUMN password;
            END IF;
        END $$;
    """)
    
    # Update existing rows to have a default full_name based on email
    # This ensures no NULL values remain before making it NOT NULL
    op.execute("""
        UPDATE users 
        SET full_name = COALESCE(
            SPLIT_PART(email, '@', 1),
            'User'
        )
        WHERE full_name IS NULL
    """)
    
    # Now make full_name NOT NULL (only if column exists and has no NULLs)
    op.execute("""
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
    """)


def downgrade() -> None:
    # Remove added columns
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'full_name'
            ) THEN
                ALTER TABLE users DROP COLUMN full_name;
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'google_id'
            ) THEN
                DROP INDEX IF EXISTS ix_users_google_id;
                ALTER TABLE users DROP COLUMN google_id;
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'users' AND column_name = 'password_hash'
            ) THEN
                ALTER TABLE users DROP COLUMN password_hash;
            END IF;
        END $$;
    """)















