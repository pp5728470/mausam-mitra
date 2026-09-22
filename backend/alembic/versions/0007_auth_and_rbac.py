"""auth and rbac

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-22 15:47:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '0007'
down_revision: Union[str, None] = '0006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # create role enum
    user_role_enum = postgresql.ENUM('CITIZEN', 'VERIFIER', 'ANALYST', 'ADMIN', name='user_role', create_type=False)
    user_role_enum.create(op.get_bind(), checkfirst=True)

    op.create_table('users',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('full_name', sa.String(length=255), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('role', user_role_enum, nullable=False, server_default='CITIZEN'),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    op.add_column('reports', sa.Column('reporter_user_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_reports_reporter_user_id'), 'reports', ['reporter_user_id'], unique=False)
    op.create_foreign_key('fk_reports_reporter_user_id', 'reports', 'users', ['reporter_user_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('fk_reports_reporter_user_id', 'reports', type_='foreignkey')
    op.drop_index(op.f('ix_reports_reporter_user_id'), table_name='reports')
    op.drop_column('reports', 'reporter_user_id')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    user_role_enum = postgresql.ENUM('CITIZEN', 'VERIFIER', 'ANALYST', 'ADMIN', name='user_role', create_type=False)
    user_role_enum.drop(op.get_bind(), checkfirst=True)
