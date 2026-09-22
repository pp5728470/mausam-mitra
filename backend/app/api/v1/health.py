from fastapi import APIRouter

from app.schemas.common import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service health",
    description="Liveness probe for the Mausam Mitra API. Does not expose infrastructure details.",
)
async def health() -> HealthResponse:
    return HealthResponse(status="ok", service="mausam-mitra-api")
