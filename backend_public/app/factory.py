from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .config import settings

# Middleware
from .middleware.error_handler import error_handling_middleware  # type: ignore
from .middleware.logging import logging_middleware, request_id_middleware  # type: ignore

# Routers
from .api.health import router as health_router  # type: ignore
from .api.analysis import router as analysis_router  # type: ignore
from .api.admin import router as admin_router  # type: ignore

# Keep existing routers to avoid breaking functionality while migrating
from .routers import spec_proxy as proxy_router
from .routers import proxy as internal_proxy_router
from .routers import metrics as metrics_router
from .routers import workflow as workflow_router
from .routers import auth as auth_router
from fastapi import Depends
from .deps import require_admin
from .observability import metrics_router as observability_router
from .db import engine
from sqlmodel import SQLModel

# Import ORM models to register metadata
from .orm import models as orm_models  # noqa: F401


def create_app() -> FastAPI:
    """Application factory pattern for backend_public."""

    app = FastAPI(
        title="Auditor Public API",
        version="0.1.0",
        docs_url="/pub-docs",
        redoc_url=None,
        openapi_url="/public-openapi.json",
    )

    # Security middleware
    if settings.env.lower() == "production":
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts or ["*"])

    # CORS middleware
    origins = settings.cors_origins if settings.cors_origins else ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom middleware (order: request_id -> logging -> error handling)
    app.middleware("http")(request_id_middleware)
    app.middleware("http")(logging_middleware)
    app.middleware("http")(error_handling_middleware)

    # New routers per guidelines
    app.include_router(health_router)
    app.include_router(analysis_router, prefix="/api")
    app.include_router(admin_router)

    # Preserve existing feature-flagged routers
    if settings.feature_proxy:
        app.include_router(proxy_router.router)
    if settings.feature_internal_proxy:
        app.include_router(internal_proxy_router.router, dependencies=[Depends(require_admin)])
    if settings.feature_metrics:
        app.include_router(metrics_router.router)
        app.include_router(observability_router)
    if settings.feature_workflow_api:
        app.include_router(workflow_router.router)
    if settings.feature_auth:
        app.include_router(auth_router.router)

    @app.on_event("startup")
    async def _on_startup() -> None:
        # DB schema managed by Alembic migrations.
        # No-op startup hook retained for future initialization tasks.
        return None

    return app
