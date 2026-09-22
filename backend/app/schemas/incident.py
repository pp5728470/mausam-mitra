from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import (
    IncidentOrigin,
    IncidentSeverity,
    IncidentStatus,
    IncidentTrend,
)
from app.schemas.report import ReportRead


class IncidentCreate(BaseModel):
    """Payload for creating a demo / operational incident."""

    title: str = Field(min_length=1, max_length=255)
    incident_type: str = Field(min_length=1, max_length=128)
    description: str | None = None
    severity: IncidentSeverity
    status: IncidentStatus
    trend: IncidentTrend = IncidentTrend.STABLE
    origin: IncidentOrigin = IncidentOrigin.MANUAL
    latitude: float
    longitude: float
    evidence_score: float = Field(default=0.0, ge=0, le=100)
    report_count: int = Field(default=0, ge=0)
    correlation_score: float | None = Field(default=None, ge=0, le=100)
    independent_report_count: int = Field(default=0, ge=0)
    radius_km: float | None = Field(default=None, ge=0)
    time_window_minutes: int | None = Field(default=None, ge=0)
    incident_code: str | None = Field(
        default=None,
        max_length=32,
        description="Optional code; generated as MM-INC-#### when omitted",
    )
    first_detected_at: datetime | None = None

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, value: float) -> float:
        if value < -90 or value > 90:
            raise ValueError("latitude must be between -90 and 90")
        return value

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, value: float) -> float:
        if value < -180 or value > 180:
            raise ValueError("longitude must be between -180 and 180")
        return value


class IncidentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    incident_type: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = None
    severity: IncidentSeverity | None = None
    status: IncidentStatus | None = None
    trend: IncidentTrend | None = None
    latitude: float | None = None
    longitude: float | None = None
    evidence_score: float | None = Field(default=None, ge=0, le=100)
    report_count: int | None = Field(default=None, ge=0)
    correlation_score: float | None = Field(default=None, ge=0, le=100)
    independent_report_count: int | None = Field(default=None, ge=0)
    radius_km: float | None = Field(default=None, ge=0)
    time_window_minutes: int | None = Field(default=None, ge=0)

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, value: float | None) -> float | None:
        if value is None:
            return value
        if value < -90 or value > 90:
            raise ValueError("latitude must be between -90 and 90")
        return value

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, value: float | None) -> float | None:
        if value is None:
            return value
        if value < -180 or value > 180:
            raise ValueError("longitude must be between -180 and 180")
        return value


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    incident_code: str
    title: str
    incident_type: str
    description: str | None
    severity: IncidentSeverity
    status: IncidentStatus
    trend: IncidentTrend
    origin: IncidentOrigin = IncidentOrigin.SEEDED
    latitude: float
    longitude: float
    evidence_score: float
    report_count: int
    linked_report_count: int = 0
    correlation_score: float | None = None
    independent_report_count: int = 0
    radius_km: float | None = None
    time_window_minutes: int | None = None
    first_detected_at: datetime
    last_updated_at: datetime
    created_at: datetime
    updated_at: datetime
    is_correlated: bool = False


class NearbyIncidentRead(IncidentRead):
    distance_km: float = Field(description="PostGIS geodesic distance in kilometers")


class CorrelateRequest(BaseModel):
    latitude: float
    longitude: float
    radius_km: float | None = Field(default=None, gt=0, le=500)
    window_minutes: int | None = Field(default=None, gt=0, le=24 * 60)
    category: str | None = None
    create_incident: bool = True

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, value: float) -> float:
        if value < -90 or value > 90:
            raise ValueError("latitude must be between -90 and 90")
        return value

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, value: float) -> float:
        if value < -180 or value > 180:
            raise ValueError("longitude must be between -180 and 180")
        return value


class CorrelationFactorRead(BaseModel):
    name: str
    score: float
    weight: float
    detail: str


class CorrelateResponse(BaseModel):
    correlation_score: float
    threshold_met: bool
    factors: list[CorrelationFactorRead]
    report_count: int
    independent_report_count: int
    radius_km: float
    time_window_minutes: int
    centroid_latitude: float
    centroid_longitude: float
    incident_type: str
    title: str
    severity: IncidentSeverity
    status: IncidentStatus
    trend: IncidentTrend
    evidence_support: float
    report_ids: list[UUID]
    independent_report_ids: list[UUID]
    notes: list[str]
    incident: IncidentRead | None = None
    message: str


class TimelineEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    incident_id: UUID
    event_type: str
    title: str
    detail: str | None
    occurred_at: datetime
    created_at: datetime


class IncidentDetailRead(BaseModel):
    incident: IncidentRead
    reports: list[ReportRead]
    timeline: list[TimelineEventRead]
    correlation_explanation: list[CorrelationFactorRead] | None = None
