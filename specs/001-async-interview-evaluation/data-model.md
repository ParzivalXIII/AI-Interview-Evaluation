# Phase 1 Data Model: Async Interview Evaluation Engine

## Overview

The feature requires five core persisted entities. The model preserves interview state, asynchronous processing state, and evaluation provenance needed for later analysis and debugging.

## Entities

### InterviewSession

**Purpose**: Represents one interview run for a candidate workflow.

**Fields**:

- `id`: UUID or integer primary identifier
- `role`: normalized target role label
- `difficulty`: normalized difficulty value
- `status`: `ready | failed | completed`
- `question_count`: number of generated questions
- `created_at`: timestamp
- `updated_at`: timestamp
- `failure_reason`: optional text for generation failure

**Validation Rules**:

- `role` is required and non-empty.
- `difficulty` must be one of the supported difficulty values.
- `question_count` cannot be negative.
- `failure_reason` is only populated when `status = failed`.

**Relationships**:

- One `InterviewSession` has many `InterviewQuestion` records.
- One `InterviewSession` has many `CandidateAnswer` records through questions.
- One `InterviewSession` can be summarized from its related `EvaluationResult` records.

**State Transitions**:

- Session is created directly in `ready` when synchronous question generation succeeds.
- Session creation fails instead of persisting a usable session when question generation produces unusable output.
- `ready -> completed` when the session reaches a terminal business condition defined by application logic.

### InterviewQuestion

**Purpose**: Represents one generated interview prompt within a session.

**Fields**:

- `id`: primary identifier
- `session_id`: foreign key to `InterviewSession`
- `sequence_number`: positive integer preserving question order
- `question_text`: generated question content
- `question_type`: optional label such as coding, system design, or behavioral-technical
- `generation_prompt_version`: prompt version used to produce the question
- `created_at`: timestamp

**Validation Rules**:

- `question_text` is required and non-empty.
- `sequence_number` must be unique within a session.
- `generation_prompt_version` is required for auditability.

**Relationships**:

- Many `InterviewQuestion` records belong to one `InterviewSession`.
- One `InterviewQuestion` can have many `CandidateAnswer` submissions if resubmission is allowed.

### CandidateAnswer

**Purpose**: Stores a submitted answer for a specific question.

**Fields**:

- `id`: primary identifier
- `session_id`: foreign key to `InterviewSession`
- `question_id`: foreign key to `InterviewQuestion`
- `submission_index`: positive integer for deterministic ordering of resubmissions
- `answer_text`: submitted answer content
- `status`: `pending_evaluation | in_progress | completed | failed`
- `submitted_at`: timestamp
- `updated_at`: timestamp
- `idempotency_key`: stable hash or token representing this submission payload

**Validation Rules**:

- `question_id` must belong to the provided `session_id`.
- `answer_text` is required and non-empty.
- `submission_index` increments monotonically within `(session_id, question_id)`.
- `idempotency_key` must be unique for exact duplicate submissions.

**Relationships**:

- Many `CandidateAnswer` records belong to one `InterviewSession`.
- Many `CandidateAnswer` records belong to one `InterviewQuestion`.
- One `CandidateAnswer` has one current `EvaluationJob` and zero or one completed `EvaluationResult` in the MVP model.

**State Transitions**:

- `pending_evaluation -> in_progress` when a worker begins processing.
- `in_progress -> completed` when a valid structured evaluation result is persisted.
- `in_progress -> failed` when retries are exhausted or output remains invalid.

### EvaluationJob

**Purpose**: Tracks asynchronous processing for answer evaluation.

**Fields**:

- `id`: primary identifier
- `answer_id`: foreign key to `CandidateAnswer`
- `job_type`: `answer_evaluation`
- `status`: `queued | running | completed | failed`
- `queue_name`: logical queue or worker group
- `attempt_count`: integer retry count
- `correlation_id`: request-to-worker trace identifier
- `last_error`: optional failure summary
- `queued_at`: timestamp
- `started_at`: optional timestamp
- `finished_at`: optional timestamp

**Validation Rules**:

- `attempt_count` cannot be negative.
- `finished_at` cannot precede `started_at`.
- `last_error` is only populated for non-success terminal states.

**Relationships**:

- One `EvaluationJob` belongs to one `CandidateAnswer` in the answer evaluation path.

### EvaluationResult

**Purpose**: Stores the structured assessment outcome for one answer.

**Fields**:

- `id`: primary identifier
- `answer_id`: foreign key to `CandidateAnswer`
- `score`: numeric score in configured range
- `feedback`: structured written feedback for the candidate answer
- `evaluation_status`: `completed | failed | incomplete`
- `strengths`: optional list or structured text
- `improvements`: optional list or structured text
- `rubric_version`: rubric version string
- `evaluation_prompt_version`: prompt version string
- `evaluation_schema_version`: result schema version string
- `model_provider`: provider label
- `model_name`: model identifier
- `raw_model_response`: stored raw output for debugging and audit
- `created_at`: timestamp

**Validation Rules**:

- `score` is required when `evaluation_status = completed`.
- `feedback` is required for completed evaluations.
- `rubric_version`, `evaluation_prompt_version`, and `evaluation_schema_version` are required.
- `raw_model_response` must be retained for failed parse or incomplete cases.

**Relationships**:

- One `EvaluationResult` belongs to one `CandidateAnswer`.

## Cross-Entity Rules

- A question cannot exist without a parent session.
- An answer cannot be accepted for a session until the session is `ready`.
- A result cannot be marked `completed` unless the related answer is in a terminal success state.
- Session summaries are assembled from questions, answers, and results rather than stored separately in the initial version.

## Recommended Indexes

- `InterviewSession(status, created_at)`
- `InterviewQuestion(session_id, sequence_number)` unique
- `CandidateAnswer(session_id, question_id, submission_index)` unique
- `CandidateAnswer(idempotency_key)` unique
- `CandidateAnswer(status, submitted_at)`
- `EvaluationJob(status, queued_at)`
- `EvaluationResult(answer_id)` unique