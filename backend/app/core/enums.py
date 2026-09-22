from enum import StrEnum


class Role(StrEnum):
    CITIZEN = "CITIZEN"
    VERIFIER = "VERIFIER"
    ANALYST = "ANALYST"
    ADMIN = "ADMIN"


class SourceType(StrEnum):
    CITIZEN = "CITIZEN"
    OFFICIAL = "OFFICIAL"
    SENSOR = "SENSOR"
    WEATHER_API = "WEATHER_API"
    PUBLIC_FEED = "PUBLIC_FEED"
    OTHER = "OTHER"


class ReportStatus(StrEnum):
    NEW = "NEW"
    PROCESSING = "PROCESSING"
    CORRELATED = "CORRELATED"
    REJECTED = "REJECTED"


class VerificationStatus(StrEnum):
    """Human-facing verification state — independent of pipeline status."""

    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    CORROBORATED = "CORROBORATED"
    REJECTED = "REJECTED"
    VERIFIED = "VERIFIED"


class VerificationRecommendation(StrEnum):
    """Automated recommendation only — not final verification."""

    NEEDS_REVIEW = "NEEDS_REVIEW"
    CORROBORATED = "CORROBORATED"
    HIGH_CONFIDENCE_REVIEW = "HIGH_CONFIDENCE_REVIEW"


class VerificationDecision(StrEnum):
    """Allowed human verification decisions."""

    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class EvidenceType(StrEnum):
    LOCATION_CONSISTENCY = "LOCATION_CONSISTENCY"
    TIME_CONSISTENCY = "TIME_CONSISTENCY"
    WEATHER_CORRELATION = "WEATHER_CORRELATION"
    NEARBY_REPORTS = "NEARBY_REPORTS"
    MEDIA_EVIDENCE = "MEDIA_EVIDENCE"
    DUPLICATE_RISK = "DUPLICATE_RISK"
    SOURCE_SIGNAL = "SOURCE_SIGNAL"


class IncidentStatus(StrEnum):
    """Incident lifecycle — independent from report verification_status."""

    DETECTED = "DETECTED"
    EMERGING = "EMERGING"
    ACTIVE = "ACTIVE"
    SUBSIDING = "SUBSIDING"
    RESOLVED = "RESOLVED"


class IncidentSeverity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class IncidentTrend(StrEnum):
    RISING = "RISING"
    STABLE = "STABLE"
    FALLING = "FALLING"


class IncidentOrigin(StrEnum):
    """How an incident entered the system — independent of lifecycle status."""

    SEEDED = "SEEDED"
    CORRELATED = "CORRELATED"
    MANUAL = "MANUAL"


class AlertType(StrEnum):
    INCIDENT_CREATED = "INCIDENT_CREATED"
    INCIDENT_ESCALATED = "INCIDENT_ESCALATED"
    INCIDENT_STATUS_CHANGED = "INCIDENT_STATUS_CHANGED"
    INCIDENT_TREND_CHANGED = "INCIDENT_TREND_CHANGED"
    VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
    REPORT_VERIFIED = "REPORT_VERIFIED"
    REPORT_REJECTED = "REPORT_REJECTED"


class AlertStatus(StrEnum):
    UNREAD = "UNREAD"
    READ = "READ"
    ACKNOWLEDGED = "ACKNOWLEDGED"


class RecipientScope(StrEnum):
    VERIFIER = "VERIFIER"
    ANALYST = "ANALYST"
    ADMIN = "ADMIN"
    CITIZEN_REPORTER = "CITIZEN_REPORTER"
