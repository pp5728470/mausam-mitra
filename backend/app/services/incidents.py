from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from geoalchemy2 import Geography
from geoalchemy2.functions import ST_DWithin, ST_Distance, ST_MakePoint, ST_SetSRID
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import IncidentOrigin, IncidentSeverity, IncidentStatus
from app.models.incident import Incident
from app.models.report import Report
from app.schemas.incident import IncidentCreate, IncidentRead, IncidentUpdate
from app.services.geo import point_wkt


def is_correlated_record(incident: Incident, linked_count: int | None = None) -> bool:
    """Phase 7.1 invariant: correlated incidents have score + enough independent signals."""
    linked = (
        linked_count
        if linked_count is not None
        else int(incident.report_count or 0)
    )
    return (
        incident.origin == IncidentOrigin.CORRELATED
        and incident.correlation_score is not None
        and int(incident.independent_report_count or 0) >= 2
        and linked >= 2
    )


async def count_linked_reports(session: AsyncSession, incident_id: UUID) -> int:
    result = await session.execute(
        select(func.count())
        .select_from(Report)
        .where(Report.incident_id == incident_id)
    )
    return int(result.scalar_one() or 0)


async def linked_counts_for_incidents(
    session: AsyncSession, incident_ids: list[UUID]
) -> dict[UUID, int]:
    if not incident_ids:
        return {}
    result = await session.execute(
        select(Report.incident_id, func.count())
        .where(Report.incident_id.in_(incident_ids))
        .group_by(Report.incident_id)
    )
    return {row[0]: int(row[1]) for row in result.all()}


def serialize_incident(
    incident: Incident, *, linked_report_count: int
) -> IncidentRead:
    """Build IncidentRead with honesty fields for Phase 7.1."""
    base = IncidentRead.model_validate(incident)
    return base.model_copy(
        update={
            "linked_report_count": linked_report_count,
            "is_correlated": is_correlated_record(incident, linked_report_count),
            # For correlated rows, surface actual membership; never invent scores.
            "report_count": (
                linked_report_count
                if incident.origin == IncidentOrigin.CORRELATED
                else incident.report_count
            ),
        }
    )


async def serialize_incidents(
    session: AsyncSession, incidents: list[Incident]
) -> list[IncidentRead]:
    counts = await linked_counts_for_incidents(
        session, [incident.id for incident in incidents]
    )
    return [
        serialize_incident(incident, linked_report_count=counts.get(incident.id, 0))
        for incident in incidents
    ]


async def _next_incident_code(session: AsyncSession) -> str:
    result = await session.execute(select(func.count()).select_from(Incident))
    count = int(result.scalar_one() or 0)
    return f"MM-INC-{count + 1:04d}"


async def create_incident(session: AsyncSession, payload: IncidentCreate) -> Incident:
    code = payload.incident_code.strip() if payload.incident_code else None
    if not code:
        code = await _next_incident_code(session)
    else:
        existing = await session.execute(
            select(Incident).where(Incident.incident_code == code)
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Incident code '{code}' already exists",
            )

    # Manual create cannot claim correlation without Phase 7 invariants.
    origin = payload.origin
    if origin == IncidentOrigin.CORRELATED:
        if (
            payload.correlation_score is None
            or payload.independent_report_count < 2
            or payload.report_count < 2
        ):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "CORRELATED origin requires correlation_score and "
                    "at least 2 independent reports"
                ),
            )

    now = datetime.now(timezone.utc)
    incident = Incident(
        incident_code=code,
        title=payload.title.strip(),
        incident_type=payload.incident_type.strip(),
        description=payload.description,
        severity=payload.severity,
        status=payload.status,
        trend=payload.trend,
        origin=origin,
        latitude=payload.latitude,
        longitude=payload.longitude,
        location=point_wkt(payload.longitude, payload.latitude),
        evidence_score=payload.evidence_score,
        report_count=payload.report_count,
        correlation_score=payload.correlation_score,
        independent_report_count=payload.independent_report_count,
        radius_km=payload.radius_km,
        time_window_minutes=payload.time_window_minutes,
        first_detected_at=payload.first_detected_at or now,
        last_updated_at=now,
    )
    session.add(incident)
    await session.commit()
    await session.refresh(incident)
    return incident


async def get_incident(session: AsyncSession, incident_id: UUID) -> Incident:
    incident = await session.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )
    return incident


async def list_incidents(
    session: AsyncSession,
    *,
    status_filter: IncidentStatus | None = None,
    severity: IncidentSeverity | None = None,
    incident_type: str | None = None,
    origin: IncidentOrigin | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Incident], int]:
    filters = []
    if status_filter is not None:
        filters.append(Incident.status == status_filter)
    if severity is not None:
        filters.append(Incident.severity == severity)
    if incident_type:
        filters.append(Incident.incident_type.ilike(incident_type.strip()))
    if origin is not None:
        filters.append(Incident.origin == origin)

    count_stmt = select(func.count()).select_from(Incident)
    if filters:
        count_stmt = count_stmt.where(*filters)
    total = int((await session.execute(count_stmt)).scalar_one() or 0)

    # Prefer correlated / recently updated for operational queues.
    stmt = select(Incident).order_by(
        (Incident.origin == IncidentOrigin.CORRELATED).desc(),
        Incident.last_updated_at.desc(),
    )
    if filters:
        stmt = stmt.where(*filters)
    stmt = stmt.limit(limit).offset(offset)

    result = await session.execute(stmt)
    return list(result.scalars().all()), total


async def update_incident(
    session: AsyncSession,
    incident_id: UUID,
    payload: IncidentUpdate,
) -> Incident:
    incident = await get_incident(session, incident_id)
    data = payload.model_dump(exclude_unset=True)

    lat = data.pop("latitude", None)
    lng = data.pop("longitude", None)

    for key, value in data.items():
        setattr(incident, key, value)

    if lat is not None or lng is not None:
        new_lat = lat if lat is not None else incident.latitude
        new_lng = lng if lng is not None else incident.longitude
        incident.latitude = new_lat
        incident.longitude = new_lng
        incident.location = point_wkt(new_lng, new_lat)

    incident.last_updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(incident)
    return incident


async def find_nearby_incidents(
    session: AsyncSession,
    *,
    latitude: float,
    longitude: float,
    radius_km: float,
    limit: int = 50,
) -> list[tuple[Incident, float]]:
    """Return incidents within radius_km using PostGIS geography ST_DWithin."""
    if latitude < -90 or latitude > 90:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="latitude must be between -90 and 90",
        )
    if longitude < -180 or longitude > 180:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="longitude must be between -180 and 180",
        )
    if radius_km <= 0 or radius_km > 5000:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="radius_km must be between 0 and 5000",
        )

    radius_m = radius_km * 1000.0
    origin = cast(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326), Geography)
    incident_geog = cast(Incident.location, Geography)

    distance_m = ST_Distance(incident_geog, origin)

    stmt = (
        select(Incident, (distance_m / 1000.0).label("distance_km"))
        .where(ST_DWithin(incident_geog, origin, radius_m))
        .order_by(distance_m.asc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    rows = result.all()
    return [(row[0], float(row[1])) for row in rows]


async def find_nearby_correlated_incident(
    session: AsyncSession,
    *,
    latitude: float,
    longitude: float,
    radius_km: float,
) -> Incident | None:
    """PostGIS lookup for an existing CORRELATED incident near a cluster centroid."""
    radius_m = max(radius_km, 0.1) * 1000.0
    origin = cast(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326), Geography)
    incident_geog = cast(Incident.location, Geography)
    distance_m = ST_Distance(incident_geog, origin)
    stmt = (
        select(Incident)
        .where(
            Incident.origin == IncidentOrigin.CORRELATED,
            Incident.correlation_score.is_not(None),
            ST_DWithin(incident_geog, origin, radius_m),
        )
        .order_by(distance_m.asc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()
