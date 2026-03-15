from arq.connections import RedisSettings

from app.core.logging import configure_logging
from app.core.queue import get_redis_settings
from app.workers.evaluation import evaluate_candidate_answer


async def startup(ctx: dict) -> None:  # type: ignore[type-arg]
    configure_logging()


async def shutdown(ctx: dict) -> None:  # type: ignore[type-arg]
    pass


class WorkerSettings:
    functions = [evaluate_candidate_answer]
    redis_settings: RedisSettings = get_redis_settings()
    on_startup = startup
    on_shutdown = shutdown
    max_jobs = 10
    job_timeout = 120
    max_tries = 3
    keep_result = 3600  # keep result for 1 hour
