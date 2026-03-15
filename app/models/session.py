from datetime import datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from app.core.constants import Difficulty, SessionStatus

if TYPE_CHECKING:
    from app.models.answer import CandidateAnswer
    from app.models.question import InterviewQuestion


class InterviewSession(SQLModel, table=True):
    __tablename__ = "interview_sessions"  # type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    role: str = Field(index=True, nullable=False)
    difficulty: Difficulty = Field(nullable=False)
    status: SessionStatus = Field(default=SessionStatus.READY, index=True, nullable=False)
    question_count: int = Field(default=0, nullable=False)
    failure_reason: str | None = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)

    questions: list["InterviewQuestion"] = Relationship(back_populates="session")
    answers: list["CandidateAnswer"] = Relationship(back_populates="session")
