from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.answer import CandidateAnswer
    from app.models.session import InterviewSession


class InterviewQuestion(SQLModel, table=True):
    __tablename__ = "interview_questions"           #type: ignore[assignment]

    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="interview_sessions.id", index=True, nullable=False)
    sequence_number: int = Field(nullable=False)
    question_text: str = Field(nullable=False)
    question_type: str | None = Field(default=None, nullable=True)
    generation_prompt_version: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.now, nullable=False)

    session: Optional["InterviewSession"] = Relationship(back_populates="questions")
    answers: list["CandidateAnswer"] = Relationship(back_populates="question")
