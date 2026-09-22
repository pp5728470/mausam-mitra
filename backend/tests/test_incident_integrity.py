"""Phase 7.1 — incident data integrity & correlation honesty."""

from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import IncidentOrigin, VerificationStatus
from app.models.incident import Incident
from app.models.report import Report
from app.services.incidents import is_correlated_record


def _payload(
    title: str,
    lat: float,
    lng: float,
    classification: str,
    description: str,
) -> dict:
    return {
        "source_type": "CITIZEN",
        "source_name": "Citizen Report",
        "title": title,
        "description": description,
        "latitude": lat,
        "longitude": lng,
        "classification": classification,
    }


@pytest.mark.asyncio
async def test_correlated_incident_requires_invariants(client: AsyncClient) -> None:
    """Manual CORRELATED create without score/independence must fail."""
    bad = await client.post(
        "/api/v1/incidents",
        json={
            "title": "Fake Correlated",
            "incident_type": "Heavy Rainfall",
            "severity": "CRITICAL",
            "status": "ACTIVE",
            "trend": "RISING",
            "origin": "CORRELATED",
            "latitude": 18.5,
            "longitude": 73.8,
            "report_count": 0,
            "independent_report_count": 0,
            "correlation_score": None,
        },
    )
    assert bad.status_code == 422


@pytest.mark.asyncio
async def test_legacy_manual_incident_has_no_fake_correlation(
    client: AsyncClient,
) -> None:
    created = await client.post(
        "/api/v1/incidents",
        json={
            "title": "Far Guwahati",
            "incident_type": "Flood / Waterlogging",
            "severity": "CRITICAL",
            "status": "ACTIVE",
            "trend": "RISING",
            "origin": "MANUAL",
            "latitude": 26.1445,
            "longitude": 91.7362,
            "report_count": 0,
            "evidence_score": 10,
        },
    )
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["origin"] == "MANUAL"
    assert body["correlation_score"] is None
    assert body["is_correlated"] is False
    assert body["linked_report_count"] == 0

    detail = await client.get(f"/api/v1/incidents/{body['id']}/detail")
    assert detail.status_code == 200
    assert detail.json()["correlation_explanation"] is None
    assert detail.json()["incident"]["is_correlated"] is False


@pytest.mark.asyncio
async def test_report_count_matches_linked_and_idempotent_correlate(
    client: AsyncClient,
) -> None:
    lat, lng = 17.385, 78.4867
    r1 = await client.post(
        "/api/v1/reports",
        json=_payload(
            "Hyderabad rain A integrity",
            lat,
            lng,
            "Heavy Rainfall",
            "Heavy rainfall in corridor A. SIMULATED integrity.",
        ),
    )
    r2 = await client.post(
        "/api/v1/reports",
        json=_payload(
            "Hyderabad water B integrity",
            lat + 0.01,
            lng + 0.01,
            "Flood / Waterlogging",
            "Waterlogging corridor B. SIMULATED integrity.",
        ),
    )
    assert r1.status_code == 201 and r2.status_code == 201
    v_before = {
        r1.json()["id"]: r1.json()["verification_status"],
        r2.json()["id"]: r2.json()["verification_status"],
    }

    first = await client.post(
        "/api/v1/incidents/correlate",
        json={
            "latitude": lat,
            "longitude": lng,
            "radius_km": 5,
            "window_minutes": 90,
            "create_incident": True,
        },
    )
    assert first.status_code == 200, first.text
    body1 = first.json()
    assert body1["threshold_met"] is True
    assert body1["incident"] is not None
    assert body1["incident"]["origin"] == "CORRELATED"
    assert body1["incident"]["correlation_score"] is not None
    assert body1["independent_report_count"] >= 2
    iid = body1["incident"]["id"]

    second = await client.post(
        "/api/v1/incidents/correlate",
        json={
            "latitude": lat,
            "longitude": lng,
            "radius_km": 5,
            "window_minutes": 90,
            "create_incident": True,
        },
    )
    assert second.status_code == 200, second.text
    body2 = second.json()
    assert body2["incident"]["id"] == iid  # idempotent — same incident

    detail = await client.get(f"/api/v1/incidents/{iid}/detail")
    assert detail.status_code == 200
    d = detail.json()
    linked = len(d["reports"])
    assert d["incident"]["linked_report_count"] == linked
    assert d["incident"]["report_count"] == linked
    assert d["incident"]["independent_report_count"] >= 2
    assert d["incident"]["correlation_score"] is not None
    assert d["incident"]["is_correlated"] is True

    for rid, status in v_before.items():
        fetched = await client.get(f"/api/v1/reports/{rid}")
        assert fetched.json()["verification_status"] == status
        assert fetched.json()["incident_id"] == iid


@pytest.mark.asyncio
async def test_is_correlated_record_helper() -> None:
    incident = Incident(
        incident_code="MM-INC-TEST",
        title="x",
        incident_type="Heavy Rainfall",
        severity="MEDIUM",  # type: ignore[arg-type]
        status="ACTIVE",  # type: ignore[arg-type]
        trend="STABLE",  # type: ignore[arg-type]
        origin=IncidentOrigin.CORRELATED,
        latitude=0,
        longitude=0,
        location="POINT(0 0)",
        evidence_score=50,
        report_count=2,
        correlation_score=80,
        independent_report_count=2,
    )
    assert is_correlated_record(incident, linked_count=2) is True
    assert is_correlated_record(incident, linked_count=1) is False
    incident.correlation_score = None
    assert is_correlated_record(incident, linked_count=2) is False


@pytest.mark.asyncio
async def test_overview_list_exposes_linked_counts(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    """List payload must expose honesty fields used by Overview KPIs."""
    page = await client.get("/api/v1/incidents?limit=100")
    assert page.status_code == 200
    items = page.json()["items"]
    assert isinstance(items, list)
    for item in items:
        assert "origin" in item
        assert "linked_report_count" in item
        assert "is_correlated" in item
        if item["is_correlated"]:
            assert item["correlation_score"] is not None
            assert item["independent_report_count"] >= 2
            assert item["linked_report_count"] >= 2
            assert item["report_count"] == item["linked_report_count"]
        else:
            # Legacy/seeded/manual must not pretend to be correlated clusters.
            assert item["is_correlated"] is False

    # Spot-check DB membership vs API linked_report_count for correlated rows.
    correlated = [i for i in items if i["is_correlated"]]
    for item in correlated[:5]:
        result = await db_session.execute(
            select(Report).where(Report.incident_id == UUID(item["id"]))
        )
        linked = list(result.scalars().all())
        assert len(linked) == item["linked_report_count"]
        for report in linked:
            assert report.verification_status in VerificationStatus
