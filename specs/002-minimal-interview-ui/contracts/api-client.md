# API Client Contract: Minimal Interview UI

**Phase**: 1 | **Date**: 2026-03-15 | **Plan**: [plan.md](../plan.md)

This document defines the HTTP API contract that the Gradio UI (`interview-ui/client.py`) consumes from the existing FastAPI backend. The UI does not expose any new endpoints and does not modify the backend contract. All endpoint definitions below are read-only references to the existing backend schema.

---

## Base URL

Configured via the `BACKEND_URL` environment variable.

| Environment | Default value |
|-------------|---------------|
| Local development | `http://localhost:8000` |
| Docker Compose | `http://api:8000` (internal `app-network`) |

---

## Endpoints Used

### 1. Create Interview Session

**Used by**: Start Interview button handler

```
POST {BACKEND_URL}/sessions
Content-Type: application/json

Request body:
{
  "role": string,         // e.g. "Backend Engineer" — min 1 char
  "difficulty": string,   // "junior" | "mid" | "senior"
  "questionCount": int    // 1–10 (default 5)
}

Response 201 Created:
{
  "sessionId": int,
  "status": "ready",
  "questions": [
    {
      "questionId": int,
      "sequenceNumber": int,
      "text": string,
      "type": string | null  // "coding" | "system_design" | "behavioral_technical"
    }
  ]
}

Error cases handled by UI:
  - 422 Unprocessable Entity  → display validation error on start form
  - 500 Internal Server Error → display generic "Failed to create session" error
  - Network timeout / connect error → display connection error banner
```

---

### 2. Submit Answer

**Used by**: Submit Answer button handler

```
POST {BACKEND_URL}/sessions/{session_id}/answers
Content-Type: application/json

Path parameters:
  session_id: int

Request body:
{
  "questionId": int,
  "answerText": string  // min 1 char
}

Response 202 Accepted:
{
  "answerId": int,
  "sessionId": int,
  "questionId": int,
  "status": "pending_evaluation"
}

Error cases handled by UI:
  - 404 Not Found          → session or question not found; show error, preserve answer text
  - 422 Unprocessable Entity → validation error; preserve answer text
  - 5xx                   → show retry option; preserve answer text
```

---

### 3. Get Answer Result (Polling Endpoint)

**Used by**: `gr.Timer` tick handler (every 5 seconds)

```
GET {BACKEND_URL}/sessions/{session_id}/answers/{answer_id}

Path parameters:
  session_id: int
  answer_id: int

Response 200 OK:
{
  "answerId": int,
  "sessionId": int,
  "questionId": int,
  "answerText": string,
  "status": "pending_evaluation" | "in_progress" | "completed" | "failed",
  "evaluation": {
    "evaluationStatus": "completed" | "failed",
    "score": float | null,          // 0.0–10.0
    "feedback": string | null,
    "strengths": string[],
    "improvements": string[],
    "schemaVersion": string,
    "rubricVersion": string,
    "promptVersion": string,
    "modelName": string
  } | null,
  "failureReason": string | null
}

Polling termination condition (UI stops polling this answer when):
  - status == "completed"
  - status == "failed"
```

---

### 4. Get Session Summary (End of Session)

**Used by**: End-of-session summary view (optional render when all questions answered)

```
GET {BACKEND_URL}/sessions/{session_id}/summary

Path parameters:
  session_id: int

Response 200 OK:
{
  "sessionId": int,
  "role": string,
  "difficulty": string,
  "status": string,
  "questions": [
    {
      "question": {
        "questionId": int,
        "sequenceNumber": int,
        "text": string,
        "type": string | null
      },
      "answers": [AnswerResultResponse]  // same shape as endpoint #3
    }
  ]
}
```

---

## Client Module Contract (`interview-ui/client.py`)

The `client.py` module exposes the following async functions. These are the only functions that call `httpx`. All other UI code uses these functions and never calls httpx directly.

```python
class InterviewAPIClient:
    """Thin async httpx wrapper for the FastAPI interview backend."""

    async def create_session(
        self,
        role: str,
        difficulty: str,
        question_count: int,
    ) -> SessionCreatedData:
        """POST /sessions → returns SessionCreatedData or raises APIError."""

    async def submit_answer(
        self,
        session_id: int,
        question_id: int,
        answer_text: str,
    ) -> AnswerAcceptedData:
        """POST /sessions/{session_id}/answers → returns AnswerAcceptedData or raises APIError."""

    async def get_answer_result(
        self,
        session_id: int,
        answer_id: int,
    ) -> AnswerResultData:
        """GET /sessions/{session_id}/answers/{answer_id} → returns AnswerResultData or raises APIError."""

    async def get_session_summary(
        self,
        session_id: int,
    ) -> SessionSummaryData:
        """GET /sessions/{session_id}/summary → returns SessionSummaryData or raises APIError."""
```

**Error contract**: All methods raise `APIError(message: str, status_code: int | None)` on any non-success response or network failure. Callers in `app.py` catch `APIError` and render the message to the appropriate UI component.

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BACKEND_URL` | Yes | `http://localhost:8000` | Base URL of the FastAPI backend |
| `UI_PORT` | No | `7860` | Port on which the Gradio server listens |
| `UI_HOST` | No | `0.0.0.0` | Host binding for Gradio server |
