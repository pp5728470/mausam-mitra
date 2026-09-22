"""
Mausam Mitra - SIH Demo Data Seed
==================================

Creates a deterministic, reproducible demo dataset for the SIH presentation.

USAGE:
    cd backend
    python -m app.scripts.seed_demo

SAFETY:
    - Never runs automatically on startup
    - Uses INSERT ... ON CONFLICT DO UPDATE (idempotent)
    - Safe to run multiple times
    - Never deletes existing records

DEMO SCENARIO:
    Maharashtra weather intelligence picture - all data is fictional/demo.

DEMO USERS (created if not already present):
    admin@mausam.demo     / Demo@Admin1    (ADMIN)
    analyst@mausam.demo   / Demo@Analyst1  (ANALYST)
    verifier@mausam.demo  / Demo@Verify1   (VERIFIER)
    citizen@mausam.demo   / Demo@Citizen1  (CITIZEN)

    DEVELOPMENT DATABASE ONLY. Do NOT use in production.
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import datetime, timedelta, timezone

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import text

from app.core.enums import (
    AlertStatus,
    AlertType,
    IncidentOrigin,
    IncidentSeverity,
    IncidentStatus,
    IncidentTrend,
    RecipientScope,
    ReportStatus,
    Role,
    SourceType,
    VerificationStatus,
)
from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal

# ---------------------------------------------------------------------------
# Fixed UUIDs - deterministic, safe to run repeatedly
# ---------------------------------------------------------------------------

USER_ADMIN_ID    = uuid.UUID("00000000-0000-0000-0000-000000000001")
USER_ANALYST_ID  = uuid.UUID("00000000-0000-0000-0000-000000000002")
USER_VERIFIER_ID = uuid.UUID("00000000-0000-0000-0000-000000000003")
USER_CITIZEN_ID  = uuid.UUID("00000000-0000-0000-0000-000000000004")

INC_WAKAD_ID  = uuid.UUID("10000000-0000-0000-0000-000000000001")
INC_FOG_ID    = uuid.UUID("10000000-0000-0000-0000-000000000002")
INC_NASHIK_ID = uuid.UUID("10000000-0000-0000-0000-000000000003")
INC_MUMBAI_ID = uuid.UUID("10000000-0000-0000-0000-000000000004")
INC_NAGPUR_ID = uuid.UUID("10000000-0000-0000-0000-000000000005")

DEMO_USERS = [
    {"id": USER_ADMIN_ID,    "email": "admin@mausam.demo",    "full_name": "Demo Admin",    "password": "Demo@Admin1",    "role": Role.ADMIN},
    {"id": USER_ANALYST_ID,  "email": "analyst@mausam.demo",  "full_name": "Demo Analyst",  "password": "Demo@Analyst1",  "role": Role.ANALYST},
    {"id": USER_VERIFIER_ID, "email": "verifier@mausam.demo", "full_name": "Demo Verifier", "password": "Demo@Verify1",   "role": Role.VERIFIER},
    {"id": USER_CITIZEN_ID,  "email": "citizen@mausam.demo",  "full_name": "Demo Citizen",  "password": "Demo@Citizen1",  "role": Role.CITIZEN},
]


def make_incidents(now: datetime) -> list[dict]:
    return [
        {
            "id": INC_WAKAD_ID,
            "code": "MM-DEMO-WKWL",
            "title": "Wakad / Hinjewadi Waterlogging",
            "type": "Flood / Waterlogging",
            "desc": "Severe waterlogging across Wakad, Hinjewadi Phase 1/2/3, and Tathawade after 3+ hours of intense rainfall. Underpasses flooded, traffic disrupted on NH-48.",
            "severity": IncidentSeverity.HIGH,
            "status": IncidentStatus.ACTIVE,
            "trend": IncidentTrend.RISING,
            "origin": IncidentOrigin.CORRELATED,
            "lat": 18.5983, "lng": 73.7560,
            "evidence_score": 87.0, "report_count": 5,
            "correlation_score": 84.5, "independent_count": 4,
            "radius_km": 6.2, "window_min": 90,
            "first_at": now - timedelta(hours=2, minutes=30),
            "last_at":  now - timedelta(minutes=8),
        },
        {
            "id": INC_FOG_ID,
            "code": "MM-DEMO-PNFG",
            "title": "Pune City Dense Fog",
            "type": "Visibility / Dense Fog",
            "desc": "Dense fog reducing visibility below 50 m in Shivajinagar, Deccan, and Kothrud areas. Multiple reports of near-zero visibility on Karve Road.",
            "severity": IncidentSeverity.MEDIUM,
            "status": IncidentStatus.ACTIVE,
            "trend": IncidentTrend.STABLE,
            "origin": IncidentOrigin.CORRELATED,
            "lat": 18.5204, "lng": 73.8567,
            "evidence_score": 72.0, "report_count": 3,
            "correlation_score": 68.0, "independent_count": 3,
            "radius_km": 4.8, "window_min": 60,
            "first_at": now - timedelta(hours=1, minutes=45),
            "last_at":  now - timedelta(minutes=22),
        },
        {
            "id": INC_NASHIK_ID,
            "code": "MM-DEMO-NKRL",
            "title": "Nashik District Heavy Rainfall",
            "type": "Heavy Rainfall",
            "desc": "Sustained heavy rainfall (85 mm/hr at Gangapur Dam gauge) across Nashik. Godavari at caution level. Relief teams on standby.",
            "severity": IncidentSeverity.MEDIUM,
            "status": IncidentStatus.EMERGING,
            "trend": IncidentTrend.RISING,
            "origin": IncidentOrigin.CORRELATED,
            "lat": 20.0059, "lng": 73.7898,
            "evidence_score": 75.0, "report_count": 3,
            "correlation_score": 71.0, "independent_count": 3,
            "radius_km": 8.1, "window_min": 120,
            "first_at": now - timedelta(hours=1, minutes=10),
            "last_at":  now - timedelta(minutes=35),
        },
        {
            "id": INC_MUMBAI_ID,
            "code": "MM-DEMO-MBRN",
            "title": "Mumbai Coastal Heavy Rainfall",
            "type": "Heavy Rainfall",
            "desc": "Intense rainfall band affecting Bandra, Kurla, Andheri East, and Ghatkopar. Mithi River under watch. IMD orange alert in force.",
            "severity": IncidentSeverity.HIGH,
            "status": IncidentStatus.ACTIVE,
            "trend": IncidentTrend.STABLE,
            "origin": IncidentOrigin.CORRELATED,
            "lat": 19.0760, "lng": 72.8777,
            "evidence_score": 91.0, "report_count": 3,
            "correlation_score": 89.0, "independent_count": 2,
            "radius_km": 11.4, "window_min": 90,
            "first_at": now - timedelta(hours=3),
            "last_at":  now - timedelta(minutes=12),
        },
        {
            "id": INC_NAGPUR_ID,
            "code": "MM-DEMO-NGWN",
            "title": "Nagpur Strong Winds / Storm",
            "type": "Storm / Strong Winds",
            "desc": "Gusty winds 60-75 km/hr across Nagpur and Wardha district. Minor structural damage in Civil Lines. Storm weakening based on recent signal velocity.",
            "severity": IncidentSeverity.MEDIUM,
            "status": IncidentStatus.SUBSIDING,
            "trend": IncidentTrend.FALLING,
            "origin": IncidentOrigin.CORRELATED,
            "lat": 21.1458, "lng": 79.0882,
            "evidence_score": 69.0, "report_count": 3,
            "correlation_score": 65.5, "independent_count": 3,
            "radius_km": 7.3, "window_min": 75,
            "first_at": now - timedelta(hours=4),
            "last_at":  now - timedelta(minutes=45),
        },
    ]


def make_reports(now: datetime) -> list[dict]:
    c = USER_CITIZEN_ID

    def r(rid, inc_id, lat, lng, title, desc, offset_min,
          vs=VerificationStatus.VERIFIED, ev=78.0):
        return {
            "id": rid, "incident_id": inc_id,
            "lat": lat, "lng": lng, "title": title, "desc": desc,
            "reported_at": now - timedelta(minutes=offset_min),
            "vs": vs, "ev": ev, "reporter": c,
        }

    w = [uuid.UUID(f"20000000-0000-0000-0000-{i:012d}") for i in range(1, 6)]
    f = [uuid.UUID(f"20000000-0000-0000-0001-{i:012d}") for i in range(1, 4)]
    n = [uuid.UUID(f"20000000-0000-0000-0002-{i:012d}") for i in range(1, 4)]
    m = [uuid.UUID(f"20000000-0000-0000-0003-{i:012d}") for i in range(1, 4)]
    ng = [uuid.UUID(f"20000000-0000-0000-0004-{i:012d}") for i in range(1, 4)]

    return [
        r(w[0], INC_WAKAD_ID, 18.5983, 73.7560, "Wakad underpass completely flooded", "Water level at Wakad main underpass is 4+ feet. Vehicles stranded.", 140),
        r(w[1], INC_WAKAD_ID, 18.6020, 73.7490, "Hinjewadi Phase 2 road waterlogging", "NH-48 near Hinjewadi IT Park blocked. Knee-deep water.", 125, ev=82.0),
        r(w[2], INC_WAKAD_ID, 18.5940, 73.7610, "Tathawade junction blocked", "Tathawade junction flooded. Traffic diverted via Baner road.", 110, ev=76.0),
        r(w[3], INC_WAKAD_ID, 18.5910, 73.7700, "Baner road waterlogging", "Baner road partially waterlogged near D-Mart.", 95, vs=VerificationStatus.PENDING, ev=65.0),
        r(w[4], INC_WAKAD_ID, 18.6050, 73.7420, "Hinjewadi Phase 3 strong rain", "Heavy rainfall continues. Visibility poor. Roads flooded in Phase 3.", 80),
        r(f[0], INC_FOG_ID, 18.5204, 73.8567, "Zero visibility near Shivajinagar", "Cannot see 20 meters ahead on Fergusson College Road. Dense fog.", 100, ev=70.0),
        r(f[1], INC_FOG_ID, 18.5074, 73.8259, "Kothrud dense fog", "Paud Road completely covered in fog. Very dangerous.", 85, ev=72.0),
        r(f[2], INC_FOG_ID, 18.5018, 73.8550, "Deccan visibility alert", "Fog so thick I cannot see road markings. Karve road near JM road.", 70, ev=68.0),
        r(n[0], INC_NASHIK_ID, 20.0059, 73.7898, "Nashik road flooding near CBS", "CBS Chowk flooded after 2 hours of heavy rain. Water entering shops.", 65, ev=74.0),
        r(n[1], INC_NASHIK_ID, 19.9975, 73.8008, "Godavari rising fast", "Godavari water level rising rapidly near Ramkund ghat. Evacuations started.", 50, ev=78.0),
        r(n[2], INC_NASHIK_ID, 20.0150, 73.7750, "College Road Nashik waterlogged", "College Road near Nashik Road station heavily waterlogged.", 38, ev=71.0),
        r(m[0], INC_MUMBAI_ID, 19.0545, 72.9352, "Kurla station waterlogged", "Kurla station area flooded. Trains running 45 minutes late.", 155, ev=91.0),
        r(m[1], INC_MUMBAI_ID, 19.1197, 72.8468, "Andheri East heavy rain", "Andheri East Metro station - heavy rainfall, poor visibility, roads flooded.", 140, ev=88.0),
        r(m[2], INC_MUMBAI_ID, 19.0760, 72.9244, "Ghatkopar road blocked", "LBS Marg Ghatkopar blocked due to flooding. BEST buses rerouted.", 125, ev=86.0),
        r(ng[0], INC_NAGPUR_ID, 21.1458, 79.0882, "Nagpur strong winds Civil Lines", "Gusty winds in Civil Lines. Tree fallen on road near Sitabuldi.", 215, ev=67.0),
        r(ng[1], INC_NAGPUR_ID, 21.1523, 79.0765, "Wardha road storm damage", "Strong winds on Wardha road. Tin shed blown off. Power lines down.", 200, ev=69.0),
        r(ng[2], INC_NAGPUR_ID, 21.1350, 79.0950, "Nagpur airport area wind alert", "Strong cross winds at Nagpur airport perimeter. Flights may be affected.", 185, ev=65.0),
    ]


async def upsert_users(session, users: list[dict]) -> None:
    for u in users:
        await session.execute(text("""
            INSERT INTO users (id, email, full_name, password_hash, role, is_active, created_at, updated_at)
            VALUES (:id, :email, :full_name, :pw, :role, true, now(), now())
            ON CONFLICT (id) DO UPDATE
                SET email=EXCLUDED.email, full_name=EXCLUDED.full_name,
                    role=EXCLUDED.role, is_active=true, updated_at=now()
        """), {"id": u["id"], "email": u["email"], "full_name": u["full_name"],
               "pw": get_password_hash(u["password"]), "role": u["role"].value})
    print(f"  OK {len(users)} demo users upserted")


async def upsert_incidents(session, incidents: list[dict]) -> None:
    for inc in incidents:
        await session.execute(text("""
            INSERT INTO incidents (
                id, incident_code, title, incident_type, description,
                severity, status, trend, origin,
                latitude, longitude, location,
                evidence_score, report_count,
                correlation_score, independent_report_count, radius_km, time_window_minutes,
                first_detected_at, last_updated_at, created_at, updated_at
            ) VALUES (
                :id, :code, :title, :type, :desc,
                :severity, :status, :trend, :origin,
                :lat, :lng, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326),
                :ev_score, :rep_count,
                :corr_score, :ind_count, :radius_km, :window_min,
                :first_at, :last_at, :first_at, now()
            )
            ON CONFLICT (id) DO UPDATE
                SET title=EXCLUDED.title, severity=EXCLUDED.severity,
                    status=EXCLUDED.status, trend=EXCLUDED.trend,
                    evidence_score=EXCLUDED.evidence_score,
                    report_count=EXCLUDED.report_count,
                    correlation_score=EXCLUDED.correlation_score,
                    independent_report_count=EXCLUDED.independent_report_count,
                    last_updated_at=EXCLUDED.last_updated_at,
                    updated_at=now()
        """), {
            "id": inc["id"], "code": inc["code"], "title": inc["title"],
            "type": inc["type"], "desc": inc["desc"],
            "severity": inc["severity"].value, "status": inc["status"].value,
            "trend": inc["trend"].value, "origin": inc["origin"].value,
            "lat": inc["lat"], "lng": inc["lng"],
            "ev_score": inc["evidence_score"], "rep_count": inc["report_count"],
            "corr_score": inc["correlation_score"], "ind_count": inc["independent_count"],
            "radius_km": inc["radius_km"], "window_min": inc["window_min"],
            "first_at": inc["first_at"], "last_at": inc["last_at"],
        })
    print(f"  OK {len(incidents)} demo incidents upserted")


async def upsert_reports(session, reports: list[dict]) -> None:
    for rep in reports:
        await session.execute(text("""
            INSERT INTO reports (
                id, incident_id, source_type, source_name, title, description,
                latitude, longitude, location, reported_at, received_at,
                status, classification, classification_confidence,
                verification_status, evidence_score, reporter_user_id, created_at, updated_at
            ) VALUES (
                :id, :inc_id, 'CITIZEN', 'Citizen Report (Demo)', :title, :desc,
                :lat, :lng, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326), :rep_at, :rep_at,
                'CORRELATED', 'Heavy Rainfall', 0.87,
                :vs, :ev, :reporter, :rep_at, now()
            )
            ON CONFLICT (id) DO UPDATE
                SET incident_id=EXCLUDED.incident_id,
                    verification_status=EXCLUDED.verification_status,
                    evidence_score=EXCLUDED.evidence_score,
                    updated_at=now()
        """), {
            "id": rep["id"], "inc_id": rep["incident_id"],
            "title": rep["title"], "desc": rep["desc"],
            "lat": rep["lat"], "lng": rep["lng"],
            "rep_at": rep["reported_at"],
            "vs": rep["vs"].value, "ev": rep["ev"],
            "reporter": rep["reporter"],
        })
    print(f"  OK {len(reports)} demo reports upserted")


async def upsert_timeline_events(session, incidents: list[dict]) -> None:
    count = 0
    for inc in incidents:
        eid = uuid.uuid5(inc["id"], "tl-created")
        await session.execute(text("""
            INSERT INTO incident_timeline_events
                (id, incident_id, event_type, title, detail, occurred_at, created_at)
            VALUES (:id, :inc_id, 'CREATED', :title, :detail, :at, now())
            ON CONFLICT (id) DO NOTHING
        """), {
            "id": eid, "inc_id": inc["id"],
            "title": "Incident correlated from citizen reports",
            "detail": f"Correlation score {inc['correlation_score']}. {inc['independent_count']} independent signals within {inc['radius_km']} km.",
            "at": inc["first_at"],
        })
        count += 1
        if inc["severity"] in (IncidentSeverity.HIGH, IncidentSeverity.CRITICAL):
            eid2 = uuid.uuid5(inc["id"], "tl-escalated")
            await session.execute(text("""
                INSERT INTO incident_timeline_events
                    (id, incident_id, event_type, title, detail, occurred_at, created_at)
                VALUES (:id, :inc_id, 'ESCALATED', :title, :detail, :at, now())
                ON CONFLICT (id) DO NOTHING
            """), {
                "id": eid2, "inc_id": inc["id"],
                "title": f"Severity escalated to {inc['severity'].value}",
                "detail": "Multiple corroborating reports triggered automatic severity escalation.",
                "at": inc["first_at"] + timedelta(minutes=20),
            })
            count += 1
    print(f"  OK {count} demo timeline events upserted")


async def upsert_alerts(session, incidents: list[dict]) -> None:
    scopes = [RecipientScope.ADMIN, RecipientScope.ANALYST, RecipientScope.VERIFIER]
    count = 0
    for inc in incidents:
        for scope in scopes:
            aid = uuid.uuid5(inc["id"], f"alert-{scope.value}")
            dkey = f"INCIDENT_CREATED:{inc['id']}:{scope.value}"
            await session.execute(text("""
                INSERT INTO alerts (
                    id, alert_type, severity, title, message,
                    status, recipient_scope, dedupe_key,
                    incident_id, created_at, updated_at
                ) VALUES (
                    :id, 'INCIDENT_CREATED', :severity, :title, :msg,
                    'UNREAD', :scope, :dkey,
                    :inc_id, :at, now()
                )
                ON CONFLICT (dedupe_key) DO UPDATE SET updated_at=now()
            """), {
                "id": aid,
                "severity": inc["severity"].value,
                "title": f"New Correlated Incident: {inc['title']}",
                "msg": f"Correlated incident {inc['code']} detected from citizen reports.",
                "scope": scope.value, "dkey": dkey,
                "inc_id": inc["id"], "at": inc["first_at"],
            })
            count += 1
    print(f"  OK {count} demo alerts upserted")


async def seed_demo() -> None:
    now = datetime.now(timezone.utc)
    print()
    print("=" * 60)
    print("  Mausam Mitra - SIH Demo Data Seed")
    print("=" * 60)
    print(f"  Seed time (UTC): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print("  This will INSERT or UPDATE demo records only.")
    print("  No existing records will be deleted.")
    print()

    incidents = make_incidents(now)
    reports = make_reports(now)

    async with AsyncSessionLocal() as session:
        print("Seeding demo users ...")
        await upsert_users(session, DEMO_USERS)

        print("Seeding demo incidents ...")
        await upsert_incidents(session, incidents)

        print("Seeding demo reports ...")
        await upsert_reports(session, reports)

        print("Seeding demo timeline events ...")
        await upsert_timeline_events(session, incidents)

        print("Seeding demo alerts ...")
        await upsert_alerts(session, incidents)

        await session.commit()

    print()
    print("=" * 60)
    print("  DONE - Demo seed complete!")
    print()
    print("  Demo credentials (development DB only):")
    print("    admin@mausam.demo    /  Demo@Admin1")
    print("    analyst@mausam.demo  /  Demo@Analyst1")
    print("    verifier@mausam.demo /  Demo@Verify1")
    print("    citizen@mausam.demo  /  Demo@Citizen1")
    print()
    print("  Incidents seeded:")
    for inc in incidents:
        print(f"    [{inc['code']}] {inc['title']}  ({inc['severity'].value} / {inc['status'].value})")
    print()
    print("  DO NOT use these credentials in production.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed_demo())

