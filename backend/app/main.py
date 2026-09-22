import asyncio
import sys
from contextlib import asynccontextmanager

# psycopg async requires SelectorEventLoop on Windows (not ProactorEventLoop).
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.core.config import get_settings


@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title="Mausam Mitra API",
        description=(
            "National Weather Intelligence backend foundation. "
            "Current seed records are SIMULATED DEMO intelligence — not live weather."
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        _request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        detail = exc.detail
        if not isinstance(detail, str):
            detail = str(detail)
        return JSONResponse(status_code=exc.status_code, content={"detail": detail})

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        # jsonable_encoder handles non-JSON ctx values (e.g. ValueError in Pydantic errors).
        return JSONResponse(
            status_code=422,
            content={"detail": jsonable_encoder(exc.errors())},
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(
        _request: Request, _exc: Exception
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    application.include_router(api_router)
    return application


app = create_app()
