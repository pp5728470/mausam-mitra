from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import AlertStatus, AlertType, IncidentSeverity, RecipientScope
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.report import Report
    from app.models.user import User


class Alert(Base):
    """Persistent, deduplicated alert for the Notification Center."""

    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    alert_type: Mapped[AlertType] = mapped_column(
        Enum(AlertType, name="alert_type", native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    severity: Mapped[Optional[IncidentSeverity]] = mapped_column(
        Enum(IncidentSeverity, name="incident_severity", native_enum=False, length=32, create_type=False),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[AlertStatus] = mapped_column(
        Enum(AlertStatus, name="alert_status", native_enum=False, length=32),
        nullable=False,
        default=AlertStatus.UNREAD,
        index=True,
    )

    recipient_scope: Mapped[RecipientScope] = mapped_column(
        Enum(RecipientScope, name="recipient_scope", native_enum=False, length=32),
        nullable=False,
        index=True,
    )
    
    # Required for CITIZEN_REPORTER scope.
    recipient_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    report_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    metadata_payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    dedupe_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
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
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    incident: Mapped[Optional[Incident]] = relationship("Incident")
    report: Mapped[Optional[Report]] = relationship("Report")
    recipient: Mapped[Optional[User]] = relationship("User")
