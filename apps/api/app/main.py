from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.env_validation import validate_environment
from app.core.logging_config import configure_logging
from app.db.session import AsyncSessionLocal
from app.schemas.common import HealthResponse
from app.services.ai import AIService

logger = logging.getLogger(__name__)
APP_VERSION = "0.1.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    validate_environment()
    logger.info("Starting %s API in %s mode", settings.app_name, settings.app_env)
    yield
    logger.info("Stopping %s API", settings.app_name)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        description="AI-powered study abroad platform API",
        version=APP_VERSION,
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None if settings.is_production else "/redoc",
        openapi_url=None if settings.is_production else "/openapi.json",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail, "error": {"code": "http_error", "message": exc.detail}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": exc.errors(),
                "error": {"code": "validation_error", "message": "Invalid request", "details": exc.errors()},
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled API error on %s %s", request.method, request.url.path)
        message = "Internal server error" if settings.is_production else str(exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": message, "error": {"code": "internal_error", "message": message}},
        )

    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check() -> HealthResponse:
        return HealthResponse(status="healthy", app=settings.app_name, version=APP_VERSION)

    @app.get("/health/live", tags=["Health"])
    async def liveness_check() -> dict:
        return {"status": "alive", "app": settings.app_name, "version": APP_VERSION}

    @app.get("/health/ready", tags=["Health"])
    async def readiness_check() -> dict:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "ready", "database": "ok", "app": settings.app_name, "version": APP_VERSION}

    @app.get("/version", tags=["Health"])
    async def version_check() -> dict:
        return {"app": settings.app_name, "version": APP_VERSION, "environment": settings.app_env}

    @app.get("/status", tags=["Health"])
    async def status_check() -> dict:
        return {"status": "ok", "app": settings.app_name, "version": APP_VERSION}

    @app.get("/health/ai", tags=["Health"])
    async def ai_health_check():
        ai_service = AIService()
        return await ai_service.health_check()

    return app


app = create_app()
