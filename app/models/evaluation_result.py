from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

from app.core.constants import EvaluationStatus

if TYPE_CHECKING:
    from app.models.answer import CandidateAnswer


class EvaluationResult(SQLModel, table=True):
    __tablename__ = "evaluation_results"            #type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    answer_id: int = Field(foreign_key="candidate_answers.id", unique=True, index=True, nullable=False)
    score: float | None = Field(default=None, nullable=True)
    feedback: str | None = Field(default=None, nullable=True)
    evaluation_status: EvaluationStatus = Field(
        default=EvaluationStatus.INCOMPLETE, nullable=False
    )
    strengths: str | None = Field(default=None, nullable=True)  # JSON-serialized list
    improvements: str | None = Field(default=None, nullable=True)  # JSON-serialized list
    rubric_version: str = Field(nullable=False)
    evaluation_prompt_version: str = Field(nullable=False)
    evaluation_schema_version: str = Field(nullable=False)
    model_provider: str = Field(default="openrouter", nullable=False)
    model_name: str = Field(nullable=False)
    raw_model_response: str | None = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)

    answer: Optional["CandidateAnswer"] = Relationship(back_populates="evaluation_result")
