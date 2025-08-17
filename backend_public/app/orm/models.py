from __future__ import annotations

from sqlmodel import SQLModel, Field, Relationship, Column
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid
from sqlalchemy import JSON


class ClientType(str, Enum):
    BROWSER = "browser"
    IDE = "ide"
    CLI = "cli"
    API = "api"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventType(str, Enum):
    ANALYZE_STARTED = "analyze_started"
    ANALYZE_COMPLETED = "analyze_completed"
    ANALYZE_FAILED = "analyze_failed"
    CLARIFY_REQUESTED = "clarify_requested"
    CLARIFY_COMPLETED = "clarify_completed"
    PATCHES_APPLIED = "patches_applied"
    EXPORT_REQUESTED = "export_requested"


class Prompt(SQLModel, table=True):
    __tablename__ = "prompts"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    content: str = Field(..., max_length=50000)
    format_type: str = Field(default="auto")
    language: str = Field(default="auto")
    detected_language: Optional[str] = None
    translated: bool = Field(default=False)

    # Client info
    client_type: Optional[ClientType] = None
    client_name: Optional[str] = None
    client_version: Optional[str] = None
    client_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    analyses: List["AnalysisResult"] = Relationship(back_populates="prompt")


class AnalysisResult(SQLModel, table=True):
    __tablename__ = "analysis_results"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    prompt_id: str = Field(foreign_key="prompts.id", index=True)

    # Core metrics
    overall_score: float = Field(..., ge=0, le=10)
    judge_score: float = Field(..., ge=0, le=10)
    semantic_entropy: float = Field(...)
    complexity_score: float = Field(..., ge=0, le=10)
    length_words: int = Field(..., ge=0)
    length_chars: int = Field(..., ge=0)
    risk_level: RiskLevel = Field(...)
    format_valid: bool = Field(...)

    # JSON fields for complex data
    judge_details: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    semantic_details: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))
    contradictions: List[str] = Field(default_factory=list, sa_column=Column(JSON))
    patches: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))
    questions: List[Dict[str, Any]] = Field(default_factory=list, sa_column=Column(JSON))

    # Processing metadata
    processing_time_ms: int = Field(...)
    pipeline_version: Optional[str] = None
    pipeline_metadata: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON))

    # Clarification data
    clarification_answers: Optional[List[Dict[str, Any]]] = Field(default=None, sa_column=Column(JSON))
    applied_patches: Optional[List[str]] = Field(default=None, sa_column=Column(JSON))

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    prompt: Prompt = Relationship(back_populates="analyses")
    events: List["AnalysisEvent"] = Relationship(back_populates="analysis")


class AnalysisEvent(SQLModel, table=True):
    __tablename__ = "analysis_events"

    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    analysis_id: Optional[str] = Field(foreign_key="analysis_results.id", index=True)
    prompt_id: Optional[str] = Field(foreign_key="prompts.id", index=True)

    event_type: EventType = Field(..., index=True)
    event_data: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(JSON))

    # Performance tracking
    duration_ms: Optional[int] = None
    memory_usage_mb: Optional[float] = None

    # Request context
    request_id: Optional[str] = None
    user_ip: Optional[str] = None
    user_agent: Optional[str] = None

    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)

    # Relationships
    analysis: Optional[AnalysisResult] = Relationship(back_populates="events")
