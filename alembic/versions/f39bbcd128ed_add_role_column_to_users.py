"""add_role_column_to_users

Revision ID: f39bbcd128ed
Revises: 110c8e83a2ff
Create Date: 2025-12-21 11:03:43.591100

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f39bbcd128ed'
down_revision = '110c8e83a2ff'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add role column with default "USER"
    # Check if column exists first (for SQLite compatibility and to handle already-applied migrations)
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'role' not in columns:
        op.add_column('users', sa.Column('role', sa.String(length=50), nullable=False, server_default='USER'))


def downgrade() -> None:
    # Drop role column
    op.drop_column('users', 'role')

