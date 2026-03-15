from app.contracts.question_generation_schema import QuestionGenerationOutput
from app.core.config import settings
from app.services import llm_service


def generate_questions_for_session(
    role: str,
    difficulty: str,
    count: int,
) -> QuestionGenerationOutput:
    """Orchestrate synchronous question generation for a new session."""
    actual_count = min(count, settings.max_questions_per_session)
    return llm_service.generate_questions(role=role, difficulty=difficulty, count=actual_count)
