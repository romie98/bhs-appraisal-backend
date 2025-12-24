"""Add title column to evidence table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2025-01-27 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add title column to evidence table
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'evidence' AND column_name = 'title'
            ) THEN
                ALTER TABLE evidence ADD COLUMN title TEXT;
            END IF;
        END $$;
    """)


def downgrade() -> None:
    # Remove title column from evidence table
    op.execute("""
        DO $$ 
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'evidence' AND column_name = 'title'
            ) THEN
                ALTER TABLE evidence DROP COLUMN title;
            END IF;
        END $$;
    """)












