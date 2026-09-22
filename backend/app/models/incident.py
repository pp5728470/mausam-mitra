from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Enum, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import (
    IncidentOrigin,
    IncidentSeverity,
    IncidentStatus,
    IncidentTrend,
)
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.incident_timeline import IncidentTimelineEvent
    from app.models.report import Report


class Incident(Base):
    """Correlated weather incident (operational picture — may be demo/simulated)."""

    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    incident_code: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    incident_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    severity: Mapped[IncidentSeverity] = mapped_column(
        Enum(IncidentSeverity, name="incident_severity", native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    status: Mapped[IncidentStatus] = mapped_column(
        Enum(IncidentStatus, name="incident_status", native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    trend: Mapped[IncidentTrend] = mapped_column(
        Enum(IncidentTrend, name="incident_trend", native_enum=False, length=32),
        nullable=False,
        default=IncidentTrend.STABLE,
    )
    origin: Mapped[IncidentOrigin] = mapped_column(
        Enum(IncidentOrigin, name="incident_origin", native_enum=False, length=32),
        nullable=False,
        default=IncidentOrigin.SEEDED,
        index=True,
    )

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    location = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True),
        nullable=False,
    )

    evidence_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    report_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Phase 7 correlation cluster metrics (no separate cluster table).
    correlation_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    independent_report_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    radius_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    time_window_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    first_detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
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

    reports: Mapped[list[Report]] = relationship(
        "Report",
        back_populates="incident",
        cascade="save-update",
    )
    timeline_events: Mapped[list[IncidentTimelineEvent]] = relationship(
        "IncidentTimelineEvent",
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="IncidentTimelineEvent.occurred_at",
    )
