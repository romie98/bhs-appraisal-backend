"""Add user_activity_logs table for admin analytics

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2025-01-27 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_activity_logs table
    op.create_table(
        'user_activity_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=False),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=True),
        sa.Column('entity_id', sa.String(length=36), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_activity_logs_id'), 'user_activity_logs', ['id'], unique=False)
    op.create_index(op.f('ix_user_activity_logs_user_id'), 'user_activity_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_activity_logs_action_type'), 'user_activity_logs', ['action_type'], unique=False)
    op.create_index(op.f('ix_user_activity_logs_created_at'), 'user_activity_logs', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop user_activity_logs table
    op.drop_index(op.f('ix_user_activity_logs_created_at'), table_name='user_activity_logs')
    op.drop_index(op.f('ix_user_activity_logs_action_type'), table_name='user_activity_logs')
    op.drop_index(op.f('ix_user_activity_logs_user_id'), table_name='user_activity_logs')
    op.drop_index(op.f('ix_user_activity_logs_id'), table_name='user_activity_logs')
    op.drop_table('user_activity_logs')










