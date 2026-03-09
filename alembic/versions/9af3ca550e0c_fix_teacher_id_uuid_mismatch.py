"""fix teacher_id uuid mismatch

Revision ID: 9af3ca550e0c
Revises: a1b2c3d4e5f7
Create Date: 2026-03-09 18:17:46.346086

Converts homeroom_registers.teacher_id and users.id to UUID for PostgreSQL.
No-op on SQLite (SQLite has no native UUID; string columns work with the model).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9af3ca550e0c'
down_revision = 'a1b2c3d4e5f7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return

    op.alter_column('homeroom_registers', 'teacher_id',
               existing_type=sa.VARCHAR(length=36),
               type_=sa.UUID(),
               existing_nullable=False)
    op.drop_constraint('homeroom_registers_teacher_id_fkey', 'homeroom_registers', type_='foreignkey')
    op.create_foreign_key('homeroom_registers_teacher_id_fkey', 'homeroom_registers', 'users', ['teacher_id'], ['id'], ondelete='CASCADE')
    op.alter_column('users', 'id',
               existing_type=sa.VARCHAR(length=36),
               type_=sa.UUID(),
               existing_nullable=False)
    op.alter_column('users', 'role',
               existing_type=sa.TEXT(),
               type_=sa.String(length=50),
               existing_nullable=False,
               existing_server_default=sa.text("'USER'"))
    op.alter_column('users', 'admin_premium_override',
               existing_type=sa.INTEGER(),
               type_=sa.Boolean(),
               existing_nullable=False,
               existing_server_default=sa.text("'false'"))
    op.drop_index(op.f('ix_users_id'), table_name='users')


def downgrade() -> None:
    conn = op.get_bind()
    if conn.dialect.name != "postgresql":
        return

    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.alter_column('users', 'admin_premium_override',
               existing_type=sa.Boolean(),
               type_=sa.INTEGER(),
               existing_nullable=False,
               existing_server_default=sa.text("'0'"))
    op.alter_column('users', 'role',
               existing_type=sa.String(length=50),
               type_=sa.TEXT(),
               existing_nullable=False,
               existing_server_default=sa.text("'USER'"))
    op.alter_column('users', 'id',
               existing_type=sa.UUID(),
               type_=sa.VARCHAR(length=36),
               existing_nullable=False)
    op.drop_constraint('homeroom_registers_teacher_id_fkey', 'homeroom_registers', type_='foreignkey')
    op.create_foreign_key('homeroom_registers_teacher_id_fkey', 'homeroom_registers', 'users', ['teacher_id'], ['id'])
    op.alter_column('homeroom_registers', 'teacher_id',
               existing_type=sa.UUID(),
               type_=sa.VARCHAR(length=36),
               existing_nullable=False)

