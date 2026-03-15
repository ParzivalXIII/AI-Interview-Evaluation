import json

from sqlmodel import Session

from app.api.schemas.answer import AnswerResultResponse, EvaluationResultOut
from app.api.utils import NotFoundError
from app.core.config import settings
from app.core.logging import get_logger, new_correlation_id
from app.models.answer import CandidateAnswer
from app.models.evaluation_job import EvaluationJob
from app.models.evaluation_result import EvaluationResult
from app.repositories.answer_repository import AnswerRepository
from app.repositories.evaluation_job_repository import EvaluationJobRepository
from app.repositories.evaluation_result_repository import EvaluationResultRepository

logger = get_logger(__name__)


def enqueue_evaluation(
    db: Session,
    answer: CandidateAnswer,
    arq_pool,  # type: ignore[type-arg]
) -> EvaluationJob:
    """Persist an EvaluationJob record and push the job into ARQ."""
    import asyncio

    from app.workers.job_contracts import EvaluateAnswerPayload
    from app.workers.utils import EVALUATE_ANSWER_JOB

    correlation_id = new_correlation_id()
    job_repo = EvaluationJobRepository(db)

    job = EvaluationJob(
        answer_id=answer.id,  # type: ignore[arg-type]
        correlation_id=correlation_id,
    )
    job = job_repo.create(job)

    payload = EvaluateAnswerPayload(
        answer_id=answer.id,  # type: ignore[arg-type]
        session_id=answer.session_id,
        question_id=answer.question_id,
        idempotency_key=answer.idempotency_key,
        correlation_id=correlation_id,
        evaluation_prompt_version=settings.evaluation_prompt_version,
        rubric_version=settings.rubric_version,
    )

    loop = asyncio.get_event_loop()
    loop.create_task(arq_pool.enqueue_job(EVALUATE_ANSWER_JOB, **payload.to_kwargs()))

    logger.info(
        "evaluation_enqueued",
        answer_id=answer.id,
        job_id=job.id,
        correlation_id=correlation_id,
    )
    return job


def _build_evaluation_out(result: EvaluationResult | None) -> EvaluationResultOut | None:
    if result is None:
        return None
    return EvaluationResultOut(
        evaluationStatus=result.evaluation_status.value,
        score=result.score,
        feedback=result.feedback,
        strengths=json.loads(result.strengths) if result.strengths else [],
        improvements=json.loads(result.improvements) if result.improvements else [],
        schemaVersion=result.evaluation_schema_version,
        rubricVersion=result.rubric_version,
        promptVersion=result.evaluation_prompt_version,
        modelName=result.model_name,
    )


def get_answer_result(
    db: Session,
    session_id: int,
    answer_id: int,
) -> AnswerResultResponse:
    answer_repo = AnswerRepository(db)
    result_repo = EvaluationResultRepository(db)

    answer = answer_repo.get_by_id_and_session(answer_id, session_id)
    if answer is None:
        raise NotFoundError(f"Answer {answer_id} not found in session {session_id}")

    eval_result = result_repo.get_by_answer_id(answer_id)

    return AnswerResultResponse(
        answerId=answer.id,  # type: ignore[arg-type]
        sessionId=answer.session_id,
        questionId=answer.question_id,
        answerText=answer.answer_text,
        status=answer.status,
        evaluation=_build_evaluation_out(eval_result),
    )
