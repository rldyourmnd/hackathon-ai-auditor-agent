from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional
from ..db import get_async_session
from .. import models
from ..schemas import CreateRunIn, RunOut, NodeReportIn, MetricsReportIn

router = APIRouter(prefix="/workflow", tags=["workflow"])

@router.post("/runs", response_model=RunOut)
async def create_run(payload: CreateRunIn, db: AsyncSession = Depends(get_async_session)):
    # Prompt entities live in main backend; public service does not persist prompts
    run = models.WorkflowRun(status="running", meta=payload.meta, prompt_id=payload.prompt_id)
    db.add(run)
    await db.commit()
    return run

@router.post("/runs/{run_id}/nodes/{node_key}")
async def report_node(run_id: str, node_key: str, payload: NodeReportIn, db: AsyncSession = Depends(get_async_session)):
    run = await db.get(models.WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    result = await db.execute(
        select(models.WorkflowNode).where(models.WorkflowNode.run_id == run_id, models.WorkflowNode.key == node_key)
    )
    node = result.scalar_one_or_none()
    now = datetime.utcnow()
    if not node:
        node = models.WorkflowNode(run_id=run_id, key=node_key, started_at=now)
        db.add(node)
        await db.flush()
    if payload.status:
        node.status = payload.status
    if payload.result is not None:
        node.result = payload.result
    node.finished_at = now
    await db.commit()
    return {"ok": True}

@router.post("/runs/{run_id}/metrics")
async def report_metrics(run_id: str, payload: MetricsReportIn, db: AsyncSession = Depends(get_async_session)):
    run = await db.get(models.WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    for m in payload.metrics:
        row = models.EvaluationMetric(
            run_id=run_id,
            node_key=m.node_key,
            metric_name=m.metric_name,
            metric_value=m.metric_value,
            metric_meta=m.metric_meta,
            created_at=m.created_at or datetime.utcnow(),
        )
        db.add(row)
    await db.commit()
    return {"ok": True, "count": len(payload.metrics)}

@router.post("/runs/{run_id}/finish")
async def finish_run(run_id: str, status: str = "success", db: AsyncSession = Depends(get_async_session)):
    run = await db.get(models.WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    run.status = status
    run.finished_at = datetime.utcnow()
    await db.commit()
    return {"ok": True}
