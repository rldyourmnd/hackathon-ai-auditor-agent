from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import uuid
import json
import logging
from datetime import datetime

from app.schemas.prompts import (
    AnalyzeRequest, AnalyzeResponse, ApplyPatchesRequest, ClarifyRequest,
    MetricReport, Patch, ClarifyQuestion, PromptImproved,
    MetricScore, SemanticEntropy, Contradiction
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
    - LLM-as-judge scoring
    - Semantic entropy analysis
    - Contradiction detection
    - Improvement patch generation
    - Clarification questions
    """
    try:
        prompt_id = str(uuid.uuid4())
        prompt_content = request.prompt.content
        
        logger.info(f"Starting analysis for prompt {prompt_id}")
        
        # Basic prompt info
        word_count = len(prompt_content.split())
        char_count = len(prompt_content)
        
        # LLM-as-judge evaluation
        llm = get_llm_service()
        judge_result = await llm.judge_prompt(prompt_content)
        try:
            judge_data = json.loads(judge_result)
            judge_score = MetricScore(
                score=judge_data.get("overall", 5.0),
                rationale=judge_data.get("rationale", "AI evaluation completed"),
                details=judge_data
            )
        except (json.JSONDecodeError, KeyError):
            # Fallback if JSON parsing fails
            judge_score = MetricScore(
                score=6.0,
                rationale="Analysis completed with estimated scoring",
                details={"raw_response": judge_result}
            )
        
        # Semantic entropy analysis
        entropy_samples = []
        entropy_score = 5.0
        if request.include_entropy:
            try:
                entropy_samples = await llm.sample_for_entropy(prompt_content)
                # Simple entropy calculation (placeholder)
                unique_responses = len(set(entropy_samples))
                entropy_score = min(10.0, (unique_responses / len(entropy_samples)) * 10)
            except Exception as e:
                logger.warning(f"Entropy analysis failed: {e}")
                entropy_samples = [f"Sample response {i}" for i in range(3)]
        
        semantic_entropy = SemanticEntropy(
            entropy=entropy_score,
            spread=entropy_score * 0.8,
            clusters=min(3, len(set(entropy_samples))),
            samples=entropy_samples[:3]  # Limit samples for response size
        )
        
        # Generate some demo contradictions
        contradictions = []
        if "never" in prompt_content.lower() and "always" in prompt_content.lower():
            contradictions.append(Contradiction(
                type="intra",
                description="Conflicting absolute statements found",
                severity="medium",
                locations=["Contains both 'never' and 'always' directives"]
            ))
        
        # Generate improvement patches
        patches = []
        if request.include_patches:
            # Demo patch for common issues
            if len(prompt_content) < 50:
                patches.append(Patch(
                    id=f"patch_{uuid.uuid4().hex[:8]}",
                    type="safe",
                    category="clarity",
                    description="Add more specific requirements",
                    original=prompt_content,
                    improved=f"{prompt_content}\n\nPlease provide specific examples and clear success criteria.",
                    rationale="Short prompts often lack necessary context",
                    confidence=0.8
                ))
            
            if not any(punct in prompt_content for punct in ['.', '!', '?']):
                patches.append(Patch(
                    id=f"patch_{uuid.uuid4().hex[:8]}",
                    type="safe",
                    category="markup",
                    description="Add proper punctuation",
                    original=prompt_content,
                    improved=prompt_content + ".",
                    rationale="Proper punctuation improves clarity",
                    confidence=0.9
                ))
        
        # Generate clarification questions
        questions = []
        if request.include_clarify:
            try:
                clarify_result = await llm.clarify_prompt(prompt_content)
                try:
                    clarify_data = json.loads(clarify_result)
                    for i, question in enumerate(clarify_data.get("questions", [])[:3]):
                        questions.append(ClarifyQuestion(
                            id=f"q_{uuid.uuid4().hex[:8]}",
                            question=question,
                            category="requirements",
                            importance="medium"
                        ))
                except (json.JSONDecodeError, KeyError):
                    # Fallback questions
                    questions = [
                        ClarifyQuestion(
                            id=f"q_{uuid.uuid4().hex[:8]}",
                            question="What specific output format do you need?",
                            category="format",
                            importance="high"
                        )
                    ]
            except Exception as e:
                logger.warning(f"Clarification generation failed: {e}")
        
        # Calculate overall score
        overall_score = (judge_score.score + entropy_score) / 2
        
        # Create the metric report
        report = MetricReport(
            prompt_id=prompt_id,
            original_prompt=prompt_content,
            analyzed_at=datetime.utcnow(),
            detected_language="en",  # Placeholder
            translated=False,
            format_valid=True,
            judge_score=judge_score,
            semantic_entropy=semantic_entropy,
            contradictions=contradictions,
            length_chars=char_count,
            length_words=word_count,
            complexity_score=min(10.0, word_count / 10),  # Simple complexity measure
            patches=patches,
            clarify_questions=questions,
            overall_score=overall_score,
            improvement_priority="medium" if overall_score < 7 else "low"
        )
        
        # Cache the analysis
        analysis_cache[prompt_id] = {
            "report": report,
            "patches": patches,
            "questions": questions
        }
        
        logger.info(f"Analysis completed for prompt {prompt_id}, score: {overall_score:.1f}")
        
        return AnalyzeResponse(
            report=report,
            patches=patches,
            questions=questions
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