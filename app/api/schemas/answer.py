from typing import Optional

from pydantic import BaseModel, Field

from app.core.constants import AnswerStatus


class SubmitAnswerRequest(BaseModel):
    question_id: int = Field(alias="questionId")
    answer_text: str = Field(min_length=1, alias="answerText")

    model_config = {"populate_by_name": True}


class AnswerAcceptedResponse(BaseModel):
    answer_id: int = Field(alias="answerId")
    session_id: int = Field(alias="sessionId")
    question_id: int = Field(alias="questionId")
    status: AnswerStatus

    model_config = {"populate_by_name": True}


class AnswerResultResponse(BaseModel):
    answer_id: int = Field(alias="answerId")
    session_id: int = Field(alias="sessionId")
    question_id: int = Field(alias="questionId")
    answer_text: str = Field(alias="answerText")
    status: AnswerStatus
    evaluation: Optional["EvaluationResultOut"] = None
    failure_reason: str | None = Field(default=None, alias="failureReason")

    model_config = {"populate_by_name": True}


class EvaluationResultOut(BaseModel):
    evaluation_status: str = Field(alias="evaluationStatus")
    score: float | None = None
    feedback: str | None = None
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    schema_version: str = Field(alias="schemaVersion")
    rubric_version: str = Field(alias="rubricVersion")
    prompt_version: str = Field(alias="promptVersion")
    model_name: str = Field(alias="modelName")

    model_config = {"populate_by_name": True}


AnswerResultResponse.model_rebuild()
