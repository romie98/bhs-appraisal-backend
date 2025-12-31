"""add_admin_premium_override_fields

Revision ID: f49f2f6b76ed
Revises: 7193651b6509
Create Date: 2025-12-30 19:38:19.915202

This migration adds admin premium override fields:
- admin_premium_override: Boolean (default False) - Admin can grant premium without Stripe
- admin_premium_expires_at: DateTime (nullable) - Optional expiration for admin override

These fields allow admins to grant premium access to test/invited users
without affecting Stripe-paying users.

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f49f2f6b76ed'
down_revision = '7193651b6509'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add admin_premium_override column
    # For SQLite compatibility, use Integer (0/1) instead of Boolean
    bind = op.get_bind()
    if bind.dialect.name == 'sqlite':
        op.add_column('users', sa.Column('admin_premium_override', sa.Integer(), nullable=False, server_default='0'))
    else:
        # PostgreSQL and other databases - use Boolean
        op.add_column('users', sa.Column('admin_premium_override', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add admin_premium_expires_at column (nullable)
    op.add_column('users', sa.Column('admin_premium_expires_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Drop columns in reverse order
    op.drop_column('users', 'admin_premium_expires_at')
    op.drop_column('users', 'admin_premium_override')

