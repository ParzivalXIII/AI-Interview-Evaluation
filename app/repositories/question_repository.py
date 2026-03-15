from sqlmodel import Session, col, select

from app.models.question import InterviewQuestion


class QuestionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create_bulk(self, questions: list[InterviewQuestion]) -> list[InterviewQuestion]:
        for q in questions:
            self._session.add(q)
        self._session.commit()
        for q in questions:
            self._session.refresh(q)
        return questions

    def get_by_session_id(self, session_id: int) -> list[InterviewQuestion]:
        statement = (
            select(InterviewQuestion)
            .where(InterviewQuestion.session_id == session_id)
            .order_by(col(InterviewQuestion.sequence_number))
        )
        return list(self._session.exec(statement).all())

    def get_by_id(self, question_id: int) -> InterviewQuestion | None:
        return self._session.get(InterviewQuestion, question_id)

    def get_by_id_and_session(
        self, question_id: int, session_id: int
    ) -> InterviewQuestion | None:
        statement = select(InterviewQuestion).where(
            InterviewQuestion.id == question_id,
            InterviewQuestion.session_id == session_id,
        )
        return self._session.exec(statement).first()
