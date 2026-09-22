"""
Seed SIMULATED demo incidents + reports matching the Phase 2 frontend mock set.

Usage (from backend/):
  python -m app.db.seed
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime, timedelta, timezone

# psycopg async requires SelectorEventLoop on Windows (not ProactorEventLoop).
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import delete, func, select, text

from app.core.enums import (
    IncidentOrigin,
    IncidentSeverity,
    IncidentStatus,
    IncidentTrend,
    ReportStatus,
    SourceType,
    VerificationStatus,
)
from app.db.session import AsyncSessionLocal, engine
from app.models.evidence import ReportEvidence
from app.models.incident import Incident
from app.models.report import Report
from app.services.geo import point_wkt
from app.services.evidence_engine import EvidenceEngine

IST = timezone(timedelta(hours=5, minutes=30))
BASE_TIME = datetime(2026, 9, 21, 10, 42, tzinfo=IST)

# Mirrors src/lib/mock/incidents.ts — DEMO / SIMULATED operating picture only.
DEMO_INCIDENTS: list[dict] = [
    {
        "code": "MM-INC-0001",
        "title": "Pune Waterlogging",
        "incident_type": "Flood / Waterlogging",
        "description": "Rapid signal density increase across low-lying urban corridors after intense rainfall.",
        "severity": IncidentSeverity.HIGH,
        "status": IncidentStatus.EMERGING,
        "trend": IncidentTrend.RISING,
        "lat": 18.5204,
        "lng": 73.8567,
        "evidence_score": 87,
        "report_count": 128,
        "last_signal_at": BASE_TIME - timedelta(minutes=2),
    },
    {
        "code": "MM-INC-0002",
        "title": "Mumbai Heavy Rainfall",
        "incident_type": "Heavy Rainfall",
        "description": "Sustained heavy rainfall with correlated citizen reports across coastal wards.",
        "severity": IncidentSeverity.HIGH,
        "status": IncidentStatus.ACTIVE,
        "trend": IncidentTrend.RISING,
        "lat": 19.076,
        "lng": 72.8777,
        "evidence_score": 91,
        "report_count": 214,
        "last_signal_at": BASE_TIME - timedelta(minutes=4),
    },
    {
        "code": "MM-INC-0003",
        "title": "Ahmedabad Heat Stress",
        "incident_type": "Extreme Heat",
        "description": "Verified heat-stress cluster with strong multi-source corroboration.",
        "severity": IncidentSeverity.HIGH,
        "status": IncidentStatus.ACTIVE,
        "trend": IncidentTrend.STABLE,
        "lat": 23.0225,
        "lng": 72.5714,
        "evidence_score": 94,
        "report_count": 96,
        "last_signal_at": BASE_TIME - timedelta(minutes=18),
    },
    {
        "code": "MM-INC-0004",
        "title": "Guwahati Flooding",
        "incident_type": "Flood",
        "description": "Critical flood conditions with high report volume and verified agency signals.",
        "severity": IncidentSeverity.CRITICAL,
        "status": IncidentStatus.ACTIVE,
        "trend": IncidentTrend.RISING,
        "lat": 26.1445,
        "lng": 91.7362,
        "evidence_score": 96,
        "report_count": 341,
        "last_signal_at": BASE_TIME - timedelta(minutes=6),
    },
    {
        "code": "MM-INC-0005",
        "title": "Delhi Severe Weather",
        "incident_type": "Severe Weather",
        "description": "Developing severe weather signals awaiting additional evidence for verification.",
        "severity": IncidentSeverity.MEDIUM,
        "status": IncidentStatus.EMERGING,
        "trend": IncidentTrend.RISING,
        "lat": 28.6139,
        "lng": 77.209,
        "evidence_score": 68,
        "report_count": 54,
        "last_signal_at": BASE_TIME - timedelta(minutes=11),
    },
    {
        "code": "MM-INC-0006",
        "title": "Chennai Heavy Rain",
        "incident_type": "Heavy Rainfall",
        "description": "Active rainfall incident with stable signal growth across coastal districts.",
        "severity": IncidentSeverity.MEDIUM,
        "status": IncidentStatus.ACTIVE,
        "trend": IncidentTrend.STABLE,
        "lat": 13.0827,
        "lng": 80.2707,
        "evidence_score": 82,
        "report_count": 73,
        "last_signal_at": BASE_TIME - timedelta(minutes=14),
    },
    {
        "code": "MM-INC-0007",
        "title": "Kolkata Waterlogging",
        "incident_type": "Waterlogging",
        "description": "Emerging waterlogging cluster with accelerating citizen report density.",
        "severity": IncidentSeverity.HIGH,
        "status": IncidentStatus.EMERGING,
        "trend": IncidentTrend.RISING,
        "lat": 22.5726,
        "lng": 88.3639,
        "evidence_score": 79,
        "report_count": 112,
        "last_signal_at": BASE_TIME - timedelta(minutes=3),
    },
    {
        "code": "MM-INC-0008",
        "title": "Bhopal Storm Corridor",
        "incident_type": "Severe Weather",
        "description": "Storm corridor signals intensifying across central India transit belts.",
        "severity": IncidentSeverity.MEDIUM,
        "status": IncidentStatus.ACTIVE,
        "trend": IncidentTrend.RISING,
        "lat": 23.2599,
        "lng": 77.4126,
        "evidence_score": 74,
        "report_count": 61,
        "last_signal_at": BASE_TIME - timedelta(minutes=9),
    },
    {
        "code": "MM-INC-0009",
        "title": "Jaipur Heat Advisory",
        "incident_type": "Extreme Heat",
        "description": "Verified heat advisory with stable multi-source confirmation.",
        "severity": IncidentSeverity.LOW,
        "status": IncidentStatus.ACTIVE,
        "trend": IncidentTrend.STABLE,
        "lat": 26.9124,
        "lng": 75.7873,
        "evidence_score": 88,
        "report_count": 42,
        "last_signal_at": BASE_TIME - timedelta(minutes=32),
    },
    {
        "code": "MM-INC-0010",
        "title": "Hyderabad Rain Band",
        "incident_type": "Heavy Rainfall",
        "description": "Rain-band signals under review as report velocity begins to ease.",
        "severity": IncidentSeverity.MEDIUM,
        "status": IncidentStatus.EMERGING,
        "trend": IncidentTrend.FALLING,
        "lat": 17.385,
        "lng": 78.4867,
        "evidence_score": 71,
        "report_count": 48,
        "last_signal_at": BASE_TIME - timedelta(minutes=21),
    },
    {
        "code": "MM-INC-0011",
        "title": "Patna River Rise",
        "incident_type": "Flood",
        "description": "River-rise incident with rising report volume along embankment corridors.",
        "severity": IncidentSeverity.HIGH,
        "status": IncidentStatus.ACTIVE,
        "trend": IncidentTrend.RISING,
        "lat": 25.5941,
        "lng": 85.1376,
        "evidence_score": 85,
        "report_count": 157,
        "last_signal_at": BASE_TIME - timedelta(minutes=7),
    },
    {
        "code": "MM-INC-0012",
        "title": "Kochi Coastal Rain",
        "incident_type": "Heavy Rainfall",
        "description": "Verified coastal rainfall with declining short-term signal intensity.",
        "severity": IncidentSeverity.LOW,
        "status": IncidentStatus.ACTIVE,
        "trend": IncidentTrend.FALLING,
        "lat": 9.9312,
        "lng": 76.2673,
        "evidence_score": 90,
        "report_count": 39,
        "last_signal_at": BASE_TIME - timedelta(minutes=27),
    },
]


async def seed(*, reset: bool = True) -> None:
    async with AsyncSessionLocal() as session:
        # Ensure PostGIS is available (migrations should already have done this).
        await session.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))

        if reset:
            await session.execute(delete(ReportEvidence))
            await session.execute(delete(Report))
            await session.execute(delete(Incident))
            await session.commit()

        existing = int(
            (await session.execute(select(func.count()).select_from(Incident))).scalar_one()
            or 0
        )
        if existing >= 12 and not reset:
            print(f"Seed skipped — {existing} incidents already present.")
            return

        for row in DEMO_INCIDENTS:
            incident = Incident(
                incident_code=row["code"],
                title=row["title"],
                incident_type=row["incident_type"],
                description=row["description"],
                severity=row["severity"],
                status=row["status"],
                trend=row["trend"],
                origin=IncidentOrigin.SEEDED,
                latitude=row["lat"],
                longitude=row["lng"],
                location=point_wkt(row["lng"], row["lat"]),
                evidence_score=row["evidence_score"],
                report_count=row["report_count"],
                first_detected_at=row["last_signal_at"] - timedelta(hours=2),
                last_updated_at=row["last_signal_at"],
            )
            session.add(incident)
            await session.flush()

            # Two correlated demo reports per incident (counts on incident remain mock totals).
            for i, source in enumerate(
                (
                    (SourceType.CITIZEN, "Citizen App"),
                    (SourceType.OFFICIAL, "Agency Desk"),
                )
            ):
                source_type, source_name = source
                report = Report(
                    source_type=source_type,
                    source_name=source_name,
                    title=f"{row['title']} — signal {i + 1}",
                    description=(
                        "SIMULATED demo report for Phase 3 seed. "
                        "Not a live weather observation."
                    ),
                    latitude=row["lat"] + (0.01 if i else 0),
                    longitude=row["lng"] + (0.01 if i else 0),
                    location=point_wkt(
                        row["lng"] + (0.01 if i else 0),
                        row["lat"] + (0.01 if i else 0),
                    ),
                    reported_at=row["last_signal_at"] - timedelta(minutes=i + 1),
                    received_at=row["last_signal_at"],
                    status=ReportStatus.CORRELATED,
                    classification=row["incident_type"],
                    classification_confidence=0.7 + (i * 0.05),
                    verification_status=VerificationStatus.PENDING,
                    incident_id=incident.id,
                )
                session.add(report)

        # Phase 6 verification demo reports (citizen raw signals — no incidents).
        demo_reports = [
            {
                "title": "Heavy rainfall in Hinjewadi",
                "description": (
                    "Continuous heavy rain causing waterlogging on the main road. "
                    "Vehicles are moving slowly through standing water."
                ),
                "lat": 18.5912,
                "lng": 73.7389,
                "classification": "Flood / Waterlogging",
                "media_url": "demo://local/hinjewadi-rain.jpg",
                "minutes_ago": 2,
            },
            {
                "title": "Isolated drizzle near outskirts",
                "description": (
                    "Light drizzle observed briefly. No flooding or disruption noted yet."
                ),
                "lat": 26.1445,
                "lng": 91.7362,
                "classification": "Heavy Rainfall",
                "media_url": None,
                "minutes_ago": 40,
                "reported_skew_hours": 36,
            },
            {
                "title": "Street waterlogging near junction",
                "description": (
                    "Water has reached the road and vehicles are having difficulty "
                    "passing near the junction after intense rainfall."
                ),
                "lat": 18.5204,
                "lng": 73.8567,
                "classification": "Flood / Waterlogging",
                "media_url": None,
                "minutes_ago": 8,
            },
            {
                "title": "Street waterlogging near junction",
                "description": (
                    "Water has reached the road and vehicles are having difficulty "
                    "passing near the junction after intense rainfall."
                ),
                "lat": 18.5210,
                "lng": 73.8570,
                "classification": "Flood / Waterlogging",
                "media_url": None,
                "minutes_ago": 6,
            },
            {
                "title": "Unresolved fog patch on highway",
                "description": (
                    "Dense fog reducing visibility on the approach road. "
                    "Drivers are using hazard lights."
                ),
                "lat": 28.6139,
                "lng": 77.2090,
                "classification": "Visibility / Dense Fog",
                "media_url": None,
                "minutes_ago": 15,
            },
        ]

        created_demo: list[Report] = []
        for item in demo_reports:
            received = BASE_TIME - timedelta(minutes=item["minutes_ago"])
            skew = item.get("reported_skew_hours")
            reported = (
                received - timedelta(hours=skew) if skew else received - timedelta(minutes=3)
            )
            report = Report(
                source_type=SourceType.CITIZEN,
                source_name="Citizen Report",
                title=item["title"],
                description=item["description"],
                latitude=item["lat"],
                longitude=item["lng"],
                location=point_wkt(item["lng"], item["lat"]),
                reported_at=reported,
                received_at=received,
                media_url=item["media_url"],
                status=ReportStatus.NEW,
                classification=item["classification"],
                classification_confidence=None,
                verification_status=VerificationStatus.PENDING,
                incident_id=None,
            )
            session.add(report)
            created_demo.append(report)

        await session.commit()

        # Evaluate a subset so Verification Center has realistic evidence.
        engine = EvidenceEngine()
        for report in created_demo:
            await session.refresh(report)
            await engine.evaluate_and_persist(session, report.id)

        # Phase 7 correlation demo — relative to NOW so correlate window finds them.
        now = datetime.now(timezone.utc)
        phase7 = [
            {
                "title": "Heavy rainfall in Hinjewadi",
                "description": "Continuous heavy rain in Hinjewadi. SIMULATED Phase 7 demo signal.",
                "lat": 18.5912,
                "lng": 73.7389,
                "classification": "Heavy Rainfall",
                "minutes_ago": 55,
            },
            {
                "title": "Waterlogging near Wakad junction",
                "description": "Standing water on Wakad road after rainfall. SIMULATED Phase 7 demo signal.",
                "lat": 18.5980,
                "lng": 73.7620,
                "classification": "Flood / Waterlogging",
                "minutes_ago": 43,
            },
            {
                "title": "Flooded road near Hinjewadi",
                "description": "Road flooded near Hinjewadi IT park approach. SIMULATED Phase 7 demo signal.",
                "lat": 18.5880,
                "lng": 73.7450,
                "classification": "Flood / Waterlogging",
                "minutes_ago": 38,
            },
            {
                "title": "Vehicles struggling in Wakad",
                "description": "Vehicles struggling through waterlogged stretch in Wakad. SIMULATED Phase 7 demo.",
                "lat": 18.5955,
                "lng": 73.7685,
                "classification": "Flood / Waterlogging",
                "minutes_ago": 29,
            },
            {
                "title": "Heavy rainfall Tathawade",
                "description": "Heavy rainfall reported around Tathawade. SIMULATED Phase 7 demo signal.",
                "lat": 18.6050,
                "lng": 73.7500,
                "classification": "Heavy Rainfall",
                "minutes_ago": 18,
            },
            # Near-duplicate of report B (should discount independence).
            {
                "title": "Waterlogging near Wakad junction",
                "description": "Standing water on Wakad road after rainfall. SIMULATED Phase 7 demo signal.",
                "lat": 18.5982,
                "lng": 73.7622,
                "classification": "Flood / Waterlogging",
                "minutes_ago": 41,
            },
            # Isolated — should not form its own incident alone.
            {
                "title": "Isolated shower far north",
                "description": "Brief isolated shower. SIMULATED Phase 7 isolated demo — not a cluster.",
                "lat": 28.7041,
                "lng": 77.1025,
                "classification": "Heavy Rainfall",
                "minutes_ago": 20,
            },
            # Unrelated heat.
            {
                "title": "Extreme heat advisory pocket",
                "description": "Extreme heat discomfort reported. SIMULATED Phase 7 unrelated heat demo.",
                "lat": 23.0300,
                "lng": 72.5800,
                "classification": "Extreme Heat",
                "minutes_ago": 25,
            },
            # Insufficient pair near Kochi (only one strong + weak).
            {
                "title": "Light drizzle Kochi outskirts",
                "description": "Light drizzle only. SIMULATED Phase 7 insufficient-evidence demo.",
                "lat": 9.9312,
                "lng": 76.2673,
                "classification": "Heavy Rainfall",
                "minutes_ago": 12,
            },
        ]
        for item in phase7:
            received = now - timedelta(minutes=item["minutes_ago"])
            report = Report(
                source_type=SourceType.CITIZEN,
                source_name="Citizen Report",
                title=item["title"],
                description=item["description"],
                latitude=item["lat"],
                longitude=item["lng"],
                location=point_wkt(item["lng"], item["lat"]),
                reported_at=received - timedelta(minutes=2),
                received_at=received,
                status=ReportStatus.NEW,
                classification=item["classification"],
                verification_status=VerificationStatus.PENDING,
                incident_id=None,
            )
            session.add(report)
        await session.commit()

        incident_count = int(
            (await session.execute(select(func.count()).select_from(Incident))).scalar_one()
        )
        report_count = int(
            (await session.execute(select(func.count()).select_from(Report))).scalar_one()
        )
        print(
            f"Seeded SIMULATED demo data: {incident_count} incidents, "
            f"{report_count} reports (incl. Phase 6/7 demos)."
        )


async def main() -> None:
    try:
        await seed(reset=True)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
