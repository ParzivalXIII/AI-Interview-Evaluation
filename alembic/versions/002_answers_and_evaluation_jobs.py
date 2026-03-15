"""answers and evaluation jobs

Revision ID: 002
Revises: 001
Create Date: 2026-03-15

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "candidate_answers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("question_id", sa.Integer(), nullable=False),
        sa.Column("submission_index", sa.Integer(), nullable=False),
        sa.Column("answer_text", sqlmodel.AutoString(), nullable=False),
        sa.Column("status", sqlmodel.AutoString(), nullable=False),
        sa.Column("idempotency_key", sqlmodel.AutoString(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["interview_sessions.id"]),
        sa.ForeignKeyConstraint(["question_id"], ["interview_questions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_answer_idempotency_key"),
    )
    op.create_index(op.f("ix_candidate_answers_session_id"), "candidate_answers", ["session_id"])
    op.create_index(op.f("ix_candidate_answers_question_id"), "candidate_answers", ["question_id"])
    op.create_index(op.f("ix_candidate_answers_status"), "candidate_answers", ["status"])
    op.create_index(op.f("ix_candidate_answers_idempotency_key"), "candidate_answers", ["idempotency_key"])

    op.create_table(
        "evaluation_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("answer_id", sa.Integer(), nullable=False),
        sa.Column("job_type", sqlmodel.AutoString(), nullable=False),
        sa.Column("status", sqlmodel.AutoString(), nullable=False),
        sa.Column("queue_name", sqlmodel.AutoString(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("correlation_id", sqlmodel.AutoString(), nullable=False),
        sa.Column("last_error", sqlmodel.AutoString(), nullable=True),
        sa.Column("queued_at", sa.DateTime(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["answer_id"], ["candidate_answers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_evaluation_jobs_answer_id"), "evaluation_jobs", ["answer_id"])
    op.create_index(op.f("ix_evaluation_jobs_status"), "evaluation_jobs", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_evaluation_jobs_status"), table_name="evaluation_jobs")
    op.drop_index(op.f("ix_evaluation_jobs_answer_id"), table_name="evaluation_jobs")
    op.drop_table("evaluation_jobs")
    op.drop_index(op.f("ix_candidate_answers_idempotency_key"), table_name="candidate_answers")
    op.drop_index(op.f("ix_candidate_answers_status"), table_name="candidate_answers")
    op.drop_index(op.f("ix_candidate_answers_question_id"), table_name="candidate_answers")
    op.drop_index(op.f("ix_candidate_answers_session_id"), table_name="candidate_answers")
    op.drop_table("candidate_answers")
