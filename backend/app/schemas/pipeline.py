"""Pipeline state and node contracts for LangGraph."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.prompts import ClarifyQuestion, MetricReport, Patch


class PipelineState(BaseModel):
    """Central state object that flows through the analysis pipeline."""

    # Input data
    prompt_content: str = Field(..., description="Original prompt content")
    format_type: Literal["auto", "markdown", "xml", "text"] = Field(default="text")

    # Language processing
    detected_language: Optional[str] = None
    translated: bool = False
    translated_content: Optional[str] = None

    # Format validation
    format_valid: bool = False
    markup_fixes: List[str] = Field(default_factory=list)

    # Vocabulary analysis
    vocab_unified: bool = False
    vocab_changes: List[str] = Field(default_factory=list)

    # Contradiction detection
    contradictions: List[Dict[str, Any]] = Field(default_factory=list)

    # Semantic entropy
    semantic_samples: List[str] = Field(default_factory=list)
    semantic_embeddings: List[List[float]] = Field(default_factory=list)
    entropy_score: Optional[float] = None
    entropy_spread: Optional[float] = None
    entropy_clusters: Optional[int] = None

    # LLM Judge scoring
    llm_judge_score: Optional[float] = None
    llm_judge_reasoning: Optional[str] = None

    # Patches and improvements
    patches: List[Patch] = Field(default_factory=list)

    # Clarification questions
    clarify_questions: List[ClarifyQuestion] = Field(default_factory=list)

    # Metadata
    processing_started: datetime = Field(default_factory=datetime.utcnow)
    processing_completed: Optional[datetime] = None
    errors: List[str] = Field(default_factory=list)

    # Working content (may change during processing)
    working_content: Optional[str] = None

    def get_current_content(self) -> str:
        """Get the current working content or original if no working version."""
        return self.working_content or self.translated_content or self.prompt_content

    def add_error(self, error: str):
        """Add an error to the pipeline state."""
        self.errors.append(f"{datetime.utcnow().isoformat()}: {error}")

    def to_metric_report(self) -> MetricReport:
        """Convert pipeline state to final metric report."""
        from app.schemas.prompts import Contradiction, MetricScore, SemanticEntropy

        current_content = self.get_current_content()

        # Create judge score object
        judge_score = MetricScore(
            score=self.llm_judge_score or 5.0,
            rationale=self.llm_judge_reasoning or "Analysis completed",
            details={}
        )

        # Create semantic entropy object
        semantic_entropy = SemanticEntropy(
            entropy=self.entropy_score or 0.0,
            spread=self.entropy_spread or 0.0,
            clusters=self.entropy_clusters or 1,
            samples=self.semantic_samples[:3] if self.semantic_samples else []
        )

        # Convert contradictions to proper format
        api_contradictions = []
        for contradiction in self.contradictions:
            api_contradictions.append(Contradiction(
                type=contradiction.get("type", "intra"),
                description=contradiction.get("description", ""),
                severity=contradiction.get("severity", "medium"),
                locations=[contradiction.get("sentence_1", ""), contradiction.get("sentence_2", "")]
            ))

        return MetricReport(
            prompt_id="",  # Will be set by API
            original_prompt="",  # Will be set by API
            detected_language=self.detected_language or "unknown",
            translated=self.translated,
            format_valid=self.format_valid,
            judge_score=judge_score,
            semantic_entropy=semantic_entropy,
            contradictions=api_contradictions,
            complexity_score=min(10.0, len(current_content) / 100.0),  # Simple complexity
            length_chars=len(current_content),
            length_words=len(current_content.split()),
            patches=self.patches,
            clarify_questions=self.clarify_questions,
            overall_score=self.llm_judge_score or 5.0,
            improvement_priority="high" if (self.llm_judge_score or 5.0) < 6 else "medium" if (self.llm_judge_score or 5.0) < 8 else "low"
        )


class NodeResult(BaseModel):
    """Result from a pipeline node execution."""

    success: bool = True
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    next_node: Optional[str] = None  # For conditional routing


class LanguageDetectionResult(BaseModel):
    """Result from language detection node."""

    language: str = Field(..., description="Detected language code (en, ru, etc.)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence")
    needs_translation: bool = Field(..., description="Whether translation is needed")


class TranslationResult(BaseModel):
    """Result from translation node."""

    translated_content: str = Field(..., description="Translated content")
    original_language: str = Field(..., description="Original language")
    translation_quality: float = Field(default=0.8, ge=0.0, le=1.0)


class FormatValidationResult(BaseModel):
    """Result from format validation node."""

    is_valid: bool = Field(..., description="Whether format is valid")
    errors: List[str] = Field(default_factory=list)
    suggested_fixes: List[str] = Field(default_factory=list)
    corrected_content: Optional[str] = None


class VocabularyResult(BaseModel):
    """Result from vocabulary unification node."""

    unified_content: str = Field(..., description="Content with unified vocabulary")
    changes_made: List[str] = Field(default_factory=list)
    vocabulary_score: float = Field(default=1.0, ge=0.0, le=1.0)


class ContradictionResult(BaseModel):
    """Result from contradiction detection node."""

    contradictions_found: List[Dict[str, Any]] = Field(default_factory=list)
    contradiction_score: float = Field(default=0.0, ge=0.0, le=1.0)
    severity: Literal["none", "minor", "major", "critical"] = "none"


class SemanticEntropyResult(BaseModel):
    """Result from semantic entropy analysis node."""

    entropy: float = Field(..., ge=0.0, description="Semantic entropy score")
    spread: float = Field(..., ge=0.0, description="Semantic spread")
    clusters: int = Field(..., ge=1, description="Number of semantic clusters")
    avg_similarity: float = Field(..., ge=0.0, le=1.0)
    samples_analyzed: int = Field(..., ge=1)


class JudgeScoreResult(BaseModel):
    """Result from LLM judge scoring node."""

    overall_score: float = Field(..., ge=0.0, le=10.0, description="Overall quality score")
    clarity_score: float = Field(..., ge=0.0, le=10.0)
    specificity_score: float = Field(..., ge=0.0, le=10.0)
    actionability_score: float = Field(..., ge=0.0, le=10.0)
    reasoning: str = Field(..., description="Judge reasoning")


class PatchGenerationResult(BaseModel):
    """Result from patch generation node."""

    patches: List[Patch] = Field(default_factory=list)
    safe_patches_count: int = Field(default=0, ge=0)
    risky_patches_count: int = Field(default=0, ge=0)


class QuestionGenerationResult(BaseModel):
    """Result from clarification question generation node."""

    questions: List[ClarifyQuestion] = Field(default_factory=list)
    priority_questions: List[str] = Field(default_factory=list)
    question_categories: List[str] = Field(default_factory=list)
