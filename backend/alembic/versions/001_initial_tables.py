"""Initial tables

Revision ID: 001
Revises:
Create Date: 2025-08-16 10:30:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create prompts table
    op.create_table('prompts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('format_type', sa.String(length=50), nullable=False),
        sa.Column('language', sa.String(length=10), nullable=False),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create prompt_relations table
    op.create_table('prompt_relations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('source_id', sa.String(), nullable=False),
        sa.Column('target_id', sa.String(), nullable=False),
        sa.Column('relation_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['source_id'], ['prompts.id'], ),
        sa.ForeignKeyConstraint(['target_id'], ['prompts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create analysis_results table
    op.create_table('analysis_results',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('prompt_id', sa.String(), nullable=True),
        sa.Column('prompt_content', sa.Text(), nullable=False),
        sa.Column('detected_language', sa.String(length=10), nullable=False),
        sa.Column('translated', sa.Boolean(), nullable=False),
        sa.Column('format_valid', sa.Boolean(), nullable=False),
        sa.Column('overall_score', sa.Float(), nullable=False),
        sa.Column('judge_score', sa.Float(), nullable=False),
        sa.Column('semantic_entropy', sa.Float(), nullable=False),
        sa.Column('complexity_score', sa.Float(), nullable=False),
        sa.Column('length_chars', sa.Integer(), nullable=False),
        sa.Column('length_words', sa.Integer(), nullable=False),
        sa.Column('contradictions', sa.JSON(), nullable=True),
        sa.Column('patches', sa.JSON(), nullable=True),
        sa.Column('clarify_questions', sa.JSON(), nullable=True),
        sa.Column('analysis_extra_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['prompt_id'], ['prompts.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('analysis_results')
    op.drop_table('prompt_relations')
    op.drop_table('prompts')
