from __future__ import annotations

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from ..orm.models import Prompt, AnalysisResult, EventType
from ..infra.pipeline_client import PipelineClient
from ..integration.promptbase_adapter import build_analyze_payload
from ..orm.repositories import PromptRepository, AnalysisRepository, EventRepository
from ..domain.exceptions import NotFoundError, PipelineDomainError, DomainError
from ..dto.requests import AnalyzeRequest, ClarifyRequest, ApplyRequest
from ..dto.responses import (
    AnalyzeResponse,
    MetricReport,
    Patch,
    ClarifyQuestion,
    JudgeScore,
    SemanticEntropy,
    ClarifyResponse,
    ApplyResponse,
)
from ..dto.common import Result

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(
        self,
        session: AsyncSession,
        pipeline_client: PipelineClient,
        event_logger: object | None = None,
        *,
        prompt_repo: PromptRepository | None = None,
        analysis_repo: AnalysisRepository | None = None,
        event_repo: EventRepository | None = None,
    ):
        self.session = session
        self.pipeline = pipeline_client
        # Prefer injected repositories; otherwise build from session (BC with existing API code)
        self.prompt_repo = prompt_repo or PromptRepository(session)
        self.analysis_repo = analysis_repo or AnalysisRepository(session)
        self.event_repo = event_repo or EventRepository(session)

    async def analyze_prompt(self, request: AnalyzeRequest) -> Result[AnalyzeResponse]:
        start_time = datetime.utcnow()

        # 1. Create and save prompt
        prompt = Prompt(
            content=request.prompt.content,
            format_type=request.prompt.format_type,
            language=request.prompt.language,
            client_type=request.client_info.type if request.client_info else None,
            client_name=request.client_info.name if request.client_info else None,
            client_version=request.client_info.version if request.client_info else None,
            client_metadata=request.client_info.metadata if request.client_info else None,
        )
        prompt = await self.prompt_repo.add(prompt)

        # 2. Log analysis started
        await self.event_repo.log(
            event_type=EventType.ANALYZE_STARTED,
            prompt_id=prompt.id,
            event_data={
                "content_length": len(request.prompt.content),
                "format_type": request.prompt.format_type,
                "client_info": request.client_info.model_dump() if request.client_info else None,
            },
        )

        try:
            # 3. Call pipeline service with deeper prompt-base context
            enriched_payload = build_analyze_payload(request)
            pipeline_response = await self.pipeline.analyze_with_context(enriched_payload)

            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # 4. Create analysis result
            report = pipeline_response["report"]
            analysis = AnalysisResult(
                prompt_id=prompt.id,
                overall_score=report["overall_score"],
                judge_score=report["judge_score"]["score"],
                semantic_entropy=report["semantic_entropy"]["entropy"],
                complexity_score=report["complexity_score"],
                length_words=report["length_words"],
                length_chars=report["length_chars"],
                risk_level=self._calculate_risk_level(report),
                format_valid=report["format_valid"],
                judge_details=report["judge_score"],
                semantic_details=report["semantic_entropy"],
                contradictions=report.get("contradictions", []),
                patches=pipeline_response.get("patches", []),
                questions=pipeline_response.get("questions", []),
                processing_time_ms=int(processing_time),
                pipeline_version=pipeline_response.get("version", "1.0.0"),
                pipeline_metadata=pipeline_response.get("metadata", {}),
            )

            # Update prompt with detection results
            prompt.detected_language = report.get("detected_language")
            prompt.translated = report.get("translated", False)

            analysis = await self.analysis_repo.add(analysis)

            # 5. Log success
            await self.event_repo.log(
                event_type=EventType.ANALYZE_COMPLETED,
                analysis_id=analysis.id,
                prompt_id=prompt.id,
                event_data={
                    "overall_score": analysis.overall_score,
                    "risk_level": analysis.risk_level,
                    "patches_count": len(analysis.patches or []),
                    "questions_count": len(analysis.questions or []),
                },
                duration_ms=int(processing_time),
            )

            # 6. Build response
            response = AnalyzeResponse(
                analysis_id=analysis.id,
                prompt_id=prompt.id,
                report=self._build_metric_report(report, prompt.detected_language, prompt.translated),
                patches=[Patch(**p) for p in (pipeline_response.get("patches") or [])],
                questions=[ClarifyQuestion(**q) for q in (pipeline_response.get("questions") or [])],
                created_at=analysis.created_at,
                processing_time_ms=analysis.processing_time_ms,
                pipeline_version=analysis.pipeline_version,
            )

            logger.info("Analysis completed successfully: %s", analysis.id)
            return Result.ok(response)
        except Exception as e:
            # Log failure
            await self.event_repo.log(
                event_type=EventType.ANALYZE_FAILED,
                prompt_id=prompt.id,
                event_data={"error": str(e), "error_type": type(e).__name__},
            )
            logger.error("Analysis failed for prompt %s: %s", prompt.id, e)
            return Result.fail(f"Analysis failed: {str(e)}", "ANALYSIS_ERROR")

    async def clarify(self, request: ClarifyRequest) -> Result[ClarifyResponse]:
        # Load existing analysis
        analysis = await self.analysis_repo.get(request.analysis_id)
        if not analysis:
            return Result.fail("analysis not found", "NOT_FOUND")

        payload_answers = [{"id": a.question_id, "answer": a.answer} for a in request.answers]
        start = datetime.utcnow()
        await self.event_repo.log(
            EventType.CLARIFY_REQUESTED,
            analysis_id=request.analysis_id,
            prompt_id=analysis.prompt_id,
            event_data={"answers": payload_answers},
        )

        try:
            result = await self.pipeline.clarify(analysis_id=request.analysis_id, answers=payload_answers)
        except Exception as e:
            await self.event_repo.log(
                EventType.ANALYZE_FAILED,
                analysis_id=request.analysis_id,
                prompt_id=analysis.prompt_id,
                event_data={"error": str(e)},
            )
            return Result.fail(f"Clarify failed: {str(e)}", "CLARIFY_ERROR")

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
        if result.get("new_patches"):
            existing = analysis.patches or []
            analysis.patches = existing + result["new_patches"]
        analysis.updated_at = datetime.utcnow()
        await self.analysis_repo.update(analysis)

        processing_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
        await self.event_repo.log(
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

        return Result.ok(
            ClarifyResponse(
                analysis_id=analysis.id,
                updated_report=updated_report,
                new_patches=[Patch(**p) for p in result.get("new_patches", [])],
                score_delta=score_delta,
                processing_time_ms=processing_ms,
            )
        )

    async def apply(self, request: ApplyRequest) -> Result[ApplyResponse]:
        analysis = await self.analysis_repo.get(request.analysis_id)
        if not analysis:
            return Result.fail("analysis not found", "NOT_FOUND")

        prompt = await self.prompt_repo.get(analysis.prompt_id)

        start = datetime.utcnow()
        try:
            apply_res = await self.pipeline.apply_patches(analysis_id=request.analysis_id, patch_ids=request.patch_ids)
        except Exception as e:
            await self.event_repo.log(
                EventType.ANALYZE_FAILED,
                analysis_id=request.analysis_id,
                prompt_id=analysis.prompt_id,
                event_data={"error": str(e)},
            )
            return Result.fail(f"Apply failed: {str(e)}", "APPLY_ERROR")

        improved = apply_res.get("improved_prompt", prompt.content)
        applied = apply_res.get("applied_patches", request.patch_ids)
        failed = apply_res.get("failed_patches", [])
        improvement_summary = apply_res.get("improvement_summary", "Applied patches")
        quality_gain = float(apply_res.get("quality_gain", 0.0))

        analysis.applied_patches = applied
        analysis.updated_at = datetime.utcnow()
        await self.analysis_repo.update(analysis)

        duration_ms = int((datetime.utcnow() - start).total_seconds() * 1000)
        await self.event_repo.log(
            EventType.PATCHES_APPLIED,
            analysis_id=analysis.id,
            prompt_id=analysis.prompt_id,
            duration_ms=duration_ms,
            event_data={"applied": applied, "failed": failed, "quality_gain": quality_gain},
        )

        return Result.ok(
            ApplyResponse(
                analysis_id=analysis.id,
                original_prompt=prompt.content,
                improved_prompt=improved,
                applied_patches=applied,
                failed_patches=failed,
                improvement_summary=improvement_summary,
                quality_gain=quality_gain,
            )
        )

    async def get_analysis(self, analysis_id: str) -> Result[AnalyzeResponse]:
        analysis = await self.analysis_repo.get(analysis_id)
        if not analysis:
            return Result.fail(f"Analysis {analysis_id} not found", "NOT_FOUND")

        prompt = await self.prompt_repo.get(analysis.prompt_id)
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

        return Result.ok(
            AnalyzeResponse(
                analysis_id=analysis.id,
                prompt_id=analysis.prompt_id,
                report=report,
                patches=[Patch(**p) for p in (analysis.patches or [])],
                questions=[ClarifyQuestion(**q) for q in (analysis.questions or [])],
                created_at=analysis.created_at,
                processing_time_ms=analysis.processing_time_ms,
                pipeline_version=analysis.pipeline_version,
            )
        )

    async def export(self, analysis_id: str) -> Result[Dict[str, Any]]:
        analysis = await self.analysis_repo.get(analysis_id)
        if not analysis:
            return Result.fail(f"Analysis {analysis_id} not found", "NOT_FOUND")

        prompt = await self.prompt_repo.get(analysis.prompt_id)
        await self.event_repo.log(
            EventType.EXPORT_REQUESTED,
            analysis_id=analysis.id,
            prompt_id=analysis.prompt_id,
        )

        payload = {
            "analysis_id": analysis.id,
            "prompt": {
                "id": prompt.id,
                "content": prompt.content,
                "format_type": prompt.format_type,
                "language": prompt.language,
                "detected_language": getattr(prompt, "detected_language", None),
                "translated": getattr(prompt, "translated", False),
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
        return Result.ok(payload)

    def _calculate_risk_level(self, report: dict) -> str:
        score = report["overall_score"]
        contradictions = len(report.get("contradictions", []))
        if score < 3 or contradictions > 5:
            return "critical"
        elif score < 5 or contradictions > 2:
            return "high"
        elif score < 7 or contradictions > 0:
            return "medium"
        else:
            return "low"

    def _build_metric_report(
        self, report_data: dict, detected_language: str | None, translated: bool | None
    ) -> MetricReport:
        return MetricReport(
            overall_score=report_data["overall_score"],
            judge_score=JudgeScore(**report_data["judge_score"]),
            semantic_entropy=SemanticEntropy(**report_data["semantic_entropy"]),
            complexity_score=report_data["complexity_score"],
            length_words=report_data["length_words"],
            length_chars=report_data["length_chars"],
            risk_level=self._calculate_risk_level(report_data),
            contradictions=report_data.get("contradictions", []),
            format_valid=report_data["format_valid"],
            detected_language=detected_language or report_data.get("detected_language", "auto"),
            translated=translated if translated is not None else report_data.get("translated", False),
        )
