
from sqlmodel import Session

from app.api.utils import NotFoundError
from app.core.config import settings
from app.core.constants import SessionStatus
from app.core.logging import get_logger
from app.models.question import InterviewQuestion
from app.models.session import InterviewSession
from app.repositories.question_repository import QuestionRepository
from app.repositories.session_repository import SessionRepository
from app.services.question_generation_service import generate_questions_for_session

logger = get_logger(__name__)


def create_session(
    db: Session,
    role: str,
    difficulty: str,
    question_count: int,
) -> tuple[InterviewSession, list[InterviewQuestion]]:
    """Create a new interview session with synchronously generated questions.

    Raises LLMError if question generation fails (session is NOT persisted on failure).
    """
    session_repo = SessionRepository(db)
    question_repo = QuestionRepository(db)

    # Generate questions first — do not persist the session if this fails
    generation_result = generate_questions_for_session(
        role=role, difficulty=difficulty, count=question_count
    )

    session_obj = InterviewSession(
        role=role,
        difficulty=difficulty,  # type: ignore[arg-type]
        status=SessionStatus.READY,
        question_count=len(generation_result.questions),
    )
    session_obj = session_repo.create(session_obj)

    questions: list[InterviewQuestion] = []
    for idx, q in enumerate(generation_result.questions, start=1):
        question = InterviewQuestion(
            session_id=session_obj.id,  # type: ignore[arg-type]
            sequence_number=idx,
            question_text=q.text,
            question_type=q.type,
            generation_prompt_version=settings.question_prompt_version,
        )
        questions.append(question)

    questions = question_repo.create_bulk(questions)
    logger.info("session_created", session_id=session_obj.id, question_count=len(questions))
    return session_obj, questions


def get_session_with_questions(
    db: Session,
    session_id: int,
) -> tuple[InterviewSession, list[InterviewQuestion]]:
    """Fetch a session by ID with its ordered questions."""
    session_repo = SessionRepository(db)
    question_repo = QuestionRepository(db)

    session_obj = session_repo.get_by_id(session_id)
    if session_obj is None:
        raise NotFoundError(f"Session {session_id} not found")

    questions = question_repo.get_by_session_id(session_id)
    return session_obj, questions


def get_session_summary(db: Session, session_id: int) -> dict:  # type: ignore[type-arg]
    """Build a full session summary: session + questions + answers + evaluation results."""
    from app.api.schemas.answer import AnswerResultResponse
    from app.api.schemas.evaluation import (
        QuestionOutMin,
        QuestionWithAnswers,
        SessionSummaryResponse,
    )
    from app.repositories.answer_repository import AnswerRepository
    from app.repositories.evaluation_result_repository import EvaluationResultRepository
    from app.services.evaluation_service import _build_evaluation_out

    session_repo = SessionRepository(db)
    question_repo = QuestionRepository(db)
    answer_repo = AnswerRepository(db)
    result_repo = EvaluationResultRepository(db)

    session_obj = session_repo.get_by_id(session_id)
    if session_obj is None:
        raise NotFoundError(f"Session {session_id} not found")

    questions = question_repo.get_by_session_id(session_id)
    all_answers = answer_repo.get_by_session_id(session_id)
    answers_by_question: dict[int, list] = {}
    for a in all_answers:
        answers_by_question.setdefault(a.question_id, []).append(a)

    question_entries = []
    for q in questions:
        q_answers = answers_by_question.get(q.id, [])               #type: ignore[union-attr]
        answer_outs = []
        for a in q_answers:
            result = result_repo.get_by_answer_id(a.id)  # type: ignore[arg-type]
            answer_outs.append(
                AnswerResultResponse(
                    answerId=a.id,  # type: ignore[arg-type]
                    sessionId=a.session_id,
                    questionId=a.question_id,
                    answerText=a.answer_text,
                    status=a.status,
                    evaluation=_build_evaluation_out(result),
                )
            )
        question_entries.append(
            QuestionWithAnswers(
                question=QuestionOutMin(
                    questionId=q.id,  # type: ignore[arg-type]
                    sequenceNumber=q.sequence_number,
                    text=q.question_text,
                    type=q.question_type,
                ),
                answers=answer_outs,
            )
        )

    return SessionSummaryResponse(
        sessionId=session_obj.id,  # type: ignore[arg-type]
        role=session_obj.role,
        difficulty=session_obj.difficulty.value,
        status=session_obj.status.value,
        questions=question_entries,
    )
