import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.pipeline.graph import get_analysis_pipeline
from app.schemas.prompts import (
    AnalyzeRequest,
    AnalyzeResponse,
    ApplyPatchesRequest,
    ClarifyQuestion,
    ClarifyRequest,
    Contradiction,
    MetricReport,
    MetricScore,
    Patch,
    PromptImproved,
    SemanticEntropy,
)
from app.services.llm import get_llm_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analyze", tags=["analysis"])

# In-memory storage for demo (replace with database in production)
analysis_cache: Dict[str, Any] = {}


@router.post("/", response_model=AnalyzeResponse)
async def analyze_prompt(request: AnalyzeRequest):
    """
    Analyze a prompt for quality, consistency, and potential improvements.

    This endpoint performs comprehensive prompt analysis including:
    - Language detection and translation
    - Format validation and markup fixing
    - Vocabulary unification
    - Contradiction detection
    - Semantic entropy analysis
    - LLM-as-judge scoring
    - Improvement patch generation
    - Clarification questions
    """
    try:
        prompt_id = str(uuid.uuid4())
        prompt_content = request.prompt.content

        logger.info(f"Starting analysis for prompt {prompt_id}")

        # Run the comprehensive analysis pipeline
        pipeline = get_analysis_pipeline()
        pipeline_state = await pipeline.analyze(
            prompt_content=prompt_content,
            format_type=request.prompt.format_type or "text"
        )

        # Convert pipeline state to API response format
        report = pipeline_state.to_metric_report()
        report.prompt_id = prompt_id
        report.original_prompt = prompt_content
        report.analyzed_at = datetime.utcnow()

        # Convert patches to API format
        api_patches = []
        for patch in pipeline_state.patches:
            api_patches.append(Patch(
                id=patch.id,
                type="safe" if patch.risk_level == "safe" else "risky",
                category=patch.type,
                description=patch.description,
                original=patch.current_text,
                improved=patch.suggested_text,
                rationale=patch.reasoning,
                confidence=0.8  # Default confidence
            ))

        # Convert questions to API format
        api_questions = []
        for question in pipeline_state.clarify_questions:
            api_questions.append(ClarifyQuestion(
                id=question.id,
                question=question.question,
                category=question.category,
                importance=question.priority
            ))

        # Create semantic entropy object
        semantic_entropy = SemanticEntropy(
            entropy=pipeline_state.entropy_score or 0.0,
            spread=pipeline_state.entropy_spread or 0.0,
            clusters=pipeline_state.entropy_clusters or 1,
            samples=pipeline_state.semantic_samples[:3] if pipeline_state.semantic_samples else []
        )

        # Create judge score object
        judge_score = MetricScore(
            score=pipeline_state.llm_judge_score or 5.0,
            rationale=pipeline_state.llm_judge_reasoning or "Analysis completed",
            details={}
        )

        # Create contradictions list
        contradictions = []
        for contradiction in pipeline_state.contradictions:
            contradictions.append(Contradiction(
                type="intra" if contradiction.get("type") != "inter" else "inter",
                description=contradiction.get("description", ""),
                severity=contradiction.get("severity", "medium"),
                locations=[contradiction.get("sentence_1", ""), contradiction.get("sentence_2", "")]
            ))

        # Update report with converted data
        report.judge_score = judge_score
        report.semantic_entropy = semantic_entropy
        report.contradictions = contradictions
        report.patches = api_patches
        report.clarify_questions = api_questions

        # Calculate overall score
        overall_score = pipeline_state.llm_judge_score or 5.0
        report.overall_score = overall_score
        report.improvement_priority = "high" if overall_score < 6 else "medium" if overall_score < 8 else "low"

        # Cache the analysis
        analysis_cache[prompt_id] = {
            "report": report,
            "patches": api_patches,
            "questions": api_questions,
            "pipeline_state": pipeline_state
        }

        logger.info(f"Analysis completed for prompt {prompt_id}, score: {overall_score:.1f}")

        return AnalyzeResponse(
            report=report,
            patches=api_patches,
            questions=api_questions
        )

    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/apply", response_model=PromptImproved)
async def apply_patches(request: ApplyPatchesRequest):
    """
    Apply selected improvement patches to a prompt.
    """
    if request.prompt_id not in analysis_cache:
        raise HTTPException(status_code=404, detail="Prompt analysis not found")

    cached_data = analysis_cache[request.prompt_id]
    original_prompt = cached_data["report"].original_prompt
    available_patches = {p.id: p for p in cached_data["patches"]}

    # Determine which patches to apply
    patches_to_apply = []
    if request.apply_safe_all:
        patches_to_apply = [p for p in available_patches.values() if p.type == "safe"]
    else:
        patches_to_apply = [available_patches[pid] for pid in request.patch_ids
                          if pid in available_patches]

    if not patches_to_apply:
        raise HTTPException(status_code=400, detail="No valid patches to apply")

    # Apply patches (simple implementation)
    improved_prompt = original_prompt
    applied_patch_ids = []

    for patch in patches_to_apply:
        if patch.original in improved_prompt:
            improved_prompt = improved_prompt.replace(patch.original, patch.improved)
            applied_patch_ids.append(patch.id)

    # Calculate quality improvement estimate
    quality_gain = len(applied_patch_ids) * 0.5  # Simple estimate

    improvement_summary = f"Applied {len(applied_patch_ids)} patches: " + \
                         ", ".join([p.category for p in patches_to_apply])

    logger.info(f"Applied {len(applied_patch_ids)} patches to prompt {request.prompt_id}")

    return PromptImproved(
        original_prompt=original_prompt,
        improved_prompt=improved_prompt,
        applied_patches=applied_patch_ids,
        improvement_summary=improvement_summary,
        quality_gain=quality_gain
    )


@router.post("/clarify", response_model=AnalyzeResponse)
async def process_clarification(request: ClarifyRequest):
    """
    Process clarification answers and provide updated analysis.
    """
    if request.prompt_id not in analysis_cache:
        raise HTTPException(status_code=404, detail="Prompt analysis not found")

    # For now, return the cached analysis
    # In a full implementation, this would re-analyze with clarification context
    cached_data = analysis_cache[request.prompt_id]

    logger.info(f"Processed {len(request.answers)} clarification answers for {request.prompt_id}")

    return AnalyzeResponse(
        report=cached_data["report"],
        patches=cached_data["patches"],
        questions=cached_data["questions"]
    )
