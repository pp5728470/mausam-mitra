from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import (
    ReportStatus,
    SourceType,
    VerificationRecommendation,
    VerificationStatus,
)

# Citizen-selected categories (NOT AI classification).
CITIZEN_INCIDENT_TYPES = frozenset(
    {
        "Heavy Rainfall",
        "Flood / Waterlogging",
        "Storm / Strong Winds",
        "Lightning",
        "Extreme Heat",
        "Hailstorm",
        "Landslide",
        "Visibility / Dense Fog",
        "Other",
    }
)


class ReportCreate(BaseModel):
    """Payload for ingesting a new report / raw signal.

    A report is NOT an incident. Citizen submissions stay NEW with
    incident_id=NULL until a later correlation phase.
    """

    source_type: SourceType
    source_name: str = Field(min_length=1, max_length=255)
    title: str = Field(min_length=5, max_length=120)
    description: str = Field(
        min_length=10,
        max_length=1000,
        description="Citizen / source observation text (required).",
    )
    latitude: float
    longitude: float
    reported_at: datetime | None = Field(
        default=None,
        description="Client-claimed event time (optional; server stores received_at separately)",
    )
    media_url: str | None = Field(
        default=None,
        max_length=1024,
        description=(
            "Optional media reference URL or demo://local/… placeholder. "
            "Binary uploads are not stored in PostgreSQL (S3 in a later phase)."
        ),
    )
    classification: str | None = Field(
        default=None,
        max_length=128,
        description=(
            "Optional citizen-selected category label. "
            "Not AI classification — stored for downstream review only."
        ),
    )
    incident_id: UUID | None = Field(
        default=None,
        description=(
            "Optional manual association (ignored for CITIZEN source_type). "
            "Citizen reports never auto-create or auto-link incidents."
        ),
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 5:
            raise ValueError("title must be at least 5 characters")
        if len(cleaned) > 120:
            raise ValueError("title must be at most 120 characters")
        return cleaned

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 10:
            raise ValueError("description must be at least 10 characters")
        if len(cleaned) > 1000:
            raise ValueError("description must be at most 1000 characters")
        return cleaned

    @field_validator("source_name")
    @classmethod
    def validate_source_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("source_name is required")
        return cleaned

    @field_validator("classification")
    @classmethod
    def validate_classification(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        if cleaned not in CITIZEN_INCIDENT_TYPES:
            # Allow free-text for non-citizen sources; citizen UI only sends known types.
            if len(cleaned) > 128:
                raise ValueError("classification must be at most 128 characters")
        return cleaned

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


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_type: SourceType
    source_name: str
    title: str
    description: str | None
    latitude: float
    longitude: float
    reported_at: datetime | None
    received_at: datetime
    media_url: str | None
    status: ReportStatus
    classification: str | None
    classification_confidence: float | None
    
    # Phase 10: Intelligence fields
    classified_category: str | None = None
    classifier_confidence: float | None = None
    classification_explanation: str | None = None
    classification_signals: list[dict] | None = None
    classified_at: datetime | None = None
    classifier_version: str | None = None

    verification_status: VerificationStatus
    evidence_score: float | None
    verification_recommendation: VerificationRecommendation | None
    verification_notes: str | None
    verified_at: datetime | None
    verified_by: str | None
    incident_id: UUID | None
    created_at: datetime
    updated_at: datetime
