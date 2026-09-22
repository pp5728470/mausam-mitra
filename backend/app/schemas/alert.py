from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.core.enums import AlertStatus, AlertType, IncidentSeverity, RecipientScope


class AlertBase(BaseModel):
    alert_type: AlertType
    severity: IncidentSeverity | None = None
    title: str
    message: str
    status: AlertStatus
    recipient_scope: RecipientScope
    incident_id: UUID | None = None
    report_id: UUID | None = None
    metadata_payload: dict[str, Any] | None = None


class AlertResponse(AlertBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    read_at: datetime | None = None
    acknowledged_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class AlertListResponse(BaseModel):
    items: list[AlertResponse]
    total: int
    unread_count: int
