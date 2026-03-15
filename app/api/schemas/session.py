
from pydantic import BaseModel, Field

from app.core.constants import Difficulty, SessionStatus


class CreateSessionRequest(BaseModel):
    role: str = Field(min_length=1)
    difficulty: Difficulty
    question_count: int = Field(default=5, ge=1, le=10, alias="questionCount")

    model_config = {"populate_by_name": True}


class QuestionOut(BaseModel):
    question_id: int = Field(alias="questionId")
    sequence_number: int = Field(alias="sequenceNumber")
    text: str
    type: str | None = None

    model_config = {"populate_by_name": True, "from_attributes": True}


class SessionCreatedResponse(BaseModel):
    session_id: int = Field(alias="sessionId")
    status: SessionStatus
    questions: list[QuestionOut]

    model_config = {"populate_by_name": True}


class SessionDetailResponse(BaseModel):
    session_id: int = Field(alias="sessionId")
    role: str
    difficulty: Difficulty
    status: SessionStatus
    questions: list[QuestionOut]
    failure_reason: str | None = Field(default=None, alias="failureReason")

    model_config = {"populate_by_name": True}
