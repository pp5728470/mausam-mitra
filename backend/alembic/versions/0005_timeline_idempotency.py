"""Phase 7.2: timeline source_report_id for idempotent signal events.

Revision ID: 0005_timeline_idempotency
Revises: 0004_incident_origin
Create Date: 2026-09-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_timeline_idempotency"
down_revision: Union[str, None] = "0004_incident_origin"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "incident_timeline_events",
        sa.Column("source_report_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "ix_timeline_source_report",
        "incident_timeline_events",
        ["source_report_id"],
    )
    # One REPORT_SIGNAL (or other typed) event per report per incident.
    op.create_index(
        "uq_timeline_incident_type_report",
        "incident_timeline_events",
        ["incident_id", "event_type", "source_report_id"],
        unique=True,
        postgresql_where=sa.text("source_report_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_timeline_incident_type_report",
        table_name="incident_timeline_events",
    )
    op.drop_index("ix_timeline_source_report", table_name="incident_timeline_events")
    op.drop_column("incident_timeline_events", "source_report_id")
