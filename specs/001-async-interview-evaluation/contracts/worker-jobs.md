# Worker Job Contracts

## Purpose

Define the internal payload contracts for ARQ workers so API producers and worker consumers share stable expectations.

## Answer Evaluation Job

**Job Name**: `evaluate_candidate_answer`

**Payload**:

```json
{
  "answer_id": "string",
  "session_id": "string",
  "question_id": "string",
  "idempotency_key": "string",
  "correlation_id": "string",
  "evaluation_prompt_version": "string",
  "rubric_version": "string"
}
```

**Success Result**:

```json
{
  "answer_id": "string",
  "status": "completed",
  "evaluation_status": "completed",
  "score": 8.5,
  "schema_version": "string",
  "model_name": "string"
}
```

**Failure Result**:

```json
{
  "answer_id": "string",
  "status": "failed",
  "evaluation_status": "failed",
  "error_code": "string",
  "error_message": "string",
  "attempt_count": 3
}
```

## Contract Rules

- Producers must include a `correlation_id` in every job payload.
- Consumers must treat repeated payloads with the same `idempotency_key` as safe retries.
- Workers must persist terminal state changes in PostgreSQL even when a job fails.
- Worker success contracts must map back to the API-visible status model without translation ambiguity.
- Question generation is intentionally out of scope for ARQ in this feature and is executed during synchronous session creation.