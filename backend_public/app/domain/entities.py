from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class PromptEntity:
    id: str
    content: str
    format_type: str
    language: str
    detected_language: Optional[str]
    translated: bool
    created_at: datetime


@dataclass
class AnalysisEntity:
    id: str
    prompt_id: str
    overall_score: float
    risk_level: str
    judge_details: Dict[str, Any]
    semantic_details: Dict[str, Any]
    complexity_score: float
    length_words: int
    length_chars: int
    format_valid: bool
    patches: List[Dict[str, Any]]
    questions: List[Dict[str, Any]]
    processing_time_ms: int
    pipeline_version: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]


@dataclass
class EventEntity:
    id: str
    analysis_id: Optional[str]
    prompt_id: Optional[str]
    event_type: str
    event_data: Optional[Dict[str, Any]]
    duration_ms: Optional[int]
    created_at: datetime
