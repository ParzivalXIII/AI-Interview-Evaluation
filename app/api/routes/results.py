from fastapi import APIRouter

from app.api.dependencies import SessionDep
from app.api.schemas.answer import AnswerResultResponse
from app.api.schemas.evaluation import SessionSummaryResponse
from app.services import evaluation_service, interview_service

router = APIRouter()


@router.get(
    "/{session_id}/answers/{answer_id}",
    response_model=AnswerResultResponse,
)
async def get_answer_result(
    session_id: int,
    answer_id: int,
    db: SessionDep,
) -> AnswerResultResponse:
    return evaluation_service.get_answer_result(
        db=db, session_id=session_id, answer_id=answer_id
    )


@router.get(
    "/{session_id}/summary",
    response_model=SessionSummaryResponse,
)
async def get_session_summary(
    session_id: int,
    db: SessionDep,
) -> SessionSummaryResponse:
    return interview_service.get_session_summary(db=db, session_id=session_id)          # type: ignore[return-value]
