# Phase 0 Research: Async Interview Evaluation Engine

## Decision 1: Keep question generation synchronous and answer evaluation asynchronous

- **Decision**: Generate questions during session creation and queue only answer evaluation in Redis-backed ARQ workers.
- **Rationale**: The approved spec requires session creation to return generated questions directly, while answer evaluation is explicitly asynchronous. This split preserves the user-facing session workflow and still protects answer submission latency from slow evaluation calls.
- **Alternatives considered**: Making both flows asynchronous was rejected because it conflicts with the approved session-creation behavior in the spec.

## Decision 2: Use a dedicated evaluation worker flow

- **Decision**: Model answer evaluation as its own job type with dedicated worker logic and retry behavior.
- **Rationale**: Evaluation is the only asynchronous flow in scope, and it has the highest latency and cost profile. Keeping it isolated improves observability and scaling without introducing an unnecessary second background pipeline.
- **Alternatives considered**: A generic worker flow for multiple job types was rejected because it adds complexity without current need.

## Decision 3: Persist interview lifecycle state in PostgreSQL using SQLModel

- **Decision**: Store interview sessions, generated questions, candidate answers, evaluation jobs, and evaluation results in PostgreSQL with SQLModel models and explicit migrations.
- **Rationale**: The feature requires durable state, auditability, relational integrity, and later analysis. PostgreSQL fits those needs, and SQLModel keeps model and schema work aligned with FastAPI-style validation.
- **Alternatives considered**: File-backed storage or ephemeral in-memory state was rejected because it cannot satisfy persistence, traceability, or historical retrieval requirements.

## Decision 4: Keep LLM access behind a dedicated service abstraction

- **Decision**: Isolate LangChain and OpenRouter interaction inside a dedicated LLM service consumed by orchestration services and workers.
- **Rationale**: This keeps provider-specific behavior out of the domain layer, allows consistent timeout and error handling, and makes unit testing possible with mocked structured responses.
- **Alternatives considered**: Direct model calls inside routes or worker functions were rejected because they scatter provider configuration and reduce testability.

## Decision 5: Require structured output validation at the AI boundary

- **Decision**: Treat question generation and evaluation outputs as schema-validated structured results rather than free-form text.
- **Rationale**: The constitution requires traceable, auditable outcomes. Validating structure at the boundary reduces downstream parsing risk and makes scoring results stable for clients and historical analysis.
- **Alternatives considered**: Parsing raw model text after the fact was rejected because it produces brittle behavior and weakens auditability.

## Decision 6: Store prompt and model metadata with results

- **Decision**: Persist prompt version, rubric version, model identifier, and schema version alongside evaluation results.
- **Rationale**: This is necessary to explain how a score was produced, replay issues, and maintain compatibility as prompts or output schemas evolve.
- **Alternatives considered**: Storing only final score and feedback was rejected because it hides evaluation provenance and makes regressions hard to diagnose.

## Decision 7: Use idempotent answer submission and worker execution

- **Decision**: Design answer submission and worker processing to tolerate duplicate requests and safe retries through uniqueness rules and state checks.
- **Rationale**: Background systems and HTTP clients both retry. Idempotency avoids duplicate evaluations, inconsistent history, and unnecessary model spend.
- **Alternatives considered**: Best-effort duplicate prevention only in the request layer was rejected because it does not protect against race conditions or worker restarts.

## Decision 8: Expose evaluation progress through polling-friendly contracts

- **Decision**: Return answer and evaluation status through normal read endpoints instead of designing push delivery in the initial release.
- **Rationale**: Polling keeps the MVP simple, aligns with stateless backend scaling, and is adequate for human-paced interview workflows.
- **Alternatives considered**: WebSocket or webhook delivery was rejected because it adds delivery complexity without being required by the feature goals.

## Decision 9: Use Docker for local parity across API, workers, PostgreSQL, and Redis

- **Decision**: Standardize development and runtime setup with Dockerized API, worker, PostgreSQL, and Redis services.
- **Rationale**: The chosen stack spans multiple infrastructure dependencies. Containerized local setup reduces environment drift and matches the user’s declared deployment direction.
- **Alternatives considered**: Partial local setup without containers was rejected because it increases onboarding friction and makes queue or database behavior less reproducible.

## Decision 10: Keep the initial repository as one backend service with layered modules

- **Decision**: Use one repository and one application package with explicit modules for API, services, repositories, models, and workers.
- **Rationale**: This satisfies the constitution’s simplicity rule while still separating concerns enough to keep the LLM and queue boundaries testable.
- **Alternatives considered**: Splitting into multiple services now was rejected because the expected MVP scale does not justify that operational complexity.

## Best-Practice Findings

### FastAPI

- Use async route handlers for I/O-bound operations only.
- Keep routes thin and move orchestration into services.
- Use dependency injection for database sessions, settings, and request context.
- Return typed request and response schemas for every external contract.

### ARQ and Redis

- Give the evaluation job a clear timeout and bounded retry policy.
- Persist job status in PostgreSQL rather than relying on queue state alone.
- Ensure worker logic checks current state before reprocessing to remain idempotent.
- Log correlation identifiers through request and worker boundaries.

### SQLModel and PostgreSQL

- Separate table models from request and response schemas.
- Add indexes on session status, answer status, and foreign keys.
- Prefer explicit relationships and query paths over broad eager-loading defaults.
- Use Alembic migrations from the start so schema evolution stays explicit.

### LangChain and OpenRouter

- Centralize provider configuration with base URL, model name, and key handling.
- Use prompt templates with explicit version strings.
- Validate model responses against Pydantic-style schemas before persistence.
- Distinguish model settings for question generation and evaluation consistency.

### Docker

- Run API and worker containers separately even if they share the same image base.
- Keep PostgreSQL and Redis as explicit compose services.
- Provide health checks for API, PostgreSQL, and Redis.
- Use development compose overrides for live reload and mounted source.
