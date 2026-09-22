import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WeatherObservationBase(BaseModel):
    provider: str = Field(..., description="Name of the weather provider")
    observed_at: datetime = Field(..., description="Timestamp of the observation")
    latitude: float = Field(..., description="Latitude of the observation")
    longitude: float = Field(..., description="Longitude of the observation")

    temperature: float | None = Field(None, description="Temperature in Celsius")
    humidity: float | None = Field(None, description="Humidity percentage")
    pressure: float | None = Field(None, description="Pressure in hPa")
    wind_speed: float | None = Field(None, description="Wind speed in m/s")
    wind_direction: float | None = Field(None, description="Wind direction in degrees")
    precipitation_mm: float | None = Field(None, description="Precipitation in mm (e.g. 1h volume)")
    visibility: float | None = Field(None, description="Visibility in meters")
    weather_condition: str | None = Field(None, description="Short textual description of weather")


class WeatherObservationCreate(WeatherObservationBase):
    raw_payload: dict[str, Any] = Field(..., description="Raw provider response payload")


class WeatherObservationRead(WeatherObservationBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
