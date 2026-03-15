
from pydantic import BaseModel, Field

from app.api.schemas.answer import AnswerResultResponse


class QuestionWithAnswers(BaseModel):
    question: "QuestionOutMin"
    answers: list[AnswerResultResponse]

    model_config = {"populate_by_name": True}


class QuestionOutMin(BaseModel):
    question_id: int = Field(alias="questionId")
    sequence_number: int = Field(alias="sequenceNumber")
    text: str
    type: str | None = None

    model_config = {"populate_by_name": True}


class SessionSummaryResponse(BaseModel):
    session_id: int = Field(alias="sessionId")
    role: str
    difficulty: str
    status: str
    questions: list[QuestionWithAnswers]

    model_config = {"populate_by_name": True}


QuestionWithAnswers.model_rebuild()
SessionSummaryResponse.model_rebuild()
