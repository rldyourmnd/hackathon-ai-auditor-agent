from __future__ import annotations

from datetime import datetime, timedelta
from typing import List, Optional
import hashlib
import os

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_async_session
from ..deps import require_admin
from ..dto.responses import (
    AdminAnalysisItem,
    AdminAnalysisListResponse,
    TimeSeriesPoint,
    TimeSeriesResponse,
    ModelStats,
    ModelsResponse,
    ApiKeyInfo,
    ApiKeyCreateResponse,
)
from ..orm.models import AnalysisResult
from ..models import ApiKey

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


# Request DTOs
class CreateApiKeyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    scopes: List[str] = Field(default_factory=list)
    user_id: Optional[str] = None


@router.get("/analyses", response_model=AdminAnalysisListResponse)
async def list_analyses(
    session: AsyncSession = Depends(get_async_session),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    risk: Optional[str] = Query(None, description="Filter by risk level"),
):
    stmt = select(AnalysisResult)
    count_stmt = select(func.count(AnalysisResult.id))
    if risk:
        stmt = stmt.where(AnalysisResult.risk_level == risk)
        count_stmt = count_stmt.where(AnalysisResult.risk_level == risk)

    stmt = stmt.order_by(AnalysisResult.created_at.desc()).offset(offset).limit(limit)

    rows = (await session.execute(stmt)).scalars().all()
    total = (await session.execute(count_stmt)).scalar_one()

    items = [
        AdminAnalysisItem(
            id=r.id,
            prompt_id=r.prompt_id,
            overall_score=r.overall_score,
            risk_level=r.risk_level,
            created_at=r.created_at,
            processing_time_ms=r.processing_time_ms,
        )
        for r in rows
    ]

    return AdminAnalysisListResponse(total=total, items=items)


@router.get("/timeseries", response_model=TimeSeriesResponse)
async def timeseries(
    session: AsyncSession = Depends(get_async_session),
    window: str = Query("day", pattern="^(hour|day|week)$"),
    points: int = Query(14, ge=1, le=365),
):
    # Postgres date_trunc grouping
    if window == "hour":
        trunc = "hour"
    elif window == "week":
        trunc = "week"
    else:
        trunc = "day"

    sql = text(
        f"""
        SELECT date_trunc(:trunc, created_at) AS ts,
               COUNT(*)::int AS count,
               AVG(overall_score)::float AS avg_score
        FROM analysis_results
        GROUP BY 1
        ORDER BY 1 DESC
        LIMIT :points
        """
    )
    res = await session.execute(sql, {"trunc": trunc, "points": points})
    rows = res.fetchall()

    pts = [
        TimeSeriesPoint(timestamp=row[0], count=row[1], avg_score=row[2])
        for row in reversed(rows)
    ]

    return TimeSeriesResponse(window=window, points=pts)


@router.get("/models", response_model=ModelsResponse)
async def models_stats(session: AsyncSession = Depends(get_async_session)):
    # Try to infer model from pipeline_metadata->>'model' if present
    sql = text(
        """
        SELECT COALESCE(pipeline_metadata->>'model', pipeline_version) AS model,
               COUNT(*)::int AS invocations,
               AVG(processing_time_ms)::float AS avg_latency_ms,
               MAX(created_at) AS last_used_at
        FROM analysis_results
        GROUP BY 1
        ORDER BY invocations DESC
        """
    )
    res = await session.execute(sql)
    models = [
        ModelStats(
            name=row[0] or "unknown",
            invocations=row[1],
            avg_latency_ms=row[2],
            last_used_at=row[3],
        )
        for row in res.fetchall()
    ]
    return ModelsResponse(models=models)


def _generate_api_key_token(prefix_len: int = 6) -> tuple[str, str, str]:
    raw = os.urandom(24).hex()
    prefix = f"ak_{raw[:prefix_len]}"
    token = f"{prefix}.{os.urandom(16).hex()}-{os.urandom(16).hex()}"
    masked = prefix + "..." + token[-4:]
    return token, prefix, masked


@router.get("/api-keys", response_model=List[ApiKeyInfo])
async def list_api_keys(session: AsyncSession = Depends(get_async_session)):
    rows = (await session.execute(select(ApiKey).order_by(ApiKey.created_at.desc()))).scalars().all()
    return [
        ApiKeyInfo(
            id=k.id,
            name=k.name,
            prefix=k.prefix,
            masked=k.prefix + "...",
            active=k.active,
            created_at=k.created_at,
            last_used_at=k.last_used_at,
            scopes=list(k.scopes or []),
        )
        for k in rows
    ]


@router.post("/api-keys", response_model=ApiKeyCreateResponse)
async def create_api_key(req: CreateApiKeyRequest, session: AsyncSession = Depends(get_async_session)):
    token, prefix, masked = _generate_api_key_token()
    hashed = hashlib.sha256(token.encode("utf-8")).hexdigest()

    key = ApiKey(
        name=req.name,
        prefix=prefix,
        hashed_token=hashed,
        scopes={"scopes": req.scopes},
        user_id=req.user_id,
    )
    session.add(key)
    await session.commit()
    await session.refresh(key)

    return ApiKeyCreateResponse(
        id=key.id,
        name=key.name,
        token=token,
        prefix=prefix,
        masked=masked,
        created_at=key.created_at,
        scopes=req.scopes,
    )


@router.delete("/api-keys/{key_id}")
async def delete_api_key(key_id: str, session: AsyncSession = Depends(get_async_session)):
    key = await session.get(ApiKey, key_id)
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    await session.delete(key)
    await session.commit()
    return {"deleted": True}
