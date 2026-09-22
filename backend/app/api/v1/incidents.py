from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.enums import IncidentOrigin, IncidentSeverity, IncidentStatus, Role
from app.api.deps import get_db, require_roles
from app.schemas.common import PaginatedMeta, PaginatedResponse
from app.schemas.incident import (
    CorrelateRequest,
    CorrelateResponse,
    CorrelationFactorRead,
    IncidentCreate,
    IncidentDetailRead,
    IncidentRead,
    IncidentUpdate,
    NearbyIncidentRead,
    TimelineEventRead,
)
from app.schemas.report import ReportRead
from app.services import correlation_engine
from app.services import incidents as incident_service

router = APIRouter()


@router.post(
    "/correlate",
    response_model=CorrelateResponse,
    summary="Run incident correlation engine",
    description=(
        "Deterministic PostGIS-backed correlation over candidate reports. "
        "Creates/updates an incident only when the correlation threshold is met. "
        "Does NOT set report verification_status to VERIFIED."
    ),
    dependencies=[Depends(require_roles(Role.ANALYST, Role.ADMIN))],
)
async def correlate_incidents(
    payload: CorrelateRequest,
    session: AsyncSession = Depends(get_db),
) -> CorrelateResponse:
    result = await correlation_engine.correlate_area(
        session,
        latitude=payload.latitude,
        longitude=payload.longitude,
        radius_km=payload.radius_km,
        window_minutes=payload.window_minutes,
        category=payload.category,
        create_incident=payload.create_incident,
    )
    incident_read = None
    if result.incident is not None:
        linked = await incident_service.count_linked_reports(
            session, result.incident.id
        )
        incident_read = incident_service.serialize_incident(
            result.incident, linked_report_count=linked
        )
    message = (
        "Incident created/updated from correlation cluster."
        if result.incident
        else (
            "Correlation evaluated; threshold not met — no incident created."
            if not result.threshold_met
            else "Correlation evaluated without incident persistence."
        )
    )
    return CorrelateResponse(
        correlation_score=result.correlation_score,
        threshold_met=result.threshold_met,
        factors=[
            CorrelationFactorRead(
                name=f.name,
                score=f.score,
                weight=f.weight,
                detail=f.detail,
            )
            for f in result.factors
        ],
        report_count=result.report_count,
        independent_report_count=result.independent_report_count,
        radius_km=result.radius_km,
        time_window_minutes=result.time_window_minutes,
        centroid_latitude=result.centroid_lat,
        centroid_longitude=result.centroid_lng,
        incident_type=result.incident_type,
        title=result.title,
        severity=result.severity,
        status=result.status,
        trend=result.trend,
        evidence_support=result.evidence_support,
        report_ids=result.report_ids,
        independent_report_ids=result.independent_report_ids,
        notes=result.notes,
        incident=incident_read,
        message=message,
    )


@router.get(
    "",
    response_model=PaginatedResponse[IncidentRead],
    summary="List incidents",
    description="Filter simulated or operational incidents by status, severity, and type.",
    dependencies=[Depends(require_roles(Role.VERIFIER, Role.ANALYST, Role.ADMIN))],
)
async def list_incidents(
    status: IncidentStatus | None = Query(default=None, alias="status"),
    severity: IncidentSeverity | None = None,
    incident_type: str | None = None,
    origin: IncidentOrigin | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
) -> PaginatedResponse[IncidentRead]:
    items, total = await incident_service.list_incidents(
        session,
        status_filter=status,
        severity=severity,
        incident_type=incident_type,
        origin=origin,
        limit=limit,
        offset=offset,
    )
    serialized = await incident_service.serialize_incidents(session, items)
    return PaginatedResponse(
        items=serialized,
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
    )


@router.get(
    "/nearby",
    response_model=list[NearbyIncidentRead],
    summary="Nearby incidents (PostGIS)",
    description=(
        "Return incidents within radius_km of a point using PostGIS geography "
        "ST_DWithin / ST_Distance. Distance is geodesic (meters → km)."
    ),
    dependencies=[Depends(require_roles(Role.VERIFIER, Role.ANALYST, Role.ADMIN))],
)
async def nearby_incidents(
    latitude: float = Query(..., description="Center latitude (−90…90)"),
    longitude: float = Query(..., description="Center longitude (−180…180)"),
    radius_km: float = Query(50, gt=0, le=5000),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
) -> list[NearbyIncidentRead]:
    rows = await incident_service.find_nearby_incidents(
        session,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        limit=limit,
    )
    counts = await incident_service.linked_counts_for_incidents(
        session, [incident.id for incident, _ in rows]
    )
    results: list[NearbyIncidentRead] = []
    for incident, distance_km in rows:
        base = incident_service.serialize_incident(
            incident, linked_report_count=counts.get(incident.id, 0)
        )
        results.append(
            NearbyIncidentRead(**base.model_dump(), distance_km=round(distance_km, 3))
        )
    return results


@router.get(
    "/{incident_id}/reports",
    response_model=list[ReportRead],
    summary="Reports linked to an incident",
    dependencies=[Depends(require_roles(Role.VERIFIER, Role.ANALYST, Role.ADMIN))],
)
async def incident_reports(
    incident_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[ReportRead]:
    reports = await correlation_engine.list_incident_reports(session, incident_id)
    return [ReportRead.model_validate(r) for r in reports]


@router.get(
    "/{incident_id}/timeline",
    response_model=list[TimelineEventRead],
    summary="Incident timeline events",
    dependencies=[Depends(require_roles(Role.VERIFIER, Role.ANALYST, Role.ADMIN))],
)
async def incident_timeline(
    incident_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[TimelineEventRead]:
    events = await correlation_engine.list_incident_timeline(session, incident_id)
    return [TimelineEventRead.model_validate(e) for e in events]


@router.get(
    "/{incident_id}/detail",
    response_model=IncidentDetailRead,
    summary="Incident intelligence detail",
    dependencies=[Depends(require_roles(Role.VERIFIER, Role.ANALYST, Role.ADMIN))],
)
async def incident_detail(
    incident_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> IncidentDetailRead:
    incident = await incident_service.get_incident(session, incident_id)
    reports = await correlation_engine.list_incident_reports(session, incident_id)
    timeline = await correlation_engine.list_incident_timeline(session, incident_id)
    explanation: list[CorrelationFactorRead] | None = None
    # Only rebuild factor explanation for genuine correlated clusters.
    # Use configured correlation radius/window — NOT incident.radius_km
    # (affected cluster spread) or incident.time_window_minutes (event span).
    if (
        incident.origin == IncidentOrigin.CORRELATED
        and incident.correlation_score is not None
        and len(reports) >= 2
    ):
        settings = get_settings()
        scored = await correlation_engine.score_cluster(
            session,
            reports,
            radius_km=settings.correlation_radius_km,
            window_minutes=settings.correlation_window_minutes,
        )
        explanation = [
            CorrelationFactorRead(
                name=f.name,
                score=f.score,
                weight=f.weight,
                detail=f.detail,
            )
            for f in scored.factors
        ]
    return IncidentDetailRead(
        incident=incident_service.serialize_incident(
            incident, linked_report_count=len(reports)
        ),
        reports=[ReportRead.model_validate(r) for r in reports],
        timeline=[TimelineEventRead.model_validate(e) for e in timeline],
        correlation_explanation=explanation,
    )


@router.get(
    "/{incident_id}",
    response_model=IncidentRead,
    summary="Get incident by ID",
    dependencies=[Depends(require_roles(Role.VERIFIER, Role.ANALYST, Role.ADMIN))],
)
async def get_incident(
    incident_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> IncidentRead:
    incident = await incident_service.get_incident(session, incident_id)
    linked = await incident_service.count_linked_reports(session, incident.id)
    return incident_service.serialize_incident(incident, linked_report_count=linked)


@router.post(
    "",
    response_model=IncidentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create incident",
    dependencies=[Depends(require_roles(Role.ANALYST, Role.ADMIN))],
)
async def create_incident(
    payload: IncidentCreate,
    session: AsyncSession = Depends(get_db),
) -> IncidentRead:
    incident = await incident_service.create_incident(session, payload)
    linked = await incident_service.count_linked_reports(session, incident.id)
    return incident_service.serialize_incident(incident, linked_report_count=linked)


@router.patch(
    "/{incident_id}",
    response_model=IncidentRead,
    summary="Update incident",
    dependencies=[Depends(require_roles(Role.ANALYST, Role.ADMIN))],
)
async def update_incident(
    incident_id: UUID,
    payload: IncidentUpdate,
    session: AsyncSession = Depends(get_db),
) -> IncidentRead:
    incident = await incident_service.update_incident(session, incident_id, payload)
    linked = await incident_service.count_linked_reports(session, incident.id)
    return incident_service.serialize_incident(incident, linked_report_count=linked)
