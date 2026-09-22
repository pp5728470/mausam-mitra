"""Phase 7 correlation engine tests."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import SourceType, VerificationStatus
from app.models.report import Report
from app.services.category_compatibility import (
    category_compatibility_score,
    cluster_category_score,
)
from app.services.correlation_engine import _partition_independent, score_cluster
from app.services.geo import point_wkt
from app.services.incident_type_derivation import (
    derive_incident_title,
    derive_incident_type,
)


def _payload(
    title: str,
    lat: float,
    lng: float,
    classification: str,
    description: str | None = None,
) -> dict:
    return {
        "source_type": "CITIZEN",
        "source_name": "Citizen Report",
        "title": title,
        "description": description
        or f"SIMULATED test signal for {title}. Not a live observation.",
        "latitude": lat,
        "longitude": lng,
        "classification": classification,
    }


@pytest.mark.asyncio
async def test_category_compatibility_matrix() -> None:
    strong, _ = category_compatibility_score("Heavy Rainfall", "Flood / Waterlogging")
    assert strong >= 90
    weak, _ = category_compatibility_score("Extreme Heat", "Dense Fog")
    assert weak <= 20
    neutral, _ = category_compatibility_score(None, "Heavy Rainfall")
    assert neutral == 50.0
    cluster, _ = cluster_category_score(
        ["Heavy Rainfall", "Flood / Waterlogging", "Heavy Rainfall"]
    )
    assert cluster >= 80


@pytest.mark.asyncio
async def test_incident_type_and_title_derivation() -> None:
    assert (
        derive_incident_type(["Heavy Rainfall", "Flood / Waterlogging"])
        == "Flood / Waterlogging"
    )
    assert derive_incident_type(["Storm / Strong Winds", "Lightning"]) == "Severe Storm"
    title = derive_incident_title(
        latitude=18.59,
        longitude=73.74,
        incident_type="Flood / Waterlogging",
        texts=["waterlogging in hinjewadi after rain"],
    )
    assert "Hinjewadi" in title or "Pune" in title
    assert "Waterlogging" in title


@pytest.mark.asyncio
async def test_duplicate_partition_discounts_copies() -> None:
    now = datetime.now(timezone.utc)
    a = Report(
        source_type=SourceType.CITIZEN,
        source_name="Citizen Report",
        title="Waterlogging near Wakad junction",
        description="Standing water on Wakad road after rainfall.",
        latitude=18.598,
        longitude=73.762,
        location=point_wkt(73.762, 18.598),
        received_at=now,
        verification_status=VerificationStatus.PENDING,
    )
    b = Report(
        source_type=SourceType.CITIZEN,
        source_name="Citizen Report",
        title="Waterlogging near Wakad junction",
        description="Standing water on Wakad road after rainfall.",
        latitude=18.5982,
        longitude=73.7622,
        location=point_wkt(73.7622, 18.5982),
        received_at=now,
        verification_status=VerificationStatus.PENDING,
    )
    c = Report(
        source_type=SourceType.CITIZEN,
        source_name="Citizen Report",
        title="Vehicles struggling after flood",
        description="Cars moving slowly through flooded stretch near IT park.",
        latitude=18.59,
        longitude=73.75,
        location=point_wkt(73.75, 18.59),
        received_at=now,
        verification_status=VerificationStatus.PENDING,
    )
    independents, groups = _partition_independent([a, b, c])
    assert groups == 2
    assert len(independents) == 2


@pytest.mark.asyncio
async def test_single_report_does_not_create_incident(client: AsyncClient) -> None:
    iso = await client.post(
        "/api/v1/reports",
        json=_payload(
            "Kashmir isolated drizzle",
            34.0837,
            74.7973,
            "Heavy Rainfall",
        ),
    )
    assert iso.status_code == 201
    only = await client.post(
        "/api/v1/incidents/correlate",
        json={
            "latitude": 34.0837,
            "longitude": 74.7973,
            "radius_km": 3,
            "window_minutes": 90,
        },
    )
    assert only.status_code == 200, only.text
    body = only.json()
    assert body["independent_report_count"] == 1
    assert body["threshold_met"] is False
    assert body["incident"] is None


@pytest.mark.asyncio
async def test_two_compatible_reports_can_create_incident(client: AsyncClient) -> None:
    lat, lng = 16.5062, 80.6480
    r1 = await client.post(
        "/api/v1/reports",
        json=_payload(
            "Heavy rainfall Vijayawada A",
            lat,
            lng,
            "Heavy Rainfall",
            "Heavy rainfall starting across low areas. SIMULATED.",
        ),
    )
    r2 = await client.post(
        "/api/v1/reports",
        json=_payload(
            "Waterlogging Vijayawada B",
            lat + 0.01,
            lng + 0.01,
            "Flood / Waterlogging",
            "Waterlogging on approach road after rain. SIMULATED.",
        ),
    )
    assert r1.status_code == 201 and r2.status_code == 201
    v_before = r1.json()["verification_status"]

    corr = await client.post(
        "/api/v1/incidents/correlate",
        json={"latitude": lat, "longitude": lng, "radius_km": 5, "window_minutes": 90},
    )
    assert corr.status_code == 200, corr.text
    body = corr.json()
    assert body["independent_report_count"] >= 2
    assert body["correlation_score"] >= 70
    assert body["threshold_met"] is True
    assert body["incident"] is not None
    assert body["incident"]["status"] in ("DETECTED", "EMERGING", "ACTIVE")
    assert body["incident"]["incident_code"].startswith("MM-INC-")
    assert body["incident"]["correlation_score"] is not None

    fetched = await client.get(f"/api/v1/reports/{r1.json()['id']}")
    assert fetched.json()["verification_status"] == v_before
    assert fetched.json()["incident_id"] == body["incident"]["id"]
    assert fetched.json()["status"] == "CORRELATED"

    iid = body["incident"]["id"]
    detail = await client.get(f"/api/v1/incidents/{iid}/detail")
    assert detail.status_code == 200
    assert len(detail.json()["reports"]) >= 2
    assert len(detail.json()["timeline"]) >= 1
    assert detail.json()["correlation_explanation"]

    reports = await client.get(f"/api/v1/incidents/{iid}/reports")
    assert reports.status_code == 200
    assert len(reports.json()) >= 2

    timeline = await client.get(f"/api/v1/incidents/{iid}/timeline")
    assert timeline.status_code == 200
    assert len(timeline.json()) >= 1


@pytest.mark.asyncio
async def test_rejected_reports_do_not_strengthen_evidence(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    lat, lng = 15.3173, 75.7139
    a = await client.post(
        "/api/v1/reports",
        json=_payload(
            "Rain Hubli A",
            lat,
            lng,
            "Heavy Rainfall",
            "Rain building. SIMULATED A unique.",
        ),
    )
    b = await client.post(
        "/api/v1/reports",
        json=_payload(
            "Water Hubli B",
            lat + 0.008,
            lng + 0.008,
            "Flood / Waterlogging",
            "Water on road. SIMULATED B unique.",
        ),
    )
    rid_a = a.json()["id"]
    await client.post(
        f"/api/v1/reports/{rid_a}/verify",
        json={"decision": "REJECTED", "notes": "noise"},
    )
    result = await db_session.execute(
        select(Report).where(
            Report.id.in_([UUID(rid_a), UUID(b.json()["id"])])
        )
    )
    reports = list(result.scalars().all())
    scored = await score_cluster(
        db_session, reports, radius_km=5.0, window_minutes=90
    )
    evidence_factor = next(f for f in scored.factors if f.name == "evidence")
    assert "rejected" in evidence_factor.detail.lower()


@pytest.mark.asyncio
async def test_correlation_deterministic_and_spatial_candidates(
    client: AsyncClient,
) -> None:
    lat, lng = 11.0168, 76.9558
    await client.post(
        "/api/v1/reports",
        json=_payload(
            "Coimbatore rain 1",
            lat,
            lng,
            "Heavy Rainfall",
            "Rain one SIMULATED distinct.",
        ),
    )
    await client.post(
        "/api/v1/reports",
        json=_payload(
            "Coimbatore water 2",
            lat + 0.012,
            lng + 0.01,
            "Flood / Waterlogging",
            "Water two SIMULATED distinct text.",
        ),
    )
    await client.post(
        "/api/v1/reports",
        json=_payload(
            "Far away heat",
            lat + 2.0,
            lng + 2.0,
            "Extreme Heat",
            "Unrelated heat SIMULATED.",
        ),
    )
    first = await client.post(
        "/api/v1/incidents/correlate",
        json={
            "latitude": lat,
            "longitude": lng,
            "radius_km": 5,
            "window_minutes": 90,
            "create_incident": False,
        },
    )
    second = await client.post(
        "/api/v1/incidents/correlate",
        json={
            "latitude": lat,
            "longitude": lng,
            "radius_km": 5,
            "window_minutes": 90,
            "create_incident": False,
        },
    )
    assert first.status_code == 200 and second.status_code == 200
    assert first.json()["correlation_score"] == second.json()["correlation_score"]
    assert first.json()["report_count"] >= 2
    assert first.json()["radius_km"] <= 5.5
    assert len(first.json()["factors"]) == 6
