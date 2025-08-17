from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

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
    ExportResponse,
)
from ..dto.common import RiskLevel
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
    service = AnalysisService(session=session, pipeline_client=pipeline)
    result = await service.analyze_prompt(req)
    if not result.success:
        raise HTTPException(status_code=502, detail=result.error or "Analysis failed")
    return result.data  # type: ignore[return-value]


@router.post("/analyze/clarify", response_model=ClarifyResponse, summary="Clarify an analysis with user answers")
async def analyze_clarify(req: ClarifyRequest, session: AsyncSession = Depends(get_async_session)):
    pipeline: PipelineClient = await get_pipeline_client()
    service = AnalysisService(session=session, pipeline_client=pipeline)
    result = await service.clarify(req)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error or "analysis not found")
        raise HTTPException(status_code=502, detail=result.error or "clarify failed")
    return result.data  # type: ignore[return-value]


@router.post("/analyze/apply", response_model=ApplyResponse, summary="Apply patches to a prompt")
async def analyze_apply(req: ApplyRequest, session: AsyncSession = Depends(get_async_session)):
    pipeline: PipelineClient = await get_pipeline_client()
    service = AnalysisService(session=session, pipeline_client=pipeline)
    result = await service.apply(req)
    if not result.success:
        if result.error_code == "NOT_FOUND":
            raise HTTPException(status_code=404, detail=result.error or "analysis not found")
        raise HTTPException(status_code=502, detail=result.error or "apply failed")
    return result.data  # type: ignore[return-value]


@router.get("/analyses/{analysis_id}", response_model=AnalyzeResponse, summary="Get analysis by ID")
async def get_analysis(analysis_id: str, session: AsyncSession = Depends(get_async_session)):
    pipeline: PipelineClient = await get_pipeline_client()
    service = AnalysisService(session=session, pipeline_client=pipeline)
    result = await service.get_analysis(analysis_id)
    if not result.success:
        raise HTTPException(status_code=404, detail=result.error or "not found")
    return result.data  # type: ignore[return-value]


@router.get("/export", response_model=ExportResponse, summary="Export full analysis payload")
async def export_analysis(analysis_id: str, session: AsyncSession = Depends(get_async_session)):
    pipeline: PipelineClient = await get_pipeline_client()
    service = AnalysisService(session=session, pipeline_client=pipeline)
    result = await service.export(analysis_id)
    if not result.success:
        raise HTTPException(status_code=404, detail=result.error or "not found")
    return result.data  # type: ignore[return-value]
