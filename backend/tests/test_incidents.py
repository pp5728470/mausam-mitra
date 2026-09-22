import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_list_filter_get_incident(client: AsyncClient) -> None:
    payload = {
        "title": "Test Pune Cluster",
        "incident_type": "Flood / Waterlogging",
        "description": "Simulated test incident",
        "severity": "HIGH",
        "status": "EMERGING",
        "trend": "RISING",
        "latitude": 18.5204,
        "longitude": 73.8567,
        "evidence_score": 80,
        "report_count": 10,
    }
    created = await client.post("/api/v1/incidents", json=payload)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["incident_code"].startswith("MM-INC-")
    assert body["severity"] == "HIGH"

    listed = await client.get("/api/v1/incidents", params={"severity": "HIGH", "limit": 50})
    assert listed.status_code == 200
    data = listed.json()
    assert data["meta"]["total"] >= 1
    assert any(item["id"] == body["id"] for item in data["items"])

    filtered = await client.get(
        "/api/v1/incidents",
        params={"status": "EMERGING", "severity": "HIGH"},
    )
    assert filtered.status_code == 200
    assert all(item["status"] == "EMERGING" for item in filtered.json()["items"])

    fetched = await client.get(f"/api/v1/incidents/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == payload["title"]


@pytest.mark.asyncio
async def test_nearby_spatial_query(client: AsyncClient) -> None:
    # Create two points: one near Pune, one near Guwahati
    pune = await client.post(
        "/api/v1/incidents",
        json={
            "title": "Nearby Pune",
            "incident_type": "Flood",
            "severity": "MEDIUM",
            "status": "ACTIVE",
            "trend": "STABLE",
            "latitude": 18.52,
            "longitude": 73.85,
        },
    )
    assert pune.status_code == 201, pune.text

    guwahati = await client.post(
        "/api/v1/incidents",
        json={
            "title": "Far Guwahati",
            "incident_type": "Flood",
            "severity": "CRITICAL",
            "status": "ACTIVE",
            "trend": "RISING",
            "latitude": 26.14,
            "longitude": 91.73,
        },
    )
    assert guwahati.status_code == 201, guwahati.text

    nearby = await client.get(
        "/api/v1/incidents/nearby",
        params={"latitude": 18.52, "longitude": 73.85, "radius_km": 50},
    )
    assert nearby.status_code == 200, nearby.text
    titles = {item["title"] for item in nearby.json()}
    assert "Nearby Pune" in titles
    assert "Far Guwahati" not in titles
    assert all("distance_km" in item for item in nearby.json())


@pytest.mark.asyncio
async def test_incident_not_found(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/incidents/00000000-0000-0000-0000-000000000000"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Incident not found"


@pytest.mark.asyncio
async def test_invalid_incident_coordinates(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/incidents",
        json={
            "title": "Bad",
            "incident_type": "Flood",
            "severity": "LOW",
            "status": "ACTIVE",
            "trend": "STABLE",
            "latitude": 18.5,
            "longitude": 200,
        },
    )
    assert response.status_code == 422
