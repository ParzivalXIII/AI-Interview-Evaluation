from typing import Annotated

from arq.connections import ArqRedis
from fastapi import Depends
from sqlmodel import Session

from app.core.database import get_session

SessionDep = Annotated[Session, Depends(get_session)]


async def get_arq_pool_dep() -> ArqRedis:
    """FastAPI dependency that provides an ARQ Redis pool.

    The pool is created lazily; in production the app lifespan stores it on
    app.state and this dep retrieves it.  Declared here for easy override in
    tests.
    """
    from app.main import app  # lazy import to avoid circular

    pool: ArqRedis = app.state.arq_pool
    return pool


ArqPoolDep = Annotated[ArqRedis, Depends(get_arq_pool_dep)]
