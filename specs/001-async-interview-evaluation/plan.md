# Implementation Plan: Async Interview Evaluation Engine

**Branch**: `001-async-interview-evaluation` | **Date**: 2026-03-15 | **Spec**: `/home/parzival/projects/AI-Interview-Evaluation/specs/001-async-interview-evaluation/spec.md`
**Input**: Feature specification from `/specs/001-async-interview-evaluation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Build a backend interview evaluation service that creates interview sessions, generates role- and difficulty-specific questions during session creation, accepts answer submissions, evaluates them asynchronously, and exposes structured results and session history. The implementation will use FastAPI async request handling, Redis plus ARQ background workers for answer evaluation, PostgreSQL with SQLModel for durable state, LangChain for prompt orchestration, OpenRouter through an OpenAI-compatible client configuration, and Docker for local and deployment parity.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI, Pydantic, SQLModel, SQLAlchemy, Alembic, Redis, ARQ, LangChain, OpenAI-compatible chat client configuration, Uvicorn  
**Storage**: PostgreSQL for application state and audit artifacts; Redis for job queueing and worker coordination  
**Testing**: pytest, pytest-asyncio, FastAPI TestClient or httpx, mocked LLM integration for unit tests, container-backed integration tests  
**Target Platform**: Linux containers running backend API and worker processes  
**Project Type**: Backend web service with asynchronous worker processes  
**Performance Goals**: Session creation returns generated questions within 10 seconds for at least 95% of valid requests; answer submission acknowledgment within 2 seconds; asynchronous evaluation completion exposed through pollable status; structured output generation success rate of at least 90% for valid processed evaluations  
**Constraints**: Structured LLM output must be schema-validated; job processing must be idempotent; audit metadata must be persisted; external model calls must tolerate timeout and transient failure; local development must run in Docker  
**Scale/Scope**: MVP backend for demonstration and portfolio use, targeting dozens of concurrent interview sessions and hundreds of evaluations per day without architectural rewrites

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Pre-Research Gate

- **Backend-First Product Scope**: PASS. The feature delivers interview orchestration, prompt execution, answer evaluation, scoring, and persistence only.
- **Structured and Traceable Evaluation**: PASS. Plan requires explicit schemas for questions, answers, job state, evaluation results, and stored audit metadata.
- **Safety and Fairness by Default**: PASS. Evaluation design includes bounded scoring, role-relevant rubrics, and explicit exclusion of irrelevant candidate attributes.
- **Testable LLM Integration**: PASS. LLM access is isolated behind a dedicated service and worker boundary, enabling deterministic tests with mocked provider responses.
- **Simplicity and Observability**: PASS. Architecture stays within one backend service plus evaluation workers, with structured logging and status tracking instead of premature microservice split.

### Post-Design Re-Check

- **Backend-First Product Scope**: PASS. Data model and contracts remain limited to backend interview lifecycle behavior.
- **Structured and Traceable Evaluation**: PASS. Contracts define stable request and response schemas; data model stores schema version, prompt version, and model metadata.
- **Safety and Fairness by Default**: PASS. Evaluation contract requires evidence-based feedback and rubric-driven scoring fields.
- **Testable LLM Integration**: PASS. Quickstart and structure separate API, orchestration, provider integration, and workers for isolated testing.
- **Simplicity and Observability**: PASS. Selected structure is a single application package with clear subsystems, health checks, and status-bearing entities.

## Project Structure

### Documentation (this feature)

```text
specs/001-async-interview-evaluation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── interview-api.yaml
│   └── worker-jobs.md
└── tasks.md
```

### Source Code (repository root)

```text
app/
├── api/
│   ├── dependencies.py
│   ├── routes/
│   └── schemas/
├── core/
│   ├── config.py
│   ├── database.py
│   ├── logging.py
│   └── queue.py
├── models/
├── repositories/
├── services/
│   ├── interview_service.py
│   ├── answer_service.py
│   ├── evaluation_service.py
│   ├── question_generation_service.py
│   └── llm_service.py
├── workers/
│   ├── main.py
│   └── evaluation.py
└── main.py

tests/
├── api/
├── contract/
├── integration/
└── unit/

alembic/
├── versions/
└── env.py

docker/
├── Dockerfile.api
├── Dockerfile.worker
└── compose.yml
```

**Structure Decision**: Use a single backend service repository with one application package and a separate evaluation worker module. This preserves a simple deployment model while still isolating API, persistence, LLM orchestration, and background execution concerns required by the constitution.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |
