"""Client-side state model for the Gradio interview UI.

All UI state is held in a single gr.State component as plain dicts.
TypedDicts define the expected shape; they serialise transparently via
Gradio's gr.State mechanism.
"""
from __future__ import annotations

from typing import Literal, TypedDict

# ---------------------------------------------------------------------------
# Types
# ---------------------------------------------------------------------------

AnswerStatus = Literal["pending_evaluation", "in_progress", "completed", "failed"]

TERMINAL_STATUSES: frozenset[str] = frozenset({"completed", "failed"})


class EvaluationData(TypedDict):
    evaluation_status: str
    score: float | None
    feedback: str | None
    strengths: list[str]
    improvements: list[str]
    schema_version: str
    rubric_version: str
    prompt_version: str
    model_name: str


class QuestionData(TypedDict):
    question_id: int
    sequence_number: int
    text: str
    type: str | None


class AnswerData(TypedDict):
    answer_id: int
    question_id: int
    answer_text: str
    status: AnswerStatus
    evaluation: EvaluationData | None
    failure_reason: str | None


class SessionState(TypedDict):
    session_id: int | None
    role: str
    difficulty: str
    questions: list[QuestionData]
    current_idx: int
    answers: dict[int, AnswerData]  # keyed by question_id


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EMPTY_SESSION: SessionState = {
    "session_id": None,
    "role": "",
    "difficulty": "mid",
    "questions": [],
    "current_idx": 0,
    "answers": {},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_non_terminal_answer_ids(state: SessionState) -> list[int]:
    """Return answer_ids for all answers not yet in a terminal state."""
    return [
        answer["answer_id"]
        for answer in state["answers"].values()
        if answer["status"] not in TERMINAL_STATUSES
    ]


def get_next_unanswered_idx(state: SessionState) -> int | None:
    """Return the 0-based index of the first question without a submitted answer.

    Returns None when every question has been answered.
    """
    answered_ids = set(state["answers"].keys())
    for idx, question in enumerate(state["questions"]):
        if question["question_id"] not in answered_ids:
            return idx
    return None


def all_answers_terminal(state: SessionState) -> bool:
    """Return True when every question has an answer in a terminal state."""
    questions = state["questions"]
    if not questions:
        return False
    answers = state["answers"]
    return all(
        answers.get(q["question_id"], {}).get("status") in TERMINAL_STATUSES
        for q in questions
    )
