from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import (
    ReportStatus,
    SourceType,
    VerificationRecommendation,
    VerificationStatus,
)
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.evidence import ReportEvidence
    from app.models.incident import Incident
    from app.models.user import User


class Report(Base):
    """Individual signal / report ingested by Mausam Mitra (simulated or live)."""

    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, name="source_type", native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    location = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )

    reported_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    media_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus, name="report_status", native_enum=False, length=32),
        nullable=False,
        default=ReportStatus.NEW,
        index=True,
    )
    classification: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    classification_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Phase 10: AI-Assisted Signal Intelligence
    classified_category: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    classifier_confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    classification_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    classification_signals: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    classified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    classifier_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)

    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(
            VerificationStatus,
            name="verification_status",
            native_enum=False,
            length=32,
        ),
        nullable=False,
        default=VerificationStatus.PENDING,
        index=True,
    )
    evidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    verification_recommendation: Mapped[Optional[VerificationRecommendation]] = (
        mapped_column(
            Enum(
                VerificationRecommendation,
                name="verification_recommendation",
                native_enum=False,
                length=64,
            ),
            nullable=True,
        )
    )
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    verified_by: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reporter_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    incident: Mapped[Optional[Incident]] = relationship(
        "Incident",
        back_populates="reports",
    )
    evidence_items: Mapped[list[ReportEvidence]] = relationship(
        "ReportEvidence",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="ReportEvidence.created_at",
    )
    reporter: Mapped[Optional[User]] = relationship(
        "User",
        back_populates="reports",
    )
