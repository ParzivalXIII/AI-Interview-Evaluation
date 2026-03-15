import json

from sqlmodel import Session

from app.core.config import settings
from app.core.constants import AnswerStatus, EvaluationJobStatus, EvaluationStatus
from app.core.database import engine
from app.core.logging import get_logger
from app.models.evaluation_result import EvaluationResult
from app.repositories.answer_repository import AnswerRepository
from app.repositories.evaluation_job_repository import EvaluationJobRepository
from app.repositories.evaluation_result_repository import EvaluationResultRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.session_repository import SessionRepository
from app.services import llm_service
from app.workers.utils import EVALUATE_ANSWER_JOB, log_job_end, log_job_start

logger = get_logger(__name__)


async def evaluate_candidate_answer(
    ctx: dict,  # type: ignore[type-arg]
    *,
    answer_id: int,
    session_id: int,
    question_id: int,
    idempotency_key: str,
    correlation_id: str,
    evaluation_prompt_version: str,
    rubric_version: str,
) -> dict:  # type: ignore[type-arg]
    """ARQ worker function: evaluate a candidate answer using the LLM.

    This function is idempotent — if the answer already has a completed result it
    returns early without calling the LLM again.
    """
    await log_job_start(
        EVALUATE_ANSWER_JOB,
        correlation_id,
        answer_id=answer_id,
        session_id=session_id,
    )

    with Session(engine) as db:
        answer_repo = AnswerRepository(db)
        job_repo = EvaluationJobRepository(db)
        result_repo = EvaluationResultRepository(db)
        question_repo = QuestionRepository(db)
        session_repo = SessionRepository(db)

        answer = answer_repo.get_by_id(answer_id)
        if answer is None:
            logger.error("worker_answer_not_found", answer_id=answer_id, correlation_id=correlation_id)
            return {"status": "failed", "error_code": "ANSWER_NOT_FOUND", "answer_id": answer_id}

        # Idempotency: if already completed, skip silently
        existing_result = result_repo.get_by_answer_id(answer_id)
        if existing_result is not None and existing_result.evaluation_status == EvaluationStatus.COMPLETED:
            logger.info("worker_already_completed", answer_id=answer_id)
            return {"status": "completed", "answer_id": answer_id, "idempotent": True}

        # Load context
        question = question_repo.get_by_id(question_id)
        session_obj = session_repo.get_by_id(session_id)
        if question is None or session_obj is None:
            logger.error("worker_context_not_found", question_id=question_id, session_id=session_id)
            return {"status": "failed", "error_code": "CONTEXT_NOT_FOUND", "answer_id": answer_id}

        # Mark answer and job as running
        jobs = job_repo.get_by_answer_id(answer_id)
        active_job = jobs[0] if jobs else None
        if active_job:
            active_job.attempt_count += 1
            job_repo.update_status(active_job, EvaluationJobStatus.RUNNING)
        answer_repo.update_status(answer, AnswerStatus.IN_PROGRESS)

        try:
            output = llm_service.evaluate_answer(
                role=session_obj.role,
                difficulty=session_obj.difficulty.value,
                question_text=question.question_text,
                answer_text=answer.answer_text,
            )

            eval_result = EvaluationResult(
                answer_id=answer_id,
                score=output.score,
                feedback=output.feedback,
                evaluation_status=EvaluationStatus.COMPLETED,
                strengths=json.dumps(output.strengths),
                improvements=json.dumps(output.improvements),
                rubric_version=rubric_version,
                evaluation_prompt_version=evaluation_prompt_version,
                evaluation_schema_version=settings.evaluation_schema_version,
                model_provider="openrouter",
                model_name=settings.openrouter_model,
                raw_model_response=json.dumps(
                    {"score": output.score, "feedback": output.feedback}
                ),
            )

            # Upsert: only create if no existing record
            if existing_result is None:
                result_repo.create(eval_result)
            else:
                existing_result.score = eval_result.score
                existing_result.feedback = eval_result.feedback
                existing_result.evaluation_status = EvaluationStatus.COMPLETED
                existing_result.strengths = eval_result.strengths
                existing_result.improvements = eval_result.improvements
                db.add(existing_result)
                db.commit()

            answer_repo.update_status(answer, AnswerStatus.COMPLETED)
            if active_job:
                job_repo.update_status(active_job, EvaluationJobStatus.COMPLETED)

            await log_job_end(EVALUATE_ANSWER_JOB, correlation_id, success=True, answer_id=answer_id)
            return {
                "answer_id": answer_id,
                "status": "completed",
                "evaluation_status": "completed",
                "score": output.score,
                "schema_version": settings.evaluation_schema_version,
                "model_name": settings.openrouter_model,
            }

        except Exception as exc:
            error_msg = str(exc)
            logger.error(
                "worker_evaluation_failed",
                answer_id=answer_id,
                correlation_id=correlation_id,
                error=error_msg,
            )
            answer_repo.update_status(answer, AnswerStatus.FAILED)
            if active_job:
                job_repo.update_status(active_job, EvaluationJobStatus.FAILED, last_error=error_msg)

            # Persist failed result for auditability
            if existing_result is None:
                failed_result = EvaluationResult(
                    answer_id=answer_id,
                    evaluation_status=EvaluationStatus.FAILED,
                    rubric_version=rubric_version,
                    evaluation_prompt_version=evaluation_prompt_version,
                    evaluation_schema_version=settings.evaluation_schema_version,
                    model_provider="openrouter",
                    model_name=settings.openrouter_model,
                    raw_model_response=json.dumps({"error": error_msg}),
                )
                result_repo.create(failed_result)

            await log_job_end(
                EVALUATE_ANSWER_JOB, correlation_id, success=False, answer_id=answer_id, error=error_msg
            )
            return {
                "answer_id": answer_id,
                "status": "failed",
                "evaluation_status": "failed",
                "error_code": "EVALUATION_FAILED",
                "error_message": error_msg,
                "attempt_count": active_job.attempt_count if active_job else 1,
            }
