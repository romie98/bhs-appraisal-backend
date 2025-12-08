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
    # Add all required columns to photo_evidence table
    op.execute("""
        DO $$ 
        BEGIN
            -- Add filename column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'photo_evidence' AND column_name = 'filename'
            ) THEN
                ALTER TABLE photo_evidence ADD COLUMN filename TEXT;
                -- Populate filename from file_path for existing records
                UPDATE photo_evidence SET filename = SUBSTRING(file_path FROM '[^/\\\\]+$') WHERE filename IS NULL AND file_path IS NOT NULL;
                -- Set default for any remaining NULL values
                UPDATE photo_evidence SET filename = 'unknown' WHERE filename IS NULL;
                -- Make filename NOT NULL after populating
                ALTER TABLE photo_evidence ALTER COLUMN filename SET NOT NULL;
            END IF;
            
            -- Add file_path column if it doesn't exist (make it nullable)
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'photo_evidence' AND column_name = 'file_path'
            ) THEN
                ALTER TABLE photo_evidence ADD COLUMN file_path TEXT;
            ELSE
                -- Make existing file_path nullable
                ALTER TABLE photo_evidence ALTER COLUMN file_path DROP NOT NULL;
            END IF;
            
            -- Add supabase_path column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'photo_evidence' AND column_name = 'supabase_path'
            ) THEN
                ALTER TABLE photo_evidence ADD COLUMN supabase_path TEXT;
            END IF;
            
            -- Add supabase_url column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'photo_evidence' AND column_name = 'supabase_url'
            ) THEN
                ALTER TABLE photo_evidence ADD COLUMN supabase_url TEXT;
            END IF;
            
            -- Add ocr_text column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'photo_evidence' AND column_name = 'ocr_text'
            ) THEN
                ALTER TABLE photo_evidence ADD COLUMN ocr_text TEXT;
            END IF;
            
            -- Add gp_recommendations as JSONB if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'photo_evidence' AND column_name = 'gp_recommendations'
            ) THEN
                ALTER TABLE photo_evidence ADD COLUMN gp_recommendations JSONB;
            ELSE
                -- Convert existing TEXT column to JSONB if needed
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'photo_evidence' 
                    AND column_name = 'gp_recommendations' 
                    AND data_type = 'text'
                ) THEN
                    -- Convert TEXT to JSONB
                    ALTER TABLE photo_evidence ALTER COLUMN gp_recommendations TYPE JSONB USING gp_recommendations::jsonb;
                END IF;
            END IF;
            
            -- Add gp_subsections as JSONB if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'photo_evidence' AND column_name = 'gp_subsections'
            ) THEN
                ALTER TABLE photo_evidence ADD COLUMN gp_subsections JSONB;
            ELSE
                -- Convert existing TEXT column to JSONB if needed
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'photo_evidence' 
                    AND column_name = 'gp_subsections' 
                    AND data_type = 'text'
                ) THEN
                    -- Convert TEXT to JSONB
                    ALTER TABLE photo_evidence ALTER COLUMN gp_subsections TYPE JSONB USING gp_subsections::jsonb;
                END IF;
            END IF;
            
            -- Add created_at column if it doesn't exist
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'photo_evidence' AND column_name = 'created_at'
            ) THEN
                ALTER TABLE photo_evidence ADD COLUMN created_at TIMESTAMP DEFAULT NOW();
            END IF;
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



