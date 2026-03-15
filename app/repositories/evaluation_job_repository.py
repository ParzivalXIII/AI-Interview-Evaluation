from datetime import datetime

from sqlmodel import Session, select

from app.core.constants import EvaluationJobStatus
from app.models.evaluation_job import EvaluationJob


class EvaluationJobRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, job: EvaluationJob) -> EvaluationJob:
        self._session.add(job)
        self._session.commit()
        self._session.refresh(job)
        return job

    def get_by_id(self, job_id: int) -> EvaluationJob | None:
        return self._session.get(EvaluationJob, job_id)

    def get_by_answer_id(self, answer_id: int) -> list[EvaluationJob]:
        statement = (
            select(EvaluationJob)
            .where(EvaluationJob.answer_id == answer_id)
            .order_by(EvaluationJob.queued_at.desc())  # type: ignore[attr-defined]
        )
        return list(self._session.exec(statement).all())

    def update_status(
        self,
        job: EvaluationJob,
        status: EvaluationJobStatus,
        last_error: str | None = None,
    ) -> EvaluationJob:
        job.status = status
        if status == EvaluationJobStatus.RUNNING:
            job.started_at = datetime.now()
        elif status in (EvaluationJobStatus.COMPLETED, EvaluationJobStatus.FAILED):
            job.finished_at = datetime.now()
        if last_error is not None:
            job.last_error = last_error
        self._session.add(job)
        self._session.commit()
        self._session.refresh(job)
        return job
