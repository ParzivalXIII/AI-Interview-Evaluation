
from sqlmodel import Session, select

from app.models.evaluation_result import EvaluationResult


class EvaluationResultRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, result: EvaluationResult) -> EvaluationResult:
        self._session.add(result)
        self._session.commit()
        self._session.refresh(result)
        return result

    def get_by_answer_id(self, answer_id: int) -> EvaluationResult | None:
        statement = select(EvaluationResult).where(EvaluationResult.answer_id == answer_id)
        return self._session.exec(statement).first()

    def get_by_id(self, result_id: int) -> EvaluationResult | None:
        return self._session.get(EvaluationResult, result_id)
