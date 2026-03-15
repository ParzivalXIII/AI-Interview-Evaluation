from dataclasses import dataclass


@dataclass
class EvaluateAnswerPayload:
    answer_id: int
    session_id: int
    question_id: int
    idempotency_key: str
    correlation_id: str
    evaluation_prompt_version: str
    rubric_version: str

    def to_kwargs(self) -> dict:  # type: ignore[type-arg]
        return {
            "answer_id": self.answer_id,
            "session_id": self.session_id,
            "question_id": self.question_id,
            "idempotency_key": self.idempotency_key,
            "correlation_id": self.correlation_id,
            "evaluation_prompt_version": self.evaluation_prompt_version,
            "rubric_version": self.rubric_version,
        }
