import json

from langchain_openai import ChatOpenAI

from app.contracts.evaluation_schema import EvaluationOutput
from app.contracts.prompts import (
    evaluation_prompt,
    question_generation_prompt,
)
from app.contracts.question_generation_schema import QuestionGenerationOutput
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _make_llm(timeout: int) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openrouter_model,
        api_key=settings.openrouter_api_key,  # type: ignore[arg-type]
        base_url=settings.openrouter_base_url,
        timeout=timeout,
        max_retries=2,
    )


def generate_questions(
    role: str,
    difficulty: str,
    count: int,
) -> QuestionGenerationOutput:
    """Call the LLM synchronously to generate interview questions.

    Returns a validated QuestionGenerationOutput.
    Raises LLMError on failure.
    """
    from app.api.utils import LLMError

    llm = _make_llm(settings.question_generation_timeout)
    chain = question_generation_prompt | llm
    try:
        result = chain.invoke({"role": role, "difficulty": difficulty, "count": count})
        raw = result.content if hasattr(result, "content") else str(result)
        data = json.loads(raw)          # type: ignore[assignment]
        return QuestionGenerationOutput.model_validate(data)
    except Exception as exc:
        logger.error("question_generation_failed", role=role, difficulty=difficulty, error=str(exc))
        raise LLMError(f"Question generation failed: {exc}") from exc


def evaluate_answer(
    role: str,
    difficulty: str,
    question_text: str,
    answer_text: str,
) -> EvaluationOutput:
    """Call the LLM to evaluate a candidate answer.

    Returns a validated EvaluationOutput.
    Raises LLMError on failure.
    """
    from app.api.utils import LLMError

    llm = _make_llm(settings.evaluation_timeout)
    chain = evaluation_prompt | llm
    try:
        result = chain.invoke(
            {
                "role": role,
                "difficulty": difficulty,
                "question_text": question_text,
                "answer_text": answer_text,
            }
        )
        raw = result.content if hasattr(result, "content") else str(result)
        data = json.loads(raw)              # type: ignore[assignment]
        return EvaluationOutput.model_validate(data)
    except Exception as exc:
        logger.error("answer_evaluation_failed", question=question_text[:80], error=str(exc))
        raise LLMError(f"Answer evaluation failed: {exc}") from exc
