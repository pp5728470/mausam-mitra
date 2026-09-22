import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cors_allows_localhost_and_loopback_origins(
    client: AsyncClient,
) -> None:
    """Browsers treat localhost and 127.0.0.1 as distinct origins."""
    for origin in ("http://localhost:3000", "http://127.0.0.1:3000"):
        response = await client.get(
            "/api/v1/reports",
            params={"limit": 1},
            headers={"Origin": origin},
        )
        assert response.status_code == 200
        assert response.headers.get("access-control-allow-origin") == origin


@pytest.mark.asyncio
async def test_reports_list_shape_for_verification_queue(
    client: AsyncClient,
) -> None:
    """Verification Center expects { items, meta } with verification fields."""
    response = await client.get("/api/v1/reports", params={"limit": 5, "offset": 0})
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body.get("items"), list)
    assert isinstance(body.get("meta"), dict)
    assert isinstance(body["meta"].get("total"), int)
    if body["items"]:
        row = body["items"][0]
        for key in (
            "id",
            "title",
            "latitude",
            "longitude",
            "status",
            "verification_status",
            "evidence_score",
            "incident_id",
            "source_type",
            "received_at",
        ):
            assert key in row
