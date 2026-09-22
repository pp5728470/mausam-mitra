import asyncio
import sys
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from app.main import app
from app.core.config import get_settings
from app.db.session import engine

async def run_live_validation():
    settings = get_settings()
    if not settings.weather_api_key:
        print("ERROR: WEATHER_API_KEY is not configured in .env")
        return

    print("1. WEATHER_API_KEY exists (hidden)")

    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT count(*) FROM weather_observations;"))
        count_before = res.scalar()
    print(f"DB Row Count Before: {count_before}")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Trigger Ingestion
        print("\n--- Triggering Ingestion for Pune ---")
        ingest_res = await client.post("/api/v1/weather/ingest", params={"latitude": 18.5204, "longitude": 73.8567})
        print(f"Ingestion HTTP Status: {ingest_res.status_code}")
        
        if ingest_res.status_code != 201:
            print(f"Error: {ingest_res.text}")
            return
            
        ingest_data = ingest_res.json()
        print("Ingestion Result:")
        print(f"  ID: {ingest_data.get('id')}")
        print(f"  Provider: {ingest_data.get('provider')}")
        print(f"  Observed At: {ingest_data.get('observed_at')}")
        print(f"  Coordinates: {ingest_data.get('latitude')}, {ingest_data.get('longitude')}")
        print(f"  Temperature: {ingest_data.get('temperature')} C")
        print(f"  Humidity: {ingest_data.get('humidity')} %")
        print(f"  Pressure: {ingest_data.get('pressure')} hPa")
        print(f"  Wind Speed: {ingest_data.get('wind_speed')} m/s")
        print(f"  Precipitation: {ingest_data.get('precipitation_mm')} mm")
        print(f"  Weather Condition: {ingest_data.get('weather_condition')}")

        async with engine.connect() as conn:
            res = await conn.execute(text("SELECT count(*) FROM weather_observations;"))
            count_after = res.scalar()
        print(f"\nDB Row Count After: {count_after}")
        print(f"Observation Inserted: {'YES' if count_after > count_before else 'NO'}")

        # Fetch from API
        print("\n--- Querying /api/v1/weather/observations ---")
        obs_res = await client.get("/api/v1/weather/observations", params={"radius_km": 10.0, "latitude": 18.5204, "longitude": 73.8567})
        print(f"Fetch HTTP Status: {obs_res.status_code}")
        obs_data = obs_res.json()
        print(f"Total found in API: {obs_data.get('meta', {}).get('total')}")

        # Evaluate Report
        print("\n--- Evaluating Test Report against Weather ---")
        report_payload = {
            "source_type": "CITIZEN",
            "source_name": "Validation Tester",
            "title": "Rain and flooding",
            "description": "Heavy rain causing standing water",
            "latitude": 18.5204,
            "longitude": 73.8567,
            "classification": "Flood / Waterlogging"
        }
        report_res = await client.post("/api/v1/reports", json=report_payload)
        report_id = report_res.json()["id"]

        eval_res = await client.post(f"/api/v1/reports/{report_id}/evaluate")
        eval_data = eval_res.json()
        
        weather_factor = next((f for f in eval_data["evidence"] if f["evidence_type"] == "WEATHER_CORRELATION"), None)
        if weather_factor:
            print("\nWEATHER_CORRELATION Factor:")
            print(f"  Available: {weather_factor.get('metadata', {}).get('available')}")
            print(f"  Live Weather Used: {weather_factor.get('metadata', {}).get('live_weather')}")
            print(f"  Score: {weather_factor.get('score')}")
            print(f"  Explanation: {weather_factor.get('description')}")
        else:
            print("\nWEATHER_CORRELATION Factor NOT FOUND")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_live_validation())
