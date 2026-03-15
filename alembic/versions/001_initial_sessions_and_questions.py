"""initial sessions and questions

Revision ID: 001
Revises:
Create Date: 2026-03-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "interview_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("role", sqlmodel.AutoString(), nullable=False),
        sa.Column("difficulty", sqlmodel.AutoString(), nullable=False),
        sa.Column("status", sqlmodel.AutoString(), nullable=False),
        sa.Column("question_count", sa.Integer(), nullable=False),
        sa.Column("failure_reason", sqlmodel.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_interview_sessions_role"), "interview_sessions", ["role"])
    op.create_index(op.f("ix_interview_sessions_status"), "interview_sessions", ["status"])

    op.create_table(
        "interview_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("question_text", sqlmodel.AutoString(), nullable=False),
        sa.Column("question_type", sqlmodel.AutoString(), nullable=True),
        sa.Column("generation_prompt_version", sqlmodel.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id", "sequence_number", name="uq_question_session_seq"),
    )
    op.create_index(op.f("ix_interview_questions_session_id"), "interview_questions", ["session_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_interview_questions_session_id"), table_name="interview_questions")
    op.drop_table("interview_questions")
    op.drop_index(op.f("ix_interview_sessions_status"), table_name="interview_sessions")
    op.drop_index(op.f("ix_interview_sessions_role"), table_name="interview_sessions")
    op.drop_table("interview_sessions")
