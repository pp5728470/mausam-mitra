import pytest
import uuid
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.alert import Alert
from app.models.incident import Incident
from app.models.report import Report
from app.models.user import User
from app.core.enums import (
    AlertStatus, AlertType, IncidentOrigin, IncidentSeverity,
    IncidentStatus, IncidentTrend, RecipientScope, Role, 
    ReportStatus, VerificationStatus, SourceType
)
from app.services.alerts import (
    evaluate_new_correlated_incident,
    evaluate_incident_escalation,
    evaluate_incident_status_change,
    evaluate_incident_trend_change,
    evaluate_verification_required,
    evaluate_report_verification_decision,
)
from app.main import app
from app.api.deps import get_current_user, get_db

@pytest.fixture
def mock_user_id():
    return uuid.uuid4()

@pytest.fixture
def mock_incident_id():
    return uuid.uuid4()

@pytest.fixture
def mock_report_id():
    return uuid.uuid4()

# Helper for creating Incidents
def create_mock_incident(incident_id, severity, status, trend, origin=IncidentOrigin.CORRELATED):
    return Incident(
        id=incident_id,
        incident_code=f"INC-{uuid.uuid4().hex[:8]}",
        title=f"Test Inc {uuid.uuid4().hex[:8]}",
        incident_type="Flood",
        origin=origin,
        severity=severity,
        status=status,
        trend=trend,
        latitude=0, longitude=0, location="POINT(0 0)"
    )

# Helper for creating Reports
def create_mock_report(report_id, verification_status, reporter_id=None):
    return Report(
        id=report_id,
        source_type=SourceType.CITIZEN,
        source_name="Test Source",
        title="Test Report",
        description="D",
        status=ReportStatus.NEW,
        verification_status=verification_status,
        reporter_user_id=reporter_id,
        latitude=0, longitude=0, location="POINT(0 0)"
    )

# A. ALERT CREATION

@pytest.mark.asyncio
async def test_incident_created_alert(db_session: AsyncSession, mock_incident_id):
    incident = create_mock_incident(mock_incident_id, IncidentSeverity.HIGH, IncidentStatus.EMERGING, IncidentTrend.STABLE)
    db_session.add(incident)
    await db_session.commit()
    await evaluate_new_correlated_incident(db_session, incident=incident)
    await db_session.commit()
    result = await db_session.execute(select(Alert).where(Alert.incident_id == mock_incident_id))
    alerts = result.scalars().all()
    assert len(alerts) > 0
    assert alerts[0].alert_type == AlertType.INCIDENT_CREATED

@pytest.mark.asyncio
async def test_seeded_incident_no_operational_alert(db_session: AsyncSession, mock_incident_id):
    incident = create_mock_incident(mock_incident_id, IncidentSeverity.HIGH, IncidentStatus.EMERGING, IncidentTrend.STABLE, origin=IncidentOrigin.SEEDED)
    db_session.add(incident)
    await db_session.commit()
    if incident.origin == IncidentOrigin.CORRELATED:
        await evaluate_new_correlated_incident(db_session, incident=incident)
    await db_session.commit()
    result = await db_session.execute(select(Alert).where(Alert.incident_id == mock_incident_id))
    assert len(result.scalars().all()) == 0

@pytest.mark.asyncio
async def test_manual_incident_no_operational_alert(db_session: AsyncSession, mock_incident_id):
    incident = create_mock_incident(mock_incident_id, IncidentSeverity.HIGH, IncidentStatus.EMERGING, IncidentTrend.STABLE, origin=IncidentOrigin.MANUAL)
    db_session.add(incident)
    await db_session.commit()
    if incident.origin == IncidentOrigin.CORRELATED:
        await evaluate_new_correlated_incident(db_session, incident=incident)
    await db_session.commit()
    result = await db_session.execute(select(Alert).where(Alert.incident_id == mock_incident_id))
    assert len(result.scalars().all()) == 0

# B. SEVERITY

@pytest.mark.asyncio
async def test_severity_escalation(db_session: AsyncSession, mock_incident_id):
    incident = create_mock_incident(mock_incident_id, IncidentSeverity.HIGH, IncidentStatus.ACTIVE, IncidentTrend.STABLE)
    db_session.add(incident)
    await db_session.commit()
    await evaluate_incident_escalation(db_session, incident=incident, old_severity=IncidentSeverity.MEDIUM)
    await db_session.commit()
    result = await db_session.execute(select(Alert).where(Alert.incident_id == mock_incident_id))
    alerts = result.scalars().all()
    assert len(alerts) > 0
    assert alerts[0].alert_type == AlertType.INCIDENT_ESCALATED

@pytest.mark.asyncio
async def test_downward_severity_no_escalation(db_session: AsyncSession, mock_incident_id):
    incident = create_mock_incident(mock_incident_id, IncidentSeverity.MEDIUM, IncidentStatus.ACTIVE, IncidentTrend.STABLE)
    db_session.add(incident)
    await db_session.commit()
    await evaluate_incident_escalation(db_session, incident=incident, old_severity=IncidentSeverity.HIGH)
    await db_session.commit()
    result = await db_session.execute(select(Alert).where(Alert.incident_id == mock_incident_id))
    assert len(result.scalars().all()) == 0

@pytest.mark.asyncio
async def test_unchanged_severity_no_alert(db_session: AsyncSession, mock_incident_id):
    incident = create_mock_incident(mock_incident_id, IncidentSeverity.HIGH, IncidentStatus.ACTIVE, IncidentTrend.STABLE)
    db_session.add(incident)
    await db_session.commit()
    await evaluate_incident_escalation(db_session, incident=incident, old_severity=IncidentSeverity.HIGH)
    await db_session.commit()
    result = await db_session.execute(select(Alert).where(Alert.incident_id == mock_incident_id))
    assert len(result.scalars().all()) == 0

# C. STATUS

@pytest.mark.asyncio
async def test_status_transition(db_session: AsyncSession, mock_incident_id):
    incident = create_mock_incident(mock_incident_id, IncidentSeverity.HIGH, IncidentStatus.ACTIVE, IncidentTrend.STABLE)
    db_session.add(incident)
    await db_session.commit()
    await evaluate_incident_status_change(db_session, incident=incident, old_status=IncidentStatus.EMERGING)
    await db_session.commit()
    result = await db_session.execute(select(Alert).where(Alert.incident_id == mock_incident_id))
    alerts = result.scalars().all()
    assert len(alerts) > 0
    assert alerts[0].alert_type == AlertType.INCIDENT_STATUS_CHANGED

@pytest.mark.asyncio
async def test_unchanged_status_no_alert(db_session: AsyncSession, mock_incident_id):
    incident = create_mock_incident(mock_incident_id, IncidentSeverity.HIGH, IncidentStatus.ACTIVE, IncidentTrend.STABLE)
    db_session.add(incident)
    await db_session.commit()
    await evaluate_incident_status_change(db_session, incident=incident, old_status=IncidentStatus.ACTIVE)
    await db_session.commit()
    result = await db_session.execute(select(Alert).where(Alert.incident_id == mock_incident_id))
    assert len(result.scalars().all()) == 0

# D. TREND

@pytest.mark.asyncio
async def test_trend_transition(db_session: AsyncSession, mock_incident_id):
    incident = create_mock_incident(mock_incident_id, IncidentSeverity.HIGH, IncidentStatus.ACTIVE, IncidentTrend.RISING)
    db_session.add(incident)
    await db_session.commit()
    await evaluate_incident_trend_change(db_session, incident=incident, old_trend=IncidentTrend.STABLE)
    await db_session.commit()
    result = await db_session.execute(select(Alert).where(Alert.incident_id == mock_incident_id))
    alerts = result.scalars().all()
    assert len(alerts) > 0
    assert alerts[0].alert_type == AlertType.INCIDENT_TREND_CHANGED

@pytest.mark.asyncio
async def test_unchanged_trend_no_alert(db_session: AsyncSession, mock_incident_id):
    incident = create_mock_incident(mock_incident_id, IncidentSeverity.HIGH, IncidentStatus.ACTIVE, IncidentTrend.RISING)
    db_session.add(incident)
    await db_session.commit()
    await evaluate_incident_trend_change(db_session, incident=incident, old_trend=IncidentTrend.RISING)
    await db_session.commit()
    result = await db_session.execute(select(Alert).where(Alert.incident_id == mock_incident_id))
    assert len(result.scalars().all()) == 0

# E. VERIFICATION

@pytest.mark.asyncio
async def test_verification_required(db_session: AsyncSession, mock_report_id):
    report = create_mock_report(mock_report_id, VerificationStatus.PENDING)
    db_session.add(report)
    await db_session.commit()
    await evaluate_verification_required(db_session, report=report)
    await db_session.commit()
    result = await db_session.execute(select(Alert).where(Alert.report_id == mock_report_id))
    alerts = result.scalars().all()
    assert len(alerts) > 0
    assert alerts[0].alert_type == AlertType.VERIFICATION_REQUIRED

@pytest.mark.asyncio
async def test_report_verified_alert(db_session: AsyncSession, mock_report_id, mock_user_id):
    u = User(id=mock_user_id, email=f"u_{uuid.uuid4().hex[:8]}@test.com", full_name="User", password_hash="h", role=Role.CITIZEN, is_active=True)
    db_session.add(u)
    await db_session.commit()
    report = create_mock_report(mock_report_id, VerificationStatus.VERIFIED, reporter_id=mock_user_id)
    db_session.add(report)
    await db_session.commit()
    await evaluate_report_verification_decision(db_session, report=report, decision="VERIFIED")
    await db_session.commit()
    result = await db_session.execute(select(Alert).where(Alert.report_id == mock_report_id))
    alerts = result.scalars().all()
    assert len(alerts) == 4
    scopes = {a.recipient_scope for a in alerts}
    assert RecipientScope.CITIZEN_REPORTER in scopes

@pytest.mark.asyncio
async def test_report_rejected_alert(db_session: AsyncSession, mock_report_id, mock_user_id):
    u = User(id=mock_user_id, email=f"u_{uuid.uuid4().hex[:8]}@test.com", full_name="User", password_hash="h", role=Role.CITIZEN, is_active=True)
    db_session.add(u)
    await db_session.commit()
    report = create_mock_report(mock_report_id, VerificationStatus.REJECTED, reporter_id=mock_user_id)
    db_session.add(report)
    await db_session.commit()
    await evaluate_report_verification_decision(db_session, report=report, decision="REJECTED")
    await db_session.commit()
    result = await db_session.execute(select(Alert).where(Alert.report_id == mock_report_id))
    alerts = result.scalars().all()
    assert len(alerts) == 4
    scopes = {a.recipient_scope for a in alerts}
    assert RecipientScope.CITIZEN_REPORTER in scopes
    assert any(a.alert_type == AlertType.REPORT_REJECTED for a in alerts)

# F. DEDUPLICATION / IDEMPOTENCY

@pytest.mark.asyncio
async def test_alert_deduplication(db_session: AsyncSession, mock_incident_id):
    incident = create_mock_incident(mock_incident_id, IncidentSeverity.HIGH, IncidentStatus.ACTIVE, IncidentTrend.STABLE)
    db_session.add(incident)
    await db_session.commit()
    await evaluate_new_correlated_incident(db_session, incident=incident)
    await evaluate_new_correlated_incident(db_session, incident=incident)
    await db_session.commit()
    result = await db_session.execute(
        select(Alert).where(Alert.incident_id == mock_incident_id, Alert.recipient_scope == RecipientScope.ADMIN)
    )
    alerts = result.scalars().all()
    assert len(alerts) == 1

@pytest.mark.asyncio
async def test_recipient_aware_deduplication(db_session: AsyncSession, mock_incident_id):
    incident = create_mock_incident(mock_incident_id, IncidentSeverity.HIGH, IncidentStatus.ACTIVE, IncidentTrend.STABLE)
    db_session.add(incident)
    await db_session.commit()
    await evaluate_new_correlated_incident(db_session, incident=incident)
    await db_session.commit()
    result = await db_session.execute(select(Alert).where(Alert.incident_id == mock_incident_id))
    alerts = result.scalars().all()
    assert len(alerts) == 3
    scopes = {a.recipient_scope for a in alerts}
    assert scopes == {RecipientScope.ADMIN, RecipientScope.ANALYST, RecipientScope.VERIFIER}

@pytest.mark.asyncio
async def test_correlation_rerun_no_duplicate_alert(db_session: AsyncSession, mock_incident_id):
    incident = create_mock_incident(mock_incident_id, IncidentSeverity.HIGH, IncidentStatus.ACTIVE, IncidentTrend.STABLE)
    db_session.add(incident)
    await db_session.commit()
    await evaluate_new_correlated_incident(db_session, incident=incident)
    await evaluate_new_correlated_incident(db_session, incident=incident)
    await db_session.commit()
    count = await db_session.scalar(select(func.count()).select_from(Alert).where(Alert.incident_id == mock_incident_id))
    assert count == 3


@pytest.mark.asyncio
async def test_alert_insert_does_not_rollback_parent_transaction(db_session: AsyncSession, mock_incident_id):
    incident = create_mock_incident(mock_incident_id, IncidentSeverity.HIGH, IncidentStatus.ACTIVE, IncidentTrend.STABLE)
    db_session.add(incident)
    await db_session.commit()
    await evaluate_new_correlated_incident(db_session, incident=incident)
    incident.title = "Updated Title"
    db_session.add(incident)
    await evaluate_new_correlated_incident(db_session, incident=incident)
    await db_session.commit()
    result = await db_session.execute(select(Incident).where(Incident.id == mock_incident_id))
    i = result.scalar_one()
    assert i.title == "Updated Title"

# RBAC AND API HELPERS

async def get_test_client_as(user: User, db_session: AsyncSession):
    def override_get_current_user():
        return user
    
    async def override_get_db():
        yield db_session
        
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    client = AsyncClient(transport=transport, base_url="http://test")
    return client

@pytest.mark.asyncio
async def test_citizen_only_sees_own_report_alerts(db_session: AsyncSession):
    u = User(id=uuid.uuid4(), email=f"u_{uuid.uuid4().hex[:8]}@test.com", full_name="Cit", password_hash="hash", role=Role.CITIZEN, is_active=True)
    # other_user must be persisted so the FK on alert_other is satisfied
    other_user = User(id=uuid.uuid4(), email=f"other_{uuid.uuid4().hex[:8]}@test.com", full_name="Other", password_hash="hash", role=Role.CITIZEN, is_active=True)
    db_session.add_all([u, other_user])
    alert_mine = Alert(id=uuid.uuid4(), alert_type=AlertType.REPORT_VERIFIED, title="Mine", message="M", recipient_scope=RecipientScope.CITIZEN_REPORTER, recipient_user_id=u.id, dedupe_key=f"D_{uuid.uuid4().hex[:8]}")
    alert_other = Alert(id=uuid.uuid4(), alert_type=AlertType.REPORT_VERIFIED, title="Other", message="M", recipient_scope=RecipientScope.CITIZEN_REPORTER, recipient_user_id=other_user.id, dedupe_key=f"D_{uuid.uuid4().hex[:8]}")
    db_session.add_all([alert_mine, alert_other])
    await db_session.commit()
    
    client = await get_test_client_as(u, db_session)
    async with client:
        res = await client.get("/api/v1/alerts")
        assert res.status_code == 200
        data = res.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == str(alert_mine.id)
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_citizen_cannot_see_operational_alerts(db_session: AsyncSession):
    u = User(id=uuid.uuid4(), email=f"u_{uuid.uuid4().hex[:8]}@test.com", full_name="Cit", password_hash="hash", role=Role.CITIZEN, is_active=True)
    db_session.add(u)
    alert_op = Alert(id=uuid.uuid4(), alert_type=AlertType.INCIDENT_CREATED, title="Op", message="M", recipient_scope=RecipientScope.ADMIN, dedupe_key=f"D_{uuid.uuid4().hex[:8]}")
    db_session.add(alert_op)
    await db_session.commit()
    
    client = await get_test_client_as(u, db_session)
    async with client:
        res = await client.get("/api/v1/alerts")
        assert len(res.json()["items"]) == 0
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_verifier_alert_scope(db_session: AsyncSession):
    u = User(id=uuid.uuid4(), email=f"u_{uuid.uuid4().hex[:8]}@test.com", full_name="Ver", password_hash="hash", role=Role.VERIFIER, is_active=True)
    db_session.add(u)
    alert_ver = Alert(id=uuid.uuid4(), alert_type=AlertType.INCIDENT_CREATED, title="Ver", message="M", recipient_scope=RecipientScope.VERIFIER, dedupe_key=f"D_{uuid.uuid4().hex[:8]}")
    alert_admin = Alert(id=uuid.uuid4(), alert_type=AlertType.INCIDENT_CREATED, title="Adm", message="M", recipient_scope=RecipientScope.ADMIN, dedupe_key=f"D_{uuid.uuid4().hex[:8]}")
    db_session.add_all([alert_ver, alert_admin])
    await db_session.commit()
    
    client = await get_test_client_as(u, db_session)
    async with client:
        res = await client.get("/api/v1/alerts")
        assert len(res.json()["items"]) == 1
        assert res.json()["items"][0]["id"] == str(alert_ver.id)
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_analyst_alert_scope(db_session: AsyncSession):
    u = User(id=uuid.uuid4(), email=f"u_{uuid.uuid4().hex[:8]}@test.com", full_name="Ana", password_hash="hash", role=Role.ANALYST, is_active=True)
    db_session.add(u)
    alert_ana = Alert(id=uuid.uuid4(), alert_type=AlertType.INCIDENT_CREATED, title="Ana", message="M", recipient_scope=RecipientScope.ANALYST, dedupe_key=f"D_{uuid.uuid4().hex[:8]}")
    alert_admin = Alert(id=uuid.uuid4(), alert_type=AlertType.INCIDENT_CREATED, title="Adm", message="M", recipient_scope=RecipientScope.ADMIN, dedupe_key=f"D_{uuid.uuid4().hex[:8]}")
    db_session.add_all([alert_ana, alert_admin])
    await db_session.commit()
    
    client = await get_test_client_as(u, db_session)
    async with client:
        res = await client.get("/api/v1/alerts")
        assert len(res.json()["items"]) == 1
        assert res.json()["items"][0]["id"] == str(alert_ana.id)
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_admin_alert_scope(db_session: AsyncSession):
    u = User(id=uuid.uuid4(), email=f"u_{uuid.uuid4().hex[:8]}@test.com", full_name="Adm", password_hash="hash", role=Role.ADMIN, is_active=True)
    db_session.add(u)
    alert_admin = Alert(id=uuid.uuid4(), alert_type=AlertType.INCIDENT_CREATED, title="Adm", message="M", recipient_scope=RecipientScope.ADMIN, dedupe_key=f"D_{uuid.uuid4().hex[:8]}")
    alert_ana = Alert(id=uuid.uuid4(), alert_type=AlertType.INCIDENT_CREATED, title="Ana", message="M", recipient_scope=RecipientScope.ANALYST, dedupe_key=f"D_{uuid.uuid4().hex[:8]}")
    db_session.add_all([alert_admin, alert_ana])
    await db_session.commit()
    
    client = await get_test_client_as(u, db_session)
    async with client:
        res = await client.get("/api/v1/alerts")
        assert len(res.json()["items"]) == 1
        assert res.json()["items"][0]["id"] == str(alert_admin.id)
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_user_cannot_access_another_users_alert(db_session: AsyncSession):
    u1 = User(id=uuid.uuid4(), email=f"u1_{uuid.uuid4().hex[:8]}@test.com", full_name="U1", password_hash="hash", role=Role.CITIZEN, is_active=True)
    u2 = User(id=uuid.uuid4(), email=f"u2_{uuid.uuid4().hex[:8]}@test.com", full_name="U2", password_hash="hash", role=Role.CITIZEN, is_active=True)
    db_session.add_all([u1, u2])
    alert = Alert(id=uuid.uuid4(), alert_type=AlertType.REPORT_VERIFIED, title="Mine", message="M", recipient_scope=RecipientScope.CITIZEN_REPORTER, recipient_user_id=u2.id, dedupe_key=f"D_{uuid.uuid4().hex[:8]}")
    db_session.add(alert)
    await db_session.commit()
    
    client = await get_test_client_as(u1, db_session)
    async with client:
        res = await client.get(f"/api/v1/alerts/{alert.id}")
        assert res.status_code == 404
    app.dependency_overrides.clear()

# H. READ / ACKNOWLEDGE

@pytest.mark.asyncio
async def test_unread_count(db_session: AsyncSession):
    u = User(id=uuid.uuid4(), email=f"u_{uuid.uuid4().hex[:8]}@test.com", full_name="U2", password_hash="hash", role=Role.CITIZEN, is_active=True)
    db_session.add(u)
    a1 = Alert(id=uuid.uuid4(), alert_type=AlertType.REPORT_VERIFIED, title="A1", message="M", recipient_scope=RecipientScope.CITIZEN_REPORTER, recipient_user_id=u.id, dedupe_key=f"D_{uuid.uuid4().hex[:8]}", status=AlertStatus.UNREAD)
    a2 = Alert(id=uuid.uuid4(), alert_type=AlertType.REPORT_VERIFIED, title="A2", message="M", recipient_scope=RecipientScope.CITIZEN_REPORTER, recipient_user_id=u.id, dedupe_key=f"D_{uuid.uuid4().hex[:8]}", status=AlertStatus.READ)
    db_session.add_all([a1, a2])
    await db_session.commit()
    
    client = await get_test_client_as(u, db_session)
    async with client:
        res = await client.get("/api/v1/alerts/unread-count")
        assert res.json()["unread_count"] == 1
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_mark_read(db_session: AsyncSession):
    u = User(id=uuid.uuid4(), email=f"u_{uuid.uuid4().hex[:8]}@test.com", full_name="U3", password_hash="hash", role=Role.CITIZEN, is_active=True)
    db_session.add(u)
    alert = Alert(id=uuid.uuid4(), alert_type=AlertType.REPORT_VERIFIED, title="A", message="M", recipient_scope=RecipientScope.CITIZEN_REPORTER, recipient_user_id=u.id, dedupe_key=f"D_{uuid.uuid4().hex[:8]}", status=AlertStatus.UNREAD)
    db_session.add(alert)
    await db_session.commit()
    
    client = await get_test_client_as(u, db_session)
    async with client:
        res = await client.patch(f"/api/v1/alerts/{alert.id}/read")
        assert res.status_code == 200
        assert res.json()["status"] == "READ"
        assert res.json()["read_at"] is not None
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_acknowledge(db_session: AsyncSession):
    u = User(id=uuid.uuid4(), email=f"u_{uuid.uuid4().hex[:8]}@test.com", full_name="U4", password_hash="hash", role=Role.CITIZEN, is_active=True)
    db_session.add(u)
    alert = Alert(id=uuid.uuid4(), alert_type=AlertType.REPORT_VERIFIED, title="A", message="M", recipient_scope=RecipientScope.CITIZEN_REPORTER, recipient_user_id=u.id, dedupe_key=f"D_{uuid.uuid4().hex[:8]}", status=AlertStatus.UNREAD)
    db_session.add(alert)
    await db_session.commit()
    
    client = await get_test_client_as(u, db_session)
    async with client:
        res = await client.patch(f"/api/v1/alerts/{alert.id}/acknowledge")
        assert res.status_code == 200
        assert res.json()["status"] == "ACKNOWLEDGED"
        assert res.json()["acknowledged_at"] is not None
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_acknowledged_alert_not_counted_as_unread(db_session: AsyncSession):
    u = User(id=uuid.uuid4(), email=f"u_{uuid.uuid4().hex[:8]}@test.com", full_name="U5", password_hash="hash", role=Role.CITIZEN, is_active=True)
    db_session.add(u)
    alert = Alert(id=uuid.uuid4(), alert_type=AlertType.REPORT_VERIFIED, title="A", message="M", recipient_scope=RecipientScope.CITIZEN_REPORTER, recipient_user_id=u.id, dedupe_key=f"D_{uuid.uuid4().hex[:8]}", status=AlertStatus.ACKNOWLEDGED)
    db_session.add(alert)
    await db_session.commit()
    
    client = await get_test_client_as(u, db_session)
    async with client:
        res = await client.get("/api/v1/alerts/unread-count")
        assert res.json()["unread_count"] == 0
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_unauthorized_read_or_acknowledge_rejected(db_session: AsyncSession):
    u = User(id=uuid.uuid4(), email=f"u_{uuid.uuid4().hex[:8]}@test.com", full_name="U6", password_hash="hash", role=Role.CITIZEN, is_active=True)
    u2 = User(id=uuid.uuid4(), email=f"u2_{uuid.uuid4().hex[:8]}@test.com", full_name="U2", password_hash="hash", role=Role.CITIZEN, is_active=True)
    db_session.add_all([u, u2])
    alert = Alert(id=uuid.uuid4(), alert_type=AlertType.REPORT_VERIFIED, title="A", message="M", recipient_scope=RecipientScope.CITIZEN_REPORTER, recipient_user_id=u2.id, dedupe_key=f"D_{uuid.uuid4().hex[:8]}", status=AlertStatus.UNREAD)
    db_session.add(alert)
    await db_session.commit()
    
    client = await get_test_client_as(u, db_session)
    async with client:
        res1 = await client.patch(f"/api/v1/alerts/{alert.id}/read")
        assert res1.status_code == 404
        res2 = await client.patch(f"/api/v1/alerts/{alert.id}/acknowledge")
        assert res2.status_code == 404
    app.dependency_overrides.clear()

# I. API

@pytest.mark.asyncio
async def test_get_alerts(db_session: AsyncSession):
    u = User(id=uuid.uuid4(), email=f"u_{uuid.uuid4().hex[:8]}@test.com", full_name="U7", password_hash="hash", role=Role.CITIZEN, is_active=True)
    db_session.add(u)
    alert = Alert(id=uuid.uuid4(), alert_type=AlertType.REPORT_VERIFIED, title="A", message="M", recipient_scope=RecipientScope.CITIZEN_REPORTER, recipient_user_id=u.id, dedupe_key=f"D_{uuid.uuid4().hex[:8]}")
    db_session.add(alert)
    await db_session.commit()
    
    client = await get_test_client_as(u, db_session)
    async with client:
        res = await client.get("/api/v1/alerts")
        assert res.status_code == 200
        assert len(res.json()["items"]) == 1
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_alert_by_id(db_session: AsyncSession):
    u = User(id=uuid.uuid4(), email=f"u_{uuid.uuid4().hex[:8]}@test.com", full_name="U8", password_hash="hash", role=Role.CITIZEN, is_active=True)
    db_session.add(u)
    alert = Alert(id=uuid.uuid4(), alert_type=AlertType.REPORT_VERIFIED, title="A", message="M", recipient_scope=RecipientScope.CITIZEN_REPORTER, recipient_user_id=u.id, dedupe_key=f"D_{uuid.uuid4().hex[:8]}")
    db_session.add(alert)
    await db_session.commit()
    
    client = await get_test_client_as(u, db_session)
    async with client:
        res = await client.get(f"/api/v1/alerts/{alert.id}")
        assert res.status_code == 200
        assert res.json()["id"] == str(alert.id)
    app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_get_unread_count_api(db_session: AsyncSession):
    u = User(id=uuid.uuid4(), email=f"u_{uuid.uuid4().hex[:8]}@test.com", full_name="U9", password_hash="hash", role=Role.CITIZEN, is_active=True)
    db_session.add(u)
    alert = Alert(id=uuid.uuid4(), alert_type=AlertType.REPORT_VERIFIED, title="A", message="M", recipient_scope=RecipientScope.CITIZEN_REPORTER, recipient_user_id=u.id, dedupe_key=f"D_{uuid.uuid4().hex[:8]}", status=AlertStatus.UNREAD)
    db_session.add(alert)
    await db_session.commit()
    
    client = await get_test_client_as(u, db_session)
    async with client:
        res = await client.get("/api/v1/alerts/unread-count")
        assert res.status_code == 200
        assert res.json()["unread_count"] == 1
    app.dependency_overrides.clear()
