"""harden_subscription_defaults_add_stripe_customer

Revision ID: f77415747eee
Revises: 80a97cf4eb69
Create Date: 2025-12-21 18:42:10.460136

This migration hardens subscription defaults to ensure ONLY Stripe webhooks can grant premium access:
- Adds stripe_customer_id column (nullable, unique, indexed)
- Updates existing FREE users with ACTIVE status to INACTIVE
- New users will default to subscription_status="INACTIVE" (via model server_default)

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f77415747eee'
down_revision = '80a97cf4eb69'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add stripe_customer_id column (nullable, unique, indexed)
    # This allows tracking which Stripe customer is associated with each user
    # For SQLite compatibility, we add the column first, then create the unique index
    op.add_column('users', sa.Column('stripe_customer_id', sa.String(length=255), nullable=True))
    
    # Create unique index for stripe_customer_id for faster lookups
    # SQLite supports unique indexes on nullable columns
    op.create_index('ix_users_stripe_customer_id', 'users', ['stripe_customer_id'], unique=True)
    
    # Harden subscription defaults: Update existing FREE users with ACTIVE status to INACTIVE
    # This ensures existing users do NOT automatically have premium access
    # Only Stripe webhooks should be able to set status to ACTIVE for premium plans
    bind = op.get_bind()
    if bind.dialect.name == 'sqlite':
        # SQLite-compatible update
        op.execute("""
            UPDATE users 
            SET subscription_status = 'INACTIVE' 
            WHERE subscription_plan = 'FREE' AND subscription_status = 'ACTIVE'
        """)
    else:
        # PostgreSQL and other databases
        op.execute("""
            UPDATE users 
            SET subscription_status = 'INACTIVE' 
            WHERE subscription_plan = 'FREE' AND subscription_status = 'ACTIVE'
        """)


def downgrade() -> None:
    # Drop index first
    op.drop_index('ix_users_stripe_customer_id', table_name='users')
    
    # Drop stripe_customer_id column
    op.drop_column('users', 'stripe_customer_id')
    
    # Note: We don't revert the subscription_status changes as that would re-grant premium access
    # If needed, manually update users back to ACTIVE status

