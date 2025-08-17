from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..db import get_async_session
from ..infra.pipeline_client import PipelineClient, get_pipeline_client
from ..dto.responses import HealthResponse
from datetime import datetime
from sqlalchemy import text

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthResponse)
async def health_check(
    session: AsyncSession = Depends(get_async_session),
    pipeline: PipelineClient = Depends(get_pipeline_client),
):
    health_data = {
        "service": "backend_public",
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "checks": {},
    }

    # Database check
    try:
        await session.execute(text("SELECT 1"))
        health_data["checks"]["database"] = "healthy"
    except Exception as e:
        health_data["checks"]["database"] = f"unhealthy: {str(e)}"
        health_data["status"] = "degraded"

    # Pipeline service check
    try:
        pipeline_health = await pipeline.health_check()
        health_data["checks"]["pipeline"] = "healthy" if pipeline_health else "unhealthy"
        if not pipeline_health:
            health_data["status"] = "degraded"
    except Exception as e:
        health_data["checks"]["pipeline"] = f"unhealthy: {str(e)}"
        health_data["status"] = "degraded"

    return HealthResponse(**health_data)


@router.get("/")
async def root():
    return {
        "service": "Curestry API Proxy",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/healthz",
        "endpoints": {"analyze": "/api/analyze", "admin": "/admin/analyses"},
    }
