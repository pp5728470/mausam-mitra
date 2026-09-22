from typing import Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from geoalchemy2.functions import ST_DWithin, ST_MakePoint, ST_SetSRID
from sqlalchemy import func

from app.api.deps import get_db, require_roles
from app.core.enums import Role
from app.models.weather import WeatherObservation
from app.schemas.weather import WeatherObservationRead
from app.schemas.common import PaginatedResponse, PaginatedMeta
from app.services.weather_ingestion import WeatherIngestionService

router = APIRouter()

@router.get(
    "/observations",
    response_model=PaginatedResponse[WeatherObservationRead],
    summary="List weather observations",
    dependencies=[Depends(require_roles(Role.ANALYST, Role.ADMIN, Role.VERIFIER))],
)
async def list_weather_observations(
    latitude: float | None = Query(None, description="Latitude for spatial filtering"),
    longitude: float | None = Query(None, description="Longitude for spatial filtering"),
    radius_km: float = Query(10.0, description="Search radius in kilometers"),
    provider: str | None = Query(None, description="Filter by provider name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> Any:
    stmt = select(WeatherObservation)
    
    if latitude is not None and longitude is not None:
        origin_geog = func.ST_SetSRID(ST_MakePoint(longitude, latitude), 4326).cast(
            func.Geometry
        )
        report_geog = WeatherObservation.location
        # ST_DWithin uses meters if cast to Geography, but since we are keeping it as Geometry (SRID 4326), we need Geography cast
        # Let's cast both to Geography for meter-based radius search
        stmt = stmt.where(
            ST_DWithin(
                report_geog.cast(func.Geography),
                origin_geog.cast(func.Geography),
                radius_km * 1000.0,
            )
        )
        
    if provider:
        stmt = stmt.where(WeatherObservation.provider == provider)
        
    stmt = stmt.order_by(WeatherObservation.observed_at.desc())
    
    total = await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    stmt = stmt.offset(skip).limit(limit)
    rows = await db.execute(stmt)
    observations = rows.scalars().all()
    
    # Hide raw payload from API response manually for security/audit requirement
    result_list = []
    for obs in observations:
        read_obj = WeatherObservationRead.model_validate(obs)
        result_list.append(read_obj)

    return PaginatedResponse(
        items=result_list,
        meta=PaginatedMeta(total=total, offset=skip, limit=limit),
    )


@router.post(
    "/ingest",
    response_model=WeatherObservationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger real-time weather ingestion",
    dependencies=[Depends(require_roles(Role.ANALYST, Role.ADMIN))],
)
async def ingest_weather_observation(
    latitude: float = Query(..., description="Latitude to fetch weather for"),
    longitude: float = Query(..., description="Longitude to fetch weather for"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    service = WeatherIngestionService()
    observation = await service.fetch_and_ingest(db, latitude, longitude)
    
    if not observation:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to fetch weather data from provider.",
        )
        
    return observation
