from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base application exception."""

    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class NotFoundError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, error_code="NOT_FOUND")


class ValidationError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, error_code="VALIDATION_ERROR")


class ConflictError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, error_code="CONFLICT")


class LLMError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, error_code="LLM_ERROR")


def error_response(code: str, message: str) -> dict:  # type: ignore[type-arg]
    return {"code": code, "message": message}


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    status_map = {
        "NOT_FOUND": 404,
        "VALIDATION_ERROR": 400,
        "CONFLICT": 409,
        "LLM_ERROR": 502,
    }
    status_code = status_map.get(exc.error_code, 500)
    return JSONResponse(
        status_code=status_code,
        content=error_response(exc.error_code, exc.message),
    )
