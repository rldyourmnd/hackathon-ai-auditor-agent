"""
Initial schema for backend_public: prompts, analysis_results, analysis_events

Revision ID: 20250817_01_initial
Revises: 
Create Date: 2025-08-17
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20250817_01_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # prompts table
    op.create_table(
        "prompts",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("format_type", sa.String(length=50), nullable=False, server_default="auto"),
        sa.Column("language", sa.String(length=50), nullable=False, server_default="auto"),
        sa.Column("detected_language", sa.String(length=50), nullable=True),
        sa.Column("translated", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("client_type", sa.String(length=20), nullable=True),
        sa.Column("client_name", sa.String(length=100), nullable=True),
        sa.Column("client_version", sa.String(length=100), nullable=True),
        sa.Column("client_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_prompts_id", "prompts", ["id"], unique=False)

    # analysis_results table
    op.create_table(
        "analysis_results",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("prompt_id", sa.String(), sa.ForeignKey("prompts.id"), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("judge_score", sa.Float(), nullable=False),
        sa.Column("semantic_entropy", sa.Float(), nullable=False),
        sa.Column("complexity_score", sa.Float(), nullable=False),
        sa.Column("length_words", sa.Integer(), nullable=False),
        sa.Column("length_chars", sa.Integer(), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("format_valid", sa.Boolean(), nullable=False),
        sa.Column("judge_details", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("semantic_details", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("contradictions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("patches", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("questions", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("processing_time_ms", sa.Integer(), nullable=False),
        sa.Column("pipeline_version", sa.String(length=50), nullable=True),
        sa.Column("pipeline_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("clarification_answers", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("applied_patches", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_analysis_results_id", "analysis_results", ["id"], unique=False)
    op.create_index("ix_analysis_results_prompt_id", "analysis_results", ["prompt_id"], unique=False)

    # analysis_events table
    op.create_table(
        "analysis_events",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("analysis_id", sa.String(), sa.ForeignKey("analysis_results.id"), nullable=True),
        sa.Column("prompt_id", sa.String(), sa.ForeignKey("prompts.id"), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False, index=True),
        sa.Column("event_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("memory_usage_mb", sa.Float(), nullable=True),
        sa.Column("request_id", sa.String(length=100), nullable=True),
        sa.Column("user_ip", sa.String(length=100), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_analysis_events_analysis_id", "analysis_events", ["analysis_id"], unique=False)
    op.create_index("ix_analysis_events_prompt_id", "analysis_events", ["prompt_id"], unique=False)
    op.create_index("ix_analysis_events_timestamp", "analysis_events", ["timestamp"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_analysis_events_timestamp", table_name="analysis_events")
    op.drop_index("ix_analysis_events_prompt_id", table_name="analysis_events")
    op.drop_index("ix_analysis_events_analysis_id", table_name="analysis_events")
    op.drop_table("analysis_events")

    op.drop_index("ix_analysis_results_prompt_id", table_name="analysis_results")
    op.drop_index("ix_analysis_results_id", table_name="analysis_results")
    op.drop_table("analysis_results")

    op.drop_index("ix_prompts_id", table_name="prompts")
    op.drop_table("prompts")
