"""HTTP client for the FastAPI interview backend.

All backend calls go through InterviewAPIClient.
All methods raise APIError on non-2xx responses or network failures.
A module-level ``client`` singleton is shared across Gradio event handlers.
"""
from __future__ import annotations

import os
from typing import Any, TypedDict

import httpx
from state import EvaluationData, QuestionData

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000")

# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class APIError(Exception):
    """Raised when the backend returns a non-2xx response or a network error."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


# ---------------------------------------------------------------------------
# Response TypedDicts (shapes returned by client methods)
# ---------------------------------------------------------------------------


class SessionCreatedData(TypedDict):
    session_id: int
    status: str
    questions: list[QuestionData]


class AnswerAcceptedData(TypedDict):
    answer_id: int
    session_id: int
    question_id: int
    status: str


class AnswerResultData(TypedDict):
    answer_id: int
    session_id: int
    question_id: int
    answer_text: str
    status: str
    evaluation: EvaluationData | None
    failure_reason: str | None


class SessionSummaryData(TypedDict):
    session_id: int
    role: str
    difficulty: str
    status: str
    questions: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class InterviewAPIClient:
    """Thin async httpx wrapper for the FastAPI interview backend."""

    def __init__(self, http_client: httpx.AsyncClient | None = None) -> None:
        # Accepts an optional pre-built client (useful in tests).
        self._http = http_client

    async def _get_http(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(base_url=BACKEND_URL, timeout=30.0)
        return self._http

    async def _check_response(self, response: httpx.Response) -> None:
        if response.is_success:
            return
        try:
            detail = response.json().get("detail", response.text)
        except Exception:
            detail = response.text or f"HTTP {response.status_code}"
        raise APIError(str(detail), status_code=response.status_code)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    async def create_session(
        self,
        role: str,
        difficulty: str,
        question_count: int,
    ) -> SessionCreatedData:
        """POST /sessions → SessionCreatedData or raises APIError."""
        http = await self._get_http()
        try:
            resp = await http.post(
                "/sessions",
                json={
                    "role": role,
                    "difficulty": difficulty,
                    "questionCount": question_count,
                },
            )
        except httpx.RequestError as exc:
            raise APIError(f"Connection error: {exc}", status_code=None) from exc
        await self._check_response(resp)
        data = resp.json()
        return SessionCreatedData(
            session_id=data["sessionId"],
            status=data["status"],
            questions=[
                QuestionData(
                    question_id=q["questionId"],
                    sequence_number=q["sequenceNumber"],
                    text=q["text"],
                    type=q.get("type"),
                )
                for q in data.get("questions", [])
            ],
        )

    async def submit_answer(
        self,
        session_id: int,
        question_id: int,
        answer_text: str,
    ) -> AnswerAcceptedData:
        """POST /sessions/{session_id}/answers → AnswerAcceptedData or raises APIError."""
        http = await self._get_http()
        try:
            resp = await http.post(
                f"/sessions/{session_id}/answers",
                json={"questionId": question_id, "answerText": answer_text},
            )
        except httpx.RequestError as exc:
            raise APIError(f"Connection error: {exc}", status_code=None) from exc
        await self._check_response(resp)
        data = resp.json()
        return AnswerAcceptedData(
            answer_id=data["answerId"],
            session_id=data["sessionId"],
            question_id=data["questionId"],
            status=data["status"],
        )

    async def get_answer_result(
        self,
        session_id: int,
        answer_id: int,
    ) -> AnswerResultData:
        """GET /sessions/{session_id}/answers/{answer_id} → AnswerResultData or raises APIError."""
        http = await self._get_http()
        try:
            resp = await http.get(f"/sessions/{session_id}/answers/{answer_id}")
        except httpx.RequestError as exc:
            raise APIError(f"Connection error: {exc}", status_code=None) from exc
        await self._check_response(resp)
        data = resp.json()
        evaluation: EvaluationData | None = None
        if data.get("evaluation"):
            ev = data["evaluation"]
            evaluation = EvaluationData(
                evaluation_status=ev.get("evaluationStatus", ""),
                score=ev.get("score"),
                feedback=ev.get("feedback"),
                strengths=ev.get("strengths") or [],
                improvements=ev.get("improvements") or [],
                schema_version=ev.get("schemaVersion", ""),
                rubric_version=ev.get("rubricVersion", ""),
                prompt_version=ev.get("promptVersion", ""),
                model_name=ev.get("modelName", ""),
            )
        return AnswerResultData(
            answer_id=data["answerId"],
            session_id=data["sessionId"],
            question_id=data["questionId"],
            answer_text=data.get("answerText", ""),
            status=data["status"],
            evaluation=evaluation,
            failure_reason=data.get("failureReason"),
        )

    async def get_session_summary(
        self,
        session_id: int,
    ) -> SessionSummaryData:
        """GET /sessions/{session_id}/summary → SessionSummaryData or raises APIError."""
        http = await self._get_http()
        try:
            resp = await http.get(f"/sessions/{session_id}/summary")
        except httpx.RequestError as exc:
            raise APIError(f"Connection error: {exc}", status_code=None) from exc
        await self._check_response(resp)
        data = resp.json()
        return SessionSummaryData(
            session_id=data["sessionId"],
            role=data["role"],
            difficulty=data["difficulty"],
            status=data["status"],
            questions=data.get("questions", []),
        )


# ---------------------------------------------------------------------------
# Module-level singleton shared across all Gradio event handlers
# ---------------------------------------------------------------------------

client = InterviewAPIClient()
