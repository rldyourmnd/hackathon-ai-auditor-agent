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

from .factory import create_app

# Create application using the factory (centralized middleware/routers)
app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=str(settings.app_host or "0.0.0.0"),
        port=int(settings.app_port or 8080),
        reload=True,
        log_level="info",
    )
