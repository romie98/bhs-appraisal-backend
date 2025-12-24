"""add_user_id_to_log_entries

Revision ID: 7193651b6509
Revises: f77415747eee
Create Date: 2025-12-23 20:35:33.510354

This migration adds user_id to log_entries table for data isolation:
- Adds user_id column (nullable initially)
- Assigns existing entries to first user (or deletes if no users exist)
- Makes user_id non-nullable
- Adds foreign key constraint to users table
- Adds index for performance

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7193651b6509'
down_revision = 'f77415747eee'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Add user_id column as nullable initially
    op.add_column('log_entries', sa.Column('user_id', sa.String(length=36), nullable=True))
    
    # Step 2: Handle existing entries - assign to first user or delete if no users exist
    bind = op.get_bind()
    result = bind.execute(sa.text("SELECT id FROM users LIMIT 1"))
    first_user = result.fetchone()
    
    if first_user:
        first_user_id = first_user[0]
        # Update all existing log entries to use first user
        bind.execute(sa.text("UPDATE log_entries SET user_id = :user_id WHERE user_id IS NULL"),
                     {"user_id": first_user_id})
    else:
        # No users exist - delete orphaned log entries
        bind.execute(sa.text("DELETE FROM log_entries WHERE user_id IS NULL"))
    
    # Step 3: Make user_id non-nullable
    op.alter_column('log_entries', 'user_id', nullable=False)
    
    # Step 4: Add foreign key constraint
    op.create_foreign_key(
        'fk_log_entries_user_id',
        'log_entries',
        'users',
        ['user_id'],
        ['id']
    )
    
    # Step 5: Add index for performance
    op.create_index('ix_log_entries_user_id', 'log_entries', ['user_id'])


def downgrade() -> None:
    # Drop index first
    op.drop_index('ix_log_entries_user_id', table_name='log_entries')
    
    # Drop foreign key constraint
    op.drop_constraint('fk_log_entries_user_id', 'log_entries', type_='foreignkey')
    
    # Drop user_id column
    op.drop_column('log_entries', 'user_id')

