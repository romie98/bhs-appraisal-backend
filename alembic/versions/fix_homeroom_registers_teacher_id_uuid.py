"""fix homeroom_registers teacher_id to UUID

Revision ID: a1b2c3d4e5f7
Revises: 3d7555b1b561
Create Date: 2026-03-09

Converts homeroom_registers.teacher_id from VARCHAR to UUID so it matches
users.id (UUID) and fixes the foreign key constraint type mismatch.
PostgreSQL only; no-op for SQLite.
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f7"
down_revision = "3d7555b1b561"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    dialect_name = conn.dialect.name

    if dialect_name != "postgresql":
        return

    # Drop existing foreign key so we can change column type
    op.drop_constraint(
        "homeroom_registers_teacher_id_fkey",
        "homeroom_registers",
        type_="foreignkey",
    )

    # Convert teacher_id from VARCHAR to UUID
    op.execute(
        """
        ALTER TABLE homeroom_registers
        ALTER COLUMN teacher_id TYPE uuid
        USING teacher_id::uuid
        """
    )

    # Recreate foreign key to users.id
    op.create_foreign_key(
        "homeroom_registers_teacher_id_fkey",
        "homeroom_registers",
        "users",
        ["teacher_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    conn = op.get_bind()
    dialect_name = conn.dialect.name

    if dialect_name != "postgresql":
        return

    op.drop_constraint(
        "homeroom_registers_teacher_id_fkey",
        "homeroom_registers",
        type_="foreignkey",
    )

    # Convert teacher_id back to VARCHAR(36)
    op.execute(
        """
        ALTER TABLE homeroom_registers
        ALTER COLUMN teacher_id TYPE character varying(36)
        USING teacher_id::text
        """
    )

    op.create_foreign_key(
        "homeroom_registers_teacher_id_fkey",
        "homeroom_registers",
        "users",
        ["teacher_id"],
        ["id"],
    )
