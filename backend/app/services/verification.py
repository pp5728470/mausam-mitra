"""Human verification decisions — separate from automated evidence evaluation."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.enums import (
    ReportStatus,
    VerificationDecision,
    VerificationStatus,
)
from app.models.report import Report
from app.schemas.evidence import VerifyReportRequest
from app.services import alerts as alerts_service



async def verify_report(
    session: AsyncSession,
    report_id: UUID,
    payload: VerifyReportRequest,
) -> Report:
    """Apply a human verification decision. Does NOT create an Incident.

    TODO(phase-later): require authenticated authorized-admin role.
    """
    result = await session.execute(
        select(Report)
        .options(selectinload(Report.evidence_items))
        .where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )

    now = datetime.now(timezone.utc)
    operator = (payload.verified_by or "authorized_operator").strip()

    if payload.decision == VerificationDecision.VERIFIED:
        report.verification_status = VerificationStatus.VERIFIED
        report.verified_at = now
        report.verified_by = operator
        report.verification_notes = payload.notes
        # Human verification is tracked only via verification_status.
        # Do NOT move NEW → PROCESSING (PROCESSING is in-pipeline, not final).
        # Do NOT set CORRELATED here — that requires an incident linkage.
        # Leave operational status unchanged (typically NEW until incident correlation).
    elif payload.decision == VerificationDecision.REJECTED:
        report.verification_status = VerificationStatus.REJECTED
        report.status = ReportStatus.REJECTED
        report.verified_at = now
        report.verified_by = operator
        report.verification_notes = payload.notes
    elif payload.decision == VerificationDecision.NEEDS_REVIEW:
        report.verification_status = VerificationStatus.UNDER_REVIEW
        report.verified_at = None
        report.verified_by = operator
        report.verification_notes = payload.notes
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid verification decision",
        )

    # Explicit: never create or attach an incident here.
    
    if payload.decision in (VerificationDecision.VERIFIED, VerificationDecision.REJECTED):
        await alerts_service.evaluate_report_verification_decision(
            session, report=report, decision=payload.decision.value
        )
    elif payload.decision == VerificationDecision.NEEDS_REVIEW:
        await alerts_service.evaluate_verification_required(
            session, report=report
        )

    await session.commit()
    await session.refresh(report)
    return report


async def list_evidence(
    session: AsyncSession, report_id: UUID
) -> tuple[Report, list]:
    from app.models.evidence import ReportEvidence

    report = await session.get(Report, report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    result = await session.execute(
        select(ReportEvidence)
        .where(ReportEvidence.report_id == report_id)
        .order_by(ReportEvidence.created_at.asc())
    )
    return report, list(result.scalars().all())
