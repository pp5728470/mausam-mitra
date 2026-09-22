from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_roles
from app.core.enums import Role
from app.schemas.analytics import (
    AnalyticsCategoriesResponse,
    AnalyticsGeographyResponse,
    AnalyticsOverviewResponse,
    AnalyticsSeverityResponse,
    AnalyticsTrendsResponse,
    AnalyticsWeatherResponse,
)
from app.services import analytics as analytics_service

router = APIRouter(
    dependencies=[Depends(require_roles(Role.ANALYST, Role.ADMIN))]
)


@router.get("/overview", response_model=AnalyticsOverviewResponse, summary="Get global operational metrics")
async def get_overview(
    days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_db)
) -> AnalyticsOverviewResponse:
    return await analytics_service.get_overview(session, days=days)


@router.get("/trends", response_model=AnalyticsTrendsResponse, summary="Get time series data for charts")
async def get_trends(
    session: AsyncSession = Depends(get_db)
) -> AnalyticsTrendsResponse:
    return await analytics_service.get_trends(session)


@router.get("/categories", response_model=AnalyticsCategoriesResponse, summary="Get category distribution")
async def get_categories(
    days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_db)
) -> AnalyticsCategoriesResponse:
    return await analytics_service.get_categories(session, days=days)


@router.get("/severity", response_model=AnalyticsSeverityResponse, summary="Get severity distribution")
async def get_severity(
    days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_db)
) -> AnalyticsSeverityResponse:
    return await analytics_service.get_severity(session, days=days)


@router.get("/geography", response_model=AnalyticsGeographyResponse, summary="Get geographic cluster points")
async def get_geography(
    days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_db)
) -> AnalyticsGeographyResponse:
    return await analytics_service.get_geography(session, days=days)


@router.get("/weather", response_model=AnalyticsWeatherResponse, summary="Get weather observation analytics")
async def get_weather(
    days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_db)
) -> AnalyticsWeatherResponse:
    return await analytics_service.get_weather(session, days=days)
