"""merge_role_and_activity_logs

Revision ID: 80a97cf4eb69
Revises: 96dd5e564789, f39bbcd128ed
Create Date: 2025-12-21 18:42:05.575504

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '80a97cf4eb69'
down_revision = ('96dd5e564789', 'f39bbcd128ed')
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

