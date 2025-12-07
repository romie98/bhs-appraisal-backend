"""Add full_name column to users table

Revision ID: a1b2c3d4e5f6
Revises: 3cfe11189e3f
Create Date: 2025-01-27 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '3cfe11189e3f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add full_name column to users table
    # Using nullable=True initially to handle existing rows
    # Existing rows will get a default value, then we can make it NOT NULL if needed
    op.add_column('users', sa.Column('full_name', sa.String(length=255), nullable=True))
    
    # Update existing rows to have a default full_name based on email
    # This ensures no NULL values remain
    op.execute("""
        UPDATE users 
        SET full_name = COALESCE(
            SPLIT_PART(email, '@', 1),
            'User'
        )
        WHERE full_name IS NULL
    """)
    
    # Now make the column NOT NULL
    op.alter_column('users', 'full_name',
                    existing_type=sa.String(length=255),
                    nullable=False)


def downgrade() -> None:
    # Remove full_name column
    op.drop_column('users', 'full_name')
