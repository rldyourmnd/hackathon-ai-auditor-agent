import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Text
from sqlmodel import JSON, Column, Field, Relationship, SQLModel


class PromptBase(SQLModel):
    """Base class for Prompt model."""
    name: str = Field(max_length=255, description="Prompt name/title")
    description: Optional[str] = Field(default=None, description="Prompt description")
    content: str = Field(sa_column=Column(Text), description="The prompt text")
    format_type: str = Field(default="auto", max_length=50, description="Prompt format (auto/xml/markdown)")
    language: str = Field(default="en", max_length=10, description="Prompt language")
    tags: Optional[List[str]] = Field(default_factory=list, sa_column=Column(JSON), description="Tags for categorization")
    extra_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSON), description="Additional metadata")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


class Prompt(PromptBase, table=True):
    """Prompt model for storing prompts in prompt-base."""
    __tablename__ = "prompts"

    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        description="Unique prompt identifier"
    )

    # Relationships
    relations_from: List["PromptRelation"] = Relationship(
        back_populates="source_prompt",
        sa_relationship_kwargs={"foreign_keys": "PromptRelation.source_id"}
    )
    relations_to: List["PromptRelation"] = Relationship(
        back_populates="target_prompt",
        sa_relationship_kwargs={"foreign_keys": "PromptRelation.target_id"}
    )
    analyses: List["AnalysisResult"] = Relationship(back_populates="prompt")


class PromptCreate(PromptBase):
    """Schema for creating a new prompt."""
    pass


class PromptRead(PromptBase):
    """Schema for reading a prompt."""
    id: str
    created_at: datetime
    updated_at: datetime


class PromptUpdate(SQLModel):
    """Schema for updating a prompt."""
    name: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    format_type: Optional[str] = None
    language: Optional[str] = None
    tags: Optional[List[str]] = None
    extra_metadata: Optional[Dict[str, Any]] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PromptRelationBase(SQLModel):
    """Base class for prompt relationships."""
    relation_type: str = Field(max_length=50, description="Relationship type: depends_on, overrides, conflicts_with")
    description: Optional[str] = Field(default=None, description="Description of the relationship")
    extra_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PromptRelation(PromptRelationBase, table=True):
    """Prompt relationship model."""
    __tablename__ = "prompt_relations"

    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )
    source_id: str = Field(foreign_key="prompts.id", description="Source prompt ID")
    target_id: str = Field(foreign_key="prompts.id", description="Target prompt ID")

    # Relationships
    source_prompt: Prompt = Relationship(
        back_populates="relations_from",
        sa_relationship_kwargs={"foreign_keys": "PromptRelation.source_id"}
    )
    target_prompt: Prompt = Relationship(
        back_populates="relations_to",
        sa_relationship_kwargs={"foreign_keys": "PromptRelation.target_id"}
    )


class PromptRelationCreate(PromptRelationBase):
    """Schema for creating a prompt relationship."""
    source_id: str
    target_id: str


class PromptRelationRead(PromptRelationBase):
    """Schema for reading a prompt relationship."""
    id: str
    source_id: str
    target_id: str
    created_at: datetime


class AnalysisResultBase(SQLModel):
    """Base class for analysis results."""
    prompt_content: str = Field(sa_column=Column(Text), description="Content that was analyzed")
    detected_language: str = Field(max_length=10, description="Detected language")
    translated: bool = Field(default=False, description="Whether content was translated")
    format_valid: bool = Field(description="Whether format is valid")

    # Metrics
    overall_score: float = Field(ge=0, le=10, description="Overall quality score")
    judge_score: float = Field(ge=0, le=10, description="LLM judge score")
    semantic_entropy: float = Field(description="Semantic entropy score")
    complexity_score: float = Field(ge=0, le=10, description="Vocabulary complexity")
    length_chars: int = Field(description="Character count")
    length_words: int = Field(description="Word count")

    # Analysis data
    contradictions: Optional[List[Dict[str, Any]]] = Field(default_factory=list, sa_column=Column(JSON))
    patches: Optional[List[Dict[str, Any]]] = Field(default_factory=list, sa_column=Column(JSON))
    clarify_questions: Optional[List[Dict[str, Any]]] = Field(default_factory=list, sa_column=Column(JSON))

    # Metadata  
    analysis_extra_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AnalysisResult(AnalysisResultBase, table=True):
    """Analysis result model for storing analysis history."""
    __tablename__ = "analysis_results"

    id: Optional[str] = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True
    )
    prompt_id: Optional[str] = Field(foreign_key="prompts.id", description="Associated prompt ID (if stored)")

    # Relationships
    prompt: Optional[Prompt] = Relationship(back_populates="analyses")


class AnalysisResultCreate(AnalysisResultBase):
    """Schema for creating an analysis result."""
    prompt_id: Optional[str] = None


class AnalysisResultRead(AnalysisResultBase):
    """Schema for reading an analysis result."""
    id: str
    prompt_id: Optional[str]
    created_at: datetime


# Export all models for easy imports
__all__ = [
    "Prompt", "PromptCreate", "PromptRead", "PromptUpdate",
    "PromptRelation", "PromptRelationCreate", "PromptRelationRead",
    "AnalysisResult", "AnalysisResultCreate", "AnalysisResultRead"
]
