"""add_subscription_fields_to_users

Revision ID: 110c8e83a2ff
Revises: 501622e712fb
Create Date: 2025-12-14 15:46:59.733886

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '110c8e83a2ff'
down_revision = '501622e712fb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add subscription_plan column with default "FREE"
    op.add_column('users', sa.Column('subscription_plan', sa.String(length=50), nullable=False, server_default='FREE'))
    
    # Add subscription_status column with default "ACTIVE"
    op.add_column('users', sa.Column('subscription_status', sa.String(length=50), nullable=False, server_default='ACTIVE'))
    
    # Add subscription_expires_at column (nullable)
    op.add_column('users', sa.Column('subscription_expires_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Drop columns in reverse order
    op.drop_column('users', 'subscription_expires_at')
    op.drop_column('users', 'subscription_status')
    op.drop_column('users', 'subscription_plan')
