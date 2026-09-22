"""initial postgis reports incidents

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-22

"""

from typing import Sequence, Union

import geoalchemy2.types
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    op.create_table(
        "incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("incident_code", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("incident_type", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("trend", sa.String(length=32), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column(
            "location",
            geoalchemy2.types.Geometry(
                geometry_type="POINT", srid=4326, from_text="ST_GeomFromEWKT", name="geometry"
            ),
            nullable=False,
        ),
        sa.Column("evidence_score", sa.Float(), nullable=False),
        sa.Column("report_count", sa.Integer(), nullable=False),
        sa.Column(
            "first_detected_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("incident_code"),
    )
    op.create_index("ix_incidents_incident_code", "incidents", ["incident_code"])
    op.create_index("ix_incidents_incident_type", "incidents", ["incident_type"])
    op.create_index("ix_incidents_severity", "incidents", ["severity"])
    op.create_index("ix_incidents_status", "incidents", ["status"])
    op.create_index("ix_incidents_created_at", "incidents", ["created_at"])
    # Spatial GiST index is created automatically by GeoAlchemy2 Geometry(spatial_index=True).

    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_name", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column(
            "location",
            geoalchemy2.types.Geometry(
                geometry_type="POINT", srid=4326, from_text="ST_GeomFromEWKT", name="geometry"
            ),
            nullable=False,
        ),
        sa.Column("reported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("media_url", sa.String(length=1024), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("classification", sa.String(length=128), nullable=True),
        sa.Column("classification_confidence", sa.Float(), nullable=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["incident_id"], ["incidents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reports_source_type", "reports", ["source_type"])
    op.create_index("ix_reports_reported_at", "reports", ["reported_at"])
    op.create_index("ix_reports_status", "reports", ["status"])
    op.create_index("ix_reports_incident_id", "reports", ["incident_id"])
    op.create_index("ix_reports_created_at", "reports", ["created_at"])
    # Spatial GiST index is created automatically by GeoAlchemy2 Geometry(spatial_index=True).


def downgrade() -> None:
    op.drop_index("ix_reports_created_at", table_name="reports")
    op.drop_index("ix_reports_incident_id", table_name="reports")
    op.drop_index("ix_reports_status", table_name="reports")
    op.drop_index("ix_reports_reported_at", table_name="reports")
    op.drop_index("ix_reports_source_type", table_name="reports")
    op.drop_index("idx_reports_location", table_name="reports", postgresql_using="gist")
    op.drop_table("reports")

    op.drop_index("ix_incidents_created_at", table_name="incidents")
    op.drop_index("ix_incidents_status", table_name="incidents")
    op.drop_index("ix_incidents_severity", table_name="incidents")
    op.drop_index("ix_incidents_incident_type", table_name="incidents")
    op.drop_index("ix_incidents_incident_code", table_name="incidents")
    op.drop_index("idx_incidents_location", table_name="incidents", postgresql_using="gist")
    op.drop_table("incidents")
