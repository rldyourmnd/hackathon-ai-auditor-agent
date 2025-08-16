import json
import logging
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import analysis, prompt_base
from app.core.config import settings
from app.core.database import db_manager, init_db
from app.schemas.prompts import HealthResponse
from app.services.llm import get_llm_service


# Configure structured JSON logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "__dict__"):
            for key, value in record.__dict__.items():
                if key not in ["name", "msg", "args", "levelname", "levelno", "pathname",
                              "filename", "module", "lineno", "funcName", "created",
                              "msecs", "relativeCreated", "thread", "threadName",
                              "processName", "process", "getMessage"]:
                    log_entry[key] = value

        return json.dumps(log_entry)

# Setup logging
logger = logging.getLogger()
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.handlers = [handler]
logger.setLevel(getattr(logging, settings.log_level))

app_logger = logging.getLogger(__name__)

app = FastAPI(
    title="Curestry API",
    description="AI Prompt Analysis & Optimization Platform",
    version="0.1.0",
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analysis.router)
app.include_router(prompt_base.router)


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    # Initialize database
    try:
        await init_db()
        app_logger.info("Database initialized successfully")
    except Exception as e:
        app_logger.error(f"Database initialization failed: {e}")
        # Don't fail startup - allow API to run without DB for demo

    app_logger.info(
        "Curestry API starting up",
        extra={
            "version": "0.1.0",
            "environment": settings.env,
            "log_level": settings.log_level,
            "openai_configured": bool(settings.openai_api_key),
        }
    )


@app.get("/healthz", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with OpenAI and database connectivity verification."""
    openai_configured = bool(settings.openai_api_key)

    # Quick OpenAI connectivity test in development
    openai_working = openai_configured
    if settings.is_development and openai_configured:
        try:
            # Simple test call to verify OpenAI connectivity
            llm = get_llm_service()
            test_response = await llm.ask("cheap", "Test", max_tokens=5)
            openai_working = bool(test_response)
        except Exception as e:
            app_logger.warning(f"OpenAI connectivity test failed: {e}")
            openai_working = False

    # Check database connectivity
    db_health = await db_manager.health_check()

    app_logger.info(
        "Health check performed",
        extra={
            "openai_configured": openai_configured,
            "openai_working": openai_working,
            "database_connected": db_health["connected"],
        }
    )

    return HealthResponse(
        status="healthy",
        message="Curestry API is running",
        version="0.1.0",
        environment=settings.env,
        openai_configured=openai_working
    )


@app.get("/")
async def root():
    """Root endpoint with basic API information."""
    return {
        "message": "Welcome to Curestry API",
        "version": "0.1.0",
        "docs": "/docs" if settings.is_development else "Documentation disabled in production",
        "health": "/healthz"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
