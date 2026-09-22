from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TimeSeriesPoint(BaseModel):
    timestamp: datetime
    value: int


class CategoryCount(BaseModel):
    category: str
    count: int


class SeverityCount(BaseModel):
    severity: str
    count: int


class AnalyticsOverviewResponse(BaseModel):
    # REPORT OVERVIEW
    total_reports: int
    reports_last_24h: int
    reports_last_7d: int
    new_reports: int
    under_review_reports: int
    verified_reports: int
    rejected_reports: int
    pending_reports: int

    # INCIDENT OVERVIEW
    total_incidents: int
    correlated_incidents: int
    seeded_incidents: int
    manual_incidents: int
    active_incidents: int
    emerging_incidents: int
    critical_incidents: int
    high_severity_incidents: int
    rising_incidents: int

    # CORRELATION
    linked_reports: int
    unlinked_reports: int
    correlation_rate: float

    # CLASSIFICATION
    classified_reports: int
    unclassified_reports: int
    average_classifier_confidence: Optional[float] = None


class AnalyticsTrendsResponse(BaseModel):
    reports_24h: list[TimeSeriesPoint]
    reports_7d: list[TimeSeriesPoint]
    reports_30d: list[TimeSeriesPoint]


class AnalyticsCategoriesResponse(BaseModel):
    distribution: list[CategoryCount]


class AnalyticsSeverityResponse(BaseModel):
    distribution: list[SeverityCount]


class GeographicPoint(BaseModel):
    latitude: float
    longitude: float
    report_count: int
    incident_count: int


class AnalyticsGeographyResponse(BaseModel):
    points: list[GeographicPoint]


class AnalyticsWeatherResponse(BaseModel):
    observation_count: int
    average_temperature: Optional[float] = None
    maximum_temperature: Optional[float] = None
    average_humidity: Optional[float] = None
    average_wind_speed: Optional[float] = None
