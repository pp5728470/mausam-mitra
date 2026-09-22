import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.models.report import Report
from app.core.enums import SourceType
from app.services.intelligence.schemas import SystemCategory
from app.services.intelligence.classifier import classify_text

pytestmark = pytest.mark.asyncio

async def test_classifier_categories():
    # 1. Heavy rainfall
    res = classify_text("Heavy rain all day", None)
    assert res.classified_category == SystemCategory.HEAVY_RAINFALL
    
    # 2. Flood/waterlogging
    res = classify_text("Road is completely flooded", None)
    assert res.classified_category == SystemCategory.FLOOD_WATERLOGGING
    
    # 3. Storm
    res = classify_text("Strong wind uprooted tree", None)
    assert res.classified_category == SystemCategory.STORM_STRONG_WINDS
    
    # 4. Lightning
    res = classify_text("House struck by lightning", None)
    assert res.classified_category == SystemCategory.LIGHTNING
    
    # 5. Extreme heat
    res = classify_text("Extreme heat wave today", None)
    assert res.classified_category == SystemCategory.EXTREME_HEAT
    
    # 6. Hailstorm
    res = classify_text("Large hail falling", None)
    assert res.classified_category == SystemCategory.HAILSTORM
    
    # 7. Landslide
    res = classify_text("Mudslide blocked the road", None)
    assert res.classified_category == SystemCategory.LANDSLIDE
    
    # 8. Dense fog
    res = classify_text("Dense fog zero visibility", None)
    assert res.classified_category == SystemCategory.DENSE_FOG
    
    # 9. Unknown/OTHER classification
    res = classify_text("Nothing to see here just a normal day", None)
    assert res.classified_category == SystemCategory.OTHER

async def test_deterministic_output():
    # 10. Deterministic output
    input_text = "Heavy rain and flooded roads"
    res1 = classify_text(input_text, None)
    res2 = classify_text(input_text, None)
    assert res1.model_dump() == res2.model_dump()

async def create_dummy_report(db: AsyncSession) -> Report:
    report = Report(
        source_type=SourceType.CITIZEN,
        source_name="Test Citizen",
        title="Heavy rain and flood",
        description="The street is completely flooded and raining heavily.",
        latitude=18.5,
        longitude=73.8,
        location=f"SRID=4326;POINT({73.8} {18.5})"
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report

async def test_api_classify_endpoint(
    client: AsyncClient, 
    db_session: AsyncSession
):
    report = await create_dummy_report(db_session)
    
    # 12. API authorization (using default mocked ADMIN token)
    response = await client.post(
        f"/api/v1/reports/{report.id}/classify"
    )
    assert response.status_code == 200
    data = response.json()
    
    assert data["classified_category"] == SystemCategory.FLOOD_WATERLOGGING.value
    assert data["confidence"] > 0
    assert len(data["signals"]) > 0
    
    # 11. Classification persistence
    await db_session.refresh(report)
    assert report.classified_category == SystemCategory.FLOOD_WATERLOGGING.value
    assert report.classifier_confidence > 0
    assert report.classification_signals is not None
    
    # 14. Classification does not verify report
    assert report.verification_status.value == "PENDING"
    
    # 15. Classification does not create incident
    assert report.incident_id is None

async def test_api_authorization_citizen(
    client: AsyncClient, 
    db_session: AsyncSession
):
    from app.main import app
    from app.api.deps import get_current_user
    from app.models.user import User
    import uuid

    # Override the mock to return a CITIZEN
    async def _override_citizen():
        return User(
            id=uuid.uuid4(),
            email="citizen@example.com",
            full_name="Citizen",
            password_hash="fake",
            role=SourceType.CITIZEN.name, # "CITIZEN"
            is_active=True
        )
    
    app.dependency_overrides[get_current_user] = _override_citizen
    
    try:
        report = await create_dummy_report(db_session)
        response = await client.post(
            f"/api/v1/reports/{report.id}/classify"
        )
        assert response.status_code == 403
    finally:
        # Revert back to the admin mock from conftest
        app.dependency_overrides.pop(get_current_user, None)

async def test_invalid_report_id(
    client: AsyncClient
):
    # 13. Invalid report ID
    response = await client.post(
        f"/api/v1/reports/{uuid4()}/classify"
    )
    assert response.status_code == 404
