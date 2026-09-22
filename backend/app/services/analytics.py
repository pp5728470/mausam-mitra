from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select, literal_column, cast, Integer, Numeric
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import IncidentOrigin, IncidentSeverity, IncidentStatus, IncidentTrend, ReportStatus, VerificationStatus
from app.models.incident import Incident
from app.models.report import Report
from app.models.weather import WeatherObservation
from app.schemas.analytics import (
    AnalyticsCategoriesResponse,
    AnalyticsGeographyResponse,
    AnalyticsOverviewResponse,
    AnalyticsSeverityResponse,
    AnalyticsTrendsResponse,
    AnalyticsWeatherResponse,
    CategoryCount,
    GeographicPoint,
    SeverityCount,
    TimeSeriesPoint,
)


def get_cutoff(days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)


async def get_overview(session: AsyncSession, days: int = 30) -> AnalyticsOverviewResponse:
    cutoff = get_cutoff(days)
    
    # Reports
    stmt_reports = select(
        func.count(Report.id).label("total"),
        func.sum(cast(Report.received_at >= get_cutoff(1), Integer)).label("last_24h"),
        func.sum(cast(Report.received_at >= get_cutoff(7), Integer)).label("last_7d"),
        func.sum(cast(Report.status == ReportStatus.NEW, Integer)).label("new_reports"),
        func.sum(cast(Report.verification_status == VerificationStatus.UNDER_REVIEW, Integer)).label("under_review"),
        func.sum(cast(Report.verification_status == VerificationStatus.VERIFIED, Integer)).label("verified"),
        func.sum(cast(Report.verification_status == VerificationStatus.REJECTED, Integer)).label("rejected"),
        func.sum(cast(Report.verification_status == VerificationStatus.PENDING, Integer)).label("pending"),
        func.sum(cast(Report.incident_id.isnot(None), Integer)).label("linked"),
        func.sum(cast(Report.incident_id.is_(None), Integer)).label("unlinked"),
        func.sum(cast(Report.classified_category.isnot(None), Integer)).label("classified"),
        func.sum(cast(Report.classified_category.is_(None), Integer)).label("unclassified"),
        func.avg(Report.classifier_confidence).label("avg_confidence")
    ).where(Report.received_at >= cutoff)
    
    result_reports = await session.execute(stmt_reports)
    row_reports = result_reports.first()
    
    total_reports = row_reports.total or 0
    linked = row_reports.linked or 0
    correlation_rate = (linked / total_reports * 100) if total_reports > 0 else 0.0

    # Incidents
    stmt_incidents = select(
        func.count(Incident.id).label("total"),
        func.sum(cast(Incident.origin == IncidentOrigin.CORRELATED, Integer)).label("correlated"),
        func.sum(cast(Incident.origin == IncidentOrigin.SEEDED, Integer)).label("seeded"),
        func.sum(cast(Incident.origin == IncidentOrigin.MANUAL, Integer)).label("manual"),
        # Operational analytics restrict to CORRELATED for specific statuses
        func.sum(cast((Incident.origin == IncidentOrigin.CORRELATED) & (Incident.status == IncidentStatus.ACTIVE), Integer)).label("active"),
        func.sum(cast((Incident.origin == IncidentOrigin.CORRELATED) & (Incident.status == IncidentStatus.EMERGING), Integer)).label("emerging"),
        func.sum(cast((Incident.origin == IncidentOrigin.CORRELATED) & (Incident.severity == IncidentSeverity.CRITICAL), Integer)).label("critical"),
        func.sum(cast((Incident.origin == IncidentOrigin.CORRELATED) & (Incident.severity == IncidentSeverity.HIGH), Integer)).label("high"),
        func.sum(cast((Incident.origin == IncidentOrigin.CORRELATED) & (Incident.trend == IncidentTrend.RISING), Integer)).label("rising")
    ).where(Incident.created_at >= cutoff)
    
    result_incidents = await session.execute(stmt_incidents)
    row_incidents = result_incidents.first()

    return AnalyticsOverviewResponse(
        total_reports=total_reports,
        reports_last_24h=row_reports.last_24h or 0,
        reports_last_7d=row_reports.last_7d or 0,
        new_reports=row_reports.new_reports or 0,
        under_review_reports=row_reports.under_review or 0,
        verified_reports=row_reports.verified or 0,
        rejected_reports=row_reports.rejected or 0,
        pending_reports=row_reports.pending or 0,
        
        total_incidents=row_incidents.total or 0,
        correlated_incidents=row_incidents.correlated or 0,
        seeded_incidents=row_incidents.seeded or 0,
        manual_incidents=row_incidents.manual or 0,
        active_incidents=row_incidents.active or 0,
        emerging_incidents=row_incidents.emerging or 0,
        critical_incidents=row_incidents.critical or 0,
        high_severity_incidents=row_incidents.high or 0,
        rising_incidents=row_incidents.rising or 0,
        
        linked_reports=linked,
        unlinked_reports=row_reports.unlinked or 0,
        correlation_rate=correlation_rate,
        
        classified_reports=row_reports.classified or 0,
        unclassified_reports=row_reports.unclassified or 0,
        average_classifier_confidence=row_reports.avg_confidence
    )


async def get_trends(session: AsyncSession) -> AnalyticsTrendsResponse:
    # 24h reports per hour
    now = datetime.now(timezone.utc)
    cutoff_24h = now - timedelta(hours=24)
    stmt_24h = (
        select(
            func.date_trunc('hour', Report.received_at).label("time_bucket"),
            func.count(Report.id).label("count")
        )
        .where(Report.received_at >= cutoff_24h)
        .group_by("time_bucket")
        .order_by("time_bucket")
    )
    result_24h = await session.execute(stmt_24h)
    
    # 7d reports per day
    cutoff_7d = now - timedelta(days=7)
    stmt_7d = (
        select(
            func.date_trunc('day', Report.received_at).label("time_bucket"),
            func.count(Report.id).label("count")
        )
        .where(Report.received_at >= cutoff_7d)
        .group_by("time_bucket")
        .order_by("time_bucket")
    )
    result_7d = await session.execute(stmt_7d)

    # 30d reports per day
    cutoff_30d = now - timedelta(days=30)
    stmt_30d = (
        select(
            func.date_trunc('day', Report.received_at).label("time_bucket"),
            func.count(Report.id).label("count")
        )
        .where(Report.received_at >= cutoff_30d)
        .group_by("time_bucket")
        .order_by("time_bucket")
    )
    result_30d = await session.execute(stmt_30d)

    def fill_buckets(query_results, start_time, end_time, delta, trunc_func):
        # Create a dict of existing buckets
        bucket_map = {row.time_bucket.replace(tzinfo=timezone.utc): row.count for row in query_results}
        
        # Fill missing
        current = trunc_func(start_time)
        filled = []
        end_trunc = trunc_func(end_time)
        while current <= end_trunc:
            filled.append(TimeSeriesPoint(
                timestamp=current,
                value=bucket_map.get(current, 0)
            ))
            current += delta
        return filled

    def trunc_hour(dt: datetime):
        return dt.replace(minute=0, second=0, microsecond=0)
        
    def trunc_day(dt: datetime):
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    points_24h = fill_buckets(result_24h.all(), cutoff_24h, now, timedelta(hours=1), trunc_hour)
    points_7d = fill_buckets(result_7d.all(), cutoff_7d, now, timedelta(days=1), trunc_day)
    points_30d = fill_buckets(result_30d.all(), cutoff_30d, now, timedelta(days=1), trunc_day)

    return AnalyticsTrendsResponse(
        reports_24h=points_24h,
        reports_7d=points_7d,
        reports_30d=points_30d
    )


async def get_categories(session: AsyncSession, days: int = 30) -> AnalyticsCategoriesResponse:
    cutoff = get_cutoff(days)
    
    # Priority: classified_category > classification > 'OTHER'
    category_expr = func.coalesce(
        Report.classified_category,
        Report.classification,
        "OTHER"
    )
    
    stmt = (
        select(
            category_expr.label("category"),
            func.count(Report.id).label("count")
        )
        .where(Report.received_at >= cutoff)
        .group_by(category_expr)
        .order_by(func.count(Report.id).desc())
    )
    
    result = await session.execute(stmt)
    return AnalyticsCategoriesResponse(
        distribution=[
            CategoryCount(category=row.category or "OTHER", count=row.count)
            for row in result.all()
        ]
    )


async def get_severity(session: AsyncSession, days: int = 30) -> AnalyticsSeverityResponse:
    cutoff = get_cutoff(days)
    
    stmt = (
        select(
            Incident.severity.label("severity"),
            func.count(Incident.id).label("count")
        )
        .where(Incident.created_at >= cutoff)
        .group_by(Incident.severity)
    )
    
    result = await session.execute(stmt)
    return AnalyticsSeverityResponse(
        distribution=[
            SeverityCount(severity=str(row.severity), count=row.count)
            for row in result.all()
        ]
    )


async def get_geography(session: AsyncSession, days: int = 30) -> AnalyticsGeographyResponse:
    # A simple geographic overview returning known incidents + report counts.
    # We round lat/lng to 2 decimal places to cluster roughly.
    cutoff = get_cutoff(days)
    
    stmt = (
        select(
            func.round(cast(Incident.latitude, Numeric), 2).label("lat"),
            func.round(cast(Incident.longitude, Numeric), 2).label("lng"),
            func.sum(Incident.report_count).label("report_count"),
            func.count(Incident.id).label("incident_count")
        )
        .where(Incident.created_at >= cutoff)
        .group_by("lat", "lng")
        .having(func.count(Incident.id) > 0)
    )
    
    result = await session.execute(stmt)
    return AnalyticsGeographyResponse(
        points=[
            GeographicPoint(
                latitude=float(row.lat),
                longitude=float(row.lng),
                report_count=row.report_count or 0,
                incident_count=row.incident_count or 0
            )
            for row in result.all()
        ]
    )


async def get_weather(session: AsyncSession, days: int = 30) -> AnalyticsWeatherResponse:
    cutoff = get_cutoff(days)
    
    stmt = select(
        func.count(WeatherObservation.id).label("obs_count"),
        func.avg(WeatherObservation.temperature).label("avg_temp"),
        func.max(WeatherObservation.temperature).label("max_temp"),
        func.avg(WeatherObservation.humidity).label("avg_hum"),
        func.avg(WeatherObservation.wind_speed).label("avg_wind")
    ).where(WeatherObservation.observed_at >= cutoff)
    
    result = await session.execute(stmt)
    row = result.first()
    
    if not row or row.obs_count == 0:
        return AnalyticsWeatherResponse(observation_count=0)
        
    return AnalyticsWeatherResponse(
        observation_count=row.obs_count,
        average_temperature=row.avg_temp,
        maximum_temperature=row.max_temp,
        average_humidity=row.avg_hum,
        average_wind_speed=row.avg_wind
    )
