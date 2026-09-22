import pytest
from httpx import AsyncClient
from sqlalchemy import text
from datetime import datetime, timezone

from app.services.weather_provider import MockWeatherProvider
from app.services.weather_ingestion import WeatherIngestionService


@pytest.fixture
def mock_weather_service(monkeypatch):
    """Fixture to force WeatherIngestionService to use MockWeatherProvider in tests."""
    original_get_default_provider = WeatherIngestionService._get_default_provider

    def _mock_get_default_provider(self):
        return MockWeatherProvider()

    monkeypatch.setattr(
        WeatherIngestionService,
        "_get_default_provider",
        _mock_get_default_provider,
    )


@pytest.mark.asyncio
async def test_weather_ingestion_endpoint(client: AsyncClient, mock_weather_service) -> None:
    # Trigger ingestion
    response = await client.post(
        "/api/v1/weather/ingest", params={"latitude": 18.5204, "longitude": 73.8567}
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["provider"] == "MockWeatherProvider"
    assert data["latitude"] == 18.5204
    assert data["longitude"] == 73.8567
    assert data["temperature"] == 25.0
    assert data["precipitation_mm"] == 1.5


@pytest.mark.asyncio
async def test_weather_observations_list(client: AsyncClient, mock_weather_service) -> None:
    # Ingest first
    await client.post(
        "/api/v1/weather/ingest", params={"latitude": 18.52, "longitude": 73.85}
    )
    
    # List observations
    response = await client.get("/api/v1/weather/observations", params={"radius_km": 10.0})
    assert response.status_code == 200
    data = response.json()
    assert data["meta"]["total"] >= 1
    assert data["items"][0]["provider"] == "MockWeatherProvider"
    assert "raw_payload" not in data["items"][0]  # Ensure raw_payload is hidden


@pytest.mark.asyncio
async def test_weather_correlation_with_real_db(client: AsyncClient, mock_weather_service) -> None:
    # 1. Ingest mock weather data (precipitation 1.5mm)
    await client.post(
        "/api/v1/weather/ingest", params={"latitude": 18.5204, "longitude": 73.8567}
    )

    # 2. Create a report for Flood/Waterlogging at the same location
    payload = {
        "source_type": "CITIZEN",
        "source_name": "Citizen",
        "title": "Waterlogging test",
        "description": "Standing water due to rain",
        "latitude": 18.5204,
        "longitude": 73.8567,
        "classification": "Flood / Waterlogging",
        "reported_at": datetime.now(timezone.utc).isoformat(),
    }
    created = await client.post("/api/v1/reports", json=payload)
    assert created.status_code == 201
    report_id = created.json()["id"]

    # 3. Evaluate evidence
    evaluated = await client.post(f"/api/v1/reports/{report_id}/evaluate")
    assert evaluated.status_code == 200
    evidence = evaluated.json()["evidence"]
    
    # 4. Find weather correlation factor
    weather_factor = next(
        e for e in evidence if e["evidence_type"] == "WEATHER_CORRELATION"
    )
    
    # Assert that it used the DB data
    assert weather_factor["metadata"]["live_weather"] is True
    assert weather_factor["metadata"]["provider"] == "MockWeatherProvider"
    assert weather_factor["metadata"].get("status") != "UNAVAILABLE"
    # Precipitation is 1.5mm, which gives a score of 75.0 based on our deterministic logic
    assert weather_factor["score"] == 75.0


@pytest.mark.asyncio
async def test_weather_correlation_unavailable_no_data(client: AsyncClient) -> None:
    # Provide a report far away from any weather observations
    payload = {
        "source_type": "CITIZEN",
        "source_name": "Citizen",
        "title": "Heatwave far away",
        "description": "Very hot weather causing distress",
        "latitude": 40.7128,  # NY, no weather data here
        "longitude": -74.0060,
        "classification": "Heatwave",
        "reported_at": datetime.now(timezone.utc).isoformat(),
    }
    created = await client.post("/api/v1/reports", json=payload)
    assert created.status_code == 201, created.text
    report_id = created.json()["id"]

    evaluated = await client.post(f"/api/v1/reports/{report_id}/evaluate")
    evidence = evaluated.json()["evidence"]
    
    weather_factor = next(
        e for e in evidence if e["evidence_type"] == "WEATHER_CORRELATION"
    )
    
    assert weather_factor["metadata"]["live_weather"] is False
    assert weather_factor["metadata"]["status"] == "UNAVAILABLE"
    assert weather_factor["score"] is None
