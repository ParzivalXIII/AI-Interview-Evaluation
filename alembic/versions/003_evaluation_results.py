"""evaluation results and audit metadata fields

Revision ID: 003
Revises: 002
Create Date: 2026-03-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "evaluation_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("answer_id", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("feedback", sqlmodel.AutoString(), nullable=True),
        sa.Column("evaluation_status", sqlmodel.AutoString(), nullable=False),
        sa.Column("strengths", sqlmodel.AutoString(), nullable=True),
        sa.Column("improvements", sqlmodel.AutoString(), nullable=True),
        sa.Column("rubric_version", sqlmodel.AutoString(), nullable=False),
        sa.Column("evaluation_prompt_version", sqlmodel.AutoString(), nullable=False),
        sa.Column("evaluation_schema_version", sqlmodel.AutoString(), nullable=False),
        sa.Column("model_provider", sqlmodel.AutoString(), nullable=False),
        sa.Column("model_name", sqlmodel.AutoString(), nullable=False),
        sa.Column("raw_model_response", sqlmodel.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["answer_id"], ["candidate_answers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("answer_id", name="uq_evaluation_result_answer"),
    )
    op.create_index(op.f("ix_evaluation_results_answer_id"), "evaluation_results", ["answer_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_evaluation_results_answer_id"), table_name="evaluation_results")
    op.drop_table("evaluation_results")
