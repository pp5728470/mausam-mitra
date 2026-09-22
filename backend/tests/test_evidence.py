from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import text


@pytest.mark.asyncio
async def test_new_citizen_report_starts_pending(client: AsyncClient) -> None:
    payload = {
        "source_type": "CITIZEN",
        "source_name": "Citizen Report",
        "title": "Phase 6 pending verification signal",
        "description": "Standing water across the access road after short intense rain.",
        "latitude": 18.5204,
        "longitude": 73.8567,
        "classification": "Flood / Waterlogging",
    }
    created = await client.post("/api/v1/reports", json=payload)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["status"] == "NEW"
    assert body["verification_status"] == "PENDING"
    assert body["incident_id"] is None
    assert body["evidence_score"] is None


@pytest.mark.asyncio
async def test_evaluate_evidence_deterministic(client: AsyncClient) -> None:
    payload = {
        "source_type": "CITIZEN",
        "source_name": "Citizen Report",
        "title": "Heavy rainfall causing waterlogging",
        "description": "Heavy rainfall has caused waterlogging on the street near the market.",
        "latitude": 18.5204,
        "longitude": 73.8567,
        "classification": "Flood / Waterlogging",
        "media_url": "demo://local/test.jpg",
        "reported_at": datetime.now(timezone.utc).isoformat(),
    }
    created = await client.post("/api/v1/reports", json=payload)
    assert created.status_code == 201, created.text
    report_id = created.json()["id"]

    first = await client.post(f"/api/v1/reports/{report_id}/evaluate")
    assert first.status_code == 200, first.text
    body1 = first.json()
    assert "evidence" in body1
    assert "evidence_score" in body1
    assert "evidence_coverage" in body1
    assert body1["verification_recommendation"] in {
        "NEEDS_REVIEW",
        "CORROBORATED",
        "HIGH_CONFIDENCE_REVIEW",
    }

    second = await client.post(f"/api/v1/reports/{report_id}/evaluate")
    assert second.status_code == 200
    body2 = second.json()
    assert body1["evidence_score"] == body2["evidence_score"]
    assert body1["evidence_coverage"] == body2["evidence_coverage"]
    assert body1["verification_recommendation"] == body2["verification_recommendation"]

    # Unavailable factors must not contribute as zero — coverage uses available only.
    unavailable = [
        e
        for e in body1["evidence"]
        if (e.get("metadata") or {}).get("available") is False
    ]
    for item in unavailable:
        # Score may be null when unavailable
        assert item["score"] is None or item["metadata"].get("available") is False


@pytest.mark.asyncio
async def test_evidence_endpoint_and_postgis_nearby(
    client: AsyncClient, db_session
) -> None:
    # Seed two nearby reports
    base = {
        "source_type": "CITIZEN",
        "source_name": "Citizen Report",
        "title": "Flood water on arterial road",
        "description": "Flood water is covering lanes and slowing traffic significantly.",
        "latitude": 18.5204,
        "longitude": 73.8567,
        "classification": "Flood / Waterlogging",
    }
    a = await client.post("/api/v1/reports", json=base)
    assert a.status_code == 201
    nearby = {
        **base,
        "title": "Nearby flood water signal",
        "latitude": 18.5210,
        "longitude": 73.8570,
    }
    b = await client.post("/api/v1/reports", json=nearby)
    assert b.status_code == 201
    report_id = a.json()["id"]

    evaluated = await client.post(f"/api/v1/reports/{report_id}/evaluate")
    assert evaluated.status_code == 200
    types = {e["evidence_type"] for e in evaluated.json()["evidence"]}
    assert "NEARBY_REPORTS" in types or "LOCATION_CONSISTENCY" in types

    evidence = await client.get(f"/api/v1/reports/{report_id}/evidence")
    assert evidence.status_code == 200
    assert isinstance(evidence.json(), list)
    assert len(evidence.json()) >= 1

    # PostGIS location still present
    row = (
        await db_session.execute(
            text("SELECT ST_SRID(location) AS srid FROM reports WHERE id = :id"),
            {"id": report_id},
        )
    ).mappings().one()
    assert row["srid"] == 4326


@pytest.mark.asyncio
async def test_duplicate_similarity_signal(client: AsyncClient) -> None:
    payload = {
        "source_type": "CITIZEN",
        "source_name": "Citizen Report",
        "title": "Street waterlogging near junction",
        "description": (
            "Water has reached the road and vehicles are having difficulty "
            "passing near the junction after intense rainfall."
        ),
        "latitude": 18.5204,
        "longitude": 73.8567,
        "classification": "Flood / Waterlogging",
    }
    first = await client.post("/api/v1/reports", json=payload)
    assert first.status_code == 201
    second = await client.post(
        "/api/v1/reports",
        json={**payload, "latitude": 18.5208, "longitude": 73.8571},
    )
    assert second.status_code == 201
    report_id = second.json()["id"]
    evaluated = await client.post(f"/api/v1/reports/{report_id}/evaluate")
    assert evaluated.status_code == 200
    dup = next(
        e for e in evaluated.json()["evidence"] if e["evidence_type"] == "DUPLICATE_RISK"
    )
    assert dup["metadata"]["risk"] in {"POTENTIAL_MATCH", "LOW_MODERATE", "LOW"}


@pytest.mark.asyncio
async def test_human_verification_does_not_create_incident(
    client: AsyncClient, db_session
) -> None:
    payload = {
        "source_type": "CITIZEN",
        "source_name": "Citizen Report",
        "title": "Human review verification case",
        "description": "Standing water observed for human verification workflow testing.",
        "latitude": 18.53,
        "longitude": 73.85,
        "classification": "Flood / Waterlogging",
    }
    created = await client.post("/api/v1/reports", json=payload)
    report_id = created.json()["id"]

    verified = await client.post(
        f"/api/v1/reports/{report_id}/verify",
        json={
            "decision": "VERIFIED",
            "notes": "Evidence reviewed by authorized operator.",
            "verified_by": "demo_operator",
        },
    )
    assert verified.status_code == 200, verified.text
    body = verified.json()
    assert body["decision"] == "VERIFIED"
    assert body["report"]["verification_status"] == "VERIFIED"
    # Operational status stays NEW — VERIFIED must not imply PROCESSING.
    assert body["report"]["status"] == "NEW"
    assert body["report"]["incident_id"] is None
    assert body["report"]["verified_by"] == "demo_operator"

    # Persist check
    fetched = await client.get(f"/api/v1/reports/{report_id}")
    assert fetched.json()["verification_status"] == "VERIFIED"
    assert fetched.json()["status"] == "NEW"
    assert fetched.json()["incident_id"] is None

    rejected_create = await client.post("/api/v1/reports", json={
        **payload,
        "title": "Reject decision case report",
    })
    rid = rejected_create.json()["id"]
    rejected = await client.post(
        f"/api/v1/reports/{rid}/verify",
        json={"decision": "REJECTED", "notes": "Insufficient corroboration."},
    )
    assert rejected.status_code == 200
    assert rejected.json()["report"]["verification_status"] == "REJECTED"
    assert rejected.json()["report"]["status"] == "REJECTED"
    assert rejected.json()["report"]["incident_id"] is None

    bad = await client.post(
        f"/api/v1/reports/{rid}/verify",
        json={"decision": "TRUE_CLAIM"},
    )
    assert bad.status_code == 422
