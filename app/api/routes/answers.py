from fastapi import APIRouter, status

from app.api.dependencies import ArqPoolDep, SessionDep
from app.api.schemas.answer import AnswerAcceptedResponse, SubmitAnswerRequest
from app.services import answer_service, evaluation_service

router = APIRouter()


@router.post(
    "/{session_id}/answers",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=AnswerAcceptedResponse,
)
async def submit_answer(
    session_id: int,
    body: SubmitAnswerRequest,
    db: SessionDep,
    arq_pool: ArqPoolDep,
) -> AnswerAcceptedResponse:
    answer = answer_service.submit_answer(
        db=db,
        session_id=session_id,
        question_id=body.question_id,
        answer_text=body.answer_text,
    )
    evaluation_service.enqueue_evaluation(db=db, answer=answer, arq_pool=arq_pool)
    return AnswerAcceptedResponse(
        answerId=answer.id,  # type: ignore[arg-type]
        sessionId=answer.session_id,
        questionId=answer.question_id,
        status=answer.status,
    )
