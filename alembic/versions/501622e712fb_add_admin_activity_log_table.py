"""add_admin_activity_log_table

Revision ID: 501622e712fb
Revises: d4e5f6a7b8c9
Create Date: 2025-12-14 10:50:39.511652

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '501622e712fb'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create admin_activity_log table
    op.create_table(
        'admin_activity_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(length=36), nullable=True),
        sa.Column('user_email', sa.String(length=255), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource', sa.String(length=500), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),  # Column name stays "metadata" for database
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admin_activity_log_id'), 'admin_activity_log', ['id'], unique=False)
    op.create_index(op.f('ix_admin_activity_log_user_id'), 'admin_activity_log', ['user_id'], unique=False)
    op.create_index(op.f('ix_admin_activity_log_user_email'), 'admin_activity_log', ['user_email'], unique=False)
    op.create_index(op.f('ix_admin_activity_log_action'), 'admin_activity_log', ['action'], unique=False)
    op.create_index(op.f('ix_admin_activity_log_created_at'), 'admin_activity_log', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop indexes first
    op.drop_index(op.f('ix_admin_activity_log_created_at'), table_name='admin_activity_log')
    op.drop_index(op.f('ix_admin_activity_log_action'), table_name='admin_activity_log')
    op.drop_index(op.f('ix_admin_activity_log_user_email'), table_name='admin_activity_log')
    op.drop_index(op.f('ix_admin_activity_log_user_id'), table_name='admin_activity_log')
    op.drop_index(op.f('ix_admin_activity_log_id'), table_name='admin_activity_log')
    # Drop table
    op.drop_table('admin_activity_log')

