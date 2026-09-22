"""Phase 6: verification fields + report_evidence.

Revision ID: 0002_evidence
Revises: 0001_initial
Create Date: 2026-09-22

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_evidence"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "reports",
        sa.Column(
            "verification_status",
            sa.String(length=32),
            nullable=False,
            server_default="PENDING",
        ),
    )
    op.add_column("reports", sa.Column("evidence_score", sa.Float(), nullable=True))
    op.add_column(
        "reports",
        sa.Column("verification_recommendation", sa.String(length=64), nullable=True),
    )
    op.add_column("reports", sa.Column("verification_notes", sa.Text(), nullable=True))
    op.add_column(
        "reports",
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "reports",
        sa.Column("verified_by", sa.String(length=128), nullable=True),
    )
    op.create_index(
        "ix_reports_verification_status",
        "reports",
        ["verification_status"],
    )

    op.create_table(
        "report_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evidence_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=128), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_report_evidence_report_id", "report_evidence", ["report_id"]
    )
    op.create_index(
        "ix_report_evidence_evidence_type", "report_evidence", ["evidence_type"]
    )
    op.create_index(
        "ix_report_evidence_created_at", "report_evidence", ["created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_report_evidence_created_at", table_name="report_evidence")
    op.drop_index("ix_report_evidence_evidence_type", table_name="report_evidence")
    op.drop_index("ix_report_evidence_report_id", table_name="report_evidence")
    op.drop_table("report_evidence")
    op.drop_index("ix_reports_verification_status", table_name="reports")
    op.drop_column("reports", "verified_by")
    op.drop_column("reports", "verified_at")
    op.drop_column("reports", "verification_notes")
    op.drop_column("reports", "verification_recommendation")
    op.drop_column("reports", "evidence_score")
    op.drop_column("reports", "verification_status")
