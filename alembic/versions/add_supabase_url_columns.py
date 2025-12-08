"""Add supabase_url column to photo_evidence and create evidence table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2025-01-27 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add supabase_url, supabase_path, and filename columns to photo_evidence table
    op.execute("""
        DO $$ 
        BEGIN
            -- Add supabase_url column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'photo_evidence' AND column_name = 'supabase_url'
            ) THEN
                ALTER TABLE photo_evidence ADD COLUMN supabase_url VARCHAR(1000);
            END IF;
            
            -- Add supabase_path column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'photo_evidence' AND column_name = 'supabase_path'
            ) THEN
                ALTER TABLE photo_evidence ADD COLUMN supabase_path VARCHAR(500);
            END IF;
            
            -- Add filename column if it doesn't exist (for backward compatibility)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'photo_evidence' AND column_name = 'filename'
            ) THEN
                ALTER TABLE photo_evidence ADD COLUMN filename VARCHAR(500);
                -- Populate filename from file_path for existing records
                UPDATE photo_evidence SET filename = SUBSTRING(file_path FROM '[^/\\\\]+$') WHERE filename IS NULL AND file_path IS NOT NULL;
                -- Set default for any remaining NULL values
                UPDATE photo_evidence SET filename = 'unknown' WHERE filename IS NULL;
                -- Make filename NOT NULL after populating
                ALTER TABLE photo_evidence ALTER COLUMN filename SET NOT NULL;
            END IF;
            
            -- Make file_path nullable (since we now use supabase_path for Supabase files)
            ALTER TABLE photo_evidence ALTER COLUMN file_path DROP NOT NULL;
        END $$;
    """)
    
    # Create evidence table
    op.create_table(
        'evidence',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('teacher_id', sa.String(length=36), nullable=False),
        sa.Column('gp_section', sa.String(length=10), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('filename', sa.String(length=500), nullable=False),
        sa.Column('supabase_path', sa.String(length=500), nullable=False),
        sa.Column('supabase_url', sa.String(length=1000), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evidence_id'), 'evidence', ['id'], unique=False)
    op.create_index(op.f('ix_evidence_teacher_id'), 'evidence', ['teacher_id'], unique=False)


def downgrade() -> None:
    # Drop evidence table
    op.drop_index(op.f('ix_evidence_teacher_id'), table_name='evidence')
    op.drop_index(op.f('ix_evidence_id'), table_name='evidence')
    op.drop_table('evidence')
    
    # Remove supabase_url, supabase_path, and filename columns from photo_evidence
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'photo_evidence' AND column_name = 'supabase_url'
            ) THEN
                ALTER TABLE photo_evidence DROP COLUMN supabase_url;
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'photo_evidence' AND column_name = 'supabase_path'
            ) THEN
                ALTER TABLE photo_evidence DROP COLUMN supabase_path;
            END IF;
            
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'photo_evidence' AND column_name = 'filename'
            ) THEN
                ALTER TABLE photo_evidence DROP COLUMN filename;
            END IF;
            
            -- Restore file_path NOT NULL constraint
            ALTER TABLE photo_evidence ALTER COLUMN file_path SET NOT NULL;
        END $$;
    """)



