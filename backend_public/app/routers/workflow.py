from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from datetime import datetime
from typing import Optional
from ..db import get_db
from .. import models
from ..schemas import CreateRunIn, RunOut, NodeReportIn, MetricsReportIn, MetricPoint

router = APIRouter(prefix="/workflow", tags=["workflow"])

@router.post("/runs", response_model=RunOut)
def create_run(payload: CreateRunIn, db: Session = Depends(get_db)):
    prompt_id: Optional[int] = None
    if payload.prompt:
        prompt = models.Prompt(content=payload.prompt, language=payload.language)
        db.add(prompt)
        db.flush()
        prompt_id = prompt.id
    run = models.WorkflowRun(prompt_id=prompt_id, status="running", meta=payload.meta)
    db.add(run)
    db.commit()
    return run

@router.post("/runs/{run_id}/nodes/{node_key}")
def report_node(run_id: int, node_key: str, payload: NodeReportIn, db: Session = Depends(get_db)):
    run = db.get(models.WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    node = db.query(models.WorkflowNode).filter_by(run_id=run_id, key=node_key).one_or_none()
    now = datetime.utcnow()
    if not node:
        node = models.WorkflowNode(run_id=run_id, key=node_key, started_at=now)
        db.add(node)
        db.flush()
    if payload.status:
        node.status = payload.status
    if payload.result is not None:
        node.result = payload.result
    node.finished_at = now
    db.commit()
    return {"ok": True}

@router.post("/runs/{run_id}/metrics")
def report_metrics(run_id: int, payload: MetricsReportIn, db: Session = Depends(get_db)):
    run = db.get(models.WorkflowRun, run_id)
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
    db.commit()
    return {"ok": True, "count": len(payload.metrics)}

@router.post("/runs/{run_id}/finish")
def finish_run(run_id: int, status: str = "success", db: Session = Depends(get_db)):
    run = db.get(models.WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    run.status = status
    run.finished_at = datetime.utcnow()
    db.commit()
    return {"ok": True}
