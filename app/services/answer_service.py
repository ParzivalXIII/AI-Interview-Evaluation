
from sqlmodel import Session

from app.api.utils import ConflictError, NotFoundError, ValidationError
from app.core.constants import AnswerStatus
from app.core.logging import get_logger
from app.models.answer import CandidateAnswer
from app.repositories.answer_repository import AnswerRepository
from app.repositories.question_repository import QuestionRepository
from app.repositories.session_repository import SessionRepository

logger = get_logger(__name__)


def submit_answer(
    db: Session,
    session_id: int,
    question_id: int,
    answer_text: str,
) -> CandidateAnswer:
    """Validate and persist a candidate answer.

    Returns the saved CandidateAnswer or raises on validation/conflict errors.
    """
    session_repo = SessionRepository(db)
    question_repo = QuestionRepository(db)
    answer_repo = AnswerRepository(db)

    # Validate session exists
    session_obj = session_repo.get_by_id(session_id)
    if session_obj is None:
        raise NotFoundError(f"Session {session_id} not found")

    # Validate question belongs to session
    question = question_repo.get_by_id_and_session(question_id, session_id)
    if question is None:
        raise NotFoundError(f"Question {question_id} not found in session {session_id}")

    if not answer_text.strip():
        raise ValidationError("Answer text must not be empty")

    # Compute idempotency key and check for duplicate
    idem_key = AnswerRepository.build_idempotency_key(session_id, question_id, answer_text)
    existing = answer_repo.get_by_idempotency_key(idem_key)
    if existing is not None:
        raise ConflictError(
            f"Duplicate answer submission for question {question_id}. "
            f"Use answerId={existing.id} to track evaluation."
        )

    # Determine submission_index
    prior = answer_repo.get_by_session_and_question(session_id, question_id)
    submission_index = len(prior) + 1

    answer = CandidateAnswer(
        session_id=session_id,
        question_id=question_id,
        submission_index=submission_index,
        answer_text=answer_text,
        status=AnswerStatus.PENDING_EVALUATION,
        idempotency_key=idem_key,
    )
    answer = answer_repo.create(answer)
    logger.info("answer_submitted", answer_id=answer.id, session_id=session_id)
    return answer
