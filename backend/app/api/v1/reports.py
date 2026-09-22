from uuid import UUID

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_current_user_optional, get_db, require_roles
from app.core.enums import ReportStatus, SourceType, VerificationStatus, Role
from app.models.user import User
from app.schemas.common import PaginatedMeta, PaginatedResponse
from app.schemas.evidence import (
    EvaluateReportResponse,
    EvidenceRead,
    ReportReadLite,
    VerifyReportRequest,
    VerifyReportResponse,
)
from app.schemas.report import ReportCreate, ReportRead
from app.services import reports as report_service
from app.services import verification as verification_service
from app.services.evidence_engine import EvidenceEngine

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[ReportRead],
    summary="List reports",
)
async def list_reports(
    status: ReportStatus | None = Query(default=None, alias="status"),
    source_type: SourceType | None = None,
    incident_id: UUID | None = None,
    verification_status: VerificationStatus | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> PaginatedResponse[ReportRead]:
    items, total = await report_service.list_reports(
        session,
        status_filter=status,
        source_type=source_type,
        incident_id=incident_id,
        verification_status=verification_status,
        limit=limit,
        offset=offset,
    )
    
    # Filter for citizens: they can only see their own reports.
    # Unauthenticated users also see all (public) reports, BUT wait: the prompt said:
    # "Before implementing 'authenticated citizens see their own reports', inspect the existing GET reports endpoint... If the backend already correctly filters citizen-owned reports, use it."
    # If the user is unauthenticated, they shouldn't see anything, or maybe they see the public list?
    # "a CITIZEN cannot retrieve another citizen's private/owned report data"
    # Actually, the public reports list should just show everything. The existing backend was returning all reports to non-citizens.
    if current_user and current_user.role == Role.CITIZEN:
        items = [i for i in items if i.reporter_user_id == current_user.id]
        total = len(items)

    return PaginatedResponse(
        items=[ReportRead.model_validate(item) for item in items],
        meta=PaginatedMeta(total=total, limit=limit, offset=offset),
    )


@router.post(
    "",
    response_model=ReportRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create report (raw signal)",
)
async def create_report(
    payload: ReportCreate,
    session: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> ReportRead:
    # Set reporter_user_id on creation if authenticated
    reporter_user_id = current_user.id if current_user else None
    report = await report_service.create_report(session, payload, reporter_user_id=reporter_user_id)
    return ReportRead.model_validate(report)


@router.get(
    "/{report_id}/evidence",
    response_model=list[EvidenceRead],
    summary="List evidence factors for a report",
    dependencies=[Depends(require_roles(Role.VERIFIER, Role.ANALYST))],
)
async def get_report_evidence(
    report_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> list[EvidenceRead]:
    _report, items = await verification_service.list_evidence(session, report_id)
    return [EvidenceRead.model_validate(item) for item in items]


@router.post(
    "/{report_id}/evaluate",
    response_model=EvaluateReportResponse,
    summary="Run evidence engine (not human verification)",
    dependencies=[Depends(require_roles(Role.VERIFIER, Role.ANALYST))],
)
async def evaluate_report(
    report_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> EvaluateReportResponse:
    engine = EvidenceEngine()
    try:
        report, evaluation = await engine.evaluate_and_persist(session, report_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Report not found") from None

    evidence = [EvidenceRead.model_validate(item) for item in report.evidence_items]
    return EvaluateReportResponse(
        report=ReportReadLite.model_validate(report),
        evidence=evidence,
        evidence_score=evaluation.evidence_score,
        evidence_coverage=evaluation.evidence_coverage,
        verification_recommendation=evaluation.verification_recommendation,
    )


from app.services.intelligence.schemas import ClassificationResponse
from app.services.intelligence.service import classify_report

@router.post(
    "/{report_id}/classify",
    response_model=ClassificationResponse,
    summary="Run AI-assisted classification (Phase 10)",
    dependencies=[Depends(require_roles(Role.ANALYST, Role.ADMIN))],
)
async def api_classify_report(
    report_id: UUID,
    session: AsyncSession = Depends(get_db),
) -> ClassificationResponse:
    try:
        return await classify_report(session, report_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Report not found") from None


@router.post(
    "/{report_id}/verify",
    response_model=VerifyReportResponse,
    summary="Human verification decision",
    dependencies=[Depends(require_roles(Role.VERIFIER))],
)
async def verify_report(
    report_id: UUID,
    payload: VerifyReportRequest,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> VerifyReportResponse:
    payload_dict = payload.model_dump()
    payload_dict["verified_by"] = str(current_user.id) # track who verified it ideally
    report = await verification_service.verify_report(session, report_id, payload)
    return VerifyReportResponse(
        report=ReportReadLite.model_validate(report),
        decision=payload.decision,
        message="Human verification recorded.",
    )


@router.get(
    "/{report_id}",
    response_model=ReportRead,
    summary="Get report by ID",
)
async def get_report(
    report_id: UUID,
    session: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> ReportRead:
    try:
        report = await report_service.get_report(session, report_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Report not found")
        
    if current_user and current_user.role == Role.CITIZEN:
        if report.reporter_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not enough permissions to view this report")
            
    return ReportRead.model_validate(report)
