from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import (
    EvidenceType,
    VerificationDecision,
    VerificationRecommendation,
)


class EvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    report_id: UUID
    evidence_type: EvidenceType
    title: str
    description: str
    score: float | None
    confidence: float | None
    source: str
    metadata: dict[str, Any] | None = Field(
        default=None,
        validation_alias="evidence_metadata",
        serialization_alias="metadata",
    )
    created_at: datetime


class EvaluateReportResponse(BaseModel):
    report: "ReportReadLite"
    evidence: list[EvidenceRead]
    evidence_score: float | None
    evidence_coverage: str
    verification_recommendation: VerificationRecommendation


class ReportReadLite(BaseModel):
    """Subset embedded in evaluate response — mirrors ReportRead fields needed by UI."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    latitude: float
    longitude: float
    status: str
    source_type: str
    source_name: str
    classification: str | None
    media_url: str | None
    verification_status: str
    evidence_score: float | None
    verification_recommendation: VerificationRecommendation | None
    verification_notes: str | None
    verified_at: datetime | None
    verified_by: str | None
    incident_id: UUID | None
    reported_at: datetime | None
    received_at: datetime
    created_at: datetime


class VerifyReportRequest(BaseModel):
    decision: VerificationDecision
    notes: str | None = Field(default=None, max_length=2000)
    verified_by: str | None = Field(
        default="authorized_operator",
        max_length=128,
        description="Placeholder operator id until auth is added.",
    )

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None


class VerifyReportResponse(BaseModel):
    report: ReportReadLite
    decision: VerificationDecision
    message: str


# Resolve forward refs
EvaluateReportResponse.model_rebuild()
