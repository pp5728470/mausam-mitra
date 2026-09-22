import uuid
from datetime import datetime, timezone
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import (
    DateTime,
    Float,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class WeatherObservation(Base):
    __tablename__ = "weather_observations"
    __table_args__ = (
        UniqueConstraint("provider", "observed_at", "latitude", "longitude", name="uq_weather_observation_identity"),
        Index("ix_weather_observations_observed_at", "observed_at"),
        Index("ix_weather_observations_provider", "provider"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    provider: Mapped[str] = mapped_column(String, index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    
    # Normalized 3-decimal precision (~100m) is enough for weather de-duplication
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    
    location: Mapped[Any] = mapped_column(
        Geometry(
            geometry_type="POINT",
            srid=4326,
            spatial_index=True,
        )
    )

    # Weather measurements (nullable)
    temperature: Mapped[float | None] = mapped_column(Float, nullable=True) # Celsius
    humidity: Mapped[float | None] = mapped_column(Float, nullable=True) # Percentage (0-100)
    pressure: Mapped[float | None] = mapped_column(Float, nullable=True) # hPa
    wind_speed: Mapped[float | None] = mapped_column(Float, nullable=True) # m/s
    wind_direction: Mapped[float | None] = mapped_column(Float, nullable=True) # Degrees
    
    # Explicitly named precipitation units
    precipitation_mm: Mapped[float | None] = mapped_column(Float, nullable=True) # mm in the observation period (usually 1h or 3h)
    
    visibility: Mapped[float | None] = mapped_column(Float, nullable=True) # meters
    weather_condition: Mapped[str | None] = mapped_column(String, nullable=True) # e.g., 'Rain', 'Clear'

    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
