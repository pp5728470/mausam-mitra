import logging

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.weather import WeatherObservation
from app.schemas.weather import WeatherObservationCreate, WeatherObservationRead
from app.services.weather_provider import OpenWeatherProvider, WeatherProvider

logger = logging.getLogger(__name__)


class WeatherIngestionService:
    def __init__(self, provider: WeatherProvider | None = None) -> None:
        self.provider = provider or self._get_default_provider()

    def _get_default_provider(self) -> WeatherProvider:
        # Currently defaults to OpenWeatherMap
        return OpenWeatherProvider()

    async def fetch_and_ingest(
        self, session: AsyncSession, lat: float, lon: float
    ) -> WeatherObservationRead | None:
        """Fetch current weather from the provider and persist it into the database."""
        
        # 1. Fetch normalized observation from provider
        observation_data: WeatherObservationCreate | None = await self.provider.fetch_current_weather(lat, lon)
        if not observation_data:
            logger.warning("No weather data fetched from provider.")
            return None

        # 2. Persist with deduplication (ON CONFLICT DO NOTHING)
        # Identity is defined by (provider, observed_at, latitude, longitude)
        stmt = insert(WeatherObservation).values(
            provider=observation_data.provider,
            observed_at=observation_data.observed_at,
            latitude=observation_data.latitude,
            longitude=observation_data.longitude,
            # PostGIS syntax for geometry insertion
            location=f"SRID=4326;POINT({observation_data.longitude} {observation_data.latitude})",
            temperature=observation_data.temperature,
            humidity=observation_data.humidity,
            pressure=observation_data.pressure,
            wind_speed=observation_data.wind_speed,
            wind_direction=observation_data.wind_direction,
            precipitation_mm=observation_data.precipitation_mm,
            visibility=observation_data.visibility,
            weather_condition=observation_data.weather_condition,
            raw_payload=observation_data.raw_payload,
        )

        # Do nothing on conflict to gracefully handle duplicates
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["provider", "observed_at", "latitude", "longitude"]
        ).returning(WeatherObservation)

        result = await session.execute(stmt)
        inserted_row = result.scalar_one_or_none()
        await session.commit()

        # If it was a duplicate and wasn't inserted, we can just return the data as-is
        # but we should ideally return the DB record. For this explicit ingestion flow,
        # we can fetch the existing record if inserted_row is None.
        if not inserted_row:
            from sqlalchemy import select
            fetch_stmt = select(WeatherObservation).where(
                WeatherObservation.provider == observation_data.provider,
                WeatherObservation.observed_at == observation_data.observed_at,
                WeatherObservation.latitude == observation_data.latitude,
                WeatherObservation.longitude == observation_data.longitude,
            )
            inserted_row = (await session.execute(fetch_stmt)).scalar_one_or_none()

        if inserted_row:
            return WeatherObservationRead.model_validate(inserted_row)
        return None
