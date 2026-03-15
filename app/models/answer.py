from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.core.constants import AnswerStatus

if TYPE_CHECKING:
    from app.models.evaluation_job import EvaluationJob
    from app.models.evaluation_result import EvaluationResult
    from app.models.question import InterviewQuestion
    from app.models.session import InterviewSession


class CandidateAnswer(SQLModel, table=True):
    __tablename__ = "candidate_answers"         #type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="interview_sessions.id", index=True, nullable=False)
    question_id: int = Field(foreign_key="interview_questions.id", index=True, nullable=False)
    submission_index: int = Field(default=1, nullable=False)
    answer_text: str = Field(nullable=False)
    status: AnswerStatus = Field(default=AnswerStatus.PENDING_EVALUATION, index=True, nullable=False)
    idempotency_key: str = Field(unique=True, index=True, nullable=False)
    submitted_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    session: Optional["InterviewSession"] = Relationship(back_populates="answers")
    question: Optional["InterviewQuestion"] = Relationship(back_populates="answers")
    evaluation_jobs: list["EvaluationJob"] = Relationship(back_populates="answer")
    evaluation_result: Optional["EvaluationResult"] = Relationship(back_populates="answer")
