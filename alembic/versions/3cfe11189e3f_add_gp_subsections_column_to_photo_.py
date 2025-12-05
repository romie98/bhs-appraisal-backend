"""Add gp_subsections column to photo_evidence

Revision ID: 3cfe11189e3f
Revises: 6ee4360bc3ad
Create Date: 2025-11-29 09:29:03.324626

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3cfe11189e3f'
down_revision = '6ee4360bc3ad'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add gp_subsections column to photo_evidence table
    # Using try-except to handle case where column already exists (if added manually)
    try:
        op.add_column('photo_evidence', sa.Column('gp_subsections', sa.Text(), nullable=True))
    except Exception:
        # Column might already exist if added manually
        pass


def downgrade() -> None:
    # Remove gp_subsections column
    op.drop_column('photo_evidence', 'gp_subsections')

