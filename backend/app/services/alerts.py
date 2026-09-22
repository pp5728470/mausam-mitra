from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import (
    AlertStatus,
    AlertType,
    IncidentSeverity,
    IncidentStatus,
    IncidentTrend,
    RecipientScope,
)
from app.models.alert import Alert
from app.models.incident import Incident
from app.models.report import Report

logger = logging.getLogger(__name__)


async def _create_alert_idempotent(
    session: AsyncSession,
    *,
    alert_type: AlertType,
    severity: IncidentSeverity | None,
    title: str,
    message: str,
    recipient_scope: RecipientScope,
    dedupe_key: str,
    recipient_user_id: UUID | None = None,
    incident_id: UUID | None = None,
    report_id: UUID | None = None,
    metadata_payload: dict[str, Any] | None = None,
) -> Alert | None:
    """Create an alert safely using a savepoint, catching unique constraint violations.

    IMPORTANT: session.add() is called INSIDE begin_nested() so that on
    IntegrityError the savepoint rollback expunges the alert from the session's
    identity map before the exception is caught.  This keeps the parent
    transaction healthy — the incident/verification changes that surround
    this call are NOT rolled back.
    """
    now = datetime.now(timezone.utc)
    alert = Alert(
        alert_type=alert_type,
        severity=severity,
        title=title,
        message=message,
        recipient_scope=recipient_scope,
        recipient_user_id=recipient_user_id,
        incident_id=incident_id,
        report_id=report_id,
        metadata_payload=metadata_payload,
        dedupe_key=dedupe_key,
        created_at=now,
        updated_at=now,
    )
    try:
        async with session.begin_nested():
            # add() is inside the savepoint so a rollback removes the object
            # from the session entirely, leaving the parent transaction clean.
            session.add(alert)
            await session.flush()
        return alert
    except IntegrityError:
        # Duplicate dedupe_key — alert already exists.  The savepoint was
        # rolled back automatically by the context manager, so the parent
        # transaction is still active and usable.
        logger.debug("Alert ignored (dedupe_key exists): %s", dedupe_key)
        return None


async def evaluate_incident_escalation(
    session: AsyncSession,
    *,
    incident: Incident,
    old_severity: IncidentSeverity | None,
) -> None:
    """Generate INCIDENT_ESCALATED if severity went up."""
    if old_severity is None or incident.severity == old_severity:
        return
    
    # Simple hierarchy mapping
    levels = {
        IncidentSeverity.LOW: 1,
        IncidentSeverity.MEDIUM: 2,
        IncidentSeverity.HIGH: 3,
        IncidentSeverity.CRITICAL: 4,
    }
    
    old_level = levels.get(old_severity, 0)
    new_level = levels.get(incident.severity, 0)

    if new_level > old_level:
        scopes = [RecipientScope.ADMIN, RecipientScope.ANALYST, RecipientScope.VERIFIER]
        for scope in scopes:
            dedupe = f"INCIDENT_ESCALATED:{incident.id}:{incident.severity.value}:{scope.value}"
            await _create_alert_idempotent(
                session,
                alert_type=AlertType.INCIDENT_ESCALATED,
                severity=incident.severity,
                title=f"Incident Escalated: {incident.title}",
                message=f"Incident {incident.incident_code} escalated to {incident.severity.value}.",
                recipient_scope=scope,
                dedupe_key=dedupe,
                incident_id=incident.id,
            )


async def evaluate_incident_status_change(
    session: AsyncSession,
    *,
    incident: Incident,
    old_status: IncidentStatus | None,
) -> None:
    if old_status is None or incident.status == old_status:
        return

    scopes = [RecipientScope.ADMIN, RecipientScope.ANALYST, RecipientScope.VERIFIER]
    for scope in scopes:
        dedupe = f"INCIDENT_STATUS_CHANGED:{incident.id}:{incident.status.value}:{scope.value}"
        await _create_alert_idempotent(
            session,
            alert_type=AlertType.INCIDENT_STATUS_CHANGED,
            severity=incident.severity,
            title=f"Status Changed: {incident.title}",
            message=f"Incident {incident.incident_code} status changed to {incident.status.value}.",
            recipient_scope=scope,
            dedupe_key=dedupe,
            incident_id=incident.id,
        )


async def evaluate_incident_trend_change(
    session: AsyncSession,
    *,
    incident: Incident,
    old_trend: IncidentTrend | None,
) -> None:
    if old_trend is None or incident.trend == old_trend:
        return

    scopes = [RecipientScope.ADMIN, RecipientScope.ANALYST, RecipientScope.VERIFIER]
    for scope in scopes:
        dedupe = f"INCIDENT_TREND_CHANGED:{incident.id}:{incident.trend.value}:{scope.value}"
        await _create_alert_idempotent(
            session,
            alert_type=AlertType.INCIDENT_TREND_CHANGED,
            severity=incident.severity,
            title=f"Trend Changed: {incident.title}",
            message=f"Incident {incident.incident_code} trend changed to {incident.trend.value}.",
            recipient_scope=scope,
            dedupe_key=dedupe,
            incident_id=incident.id,
        )


async def evaluate_new_correlated_incident(
    session: AsyncSession,
    *,
    incident: Incident,
) -> None:
    """Generate INCIDENT_CREATED alert."""
    scopes = [RecipientScope.ADMIN, RecipientScope.ANALYST, RecipientScope.VERIFIER]
    for scope in scopes:
        dedupe = f"INCIDENT_CREATED:{incident.id}:{scope.value}"
        await _create_alert_idempotent(
            session,
            alert_type=AlertType.INCIDENT_CREATED,
            severity=incident.severity,
            title=f"New Correlated Incident: {incident.title}",
            message=f"A new incident {incident.incident_code} was correlated from reports.",
            recipient_scope=scope,
            dedupe_key=dedupe,
            incident_id=incident.id,
        )


async def evaluate_verification_required(
    session: AsyncSession,
    *,
    report: Report,
) -> None:
    """Generate VERIFICATION_REQUIRED for analysts/verifiers."""
    scopes = [RecipientScope.ADMIN, RecipientScope.ANALYST, RecipientScope.VERIFIER]
    for scope in scopes:
        dedupe = f"VERIFICATION_REQUIRED:{report.id}:{scope.value}"
        await _create_alert_idempotent(
            session,
            alert_type=AlertType.VERIFICATION_REQUIRED,
            severity=None,
            title=f"Review Required: {report.title}",
            message=f"Report requires human verification.",
            recipient_scope=scope,
            dedupe_key=dedupe,
            report_id=report.id,
        )


async def evaluate_report_verification_decision(
    session: AsyncSession,
    *,
    report: Report,
    decision: str,  # VERIFIED or REJECTED
) -> None:
    """Alert the citizen and operational users on final verification."""
    is_verified = decision.upper() == "VERIFIED"
    alert_type = AlertType.REPORT_VERIFIED if is_verified else AlertType.REPORT_REJECTED
    title = f"Report Verified: {report.title}" if is_verified else f"Report Rejected: {report.title}"
    msg = f"Your report has been verified." if is_verified else f"Your report has been rejected."
    op_msg = f"Report {report.id} was verified." if is_verified else f"Report {report.id} was rejected."

    # Citizen Alert
    if report.reporter_user_id:
        dedupe_cit = f"{alert_type.value}:{report.id}:CITIZEN_REPORTER:{report.reporter_user_id}"
        await _create_alert_idempotent(
            session,
            alert_type=alert_type,
            severity=None,
            title=title,
            message=msg,
            recipient_scope=RecipientScope.CITIZEN_REPORTER,
            recipient_user_id=report.reporter_user_id,
            dedupe_key=dedupe_cit,
            report_id=report.id,
        )

    # Operational Alerts
    scopes = [RecipientScope.ADMIN, RecipientScope.ANALYST, RecipientScope.VERIFIER]
    for scope in scopes:
        dedupe_op = f"{alert_type.value}:{report.id}:{scope.value}"
        await _create_alert_idempotent(
            session,
            alert_type=alert_type,
            severity=None,
            title=title,
            message=op_msg,
            recipient_scope=scope,
            dedupe_key=dedupe_op,
            report_id=report.id,
        )
