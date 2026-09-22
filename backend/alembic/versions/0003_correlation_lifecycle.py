"""Phase 7 Alembic migration: correlation fields + lifecycle enum remap + timeline.

Revision ID: 0003_correlation
Revises: 0002_evidence
Create Date: 2026-09-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_correlation"
down_revision: Union[str, None] = "0002_evidence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "incidents",
        sa.Column("correlation_score", sa.Float(), nullable=True),
    )
    op.add_column(
        "incidents",
        sa.Column(
            "independent_report_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column("incidents", sa.Column("radius_km", sa.Float(), nullable=True))
    op.add_column(
        "incidents",
        sa.Column("time_window_minutes", sa.Integer(), nullable=True),
    )

    # Remap legacy lifecycle / trend values into Phase 7 vocabulary.
    op.execute(
        sa.text(
            """
            UPDATE incidents SET status = 'EMERGING'
            WHERE status = 'UNDER_REVIEW'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE incidents SET status = 'ACTIVE'
            WHERE status = 'VERIFIED'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE incidents SET trend = 'RISING'
            WHERE trend = 'INCREASING'
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE incidents SET trend = 'FALLING'
            WHERE trend = 'IMPROVING'
            """
        )
    )

    op.create_table(
        "incident_timeline_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "incident_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("incidents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("detail", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_incident_timeline_events_incident_id",
        "incident_timeline_events",
        ["incident_id"],
    )
    op.create_index(
        "ix_incident_timeline_events_occurred_at",
        "incident_timeline_events",
        ["occurred_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_incident_timeline_events_occurred_at",
        table_name="incident_timeline_events",
    )
    op.drop_index(
        "ix_incident_timeline_events_incident_id",
        table_name="incident_timeline_events",
    )
    op.drop_table("incident_timeline_events")
    op.drop_column("incidents", "time_window_minutes")
    op.drop_column("incidents", "radius_km")
    op.drop_column("incidents", "independent_report_count")
    op.drop_column("incidents", "correlation_score")
