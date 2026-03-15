# Tasks: Async Interview Evaluation Engine

**Input**: Design documents from `/specs/001-async-interview-evaluation/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: No separate test-writing tasks are included here because the feature spec does not explicitly require a TDD-first workflow. Validation is still built into each user story's independent test criteria and final quickstart verification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize the backend project structure, dependencies, and container scaffolding.

- [x] T001 Create backend package and test directory structure in `app/`, `tests/`, `alembic/`, and `docker/`
- [x] T002 Initialize project dependencies and tool configuration in `pyproject.toml`
- [x] T003 [P] Add environment template and developer settings in `.env.example`
- [x] T004 [P] Add API and worker container definitions in `docker/Dockerfile.api`, `docker/Dockerfile.worker`, and `docker/compose.yml`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish core infrastructure required before implementing any user story.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [x] T005 Create application settings and OpenRouter configuration in `app/core/config.py`
- [x] T006 [P] Configure database engine, session management, and metadata setup in `app/core/database.py`
- [x] T007 [P] Configure Redis queue connections and ARQ settings in `app/core/queue.py`
- [x] T008 [P] Implement structured logging and correlation ID helpers in `app/core/logging.py`
- [x] T009 Create shared status enums and constants in `app/core/constants.py`
- [x] T010 Create FastAPI app bootstrap, router registration, and health endpoint in `app/main.py`
- [x] T011 [P] Add API dependency wiring in `app/api/dependencies.py`
- [x] T012 [P] Add shared API error response utilities in `app/api/utils.py`
- [x] T013 Configure Alembic environment and migration bootstrap in `alembic/env.py` and `alembic/script.py.mako`

**Checkpoint**: Foundation ready. User story implementation can now begin.

---

## Phase 3: User Story 1 - Start and Run an Interview Session (Priority: P1) 🎯 MVP

**Goal**: Create an interview session and return generated questions immediately.

**Independent Test**: Create a session with a valid role and difficulty, confirm the session is persisted, and verify the response includes stable question identifiers and generated questions.

### Implementation for User Story 1

- [x] T014 [P] [US1] Create interview session and interview question models in `app/models/session.py` and `app/models/question.py`
- [x] T015 [P] [US1] Create session and question repository modules in `app/repositories/session_repository.py` and `app/repositories/question_repository.py`
- [x] T016 [P] [US1] Define session and question API schemas in `app/api/schemas/session.py`
- [x] T017 [P] [US1] Implement prompt templates and schema models for question generation in `app/contracts/prompts.py` and `app/contracts/question_generation_schema.py`
- [x] T018 [US1] Implement the OpenRouter-backed LLM service for synchronous question generation in `app/services/llm_service.py`
- [x] T019 [US1] Implement question generation orchestration in `app/services/question_generation_service.py`
- [x] T020 [US1] Implement interview session creation and retrieval logic in `app/services/interview_service.py`
- [x] T021 [US1] Implement session creation and session detail routes in `app/api/routes/sessions.py`
- [x] T022 [US1] Create the initial schema migration for sessions and questions in `alembic/versions/001_initial_sessions_and_questions.py`

**Checkpoint**: User Story 1 is functional and can be demonstrated as the MVP.

---

## Phase 4: User Story 2 - Submit Candidate Answers for Evaluation (Priority: P2)

**Goal**: Accept candidate answers, persist them, and queue asynchronous evaluation work without blocking the request.

**Independent Test**: Submit an answer for a valid session question, confirm the answer is stored, and verify the response returns a pending evaluation status while creating queued evaluation work.

### Implementation for User Story 2

- [x] T023 [P] [US2] Create candidate answer and evaluation job models in `app/models/answer.py` and `app/models/evaluation_job.py`
- [x] T024 [P] [US2] Create answer and evaluation job repository modules in `app/repositories/answer_repository.py` and `app/repositories/evaluation_job_repository.py`
- [x] T025 [P] [US2] Define answer submission schemas in `app/api/schemas/answer.py`
- [x] T026 [P] [US2] Implement ARQ worker payload contracts and job helpers in `app/workers/job_contracts.py` and `app/workers/utils.py`
- [x] T027 [US2] Implement answer submission validation and persistence logic in `app/services/answer_service.py`
- [x] T028 [US2] Implement evaluation job enqueueing and status coordination in `app/services/evaluation_service.py`
- [x] T029 [US2] Implement ARQ worker settings and startup wiring in `app/workers/main.py`
- [x] T030 [US2] Implement the answer evaluation worker skeleton with idempotent job state transitions in `app/workers/evaluation.py`
- [x] T031 [US2] Implement answer submission route with duplicate handling in `app/api/routes/answers.py`
- [x] T032 [US2] Add the migration for answers and evaluation jobs in `alembic/versions/002_answers_and_evaluation_jobs.py`

**Checkpoint**: User Stories 1 and 2 work together, and answer submission is independently verifiable.

---

## Phase 5: User Story 3 - Retrieve Structured Evaluation Results (Priority: P3)

**Goal**: Persist completed evaluation outputs and expose result retrieval and session history endpoints.

**Independent Test**: Retrieve a completed answer result and a full session summary, confirming stable score, feedback, and status fields are returned without inventing results for unfinished evaluations.

### Implementation for User Story 3

- [x] T033 [P] [US3] Create evaluation result model in `app/models/evaluation_result.py`
- [x] T034 [P] [US3] Create evaluation result repository in `app/repositories/evaluation_result_repository.py`
- [x] T035 [P] [US3] Define evaluation result and session summary schemas in `app/api/schemas/evaluation.py`
- [x] T036 [P] [US3] Define structured evaluation output schemas and rubric contracts in `app/contracts/evaluation_schema.py` and `app/contracts/rubrics.py`
- [x] T037 [US3] Implement structured evaluation parsing and persistence in `app/services/evaluation_service.py`
- [x] T038 [US3] Complete the evaluation worker to call LangChain, validate structured output, and persist results in `app/workers/evaluation.py`
- [x] T039 [US3] Implement answer result retrieval and session summary query logic in `app/services/interview_service.py` and `app/services/evaluation_service.py`
- [x] T040 [US3] Implement result retrieval and session summary routes in `app/api/routes/results.py` and `app/api/routes/sessions.py`
- [x] T041 [US3] Add the migration for evaluation results and audit metadata fields in `alembic/versions/003_evaluation_results.py`

**Checkpoint**: All user stories are independently functional, and completed evaluations can be retrieved and analyzed.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish operational quality, documentation, and full-flow verification.

- [x] T042 [P] Add repository-level documentation and run instructions in `README.md`
- [x] T043 [P] Add container ignore rules and runtime shell helpers in `.dockerignore` and `docker/entrypoint.sh`
- [x] T044 Add quickstart-aligned API and worker health checks in `app/api/routes/health.py` and `app/workers/main.py`
- [x] T045 Add observability and failure logging improvements across `app/services/`, `app/workers/`, and `app/api/`
- [x] T046 Validate the full quickstart workflow and update `specs/001-async-interview-evaluation/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1: Setup** has no dependencies and starts immediately.
- **Phase 2: Foundational** depends on Phase 1 and blocks all user story work.
- **Phase 3: User Story 1** depends on Phase 2 only and is the MVP slice.
- **Phase 4: User Story 2** depends on Phase 2 and integrates with the session/question components from User Story 1.
- **Phase 5: User Story 3** depends on Phase 2 and the persisted answer/evaluation workflow introduced in User Story 2.
- **Phase 6: Polish** depends on completion of the desired user stories.

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on other stories after the foundational phase.
- **User Story 2 (P2)**: Depends on User Story 1 session and question persistence to validate answer ownership and queue work correctly.
- **User Story 3 (P3)**: Depends on User Story 2 answer and job flow so completed evaluations exist for retrieval.

### Within Each User Story

- Models before repositories.
- Repositories and schemas before services.
- Services before routes and worker completion steps.
- Migrations after the related persistence model definitions are finalized.

## Parallel Opportunities

- Setup tasks `T003` and `T004` can run in parallel after `T002` starts.
- Foundational tasks `T006`, `T007`, `T008`, `T011`, and `T012` can run in parallel after `T005`.
- In User Story 1, `T014`, `T015`, `T016`, and `T017` can run in parallel.
- In User Story 2, `T023`, `T024`, `T025`, and `T026` can run in parallel.
- In User Story 3, `T033`, `T034`, `T035`, and `T036` can run in parallel.
- Polish tasks `T042` and `T043` can run in parallel.

## Parallel Example: User Story 1

```bash
# Parallelizable model, repository, and schema work for User Story 1
T014 Create interview session and interview question models in app/models/session.py and app/models/question.py
T015 Create session and question repository modules in app/repositories/session_repository.py and app/repositories/question_repository.py
T016 Define session and question API schemas in app/api/schemas/session.py
T017 Implement prompt templates and schema models for question generation in app/contracts/prompts.py and app/contracts/question_generation_schema.py
```

## Parallel Example: User Story 2

```bash
# Parallelizable persistence and queue contract work for User Story 2
T023 Create candidate answer and evaluation job models in app/models/answer.py and app/models/evaluation_job.py
T024 Create answer and evaluation job repository modules in app/repositories/answer_repository.py and app/repositories/evaluation_job_repository.py
T025 Define answer submission schemas in app/api/schemas/answer.py
T026 Implement ARQ worker payload contracts and job helpers in app/workers/job_contracts.py and app/workers/utils.py
```

## Parallel Example: User Story 3

```bash
# Parallelizable result modeling and contract work for User Story 3
T033 Create evaluation result model in app/models/evaluation_result.py
T034 Create evaluation result repository in app/repositories/evaluation_result_repository.py
T035 Define evaluation result and session summary schemas in app/api/schemas/evaluation.py
T036 Define structured evaluation output schemas and rubric contracts in app/contracts/evaluation_schema.py and app/contracts/rubrics.py
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: User Story 1.
4. Validate that session creation returns generated questions and persisted session state.

### Incremental Delivery

1. Deliver Setup and Foundational work to establish the service skeleton.
2. Deliver User Story 1 as the first demonstrable backend slice.
3. Deliver User Story 2 to add asynchronous evaluation intake.
4. Deliver User Story 3 to expose completed evaluation outcomes and historical summaries.
5. Finish with polish and quickstart validation.

### Suggested MVP Scope

The suggested MVP scope is **User Story 1 only**, because it produces the first end-to-end value slice and establishes the session and question domain needed by later stories.

## Notes

- Every task follows the required checklist format: checkbox, task ID, optional `[P]`, optional story label, and explicit file path.
- The user stories are intentionally ordered to match business priority and technical dependency.
- `tasks.md` is immediately executable by an implementation agent without requiring extra design context.
