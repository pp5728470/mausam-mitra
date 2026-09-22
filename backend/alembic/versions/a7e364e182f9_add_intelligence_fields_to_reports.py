"""Add intelligence fields to reports

Revision ID: a7e364e182f9
Revises: 0007
Create Date: 2026-09-22 19:37:22.214667

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a7e364e182f9'
down_revision: Union[str, None] = '0007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Phase 10: AI-Assisted Signal Intelligence
    op.add_column('reports', sa.Column('classified_category', sa.String(length=128), nullable=True))
    op.add_column('reports', sa.Column('classifier_confidence', sa.Float(), nullable=True))
    op.add_column('reports', sa.Column('classification_explanation', sa.Text(), nullable=True))
    op.add_column('reports', sa.Column('classification_signals', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('reports', sa.Column('classified_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('reports', sa.Column('classifier_version', sa.String(length=32), nullable=True))


def downgrade() -> None:
    op.drop_column('reports', 'classifier_version')
    op.drop_column('reports', 'classified_at')
    op.drop_column('reports', 'classification_signals')
    op.drop_column('reports', 'classification_explanation')
    op.drop_column('reports', 'classifier_confidence')
    op.drop_column('reports', 'classified_category')
