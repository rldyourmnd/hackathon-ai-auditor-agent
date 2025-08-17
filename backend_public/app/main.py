from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from starlette.middleware.sessions import SessionMiddleware
from .routers import spec_proxy as proxy_router
from .routers import metrics as metrics_router
from .routers import workflow as workflow_router
from .db import Base, engine
import logging

# Configure root logging so module loggers (e.g., routers.spec_proxy) emit to console
logging.basicConfig(
    level=logging.INFO,
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

app.include_router(proxy_router.router)
app.include_router(metrics_router.router)
app.include_router(workflow_router.router)

@app.get("/")
def root():
    return {"name": "auditor-public", "status": "ok"}

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
        Base.metadata.create_all(bind=engine)
        logging.getLogger(__name__).info("database schema ensured")
    except Exception as e:
        logging.getLogger(__name__).exception("failed to ensure database schema: %s", e)
