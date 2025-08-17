"""
Add prompt_id FK on workflow_runs to core prompts

Revision ID: 1a23b4c5d6e7
Revises: 0b4c3a9d2f10
Create Date: 2025-08-17 18:10:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "1a23b4c5d6e7"
down_revision = "0b4c3a9d2f10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add prompt_id column (nullable) to workflow_runs
    op.add_column(
        "workflow_runs",
        sa.Column("prompt_id", sa.String(length=32), nullable=True),
    )
    # Create index for prompt_id to speed lookups
    op.create_index("idx_workflow_runs_prompt_id", "workflow_runs", ["prompt_id"], unique=False)
    # Add FK to core prompts table; set null on prompt deletion
    op.create_foreign_key(
        "fk_workflow_runs_prompt_id_prompts",
        source_table="workflow_runs",
        referent_table="prompts",
        local_cols=["prompt_id"],
        remote_cols=["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_workflow_runs_prompt_id_prompts", "workflow_runs", type_="foreignkey")
    op.drop_index("idx_workflow_runs_prompt_id", table_name="workflow_runs")
    op.drop_column("workflow_runs", "prompt_id")
