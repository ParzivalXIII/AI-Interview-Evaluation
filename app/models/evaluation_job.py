from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.core.constants import EvaluationJobStatus, JobType

if TYPE_CHECKING:
    from app.models.answer import CandidateAnswer


class EvaluationJob(SQLModel, table=True):
    __tablename__ = "evaluation_jobs"           #type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    answer_id: int = Field(foreign_key="candidate_answers.id", index=True, nullable=False)
    job_type: JobType = Field(default=JobType.ANSWER_EVALUATION, nullable=False)
    status: EvaluationJobStatus = Field(
        default=EvaluationJobStatus.QUEUED, index=True, nullable=False
    )
    queue_name: str = Field(default="arq:evaluation", nullable=False)
    attempt_count: int = Field(default=0, nullable=False)
    correlation_id: str = Field(nullable=False)
    last_error: str | None = Field(default=None, nullable=True)
    queued_at: datetime = Field(default_factory=datetime.now, nullable=False)
    started_at: datetime | None = Field(default=None, nullable=True)
    finished_at: datetime | None = Field(default=None, nullable=True)

    answer: Optional["CandidateAnswer"] = Relationship(back_populates="evaluation_jobs")
