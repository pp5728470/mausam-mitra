"""Phase 7.1: incident origin + integrity classification.

Revision ID: 0004_incident_origin
Revises: 0003_correlation
Create Date: 2026-09-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_incident_origin"
down_revision: Union[str, None] = "0003_correlation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "incidents",
        sa.Column(
            "origin",
            sa.String(length=32),
            nullable=False,
            server_default="SEEDED",
        ),
    )
    op.create_index("ix_incidents_origin", "incidents", ["origin"])

    # Genuine Phase 7 correlation clusters.
    op.execute(
        """
        UPDATE incidents
        SET origin = 'CORRELATED'
        WHERE correlation_score IS NOT NULL
          AND independent_report_count >= 2
        """
    )
    # Orphan / test incidents with no linked reports → MANUAL (not destroyed).
    op.execute(
        """
        UPDATE incidents
        SET origin = 'MANUAL'
        WHERE correlation_score IS NULL
          AND NOT EXISTS (
            SELECT 1 FROM reports r WHERE r.incident_id = incidents.id
          )
        """
    )
    # Remaining rows stay SEEDED (Phase 3 demo incidents with linked seed reports).


def downgrade() -> None:
    op.drop_index("ix_incidents_origin", table_name="incidents")
    op.drop_column("incidents", "origin")
