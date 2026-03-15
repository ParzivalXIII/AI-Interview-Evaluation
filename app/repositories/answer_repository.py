import hashlib
from datetime import datetime

from sqlmodel import Session, col, select

from app.core.constants import AnswerStatus
from app.models.answer import CandidateAnswer


class AnswerRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    @staticmethod
    def build_idempotency_key(session_id: int, question_id: int, answer_text: str) -> str:
        payload = f"{session_id}:{question_id}:{answer_text}"
        return hashlib.sha256(payload.encode()).hexdigest()

    def create(self, answer: CandidateAnswer) -> CandidateAnswer:
        self._session.add(answer)
        self._session.commit()
        self._session.refresh(answer)
        return answer

    def get_by_id(self, answer_id: int) -> CandidateAnswer | None:
        return self._session.get(CandidateAnswer, answer_id)

    def get_by_id_and_session(
        self, answer_id: int, session_id: int
    ) -> CandidateAnswer | None:
        statement = select(CandidateAnswer).where(
            CandidateAnswer.id == answer_id,
            CandidateAnswer.session_id == session_id,
        )
        return self._session.exec(statement).first()

    def get_by_idempotency_key(self, key: str) -> CandidateAnswer | None:
        statement = select(CandidateAnswer).where(CandidateAnswer.idempotency_key == key)
        return self._session.exec(statement).first()

    def get_by_session_and_question(
        self, session_id: int, question_id: int
    ) -> list[CandidateAnswer]:
        statement = (
            select(CandidateAnswer)
            .where(
                CandidateAnswer.session_id == session_id,
                CandidateAnswer.question_id == question_id,
            )
            .order_by(col(CandidateAnswer.submission_index))
        )
        return list(self._session.exec(statement).all())

    def get_by_session_id(self, session_id: int) -> list[CandidateAnswer]:
        statement = select(CandidateAnswer).where(CandidateAnswer.session_id == session_id)
        return list(self._session.exec(statement).all())

    def update_status(
        self, answer: CandidateAnswer, status: AnswerStatus
    ) -> CandidateAnswer:
        answer.status = status
        answer.updated_at = datetime.utcnow()
        self._session.add(answer)
        self._session.commit()
        self._session.refresh(answer)
        return answer
