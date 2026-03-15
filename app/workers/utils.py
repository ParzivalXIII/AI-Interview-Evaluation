from app.core.logging import get_logger

logger = get_logger(__name__)

EVALUATE_ANSWER_JOB = "evaluate_candidate_answer"


async def log_job_start(job_name: str, correlation_id: str, **kwargs: object) -> None:
    logger.info("job_started", job=job_name, correlation_id=correlation_id, **kwargs)


async def log_job_end(
    job_name: str, correlation_id: str, success: bool, **kwargs: object
) -> None:
    level = "info" if success else "error"
    getattr(logger, level)(
        "job_finished", job=job_name, correlation_id=correlation_id, success=success, **kwargs
    )
