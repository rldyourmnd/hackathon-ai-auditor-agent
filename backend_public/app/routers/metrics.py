from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime
from typing import Optional, List
from ..db import get_async_session
from .. import models
from ..schemas import MetricPoint, MetricSeries, MetricAggregatePoint

router = APIRouter(prefix="/metrics", tags=["metrics"])

@router.get("/{metric_name}", response_model=MetricSeries)
async def list_metric(metric_name: str, db: AsyncSession = Depends(get_async_session), run_id: Optional[str] = None, node_key: Optional[str] = None, limit: int = Query(default=200, le=2000), since: Optional[datetime] = None, until: Optional[datetime] = None):
    stmt = select(models.EvaluationMetric).where(models.EvaluationMetric.metric_name == metric_name)
    if run_id:
        stmt = stmt.where(models.EvaluationMetric.run_id == run_id)
    if node_key:
        stmt = stmt.where(models.EvaluationMetric.node_key == node_key)
    if since:
        stmt = stmt.where(models.EvaluationMetric.created_at >= since)
    if until:
        stmt = stmt.where(models.EvaluationMetric.created_at <= until)
    stmt = stmt.order_by(models.EvaluationMetric.created_at.desc()).limit(limit)
    rows = (await db.execute(stmt)).scalars().all()
    points = [MetricPoint(run_id=r.run_id, node_key=r.node_key, metric_name=r.metric_name, metric_value=r.metric_value, metric_meta=r.metric_meta, created_at=r.created_at) for r in reversed(rows)]
    return MetricSeries(metric_name=metric_name, points=points)

@router.get("/{metric_name}/cumulative", response_model=List[MetricAggregatePoint])
async def cumulative(metric_name: str, db: AsyncSession = Depends(get_async_session)):
    stmt = select(models.EvaluationMetric.created_at, func.sum(models.EvaluationMetric.metric_value).over(order_by=models.EvaluationMetric.created_at)).where(models.EvaluationMetric.metric_name == metric_name).order_by(models.EvaluationMetric.created_at)
    res = (await db.execute(stmt)).all()
    return [MetricAggregatePoint(ts=r[0], value=float(r[1])) for r in res]

@router.get("/{metric_name}/sma", response_model=List[MetricAggregatePoint])
async def simple_moving_average(metric_name: str, window: int = Query(default=7, ge=1, le=365), db: AsyncSession = Depends(get_async_session)):
    # Compute SMA in Python to keep it DB-agnostic
    stmt = select(models.EvaluationMetric).where(models.EvaluationMetric.metric_name == metric_name).order_by(models.EvaluationMetric.created_at)
    rows = (await db.execute(stmt)).scalars().all()
    vals = [(r.created_at, float(r.metric_value)) for r in rows]
    out: list[MetricAggregatePoint] = []
    acc: list[float] = []
    for ts, v in vals:
        acc.append(v)
        if len(acc) > window:
            acc.pop(0)
        out.append(MetricAggregatePoint(ts=ts, value=sum(acc)/len(acc)))
    return out
