from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "mausam-mitra-api"
    app_env: str = "development"
    app_debug: bool = False

    database_url: str = (
        "postgresql+psycopg://mausam:mausam_dev_password@localhost:5433/mausam_mitra"
    )

    # Comma-separated browser origins. Include both localhost and 127.0.0.1 —
    # browsers treat them as different origins, and a mismatch blocks the
    # Verification Center (Failed to fetch → empty queue).
    cors_origins: str = (
        "http://localhost:3000,http://127.0.0.1:3000"
    )

    # Phase 7 correlation defaults (overridable via env).
    correlation_radius_km: float = 5.0
    correlation_window_minutes: int = 90
    correlation_score_threshold: float = 70.0
    correlation_min_independent_reports: int = 2

    # Phase 8 weather evidence defaults
    weather_provider: str = "OpenWeatherMap"
    weather_api_key: str | None = None
    weather_base_url: str = "https://api.openweathermap.org/data/2.5"
    weather_evidence_radius_km: float = 10.0
    weather_evidence_time_window_minutes: int = 90

    # Phase 9 Auth / JWT
    jwt_secret_key: str = "PLEASE_CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
