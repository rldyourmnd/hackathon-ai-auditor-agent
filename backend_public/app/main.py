from fastapi import FastAPI
from fastapi import Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from .routers import spec_proxy as proxy_router
from .routers import proxy as internal_proxy_router
from .routers import metrics as metrics_router
from .routers import workflow as workflow_router
from .routers import auth as auth_router
from .db import engine
from sqlmodel import SQLModel
import logging
from sqlalchemy import text
from fastapi.responses import JSONResponse
from .deps import require_admin
from .observability import metrics_router as observability_router, inc_http_request
import time
import json

# Configure root logging so module loggers (e.g., routers.spec_proxy) emit to console
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

app = FastAPI(
    title="Auditor Public API",
    version="0.1.0",
    docs_url="/pub-docs",
    redoc_url=None,
    openapi_url="/public-openapi.json",
)

# CORS
origins = settings.cors_origins if settings.cors_origins else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware (required for OAuth state)
app.add_middleware(SessionMiddleware, secret_key=settings.app_secret)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Strict security headers (adjust in front proxy as needed)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        # Note: HSTS should be set only over HTTPS and usually by the proxy
        response.headers.setdefault("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        return response

app.add_middleware(SecurityHeadersMiddleware)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        log = {
            "type": "access",
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
        }
        logging.getLogger("access").info(json.dumps(log, ensure_ascii=False))
        # Increment in-process metrics for Prometheus scraping
        try:
            inc_http_request(request.method, response.status_code)
        except Exception:  # nosec - metrics must not break request flow
            logging.getLogger("metrics").exception("failed to increment http counter")
        return response

app.add_middleware(RequestLoggerMiddleware)

if settings.feature_proxy:
    app.include_router(proxy_router.router)
# Protect internal proxy with admin requirement
if settings.feature_internal_proxy:
    app.include_router(internal_proxy_router.router, dependencies=[Depends(require_admin)])
if settings.feature_metrics:
    app.include_router(metrics_router.router)
if settings.feature_workflow_api:
    app.include_router(workflow_router.router)
if settings.feature_auth:
    app.include_router(auth_router.router)
if settings.feature_metrics:
    app.include_router(observability_router)

@app.get("/")
def root():
    return {"name": "auditor-public", "status": "ok"}

# Unified error handling
@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    logging.getLogger(__name__).warning(
        "HTTP %s at %s: %s", exc.status_code, request.url.path, exc.detail
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "http_error",
                "status": exc.status_code,
                "message": exc.detail,
                "path": request.url.path,
            }
        },
    )

@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logging.getLogger(__name__).exception("Unhandled error at %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "internal_error",
                "status": 500,
                "message": "Internal Server Error",
                "path": request.url.path,
            }
        },
    )

@app.get("/healthz")
async def healthz():
    # Quick DB connectivity check (async)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        return {"status": "degraded", "message": f"db error: {e}"}
    return {"status": "healthy"}

@app.on_event("startup")
async def _on_startup():
    logging.getLogger(__name__).info(
        "public backend started: host=%s port=%s internal_api_base=%s",
        settings.app_host,
        settings.app_port,
        settings.internal_api_base,
    )
    # Ensure DB schema exists (idempotent) so metrics/workflow endpoints work out of the box
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logging.getLogger(__name__).info("database schema ensured (SQLModel, async)")
    except Exception as e:
        logging.getLogger(__name__).exception("failed to ensure database schema: %s", e)
