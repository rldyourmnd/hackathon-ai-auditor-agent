from sqlalchemy import Column, JSON, UniqueConstraint, Text, CheckConstraint, Index
from datetime import datetime
from typing import Optional
import uuid
from sqlmodel import SQLModel, Field


# ------------------------------------------------------------
# Core domain models migrated to SQLModel with UUID string PKs
# ------------------------------------------------------------

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True, index=True)
    email: Optional[str] = Field(default=None, description="unique email", index=True)
    name: Optional[str] = Field(default=None)
    avatar_url: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
    )


class Session(SQLModel, table=True):
    __tablename__ = "sessions"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    jwt_id: str = Field(index=True, description="JWT JTI or derived id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime

    __table_args__ = (
        UniqueConstraint("jwt_id", name="uq_sessions_jwt_id"),
        Index("idx_sessions_user_id", "user_id"),
    )


class AuthAccount(SQLModel, table=True):
    __tablename__ = "auth_accounts"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    user_id: str = Field(foreign_key="users.id", index=True)
    provider: str = Field(description="e.g. google")
    provider_account_id: str
    access_token: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    refresh_token: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    raw_profile: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("provider", "provider_account_id", name="uq_provider_account"),
    )


# Note: Prompts and analysis tables live in the main backend per dbguideline.


class WorkflowRun(SQLModel, table=True):
    __tablename__ = "workflow_runs"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    user_id: Optional[str] = Field(default=None, foreign_key="users.id")
    # Link to core prompts table (backend side) per dbguideline
    prompt_id: Optional[str] = Field(default=None, foreign_key="prompts.id", index=True)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = Field(default=None)
    status: str = Field(default="running", description="running|success|failed|cancelled")
    meta: Optional[dict] = Field(default=None, sa_column=Column(JSON))

    __table_args__ = (
        CheckConstraint("status IN ('running','success','failed','cancelled')", name="chk_workflow_runs_status"),
        Index("idx_workflow_runs_started_at", "started_at"),
        Index("idx_workflow_runs_user_status", "user_id", "status"),
    )


class WorkflowNode(SQLModel, table=True):
    __tablename__ = "workflow_nodes"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    run_id: str = Field(foreign_key="workflow_runs.id", index=True)
    key: str = Field(description="e.g., detect_language")
    status: str = Field(default="pending")
    started_at: Optional[datetime] = Field(default=None)
    finished_at: Optional[datetime] = Field(default=None)
    result: Optional[dict] = Field(default=None, sa_column=Column(JSON))

    __table_args__ = (
        UniqueConstraint("run_id", "key", name="uq_run_node"),
        CheckConstraint("status IN ('pending','running','success','failed')", name="chk_workflow_nodes_status"),
    )


class EvaluationMetric(SQLModel, table=True):
    __tablename__ = "evaluation_metrics"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    run_id: str = Field(foreign_key="workflow_runs.id", index=True)
    node_key: Optional[str] = Field(default=None)
    metric_name: str = Field(description="metric name")
    metric_value: float
    metric_meta: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("run_id", "node_key", "metric_name", "created_at", name="uq_metric_point"),
        Index("idx_evaluation_metrics_run_metric", "run_id", "metric_name"),
    )


# ------------------------------------------------------------
# API Keys
# ------------------------------------------------------------


class ApiKey(SQLModel, table=True):
    __tablename__ = "api_keys"

    id: str = Field(default_factory=lambda: uuid.uuid4().hex, primary_key=True)
    name: str = Field(description="Display name for the key")
    prefix: str = Field(index=True, description="Short prefix for identification, e.g., ak_1234")
    hashed_token: str = Field(description="SHA-256 hash of the full token")
    active: bool = Field(default=True)
    scopes: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    user_id: Optional[str] = Field(default=None, foreign_key="users.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used_at: Optional[datetime] = Field(default=None)

    __table_args__ = (
        UniqueConstraint("prefix", name="uq_api_keys_prefix"),
        Index("idx_api_keys_user_id", "user_id"),
    )

