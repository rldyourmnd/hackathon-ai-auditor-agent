from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime

from ..db import get_async_session
from ..dto.requests import AnalyzeRequest, ClarifyRequest, ApplyRequest
from ..dto.responses import (
    AnalyzeResponse,
    ClarifyResponse,
    ApplyResponse,
    MetricReport,
    JudgeScore,
    SemanticEntropy,
    Patch,
    ClarifyQuestion,
)
from ..dto.common import RiskLevel
from ..orm.models import Prompt, AnalysisResult, EventType
from ..infra.event_logger import EventLogger
from ..infra.pipeline_client import get_pipeline_client, PipelineClient
from ..services.analysis_service import AnalysisService

router = APIRouter(tags=["analysis"])


def _placeholder_report() -> MetricReport:
    return MetricReport(
        overall_score=7.5,
        judge_score=JudgeScore(score=7.5, rationale="Initial heuristic", criteria_scores={}, confidence=0.7),
        semantic_entropy=SemanticEntropy(entropy=0.3, spread=0.2, clusters=2, samples=[]),
        complexity_score=5.0,
        length_words=0,
        length_chars=0,
        risk_level=RiskLevel.MEDIUM,
        contradictions=[],
        format_valid=True,
        detected_language="auto",
        translated=False,
    )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest, session: AsyncSession = Depends(get_async_session)):
    pipeline: PipelineClient = await get_pipeline_client()
    events = EventLogger(session)
    service = AnalysisService(session=session, pipeline_client=pipeline, event_logger=events)
    result = await service.analyze_prompt(req)
    if not result.success:
        raise HTTPException(status_code=502, detail=result.error or "Analysis failed")
    return result.data  # type: ignore[return-value]


@router.post("/analyze/clarify", response_model=ClarifyResponse)
async def analyze_clarify(req: ClarifyRequest, session: AsyncSession = Depends(get_async_session)):
    # Load analysis
    res = await session.execute(select(AnalysisResult).where(AnalysisResult.id == req.analysis_id))
    analysis = res.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="analysis not found")
    # Call pipeline clarify
    pipeline: PipelineClient = await get_pipeline_client()
    events = EventLogger(session)
    payload_answers = [{"id": a.question_id, "answer": a.answer} for a in req.answers]
    start = datetime.utcnow()
    # Log clarify requested
    await events.log_event(
        EventType.CLARIFY_REQUESTED,
        analysis_id=req.analysis_id,
        prompt_id=analysis.prompt_id,
        event_data={"answers": payload_answers},
    )
    result = await pipeline.clarify(analysis_id=req.analysis_id, answers=payload_answers)

    # Update analysis scores from response
    report = result.get("report", {})
    new_overall = report.get("overall_score", analysis.overall_score)
    score_delta = float(new_overall) - float(analysis.overall_score)
    analysis.overall_score = new_overall
    if "judge_score" in report:
        analysis.judge_score = report["judge_score"].get("score", analysis.judge_score)
        analysis.judge_details = report["judge_score"]
    if "semantic_entropy" in report:
        analysis.semantic_entropy = report["semantic_entropy"].get("entropy", analysis.semantic_entropy)
        analysis.semantic_details = report["semantic_entropy"]
    analysis.complexity_score = report.get("complexity_score", analysis.complexity_score)
    analysis.length_words = report.get("length_words", analysis.length_words)
    analysis.length_chars = report.get("length_chars", analysis.length_chars)
    analysis.risk_level = report.get("risk_level", analysis.risk_level)
    analysis.contradictions = report.get("contradictions", analysis.contradictions)
    # append new patches if provided
    if result.get("new_patches"):
        existing = analysis.patches or []
        analysis.patches = existing + result["new_patches"]
    analysis.updated_at = datetime.utcnow()
    await session.commit()

    # Log clarify completed
    processing_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
    await events.log_event(
        EventType.CLARIFY_COMPLETED,
        analysis_id=analysis.id,
        prompt_id=analysis.prompt_id,
        duration_ms=processing_ms,
        event_data={"score_delta": score_delta},
    )

    updated_report = MetricReport(
        overall_score=analysis.overall_score,
        judge_score=JudgeScore(**analysis.judge_details),
        semantic_entropy=SemanticEntropy(**analysis.semantic_details),
        complexity_score=analysis.complexity_score,
        length_words=analysis.length_words,
        length_chars=analysis.length_chars,
        risk_level=analysis.risk_level,
        contradictions=analysis.contradictions,
        format_valid=report.get("format_valid", True),
        detected_language=result.get("detected_language", "auto"),
        translated=result.get("translated", False),
    )

    return ClarifyResponse(
        analysis_id=analysis.id,
        updated_report=updated_report,
        new_patches=[Patch(**p) for p in result.get("new_patches", [])],
        score_delta=score_delta,
        processing_time_ms=processing_ms,
    )


@router.post("/analyze/apply", response_model=ApplyResponse)
async def analyze_apply(req: ApplyRequest, session: AsyncSession = Depends(get_async_session)):
    res = await session.execute(select(AnalysisResult).where(AnalysisResult.id == req.analysis_id))
    analysis = res.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="analysis not found")
    # Load prompt
    res_p = await session.execute(select(Prompt).where(Prompt.id == analysis.prompt_id))
    prompt = res_p.scalar_one()

    # Call pipeline apply
    pipeline: PipelineClient = await get_pipeline_client()
    events = EventLogger(session)
    start = datetime.utcnow()
    apply_res = await pipeline.apply_patches(analysis_id=req.analysis_id, patch_ids=req.patch_ids)

    improved = apply_res.get("improved_prompt", prompt.content)
    applied = apply_res.get("applied_patches", req.patch_ids)
    failed = apply_res.get("failed_patches", [])
    improvement_summary = apply_res.get("improvement_summary", "Applied patches")
    quality_gain = float(apply_res.get("quality_gain", 0.0))

    # Persist applied patches summary on analysis (optional metadata)
    analysis.applied_patches = applied
    analysis.updated_at = datetime.utcnow()
    await session.commit()

    # Log patches applied
    duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
    await events.log_event(
        EventType.PATCHES_APPLIED,
        analysis_id=analysis.id,
        prompt_id=analysis.prompt_id,
        duration_ms=duration_ms,
        event_data={
            "applied": applied,
            "failed": failed,
            "quality_gain": quality_gain,
        },
    )

    return ApplyResponse(
        analysis_id=analysis.id,
        original_prompt=prompt.content,
        improved_prompt=improved,
        applied_patches=applied,
        failed_patches=failed,
        improvement_summary=improvement_summary,
        quality_gain=quality_gain,
    )


@router.get("/analyses/{analysis_id}", response_model=AnalyzeResponse)
async def get_analysis(analysis_id: str, session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(
        select(AnalysisResult).options(selectinload(AnalysisResult.prompt)).where(AnalysisResult.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

    prompt = analysis.prompt  # via relationship
    report = MetricReport(
        overall_score=analysis.overall_score,
        judge_score=JudgeScore(**analysis.judge_details),
        semantic_entropy=SemanticEntropy(**analysis.semantic_details),
        complexity_score=analysis.complexity_score,
        length_words=analysis.length_words,
        length_chars=analysis.length_chars,
        risk_level=analysis.risk_level,
        contradictions=analysis.contradictions,
        format_valid=analysis.format_valid,
        detected_language=getattr(prompt, "detected_language", "auto"),
        translated=getattr(prompt, "translated", False),
    )

    return AnalyzeResponse(
        analysis_id=analysis.id,
        prompt_id=analysis.prompt_id,
        report=report,
        patches=[Patch(**p) for p in (analysis.patches or [])],
        questions=[ClarifyQuestion(**q) for q in (analysis.questions or [])],
        created_at=analysis.created_at,
        processing_time_ms=analysis.processing_time_ms,
        pipeline_version=analysis.pipeline_version,
    )


@router.get("/export")
async def export_analysis(analysis_id: str, session: AsyncSession = Depends(get_async_session)):
    """Export full analysis (prompt, report, patches, questions) as JSON."""
    result = await session.execute(
        select(AnalysisResult).options(selectinload(AnalysisResult.prompt)).where(AnalysisResult.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")

    events = EventLogger(session)
    await events.log_event(
        EventType.EXPORT_REQUESTED,
        analysis_id=analysis.id,
        prompt_id=analysis.prompt_id,
    )

    prompt = analysis.prompt
    export_payload = {
        "analysis_id": analysis.id,
        "prompt": {
            "id": prompt.id,
            "content": prompt.content,
            "format_type": prompt.format_type,
            "language": prompt.language,
            "detected_language": prompt.detected_language,
            "translated": prompt.translated,
        },
        "report": {
            "overall_score": analysis.overall_score,
            "judge_score": analysis.judge_details,
            "semantic_entropy": analysis.semantic_details,
            "complexity_score": analysis.complexity_score,
            "length_words": analysis.length_words,
            "length_chars": analysis.length_chars,
            "risk_level": analysis.risk_level,
            "contradictions": analysis.contradictions,
            "format_valid": analysis.format_valid,
        },
        "patches": analysis.patches or [],
        "questions": analysis.questions or [],
        "created_at": analysis.created_at.isoformat(),
        "processing_time_ms": analysis.processing_time_ms,
        "pipeline_version": analysis.pipeline_version,
    }

    return export_payload
