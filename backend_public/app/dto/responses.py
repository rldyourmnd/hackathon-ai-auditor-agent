from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from .common import RiskLevel


class JudgeScore(BaseModel):
    score: float = Field(..., ge=0, le=10, description="Overall judge score (0-10)")
    rationale: str = Field(..., description="Judge reasoning")
    criteria_scores: Dict[str, float] = Field(
        default_factory=dict, description="Individual criteria scores"
    )
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Judge confidence level")


class SemanticEntropy(BaseModel):
    entropy: float = Field(..., description="Semantic entropy value")
    spread: float = Field(..., description="Semantic spread")
    clusters: int = Field(..., description="Number of semantic clusters")
    samples: List[str] = Field(default_factory=list, description="Sample variations")


class MetricReport(BaseModel):
    overall_score: float = Field(..., ge=0, le=10, description="Overall quality score")
    judge_score: JudgeScore = Field(..., description="LLM judge evaluation")
    semantic_entropy: SemanticEntropy = Field(
        ..., description="Semantic consistency metrics"
    )
    complexity_score: float = Field(..., ge=0, le=10, description="Vocabulary complexity")
    length_words: int = Field(..., ge=0, description="Word count")
    length_chars: int = Field(..., ge=0, description="Character count")
    risk_level: RiskLevel = Field(..., description="Overall risk assessment")
    contradictions: List[str] = Field(default_factory=list, description="Detected contradictions")
    format_valid: bool = Field(..., description="Format validation result")
    detected_language: str = Field(..., description="Detected language")
    translated: bool = Field(default=False, description="Whether content was translated")


class Patch(BaseModel):
    id: str = Field(..., description="Unique patch identifier")
    type: str = Field(..., pattern="^(safe|risky)$", description="Patch safety level")
    category: str = Field(..., description="Improvement category")
    title: str = Field(..., description="Short patch description")
    description: str = Field(..., description="Detailed patch description")
    original_text: Optional[str] = Field(None, description="Original text to replace")
    suggested_text: Optional[str] = Field(None, description="Suggested replacement text")
    rationale: str = Field(..., description="Why this improvement is suggested")
    risk_level: RiskLevel = Field(..., description="Risk level of applying this patch")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="Confidence in suggestion")


class ClarifyQuestion(BaseModel):
    id: str = Field(..., description="Question identifier")
    question: str = Field(..., description="Question text")
    category: str = Field(..., description="Question category")
    options: Optional[List[str]] = Field(None, description="Multiple choice options")
    required: bool = Field(default=True, description="Whether answer is required")


class AnalyzeResponse(BaseModel):
    analysis_id: str = Field(..., description="Unique analysis identifier")
    prompt_id: Optional[str] = Field(None, description="Prompt identifier")
    report: MetricReport = Field(..., description="Analysis metrics and scores")
    patches: List[Patch] = Field(default_factory=list, description="Improvement suggestions")
    questions: List[ClarifyQuestion] = Field(
        default_factory=list, description="Clarification questions"
    )
    created_at: datetime = Field(..., description="Analysis timestamp")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    pipeline_version: Optional[str] = Field(None, description="Analysis pipeline version")


class ClarifyResponse(BaseModel):
    analysis_id: str = Field(..., description="Analysis identifier")
    updated_report: MetricReport = Field(
        ..., description="Updated analysis after clarification"
    )
    new_patches: List[Patch] = Field(
        default_factory=list, description="New improvement suggestions"
    )
    score_delta: float = Field(..., description="Change in overall score")
    processing_time_ms: int = Field(..., description="Processing time for clarification")


class ApplyResponse(BaseModel):
    analysis_id: str = Field(..., description="Analysis identifier")
    original_prompt: str = Field(..., description="Original prompt text")
    improved_prompt: str = Field(..., description="Improved prompt text")
    applied_patches: List[str] = Field(
        ..., description="IDs of successfully applied patches"
    )
    failed_patches: List[str] = Field(
        default_factory=list, description="IDs of patches that failed to apply"
    )
    improvement_summary: str = Field(..., description="Summary of improvements made")
    quality_gain: float = Field(..., description="Estimated quality improvement")


class HealthResponse(BaseModel):
    service: str
    status: str
    timestamp: str
    version: str
    checks: Dict[str, Any]
