import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.main import app
from app.api.deps import get_current_user, get_current_user_optional
from app.core.enums import Role

pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
def unmock_auth(client):
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_current_user_optional, None)
    yield


async def create_user_and_get_token(client: AsyncClient, email: str, role: Role) -> str:
    # We bypass /register because it forces CITIZEN.
    # Instead, we create directly via DB, or if we mock db, wait, we can just insert it.
    pass

# Actually, the easiest way is to mock get_current_user per test, like:
def override_role(role: Role):
    async def _override():
        from app.models.user import User
        import uuid
        return User(id=uuid.uuid4(), email=f"{role}@example.com", role=role, is_active=True)
    return _override

async def test_analytics_rbac_citizen_rejected(client: AsyncClient):
    app.dependency_overrides[get_current_user] = override_role(Role.CITIZEN)
    response = await client.get("/api/v1/analytics/overview")
    assert response.status_code == 403

async def test_analytics_rbac_verifier_rejected(client: AsyncClient):
    app.dependency_overrides[get_current_user] = override_role(Role.VERIFIER)
    response = await client.get("/api/v1/analytics/overview")
    assert response.status_code == 403

async def test_analytics_rbac_analyst_allowed(client: AsyncClient):
    app.dependency_overrides[get_current_user] = override_role(Role.ANALYST)
    response = await client.get("/api/v1/analytics/overview")
    assert response.status_code == 200

async def test_analytics_rbac_admin_allowed(client: AsyncClient):
    app.dependency_overrides[get_current_user] = override_role(Role.ADMIN)
    response = await client.get("/api/v1/analytics/overview")
    assert response.status_code == 200

@pytest.fixture
def as_admin():
    app.dependency_overrides[get_current_user] = override_role(Role.ADMIN)
    yield
    app.dependency_overrides.pop(get_current_user, None)

async def test_analytics_overview_empty_db(client: AsyncClient, as_admin):
    response = await client.get("/api/v1/analytics/overview?days=7")
    assert response.status_code == 200
    data = response.json()
    assert "total_reports" in data
    assert "verified_reports" in data
    assert "rejected_reports" in data
    assert "under_review_reports" in data
    assert "pending_reports" in data
    assert "correlated_incidents" in data
    assert "seeded_incidents" in data
    assert "manual_incidents" in data
    assert "correlation_rate" in data
    assert "classified_reports" in data
    assert isinstance(data["correlation_rate"], float)

async def test_analytics_trends(client: AsyncClient, as_admin):
    response = await client.get("/api/v1/analytics/trends")
    assert response.status_code == 200
    data = response.json()
    assert len(data["reports_24h"]) >= 24
    assert len(data["reports_7d"]) >= 7
    assert len(data["reports_30d"]) >= 30

async def test_analytics_categories(client: AsyncClient, as_admin):
    response = await client.get("/api/v1/analytics/categories")
    assert response.status_code == 200
    data = response.json()
    assert "distribution" in data

async def test_analytics_severity(client: AsyncClient, as_admin):
    response = await client.get("/api/v1/analytics/severity")
    assert response.status_code == 200
    data = response.json()
    assert "distribution" in data

async def test_analytics_geography(client: AsyncClient, as_admin):
    response = await client.get("/api/v1/analytics/geography")
    assert response.status_code == 200
    data = response.json()
    assert "points" in data

async def test_analytics_weather(client: AsyncClient, as_admin):
    response = await client.get("/api/v1/analytics/weather")
    assert response.status_code == 200
    data = response.json()
    if data["observation_count"] == 0:
        assert data["average_temperature"] is None

async def test_analytics_populated_data(client: AsyncClient, db_session: AsyncSession, as_admin):
    from app.models.report import Report
    from app.models.incident import Incident
    from app.core.enums import ReportStatus, VerificationStatus, IncidentOrigin, IncidentStatus, IncidentSeverity, IncidentTrend
    from datetime import datetime, timezone
    import uuid

    now = datetime.now(timezone.utc)

    # Insert incidents
    inc_correlated_id = uuid.uuid4()
    inc_seeded_id = uuid.uuid4()
    inc_manual_id = uuid.uuid4()

    db_session.add_all([
        Incident(id=inc_correlated_id, incident_code="INC-001", incident_type="FLOOD", title="Correlated", origin=IncidentOrigin.CORRELATED, status=IncidentStatus.ACTIVE, severity=IncidentSeverity.CRITICAL, trend=IncidentTrend.RISING, latitude=10.123, longitude=20.123, location="SRID=4326;POINT(20.123 10.123)", created_at=now, updated_at=now, report_count=2),
        Incident(id=inc_seeded_id, incident_code="INC-002", incident_type="FLOOD", title="Seeded", origin=IncidentOrigin.SEEDED, status=IncidentStatus.ACTIVE, severity=IncidentSeverity.CRITICAL, trend=IncidentTrend.RISING, latitude=10.124, longitude=20.124, location="SRID=4326;POINT(20.124 10.124)", created_at=now, updated_at=now, report_count=1),
        Incident(id=inc_manual_id, incident_code="INC-003", incident_type="FLOOD", title="Manual", origin=IncidentOrigin.MANUAL, status=IncidentStatus.ACTIVE, severity=IncidentSeverity.CRITICAL, trend=IncidentTrend.RISING, latitude=10.122, longitude=20.122, location="SRID=4326;POINT(20.122 10.122)", created_at=now, updated_at=now, report_count=1),
    ])

    # Insert reports
    db_session.add_all([
        # 2 linked, verified, classified
        Report(id=uuid.uuid4(), title="Report", source_type="CITIZEN_WEB", source_name="Web", latitude=10.0, longitude=20.0, location="SRID=4326;POINT(20.0 10.0)", description="R1", incident_id=inc_correlated_id, verification_status=VerificationStatus.VERIFIED, classified_category="FLOOD", classification="RAIN", classifier_confidence=0.9, received_at=now, updated_at=now),
        Report(id=uuid.uuid4(), title="Report", source_type="CITIZEN_WEB", source_name="Web", latitude=10.0, longitude=20.0, location="SRID=4326;POINT(20.0 10.0)", description="R2", incident_id=inc_correlated_id, verification_status=VerificationStatus.REJECTED, classified_category=None, classification="WIND", classifier_confidence=None, received_at=now, updated_at=now),
        
        # 3 unlinked (1 under review, 2 pending)
        Report(id=uuid.uuid4(), title="Report", source_type="CITIZEN_WEB", source_name="Web", latitude=10.0, longitude=20.0, location="SRID=4326;POINT(20.0 10.0)", description="R3", incident_id=None, verification_status=VerificationStatus.UNDER_REVIEW, classified_category=None, classification=None, classifier_confidence=None, received_at=now, updated_at=now),
        Report(id=uuid.uuid4(), title="Report", source_type="CITIZEN_WEB", source_name="Web", latitude=10.0, longitude=20.0, location="SRID=4326;POINT(20.0 10.0)", description="R4", incident_id=None, verification_status=VerificationStatus.PENDING, classified_category="EARTHQUAKE", classification="STORM", classifier_confidence=0.8, received_at=now, updated_at=now),
        Report(id=uuid.uuid4(), title="Report", source_type="CITIZEN_WEB", source_name="Web", latitude=10.0, longitude=20.0, location="SRID=4326;POINT(20.0 10.0)", description="R5", incident_id=None, verification_status=VerificationStatus.PENDING, classified_category=None, classification=None, classifier_confidence=None, received_at=now, updated_at=now),
    ])
    await db_session.commit()

    # 1. Test Overview (reports and incidents)
    resp = await client.get("/api/v1/analytics/overview")
    data = resp.json()
    
    # Reports assertions
    assert data["total_reports"] == 5
    assert data["linked_reports"] == 2
    assert data["unlinked_reports"] == 3
    assert data["correlation_rate"] == 40.0
    
    # Verification assertions
    assert data["verified_reports"] == 1
    assert data["rejected_reports"] == 1
    assert data["under_review_reports"] == 1
    assert data["pending_reports"] == 2

    # Incidents assertions (Verify manual/seeded don't inflate operational metrics)
    assert data["total_incidents"] == 3
    assert data["correlated_incidents"] == 1
    assert data["seeded_incidents"] == 1
    assert data["manual_incidents"] == 1
    assert data["active_incidents"] == 1
    assert data["critical_incidents"] == 1
    assert data["rising_incidents"] == 1

    # 2. Test Categories
    resp_cat = await client.get("/api/v1/analytics/categories")
    cat_data = resp_cat.json()["distribution"]
    
    # R1: classified=FLOOD, class=RAIN -> FLOOD
    # R2: classified=None, class=WIND -> WIND
    # R3: classified=None, class=None -> OTHER
    # R4: classified=EARTHQUAKE, class=STORM -> EARTHQUAKE
    # R5: classified=None, class=None -> OTHER
    cat_map = {item["category"]: item["count"] for item in cat_data}
    assert cat_map["FLOOD"] == 1
    assert cat_map["WIND"] == 1
    assert cat_map["EARTHQUAKE"] == 1
    assert cat_map["OTHER"] == 2

    # 3. Test Geography
    resp_geo = await client.get("/api/v1/analytics/geography")
    geo_data = resp_geo.json()["points"]
    # We inserted 3 incidents close to 10.12, 20.12. Rounding to 2 decimal places: 10.12, 20.12
    # So they should cluster into a single point.
    assert len(geo_data) == 1
    assert geo_data[0]["latitude"] == 10.12
    assert geo_data[0]["longitude"] == 20.12
    assert geo_data[0]["incident_count"] == 3
    assert geo_data[0]["report_count"] == 4  # 2 + 1 + 1
