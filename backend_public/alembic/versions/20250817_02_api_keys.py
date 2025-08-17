"""
Add api_keys table for API key management

Revision ID: 20250817_02_api_keys
Revises: 20250817_01_initial
Create Date: 2025-08-17
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20250817_02_api_keys"
down_revision = "20250817_01_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("prefix", sa.String(length=50), nullable=False),
        sa.Column("hashed_token", sa.String(length=128), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("scopes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("user_id", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.func.now()),
        sa.Column("last_used_at", sa.DateTime(timezone=False), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ),
    )
    op.create_index("ix_api_keys_prefix", "api_keys", ["prefix"], unique=True)
    op.create_index("idx_api_keys_user_id", "api_keys", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_api_keys_user_id", table_name="api_keys")
    op.drop_index("ix_api_keys_prefix", table_name="api_keys")
    op.drop_table("api_keys")
