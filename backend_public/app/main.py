from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from starlette.middleware.sessions import SessionMiddleware
from .routers import spec_proxy as proxy_router

app = FastAPI(title="Auditor Public API", version="0.1.0")

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

@app.get("/")
def root():
    return {"name": "auditor-public", "status": "ok"}
