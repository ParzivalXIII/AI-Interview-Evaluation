# Data Model: Minimal Interview UI

**Phase**: 1 | **Date**: 2026-03-15 | **Plan**: [plan.md](./plan.md)

The UI introduces **no new database tables**. All persistence remains in the existing PostgreSQL schema owned by the FastAPI backend. This document captures the **client-side state model** — the in-memory structures that the Gradio app holds in `gr.State` during an active browser session.

---

## 1. Client-Side State Overview

All UI state is held in a single `gr.State` component and managed by the functions in `state.py`. The state is plain Python `TypedDict`-derived structures (serialised as `dict` for Gradio's internal serialiser).

```
SessionState
│
├── session_id: int | None           ←  None until POST /sessions succeeds
├── role: str                        ←  captured from start form
├── difficulty: str                  ←  "junior" | "mid" | "senior"
├── questions: list[QuestionData]    ←  ordered list from API response
├── current_idx: int                 ←  0-based index of displayed question
└── answers: dict[int, AnswerData]   ←  keyed by question_id (int)
```

---

## 2. Entity Definitions

### 2.1 SessionState

Represents the full live state of one interview session in one browser tab.

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | `int \| None` | Backend-assigned session identifier; `None` before session is created |
| `role` | `str` | Interview role entered by the user (e.g., "Backend Engineer") |
| `difficulty` | `str` | One of `"junior"`, `"mid"`, `"senior"` |
| `questions` | `list[QuestionData]` | Ordered list of questions returned by `POST /sessions` |
| `current_idx` | `int` | Index into `questions` for the currently displayed question (0-based) |
| `answers` | `dict[int, AnswerData]` | Map of `question_id → AnswerData` for all submitted answers |

**Initial value** (empty state before any session is started):
```python
{"session_id": None, "role": "", "difficulty": "mid", "questions": [], "current_idx": 0, "answers": {}}
```

---

### 2.2 QuestionData

A single question as returned by the backend and stored locally. Read-only after session creation.

| Field | Type | Description |
|-------|------|-------------|
| `question_id` | `int` | Backend-assigned question identifier |
| `sequence_number` | `int` | 1-based display order within the session |
| `text` | `str` | Full question text to render |
| `type` | `str \| None` | Question type tag (e.g., `"coding"`, `"system_design"`, `"behavioral_technical"`) |

**Source**: `questions[]` array in `POST /sessions` response (`SessionCreatedResponse`).

---

### 2.3 AnswerData

Tracks a single submitted answer and its current evaluation lifecycle.

| Field | Type | Description |
|-------|------|-------------|
| `answer_id` | `int` | Backend-assigned answer identifier |
| `question_id` | `int` | Question this answer belongs to |
| `answer_text` | `str` | The text the user submitted |
| `status` | `AnswerStatus` | Current lifecycle status (see below) |
| `evaluation` | `EvaluationData \| None` | Populated once evaluation completes; `None` while pending |
| `failure_reason` | `str \| None` | Backend error text when `status == "failed"` |

**Status values** (mirrors `AnswerStatus` enum from the backend):

| Value | Meaning | UI Representation |
|-------|---------|-------------------|
| `pending_evaluation` | Submitted, job not yet picked up | "Evaluating…" spinner |
| `in_progress` | ARQ worker is running the evaluation | "Evaluating…" spinner |
| `completed` | Evaluation result available | Score card + feedback panel |
| `failed` | Evaluation job failed | Error message with retry instructions |

---

### 2.4 EvaluationData

Stores the evaluation result for a completed answer. Populated from `GET /sessions/{id}/answers/{id}` when `status == "completed"`.

| Field | Type | Description |
|-------|------|-------------|
| `evaluation_status` | `str` | `"completed"` or `"failed"` |
| `score` | `float \| None` | Numeric score (0–10 scale from backend rubric) |
| `feedback` | `str \| None` | Narrative feedback paragraph |
| `strengths` | `list[str]` | Bullet-point list of answer strengths |
| `improvements` | `list[str]` | Bullet-point list of suggested improvements |
| `schema_version` | `str` | Evaluation schema version tag (audit) |
| `rubric_version` | `str` | Rubric version tag (audit) |
| `prompt_version` | `str` | Prompt version tag (audit) |
| `model_name` | `str` | LLM identifier used for this evaluation (audit) |

**Note**: The UI displays `score`, `feedback`, `strengths`, and `improvements` to the user. The version and model fields are stored in `AnswerData` for transparency but rendered only in a collapsed "Details" section to keep the primary view uncluttered.

---

## 3. State Transitions

```
                            ┌──────────────────────────────────────────────┐
                            │              SessionState lifecycle           │
                            └──────────────────────────────────────────────┘

 [No session]
      │
      │  User fills start form + clicks "Start Interview"
      │  → POST /sessions → 201 SessionCreatedResponse
      ▼
 [Session active, current_idx = 0]
      │
      │  User types answer + clicks "Submit"
      │  → POST /sessions/{id}/answers → 202 AnswerAcceptedResponse
      │  → AnswerData{status="pending_evaluation"} added to answers{}
      │  → if questions.length > 1: current_idx advances to next unanswered
      ▼
 [Answer submitted; polling active]
      │
      │  gr.Timer tick (every 5 s)
      │  → GET /sessions/{id}/answers/{answer_id} for each non-terminal answer
      │  → If response.status == "completed": update AnswerData.evaluation
      ▼
 [Evaluation visible to user]
```

---

## 4. Mapping: Backend API Fields → UI State Fields

| Backend field (camelCase) | UI state field (snake_case) | Location |
|--------------------------|---------------------------|----------|
| `sessionId` | `session_id` | `SessionState` |
| `questions[].questionId` | `question_id` | `QuestionData` |
| `questions[].sequenceNumber` | `sequence_number` | `QuestionData` |
| `questions[].text` | `text` | `QuestionData` |
| `questions[].type` | `type` | `QuestionData` |
| `answerId` | `answer_id` | `AnswerData` |
| `status` (answer) | `status` | `AnswerData` |
| `evaluation.score` | `score` | `EvaluationData` |
| `evaluation.feedback` | `feedback` | `EvaluationData` |
| `evaluation.strengths` | `strengths` | `EvaluationData` |
| `evaluation.improvements` | `improvements` | `EvaluationData` |
| `evaluation.evaluationStatus` | `evaluation_status` | `EvaluationData` |
| `evaluation.schemaVersion` | `schema_version` | `EvaluationData` |
| `evaluation.rubricVersion` | `rubric_version` | `EvaluationData` |
| `evaluation.promptVersion` | `prompt_version` | `EvaluationData` |
| `evaluation.modelName` | `model_name` | `EvaluationData` |

---

## 5. What This Model Does Not Include

The following are deliberately excluded from the UI state model:

- **User identity / authentication** — Out of scope per spec.
- **Interview history** — Sessions are transient to the browser tab; no persistence beyond the active session.
- **Question generation parameters beyond role/difficulty/count** — Not exposed.
- **Raw LLM prompt or completion text** — Not surfaced in the UI (backend audit artefacts only).
