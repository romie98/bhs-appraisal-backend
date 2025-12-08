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
    # Add supabase_url column to photo_evidence table
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'photo_evidence' AND column_name = 'supabase_url'
            ) THEN
                ALTER TABLE photo_evidence ADD COLUMN supabase_url VARCHAR(1000);
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
    
    # Remove supabase_url column from photo_evidence
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'photo_evidence' AND column_name = 'supabase_url'
            ) THEN
                ALTER TABLE photo_evidence DROP COLUMN supabase_url;
            END IF;
        END $$;
    """)


