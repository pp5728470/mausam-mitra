"""Phase 7: Incident Correlation Engine — deterministic, PostGIS-backed.

Correlation strength is NOT a truth / authenticity / forecast score.
Human verification remains independent and is never auto-set to VERIFIED here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import HTTPException, status
from geoalchemy2 import Geography
from geoalchemy2.functions import (
    ST_Centroid,
    ST_Collect,
    ST_DWithin,
    ST_Distance,
    ST_MakePoint,
    ST_SetSRID,
    ST_X,
    ST_Y,
)
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.correlation_config import (
    CORRELATION_WEIGHTS,
    DEFAULT_CORRELATION_RADIUS_KM,
    DEFAULT_CORRELATION_SCORE_THRESHOLD,
    DEFAULT_CORRELATION_WINDOW_MINUTES,
    DEFAULT_MIN_INDEPENDENT_REPORTS,
    DUPLICATE_SIMILARITY_THRESHOLD,
    SPATIAL_BANDS,
    TEMPORAL_BANDS,
)
from app.core.config import get_settings
from app.core.enums import (
    IncidentOrigin,
    IncidentSeverity,
    IncidentStatus,
    IncidentTrend,
    ReportStatus,
    VerificationStatus,
)
from app.models.incident import Incident
from app.models.incident_timeline import IncidentTimelineEvent
from app.models.report import Report
from app.services import incidents as incident_service
from app.services.category_compatibility import cluster_category_score
from app.services.geo import point_wkt
from app.services.incident_type_derivation import (
    derive_incident_title,
    derive_incident_type,
)
from app.services import alerts as alerts_service



def _normalize_text(value: str) -> str:
    text = value.lower().strip()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _token_jaccard(a: str, b: str) -> float:
    ta = set(_normalize_text(a).split())
    tb = set(_normalize_text(b).split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def _event_time(report: Report) -> datetime:
    for value in (report.reported_at, report.received_at, report.created_at):
        if value is None:
            continue
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    return datetime.now(timezone.utc)


def _band_score(value: float, bands: list[tuple[float, float]]) -> float:
    for limit, score in bands:
        if value <= limit:
            return score
    return 0.0


def _report_blob(report: Report) -> str:
    return f"{report.title} {report.description or ''} {report.classification or ''}"


@dataclass
class FactorScore:
    name: str
    score: float
    weight: float
    detail: str

    @property
    def weighted(self) -> float:
        return self.score * self.weight


@dataclass
class CorrelationResult:
    correlation_score: float
    factors: list[FactorScore]
    report_ids: list[UUID]
    independent_report_ids: list[UUID]
    report_count: int
    independent_report_count: int
    radius_km: float
    time_window_minutes: int
    centroid_lat: float
    centroid_lng: float
    incident_type: str
    title: str
    severity: IncidentSeverity
    status: IncidentStatus
    trend: IncidentTrend
    evidence_support: float
    threshold_met: bool
    incident: Incident | None = None
    duplicate_groups: int = 0
    notes: list[str] = field(default_factory=list)


def _partition_independent(reports: list[Report]) -> tuple[list[Report], int]:
    """Greedy clustering by text Jaccard; one representative per duplicate group."""
    remaining = list(reports)
    independents: list[Report] = []
    groups = 0
    while remaining:
        seed = remaining.pop(0)
        groups += 1
        independents.append(seed)
        seed_blob = _report_blob(seed)
        kept: list[Report] = []
        for other in remaining:
            sim = _token_jaccard(seed_blob, _report_blob(other))
            if sim < DUPLICATE_SIMILARITY_THRESHOLD:
                kept.append(other)
        remaining = kept
    return independents, groups


def _spatial_factor(
    spread_km: float,
    correlation_radius_km: float,
    *,
    signal_count: int = 0,
) -> FactorScore:
    """Score cluster spread against the configured correlation search radius."""
    if spread_km > correlation_radius_km:
        score = 0.0
        detail = (
            f"Spread {spread_km:.2f} km exceeds correlation radius "
            f"{correlation_radius_km:.1f} km."
        )
    else:
        score = _band_score(spread_km, SPATIAL_BANDS)
        if signal_count > 0:
            detail = (
                f"{signal_count} signals spread across {spread_km:.2f} km "
                f"within the {correlation_radius_km:.0f} km correlation radius."
            )
        else:
            detail = (
                f"Signals spread across {spread_km:.2f} km within the "
                f"{correlation_radius_km:.0f} km correlation radius."
            )
    return FactorScore("spatial", score, CORRELATION_WEIGHTS["spatial"], detail)


def _temporal_factor(window_minutes: float, max_window: float) -> FactorScore:
    if window_minutes > max_window:
        score = 0.0
        detail = f"Time span {window_minutes:.0f} min exceeds window {max_window:.0f} min."
    else:
        score = _band_score(window_minutes, TEMPORAL_BANDS)
        detail = f"Reports arrived within {window_minutes:.0f} minutes."
    return FactorScore("temporal", score, CORRELATION_WEIGHTS["temporal"], detail)


def _evidence_factor(reports: list[Report]) -> FactorScore:
    """REJECTED reports do not strengthen; VERIFIED/CORROBORATED boost."""
    contributing = [
        r for r in reports if r.verification_status != VerificationStatus.REJECTED
    ]
    if not contributing:
        return FactorScore(
            "evidence",
            15.0,
            CORRELATION_WEIGHTS["evidence"],
            "No non-rejected reports contribute evidence support.",
        )

    scores: list[float] = []
    for r in contributing:
        base = float(r.evidence_score) if r.evidence_score is not None else 35.0
        if r.verification_status == VerificationStatus.VERIFIED:
            base = min(100.0, base + 15.0)
        elif r.verification_status == VerificationStatus.CORROBORATED:
            base = min(100.0, base + 10.0)
        elif r.verification_status == VerificationStatus.UNDER_REVIEW:
            base = min(100.0, base + 5.0)
        scores.append(base)
    avg = sum(scores) / len(scores)
    rejected = len(reports) - len(contributing)
    detail = (
        f"Mean evidence support {avg:.0f}/100 across {len(contributing)} non-rejected "
        f"signals ({rejected} rejected excluded from strengthening)."
    )
    return FactorScore("evidence", round(avg, 1), CORRELATION_WEIGHTS["evidence"], detail)


def _density_factor(
    independent_count: int, report_count: int, radius_km: float, window_min: float
) -> FactorScore:
    # More independent signals in a tight window → higher density.
    raw = min(100.0, independent_count * 18.0 + max(0, report_count - independent_count) * 2.0)
    if radius_km <= 2.5 and window_min <= 45:
        raw = min(100.0, raw + 10.0)
    detail = (
        f"{independent_count} independent of {report_count} reports "
        f"within {radius_km:.1f} km / {window_min:.0f} min."
    )
    return FactorScore("density", round(raw, 1), CORRELATION_WEIGHTS["density"], detail)


def _duplicate_factor(report_count: int, independent_count: int) -> FactorScore:
    if report_count <= 1:
        score = 100.0
        detail = "Single report — no duplicate discount applied."
    else:
        ratio = independent_count / report_count
        score = round(ratio * 100.0, 1)
        dupes = report_count - independent_count
        detail = (
            f"{independent_count} independent / {report_count} total "
            f"({dupes} likely duplicate/similar discounted)."
        )
    return FactorScore("duplicate", score, CORRELATION_WEIGHTS["duplicate"], detail)


def _derive_severity(
    *,
    independent_count: int,
    evidence_support: float,
    radius_km: float,
    trend: IncidentTrend,
    correlation_score: float,
) -> IncidentSeverity:
    critical_hits = 0
    if independent_count >= 8 and evidence_support >= 75 and radius_km >= 2.5:
        critical_hits += 1
    if independent_count >= 6 and trend == IncidentTrend.RISING and evidence_support >= 70:
        critical_hits += 1
    if critical_hits >= 1 and correlation_score >= 85:
        return IncidentSeverity.CRITICAL
    if independent_count >= 5 and evidence_support >= 65 and correlation_score >= 75:
        return IncidentSeverity.HIGH
    if independent_count >= 3 or (independent_count >= 2 and evidence_support >= 55):
        return IncidentSeverity.MEDIUM
    return IncidentSeverity.LOW


def _derive_lifecycle(
    *,
    independent_count: int,
    trend: IncidentTrend,
    created_new: bool,
) -> IncidentStatus:
    if created_new and independent_count <= 2:
        return IncidentStatus.DETECTED
    if trend == IncidentTrend.RISING or independent_count >= 4:
        if independent_count >= 5 and trend == IncidentTrend.RISING:
            return IncidentStatus.ACTIVE
        return IncidentStatus.EMERGING
    if independent_count >= 3:
        return IncidentStatus.ACTIVE
    return IncidentStatus.DETECTED


def _derive_trend(times: list[datetime]) -> IncidentTrend:
    if len(times) < 2:
        return IncidentTrend.STABLE
    ordered = sorted(times)
    span = (ordered[-1] - ordered[0]).total_seconds()
    if span <= 0:
        return IncidentTrend.STABLE
    mid = ordered[0] + timedelta(seconds=span / 2)
    first = sum(1 for t in ordered if t <= mid)
    second = len(ordered) - first
    if second > first * 1.4:
        return IncidentTrend.RISING
    if first > second * 1.4:
        return IncidentTrend.FALLING
    return IncidentTrend.STABLE


async def _next_incident_code(session: AsyncSession) -> str:
    result = await session.execute(select(func.count()).select_from(Incident))
    count = int(result.scalar_one() or 0)
    return f"MM-INC-{count + 1:04d}"


async def _centroid_and_spread(
    session: AsyncSession, report_ids: list[UUID]
) -> tuple[float, float, float]:
    """PostGIS centroid + max geodesic distance from centroid (km)."""
    pts = select(Report.location).where(Report.id.in_(report_ids)).subquery()
    collected = ST_Collect(pts.c.location)
    centroid = ST_Centroid(collected)
    cent_lat = await session.scalar(select(ST_Y(centroid)))
    cent_lng = await session.scalar(select(ST_X(centroid)))
    if cent_lat is None or cent_lng is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unable to compute cluster centroid",
        )

    origin = cast(ST_SetSRID(ST_MakePoint(float(cent_lng), float(cent_lat)), 4326), Geography)
    report_geog = cast(Report.location, Geography)
    dist_m = ST_Distance(report_geog, origin)
    max_m = await session.scalar(
        select(func.max(dist_m)).where(Report.id.in_(report_ids))
    )
    radius_km = float(max_m or 0.0) / 1000.0
    return float(cent_lat), float(cent_lng), radius_km


async def find_candidate_reports(
    session: AsyncSession,
    *,
    latitude: float,
    longitude: float,
    radius_km: float,
    window_minutes: int,
    category: str | None = None,
    exclude_rejected: bool = False,
) -> list[Report]:
    """PostGIS spatial + temporal candidate narrowing (no Python haversine)."""
    if latitude < -90 or latitude > 90 or longitude < -180 or longitude > 180:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid latitude/longitude",
        )
    if radius_km <= 0 or radius_km > 500:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="radius_km must be between 0 and 500",
        )

    now = datetime.now(timezone.utc)
    since = now - timedelta(minutes=window_minutes)
    radius_m = radius_km * 1000.0
    origin = cast(ST_SetSRID(ST_MakePoint(longitude, latitude), 4326), Geography)
    report_geog = cast(Report.location, Geography)
    event_time = func.coalesce(Report.reported_at, Report.received_at, Report.created_at)

    filters = [
        ST_DWithin(report_geog, origin, radius_m),
        event_time >= since,
    ]
    if exclude_rejected:
        filters.append(Report.verification_status != VerificationStatus.REJECTED)
    if category:
        filters.append(Report.classification.ilike(f"%{category.strip()}%"))

    stmt = (
        select(Report)
        .where(*filters)
        .order_by(Report.received_at.asc())
        .limit(200)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def score_cluster(
    session: AsyncSession,
    reports: list[Report],
    *,
    radius_km: float,
    window_minutes: int,
) -> CorrelationResult:
    if len(reports) < 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No candidate reports for correlation",
        )

    independents, groups = _partition_independent(reports)
    ids = [r.id for r in reports]
    cent_lat, cent_lng, spread_km = await _centroid_and_spread(session, ids)

    times = [_event_time(r) for r in reports]
    span_min = (max(times) - min(times)).total_seconds() / 60.0

    spatial = _spatial_factor(
        spread_km, radius_km, signal_count=len(reports)
    )
    temporal = _temporal_factor(span_min, float(window_minutes))
    cat_score, cat_detail = cluster_category_score(
        [r.classification for r in reports]
    )
    category = FactorScore(
        "category", cat_score, CORRELATION_WEIGHTS["category"], cat_detail
    )
    evidence = _evidence_factor(reports)
    density = _density_factor(
        len(independents), len(reports), spread_km, span_min
    )
    duplicate = _duplicate_factor(len(reports), len(independents))

    factors = [spatial, temporal, category, evidence, density, duplicate]
    correlation_score = round(sum(f.weighted for f in factors), 1)

    settings = get_settings()
    threshold = settings.correlation_score_threshold
    min_indep = settings.correlation_min_independent_reports
    threshold_met = (
        correlation_score >= threshold
        and len(independents) >= min_indep
        and spatial.score > 0
        and temporal.score > 0
        and category.score >= 40
    )

    trend = _derive_trend(times)
    incident_type = derive_incident_type([r.classification for r in reports])
    texts = [_report_blob(r) for r in reports]
    title = derive_incident_title(
        latitude=cent_lat,
        longitude=cent_lng,
        incident_type=incident_type,
        texts=texts,
    )
    severity = _derive_severity(
        independent_count=len(independents),
        evidence_support=evidence.score,
        radius_km=spread_km,
        trend=trend,
        correlation_score=correlation_score,
    )
    status = _derive_lifecycle(
        independent_count=len(independents),
        trend=trend,
        created_new=True,
    )

    notes: list[str] = []
    if len(independents) < min_indep:
        notes.append(
            f"Need at least {min_indep} independent reports to create an incident."
        )
    if correlation_score < threshold:
        notes.append(
            f"Correlation strength {correlation_score} is below threshold {threshold}."
        )

    return CorrelationResult(
        correlation_score=correlation_score,
        factors=factors,
        report_ids=ids,
        independent_report_ids=[r.id for r in independents],
        report_count=len(reports),
        independent_report_count=len(independents),
        radius_km=round(spread_km, 2),
        time_window_minutes=int(round(span_min)),
        centroid_lat=cent_lat,
        centroid_lng=cent_lng,
        incident_type=incident_type,
        title=title,
        severity=severity,
        status=status,
        trend=trend,
        evidence_support=evidence.score,
        threshold_met=threshold_met,
        duplicate_groups=groups,
        notes=notes,
    )


async def _append_timeline(
    session: AsyncSession,
    incident: Incident,
    *,
    event_type: str,
    title: str,
    detail: str | None,
    occurred_at: datetime,
    source_report_id: UUID | None = None,
) -> bool:
    """Insert a timeline event if it does not already exist.

    Returns True when a new row was inserted.
    Report-linked events are deduped by (incident_id, event_type, source_report_id).
    """
    if source_report_id is not None:
        existing = await session.execute(
            select(IncidentTimelineEvent.id).where(
                IncidentTimelineEvent.incident_id == incident.id,
                IncidentTimelineEvent.event_type == event_type,
                IncidentTimelineEvent.source_report_id == source_report_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            return False

    session.add(
        IncidentTimelineEvent(
            incident_id=incident.id,
            event_type=event_type,
            title=title,
            detail=detail,
            source_report_id=source_report_id,
            occurred_at=occurred_at,
        )
    )
    return True


def _material_cluster_changed(
    incident: Incident,
    result: CorrelationResult,
    *,
    next_status: IncidentStatus,
) -> bool:
    """True when correlation state changed enough to warrant a timeline update."""
    prev_score = incident.correlation_score
    if prev_score is None or abs(float(prev_score) - float(result.correlation_score)) >= 0.05:
        return True
    if int(incident.report_count or 0) != int(result.report_count):
        return True
    if int(incident.independent_report_count or 0) != int(
        result.independent_report_count
    ):
        return True
    if incident.status != next_status:
        return True
    if incident.severity != result.severity:
        return True
    if incident.trend != result.trend:
        return True
    prev_radius = float(incident.radius_km or 0.0)
    next_radius = float(result.radius_km or 0.0)
    if abs(prev_radius - next_radius) >= 0.05:
        return True
    return False


async def persist_incident_from_cluster(
    session: AsyncSession,
    result: CorrelationResult,
    reports: list[Report],
) -> Incident:
    """Create or update incident; link reports via incident_id. Never changes verification_status."""
    if not result.threshold_met:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Correlation threshold not met — incident not created",
        )
    if (
        result.correlation_score is None
        or result.independent_report_count < DEFAULT_MIN_INDEPENDENT_REPORTS
        or result.report_count < DEFAULT_MIN_INDEPENDENT_REPORTS
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Correlated incident requires non-null correlation_score and "
                f"at least {DEFAULT_MIN_INDEPENDENT_REPORTS} independent reports"
            ),
        )

    now = datetime.now(timezone.utc)
    # Prefer updating an existing incident already linked to any candidate.
    existing_id = next((r.incident_id for r in reports if r.incident_id), None)
    incident: Incident | None = None
    created_new = False
    if existing_id:
        incident = await session.get(Incident, existing_id)

    # Idempotency: reuse nearby CORRELATED incident for the same cluster centroid.
    if incident is None:
        incident = await incident_service.find_nearby_correlated_incident(
            session,
            latitude=result.centroid_lat,
            longitude=result.centroid_lng,
            radius_km=DEFAULT_CORRELATION_RADIUS_KM,
        )

    if incident is None:
        created_new = True
        code = await _next_incident_code(session)
        times = [_event_time(r) for r in reports]
        incident = Incident(
            incident_code=code,
            title=result.title,
            incident_type=result.incident_type,
            description=(
                "Deterministic correlation cluster from related weather signals. "
                "Correlation strength is not a truth claim."
            ),
            severity=result.severity,
            status=result.status,
            trend=result.trend,
            origin=IncidentOrigin.CORRELATED,
            latitude=result.centroid_lat,
            longitude=result.centroid_lng,
            location=point_wkt(result.centroid_lng, result.centroid_lat),
            evidence_score=result.evidence_support,
            report_count=result.report_count,
            correlation_score=result.correlation_score,
            independent_report_count=result.independent_report_count,
            radius_km=result.radius_km,
            time_window_minutes=result.time_window_minutes,
            first_detected_at=min(times),
            last_updated_at=now,
        )
        session.add(incident)
        await session.flush()
        await _append_timeline(
            session,
            incident,
            event_type="DETECTED",
            title="Incident detected from correlated signals",
            detail=(
                f"Correlation strength {result.correlation_score}/100 · "
                f"{result.independent_report_count} independent of {result.report_count} reports"
            ),
            occurred_at=min(times),
        )
        
        await alerts_service.evaluate_new_correlated_incident(
            session,
            incident=incident,
        )

    else:
        next_status = (
            result.status
            if created_new
            else _derive_lifecycle(
                independent_count=result.independent_report_count,
                trend=result.trend,
                created_new=False,
            )
        )
        if incident.status == IncidentStatus.RESOLVED:
            next_status = IncidentStatus.RESOLVED

        material = _material_cluster_changed(
            incident, result, next_status=next_status
        )

        old_severity = incident.severity
        old_status = incident.status
        old_trend = incident.trend

        incident.title = result.title
        incident.incident_type = result.incident_type
        incident.severity = result.severity
        incident.trend = result.trend
        incident.origin = IncidentOrigin.CORRELATED
        if incident.status != IncidentStatus.RESOLVED:
            incident.status = next_status
        incident.latitude = result.centroid_lat
        incident.longitude = result.centroid_lng
        incident.location = point_wkt(result.centroid_lng, result.centroid_lat)
        incident.evidence_score = result.evidence_support
        incident.report_count = result.report_count
        incident.correlation_score = result.correlation_score
        incident.independent_report_count = result.independent_report_count
        incident.radius_km = result.radius_km
        incident.time_window_minutes = result.time_window_minutes
        incident.last_updated_at = now

        if material:
            await _append_timeline(
                session,
                incident,
                event_type="CLUSTER_UPDATED",
                title="Correlation cluster updated",
                detail=(
                    f"Correlation strength {result.correlation_score}/100 · "
                    f"status {incident.status.value}"
                ),
                occurred_at=now,
            )

        # Trigger alerts based strictly on state transitions
        await alerts_service.evaluate_incident_escalation(
            session, incident=incident, old_severity=old_severity
        )
        await alerts_service.evaluate_incident_status_change(
            session, incident=incident, old_status=old_status
        )
        await alerts_service.evaluate_incident_trend_change(
            session, incident=incident, old_trend=old_trend
        )


    # Link reports — do NOT mutate verification_status.
    for report in reports:
        report.incident_id = incident.id
        if report.status == ReportStatus.NEW:
            report.status = ReportStatus.CORRELATED

    # One REPORT_SIGNAL per report (idempotent via source_report_id).
    for report in sorted(reports, key=_event_time):
        await _append_timeline(
            session,
            incident,
            event_type="REPORT_SIGNAL",
            title=f"Signal: {report.title[:80]}",
            detail=(
                f"{report.source_type.value} · "
                f"verification={report.verification_status.value}"
            ),
            occurred_at=_event_time(report),
            source_report_id=report.id,
        )

    await session.commit()
    await session.refresh(incident)
    result.incident = incident
    return incident


async def correlate_area(
    session: AsyncSession,
    *,
    latitude: float,
    longitude: float,
    radius_km: float | None = None,
    window_minutes: int | None = None,
    category: str | None = None,
    create_incident: bool = True,
) -> CorrelationResult:
    settings = get_settings()
    radius = radius_km if radius_km is not None else settings.correlation_radius_km
    window = (
        window_minutes
        if window_minutes is not None
        else settings.correlation_window_minutes
    )

    candidates = await find_candidate_reports(
        session,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius,
        window_minutes=window,
        category=category,
    )
    if not candidates:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No candidate reports in the correlation window",
        )

    result = await score_cluster(
        session, candidates, radius_km=radius, window_minutes=window
    )
    if create_incident and result.threshold_met:
        await persist_incident_from_cluster(session, result, candidates)
    return result


async def list_incident_reports(
    session: AsyncSession, incident_id: UUID
) -> list[Report]:
    incident = await session.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    result = await session.execute(
        select(Report)
        .where(Report.incident_id == incident_id)
        .order_by(Report.received_at.asc())
    )
    return list(result.scalars().all())


async def list_incident_timeline(
    session: AsyncSession, incident_id: UUID
) -> list[IncidentTimelineEvent]:
    incident = await session.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    result = await session.execute(
        select(IncidentTimelineEvent)
        .where(IncidentTimelineEvent.incident_id == incident_id)
        .order_by(IncidentTimelineEvent.occurred_at.asc())
    )
    return list(result.scalars().all())
