
from sqlmodel import Session

from app.models.session import InterviewSession


class SessionRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, session_obj: InterviewSession) -> InterviewSession:
        self._session.add(session_obj)
        self._session.commit()
        self._session.refresh(session_obj)
        return session_obj

    def get_by_id(self, session_id: int) -> InterviewSession | None:
        return self._session.get(InterviewSession, session_id)

    def update(self, session_obj: InterviewSession) -> InterviewSession:
        self._session.add(session_obj)
        self._session.commit()
        self._session.refresh(session_obj)
        return session_obj
