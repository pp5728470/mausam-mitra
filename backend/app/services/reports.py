from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ReportStatus, SourceType, VerificationStatus
from app.models.incident import Incident
from app.models.report import Report
from app.schemas.report import ReportCreate
from app.services.geo import point_wkt


async def create_report(
    session: AsyncSession, payload: ReportCreate, reporter_user_id: UUID | None = None
) -> Report:
    """Persist a raw signal/report. Does NOT create an Incident.

    TODO(phase-later): add rate limiting (e.g. Redis token bucket) at this
    service boundary before accepting high-volume public CITIZEN ingestion.
    """
    is_citizen = payload.source_type == SourceType.CITIZEN

    # Citizen reports are anonymous raw signals — never auto-link incidents.
    incident_id = None if is_citizen else payload.incident_id

    if incident_id is not None:
        incident = await session.get(Incident, incident_id)
        if incident is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Incident not found",
            )

    report = Report(
        source_type=payload.source_type,
        source_name=payload.source_name.strip(),
        title=payload.title.strip(),
        description=payload.description,
        latitude=payload.latitude,
        longitude=payload.longitude,
        location=point_wkt(payload.longitude, payload.latitude),
        reported_at=payload.reported_at,
        received_at=datetime.now(timezone.utc),
        media_url=payload.media_url,
        status=ReportStatus.NEW if is_citizen or incident_id is None else ReportStatus.CORRELATED,
        classification=payload.classification,
        classification_confidence=None,  # AI confidence arrives in a later phase
        verification_status=VerificationStatus.PENDING,
        evidence_score=None,
        verification_recommendation=None,
        incident_id=incident_id,
        reporter_user_id=reporter_user_id,
    )
    session.add(report)

    if incident_id is not None:
        incident = await session.get(Incident, incident_id)
        if incident is not None:
            incident.report_count = (incident.report_count or 0) + 1
            incident.last_updated_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(report)
    return report


async def get_report(session: AsyncSession, report_id: UUID) -> Report:
    report = await session.get(Report, report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    return report


async def list_reports(
    session: AsyncSession,
    *,
    status_filter: ReportStatus | None = None,
    source_type: SourceType | None = None,
    incident_id: UUID | None = None,
    verification_status: VerificationStatus | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Report], int]:
    filters = []
    if status_filter is not None:
        filters.append(Report.status == status_filter)
    if source_type is not None:
        filters.append(Report.source_type == source_type)
    if incident_id is not None:
        filters.append(Report.incident_id == incident_id)
    if verification_status is not None:
        filters.append(Report.verification_status == verification_status)

    count_stmt = select(func.count()).select_from(Report)
    list_stmt = select(Report).order_by(Report.created_at.desc())
    if filters:
        count_stmt = count_stmt.where(*filters)
        list_stmt = list_stmt.where(*filters)

    total = int((await session.execute(count_stmt)).scalar_one() or 0)
    result = await session.execute(list_stmt.limit(limit).offset(offset))
    return list(result.scalars().all()), total
