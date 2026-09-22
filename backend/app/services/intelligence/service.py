import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.report import Report
from app.services.intelligence.classifier import classify_text
from app.services.intelligence.schemas import ClassificationResponse

async def classify_report(session: AsyncSession, report_id: uuid.UUID) -> ClassificationResponse:
    """
    Fetch a report by ID, classify it, persist the intelligence fields, and return the result.
    """
    stmt = select(Report).where(Report.id == report_id)
    result = await session.execute(stmt)
    report = result.scalar_one_or_none()
    
    if not report:
        raise LookupError(f"Report {report_id} not found")
        
    # Run deterministic classifier
    classification = classify_text(report.title, report.description)
    
    # Update report fields without overwriting citizen `classification`
    report.classified_category = classification.classified_category.value
    report.classifier_confidence = classification.confidence
    report.classification_explanation = classification.explanation
    # JSONB field accepts a list of dicts natively via Pydantic model_dump
    report.classification_signals = [signal.model_dump() for signal in classification.signals]
    report.classified_at = datetime.now(timezone.utc)
    report.classifier_version = classification.classifier_version
    
    # We do not verify, reject, or create incident here.
    
    await session.commit()
    await session.refresh(report)
    
    return ClassificationResponse(
        report_id=str(report.id),
        **classification.model_dump()
    )
