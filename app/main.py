from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.utils import AppError, app_error_handler
from app.core.logging import configure_logging
from app.core.queue import get_arq_pool


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging()
    application.state.arq_pool = await get_arq_pool()
    yield
    await application.state.arq_pool.close()


app = FastAPI(
    title="AI Interview Evaluation API",
    version="0.1.0",
    description="Async interview session management and LLM-powered answer evaluation.",
    lifespan=lifespan,
)

app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]

# Register routers
from app.api.routes import health, sessions, answers, results  # noqa: E402

app.include_router(health.router)
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(answers.router, prefix="/sessions", tags=["answers"])
app.include_router(results.router, prefix="/sessions", tags=["results"])
