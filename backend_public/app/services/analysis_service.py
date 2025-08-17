from __future__ import annotations

import logging
from datetime import datetime
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..orm.models import Prompt, AnalysisResult, EventType
from ..infra.pipeline_client import PipelineClient
from ..infra.event_logger import EventLogger
from ..dto.requests import AnalyzeRequest
from ..dto.responses import AnalyzeResponse, MetricReport, Patch, ClarifyQuestion, JudgeScore, SemanticEntropy
from ..dto.common import Result

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self, session: AsyncSession, pipeline_client: PipelineClient, event_logger: EventLogger):
        self.session = session
        self.pipeline = pipeline_client
        self.events = event_logger

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
        self.session.add(prompt)
        await self.session.commit()
        await self.session.refresh(prompt)

        # 2. Log analysis started
        await self.events.log_event(
            event_type=EventType.ANALYZE_STARTED,
            prompt_id=prompt.id,
            event_data={
                "content_length": len(request.prompt.content),
                "format_type": request.prompt.format_type,
                "client_info": request.client_info.model_dump() if request.client_info else None,
            },
        )

        try:
            # 3. Call pipeline service
            pipeline_response = await self.pipeline.analyze(
                prompt=request.prompt.content,
                format_type=request.prompt.format_type,
                language=request.prompt.language,
            )

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

            self.session.add(analysis)
            await self.session.commit()
            await self.session.refresh(analysis)

            # 5. Log success
            await self.events.log_event(
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
            await self.events.log_event(
                event_type=EventType.ANALYZE_FAILED,
                prompt_id=prompt.id,
                event_data={"error": str(e), "error_type": type(e).__name__},
            )
            logger.error("Analysis failed for prompt %s: %s", prompt.id, e)
            return Result.fail(f"Analysis failed: {str(e)}", "ANALYSIS_ERROR")

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
