from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import text


@pytest.mark.asyncio
async def test_create_citizen_report(client: AsyncClient) -> None:
    payload = {
        "source_type": "CITIZEN",
        "source_name": "Citizen Report",
        "title": "Street waterlogging near junction",
        "description": (
            "Water has reached the road and vehicles are having difficulty passing."
        ),
        "latitude": 18.5204,
        "longitude": 73.8567,
        "classification": "Flood / Waterlogging",
        "reported_at": datetime.now(timezone.utc).isoformat(),
        "incident_id": "00000000-0000-0000-0000-000000000099",
    }
    created = await client.post("/api/v1/reports", json=payload)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["source_type"] == "CITIZEN"
    assert body["source_name"] == "Citizen Report"
    assert body["status"] == "NEW"
    assert body["incident_id"] is None  # citizen never auto-links
    assert body["classification"] == "Flood / Waterlogging"
    assert body["classification_confidence"] is None
    assert "received_at" in body
    assert body["latitude"] == pytest.approx(18.5204)
    assert body["longitude"] == pytest.approx(73.8567)

    fetched = await client.get(f"/api/v1/reports/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == body["id"]
    assert fetched.json()["status"] == "NEW"


@pytest.mark.asyncio
async def test_citizen_report_has_postgis_location(
    client: AsyncClient, db_session
) -> None:
    payload = {
        "source_type": "CITIZEN",
        "source_name": "Citizen Report",
        "title": "Heavy rainfall observed",
        "description": "Continuous heavy rain for the last twenty minutes.",
        "latitude": 19.076,
        "longitude": 72.8777,
    }
    created = await client.post("/api/v1/reports", json=payload)
    assert created.status_code == 201, created.text
    report_id = created.json()["id"]

    row = (
        await db_session.execute(
            text(
                "SELECT ST_AsText(location) AS wkt, "
                "ST_SRID(location) AS srid "
                "FROM reports WHERE id = :id"
            ),
            {"id": report_id},
        )
    ).mappings().one()
    assert row["srid"] == 4326
    assert "POINT" in row["wkt"]
    assert "72.8777" in row["wkt"]
    assert "19.076" in row["wkt"]


@pytest.mark.asyncio
async def test_invalid_coordinates_rejected(client: AsyncClient) -> None:
    payload = {
        "source_type": "CITIZEN",
        "source_name": "Citizen Report",
        "title": "Bad coordinates report",
        "description": "This should fail coordinate validation on the server.",
        "latitude": 120,
        "longitude": 73.85,
    }
    response = await client.post("/api/v1/reports", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_missing_title_rejected(client: AsyncClient) -> None:
    payload = {
        "source_type": "CITIZEN",
        "source_name": "Citizen Report",
        "description": "Description without a title should be rejected.",
        "latitude": 18.52,
        "longitude": 73.85,
    }
    response = await client.post("/api/v1/reports", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_short_description_rejected(client: AsyncClient) -> None:
    payload = {
        "source_type": "CITIZEN",
        "source_name": "Citizen Report",
        "title": "Valid title here",
        "description": "Too short",
        "latitude": 18.52,
        "longitude": 73.85,
    }
    response = await client.post("/api/v1/reports", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_reports_and_filter_source_type(client: AsyncClient) -> None:
    # Ensure at least one citizen report exists
    payload = {
        "source_type": "CITIZEN",
        "source_name": "Citizen Report",
        "title": "Filterable citizen signal",
        "description": "Used to verify source_type filtering on list endpoint.",
        "latitude": 18.53,
        "longitude": 73.86,
    }
    created = await client.post("/api/v1/reports", json=payload)
    assert created.status_code == 201, created.text

    listed = await client.get("/api/v1/reports?limit=50")
    assert listed.status_code == 200
    body = listed.json()
    assert "items" in body and "meta" in body
    assert body["meta"]["total"] >= 1

    filtered = await client.get("/api/v1/reports?source_type=CITIZEN&limit=50")
    assert filtered.status_code == 200
    data = filtered.json()
    assert data["meta"]["total"] >= 1
    assert all(item["source_type"] == "CITIZEN" for item in data["items"])


@pytest.mark.asyncio
async def test_create_and_get_report(client: AsyncClient) -> None:
    """Backward-compatible create/get smoke (Phase 3). """
    payload = {
        "source_type": "CITIZEN",
        "source_name": "Test Reporter",
        "title": "Test waterlogging signal",
        "description": "Simulated test report for Phase 3 compatibility.",
        "latitude": 18.52,
        "longitude": 73.85,
        "reported_at": datetime.now(timezone.utc).isoformat(),
    }
    created = await client.post("/api/v1/reports", json=payload)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["title"] == payload["title"]
    assert body["status"] == "NEW"
    assert body["incident_id"] is None
    assert "received_at" in body

    fetched = await client.get(f"/api/v1/reports/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == body["id"]
