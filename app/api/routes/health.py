from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlmodel import Session, text

from app.core.database import get_session

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(db: Session = Depends(get_session)) -> JSONResponse:
    checks: dict = {"status": "healthy", "version": "0.1.0"}  # type: ignore[type-arg]

    try:
        db.exec(text("SELECT 1"))  # type: ignore[call-overload]
        checks["database"] = "healthy"
    except Exception as exc:
        checks["database"] = f"unhealthy: {exc}"
        checks["status"] = "degraded"

    # Check ARQ/Redis availability from app state
    try:
        from app.main import app as _app
        arq_pool = getattr(_app.state, "arq_pool", None)
        if arq_pool is not None:
            await arq_pool.ping()
            checks["redis"] = "healthy"
        else:
            checks["redis"] = "not initialized"
    except Exception as exc:
        checks["redis"] = f"unhealthy: {exc}"
        checks["status"] = "degraded"

    status_code = 200 if checks["status"] == "healthy" else 503
    return JSONResponse(content=checks, status_code=status_code)
