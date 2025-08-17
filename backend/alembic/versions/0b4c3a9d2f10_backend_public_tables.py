"""
Add backend_public user/session/workflow/metrics tables

Revision ID: 0b4c3a9d2f10
Revises: 001_initial_tables
Create Date: 2025-08-17 17:10:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0b4c3a9d2f10"
down_revision = "001_initial_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # users
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=32), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    # sessions
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(length=32), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("jwt_id", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("jwt_id", name="uq_sessions_jwt_id"),
    )
    op.create_index("idx_sessions_user_id", "sessions", ["user_id"], unique=False)
    op.create_index("ix_sessions_jwt_id", "sessions", ["jwt_id"], unique=False)

    # auth_accounts
    op.create_table(
        "auth_accounts",
        sa.Column("id", sa.String(length=32), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=32), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("provider_account_id", sa.String(length=255), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("raw_profile", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("provider", "provider_account_id", name="uq_provider_account"),
    )

    # workflow_runs
    op.create_table(
        "workflow_runs",
        sa.Column("id", sa.String(length=32), primary_key=True, nullable=False),
        sa.Column("user_id", sa.String(length=32), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("started_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("status", sa.String(length=32), server_default=sa.text("'running'"), nullable=False),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.CheckConstraint(
            "status IN ('running','success','failed','cancelled')",
            name="chk_workflow_runs_status",
        ),
    )
    op.create_index("idx_workflow_runs_started_at", "workflow_runs", ["started_at"], unique=False)
    op.create_index("idx_workflow_runs_user_status", "workflow_runs", ["user_id", "status"], unique=False)

    # workflow_nodes
    op.create_table(
        "workflow_nodes",
        sa.Column("id", sa.String(length=32), primary_key=True, nullable=False),
        sa.Column("run_id", sa.String(length=32), sa.ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), server_default=sa.text("'pending'"), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.UniqueConstraint("run_id", "key", name="uq_run_node"),
        sa.CheckConstraint(
            "status IN ('pending','running','success','failed')",
            name="chk_workflow_nodes_status",
        ),
    )
    op.create_index("ix_workflow_nodes_run_id", "workflow_nodes", ["run_id"], unique=False)

    # evaluation_metrics
    op.create_table(
        "evaluation_metrics",
        sa.Column("id", sa.String(length=32), primary_key=True, nullable=False),
        sa.Column("run_id", sa.String(length=32), sa.ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("node_key", sa.String(length=128), nullable=True),
        sa.Column("metric_name", sa.String(length=128), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("metric_meta", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("run_id", "node_key", "metric_name", "created_at", name="uq_metric_point"),
    )
    op.create_index(
        "idx_evaluation_metrics_run_metric",
        "evaluation_metrics",
        ["run_id", "metric_name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_evaluation_metrics_run_metric", table_name="evaluation_metrics")
    op.drop_table("evaluation_metrics")

    op.drop_index("ix_workflow_nodes_run_id", table_name="workflow_nodes")
    op.drop_table("workflow_nodes")

    op.drop_index("idx_workflow_runs_user_status", table_name="workflow_runs")
    op.drop_index("idx_workflow_runs_started_at", table_name="workflow_runs")
    op.drop_table("workflow_runs")

    op.drop_table("auth_accounts")

    op.drop_index("ix_sessions_jwt_id", table_name="sessions")
    op.drop_index("idx_sessions_user_id", table_name="sessions")
    op.drop_table("sessions")

    op.drop_table("users")
