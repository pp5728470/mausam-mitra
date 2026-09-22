import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import settings
from app.schemas.weather import WeatherObservationCreate

logger = logging.getLogger(__name__)


class WeatherProvider(ABC):
    @abstractmethod
    async def fetch_current_weather(
        self, lat: float, lon: float
    ) -> WeatherObservationCreate | None:
        """Fetch current weather for the given coordinates.
        Returns None if the provider fails or data is unavailable."""
        pass


class OpenWeatherProvider(WeatherProvider):
    def __init__(self) -> None:
        self.api_key = settings.weather_api_key
        self.base_url = settings.weather_base_url.rstrip("/")
        self.provider_name = "OpenWeatherMap"

    async def fetch_current_weather(
        self, lat: float, lon: float
    ) -> WeatherObservationCreate | None:
        if not self.api_key:
            logger.warning("OpenWeatherMap API key is not configured.")
            return None

        # Round coordinates slightly to avoid hitting identical points with float noise
        lat = round(lat, 4)
        lon = round(lon, 4)

        url = f"{self.base_url}/weather"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric",  # Get temperature in Celsius
        }

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                return self._normalize(data, lat, lon)
        except httpx.HTTPError as e:
            logger.error(f"HTTP error occurred while fetching weather data: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching weather data: {e}")
            return None

    def _normalize(
        self, raw_data: dict[str, Any], requested_lat: float, requested_lon: float
    ) -> WeatherObservationCreate:
        """Normalize the raw OpenWeatherMap payload to WeatherObservationCreate."""
        
        # Observed time is provided in UTC unix timestamp by OWM
        dt_unix = raw_data.get("dt")
        if dt_unix:
            observed_at = datetime.fromtimestamp(dt_unix, tz=timezone.utc)
        else:
            observed_at = datetime.now(timezone.utc)

        main = raw_data.get("main", {})
        wind = raw_data.get("wind", {})
        weather_list = raw_data.get("weather", [])
        
        # OWM provides rain/snow in 1h or 3h volumes. Normalize to 1h if available.
        rain = raw_data.get("rain", {})
        snow = raw_data.get("snow", {})
        precipitation_mm = rain.get("1h", rain.get("3h", 0)) + snow.get("1h", snow.get("3h", 0))
        if precipitation_mm == 0 and not rain and not snow:
            precipitation_mm = None

        weather_condition = weather_list[0].get("main") if weather_list else None

        return WeatherObservationCreate(
            provider=self.provider_name,
            observed_at=observed_at,
            latitude=requested_lat,
            longitude=requested_lon,
            temperature=main.get("temp"),
            humidity=main.get("humidity"),
            pressure=main.get("pressure"),
            wind_speed=wind.get("speed"),
            wind_direction=wind.get("deg"),
            precipitation_mm=precipitation_mm,
            visibility=raw_data.get("visibility"),
            weather_condition=weather_condition,
            raw_payload=raw_data,
        )


class MockWeatherProvider(WeatherProvider):
    """ONLY for pytest / test code. Production MUST never use this."""
    
    async def fetch_current_weather(
        self, lat: float, lon: float
    ) -> WeatherObservationCreate | None:
        return WeatherObservationCreate(
            provider="MockWeatherProvider",
            observed_at=datetime.now(timezone.utc),
            latitude=lat,
            longitude=lon,
            temperature=25.0,
            humidity=80.0,
            pressure=1010.0,
            wind_speed=5.5,
            wind_direction=180.0,
            precipitation_mm=1.5,
            visibility=10000.0,
            weather_condition="Rain",
            raw_payload={"mock": True},
        )
