from fastapi import APIRouter, status

from app.api.dependencies import SessionDep
from app.api.schemas.session import (
    CreateSessionRequest,
    QuestionOut,
    SessionCreatedResponse,
    SessionDetailResponse,
)
from app.models.question import InterviewQuestion
from app.services import interview_service

router = APIRouter()


def _to_question_out(q: InterviewQuestion) -> QuestionOut:
    return QuestionOut(
        questionId=q.id,  # type: ignore[arg-type]
        sequenceNumber=q.sequence_number,
        text=q.question_text,
        type=q.question_type,
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=SessionCreatedResponse)
async def create_session(
    body: CreateSessionRequest,
    db: SessionDep,
) -> SessionCreatedResponse:
    session_obj, questions = interview_service.create_session(
        db=db,
        role=body.role,
        difficulty=body.difficulty.value,
        question_count=body.question_count,
    )
    return SessionCreatedResponse(
        sessionId=session_obj.id,  # type: ignore[arg-type]
        status=session_obj.status,
        questions=[_to_question_out(q) for q in questions],
    )


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: int,
    db: SessionDep,
) -> SessionDetailResponse:
    session_obj, questions = interview_service.get_session_with_questions(db=db, session_id=session_id)
    return SessionDetailResponse(
        sessionId=session_obj.id,  # type: ignore[arg-type]
        role=session_obj.role,
        difficulty=session_obj.difficulty,
        status=session_obj.status,
        questions=[_to_question_out(q) for q in questions],
        failureReason=session_obj.failure_reason,
    )
