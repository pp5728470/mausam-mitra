from fastapi import APIRouter

from app.api.v1 import health, incidents, reports, weather, auth, analytics, alerts

api_router = APIRouter()

api_router.include_router(health.router, prefix="/api/v1", tags=["health"])
api_router.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
api_router.include_router(reports.router, prefix="/api/v1/reports", tags=["reports"])
api_router.include_router(
    incidents.router, prefix="/api/v1/incidents", tags=["incidents"]
)
api_router.include_router(
    weather.router, prefix="/api/v1/weather", tags=["weather"]
)
api_router.include_router(
    analytics.router, prefix="/api/v1/analytics", tags=["analytics"]
)
api_router.include_router(
    alerts.router, prefix="/api/v1/alerts", tags=["alerts"]
)
