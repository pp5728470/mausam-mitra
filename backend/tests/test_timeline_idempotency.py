"""Phase 7.2 — timeline idempotency + spatial factor consistency."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.correlation_config import DEFAULT_CORRELATION_RADIUS_KM, SPATIAL_BANDS
from app.services.correlation_engine import _band_score, _spatial_factor


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


def test_spatial_score_uses_configured_radius_not_cluster_spread() -> None:
    """1.72 km spread inside 5 km radius must be positive (not 0)."""
    spread = 1.72
    # Bug pattern: treating spread as the configured radius → score 0 when
    # recalculated spread slightly exceeds stored affected radius.
    buggy = _spatial_factor(1.73, 1.72, signal_count=6)
    assert buggy.score == 0.0

    correct = _spatial_factor(
        spread, DEFAULT_CORRELATION_RADIUS_KM, signal_count=6
    )
    expected = _band_score(spread, SPATIAL_BANDS)
    assert correct.score == expected
    assert correct.score == 85.0
    assert "1.72" in correct.detail
    assert "5" in correct.detail
    assert "6 signals" in correct.detail


@pytest.mark.asyncio
async def test_timeline_and_spatial_idempotent_on_repeated_correlate(
    client: AsyncClient,
) -> None:
    lat, lng = 12.9716, 77.5946
    titles = [
        ("Bangalore rain A", "Heavy Rainfall", "Rain A unique SIMULATED 7.2."),
        ("Bangalore water B", "Flood / Waterlogging", "Water B unique SIMULATED 7.2."),
        ("Bangalore flood C", "Flood / Waterlogging", "Flood C unique SIMULATED 7.2."),
    ]
    created = []
    for i, (title, cls, desc) in enumerate(titles):
        resp = await client.post(
            "/api/v1/reports",
            json=_payload(title, lat + i * 0.005, lng + i * 0.005, cls, desc),
        )
        assert resp.status_code == 201, resp.text
        created.append(resp.json())

    v_before = {r["id"]: r["verification_status"] for r in created}

    corr_payload = {
        "latitude": lat,
        "longitude": lng,
        "radius_km": 5,
        "window_minutes": 90,
        "create_incident": True,
    }
    first = await client.post("/api/v1/incidents/correlate", json=corr_payload)
    assert first.status_code == 200, first.text
    body1 = first.json()
    assert body1["threshold_met"] is True
    iid = body1["incident"]["id"]
    score1 = body1["correlation_score"]

    detail1 = await client.get(f"/api/v1/incidents/{iid}/detail")
    assert detail1.status_code == 200
    d1 = detail1.json()
    timeline1 = d1["timeline"]
    count1 = len(timeline1)
    signal1 = [e for e in timeline1 if e["event_type"] == "REPORT_SIGNAL"]
    assert len(signal1) == len(created)
    assert len({e["title"] for e in signal1}) == len(signal1)

    spatial = next(
        f for f in d1["correlation_explanation"] if f["name"] == "spatial"
    )
    assert spatial["score"] > 0
    assert "correlation radius" in spatial["detail"].lower()

    # Three identical correlation runs must not grow timeline.
    second = await client.post("/api/v1/incidents/correlate", json=corr_payload)
    third = await client.post("/api/v1/incidents/correlate", json=corr_payload)
    assert second.status_code == 200 and third.status_code == 200
    assert second.json()["incident"]["id"] == iid
    assert third.json()["incident"]["id"] == iid
    assert second.json()["correlation_score"] == score1
    assert third.json()["correlation_score"] == score1

    detail2 = await client.get(f"/api/v1/incidents/{iid}/detail")
    d2 = detail2.json()
    assert len(d2["timeline"]) == count1
    signal2 = [e for e in d2["timeline"] if e["event_type"] == "REPORT_SIGNAL"]
    assert len(signal2) == len(created)
    cluster_updates = [
        e for e in d2["timeline"] if e["event_type"] == "CLUSTER_UPDATED"
    ]
    # No material change → no extra CLUSTER_UPDATED beyond what first update may have.
    assert len(cluster_updates) <= 1

    assert len(d2["reports"]) == len(created)
    for report in d2["reports"]:
        assert report["verification_status"] == v_before[report["id"]]

    # Spatial remains positive after idempotent re-runs.
    spatial2 = next(
        f for f in d2["correlation_explanation"] if f["name"] == "spatial"
    )
    assert spatial2["score"] == spatial["score"]
    assert spatial2["detail"] == spatial["detail"]
