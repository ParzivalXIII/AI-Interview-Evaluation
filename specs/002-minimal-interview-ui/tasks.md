# Tasks: Minimal Interview UI

**Input**: Design documents from `specs/002-minimal-interview-ui/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/api-client.md ✅
**Branch**: `002-minimal-interview-ui`

## Format: `[ID] [P?] [Story?] Description with file path`

- **[P]**: Can run in parallel (different files, no blocking deps)
- **[US#]**: Which user story this task belongs to
- No `[P]` = must execute after prior task in the same phase completes

---

## Phase 1: Setup

**Purpose**: Dependency changes and project scaffold. No UI logic yet.

- [X] T001 Update pyproject.toml — add `gradio>=5.0` to `[project.dependencies]`, remove `nicegui>=3.8.0`, add `respx>=0.21` to `[project.optional-dependencies].dev`
- [X] T002 [P] Update `.env.example` — add `BACKEND_URL=http://localhost:8000`, `UI_PORT=7860`, `UI_HOST=0.0.0.0` entries with comments
- [X] T003 [P] Create `interview-ui/__init__.py` (empty) and `interview-ui/tests/__init__.py` (empty) to establish package structure

**Checkpoint**: `uv sync` succeeds; `import gradio` resolves; `respx` available in dev env.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data structures and HTTP client. Every user story handler depends on these two modules.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Implement `interview-ui/state.py` — define `QuestionData`, `AnswerData`, `EvaluationData`, `SessionState` as `TypedDict` classes matching the shapes in `specs/002-minimal-interview-ui/data-model.md`; add helper functions `get_non_terminal_answer_ids(state: SessionState) -> list[int]` and `get_next_unanswered_idx(state: SessionState) -> int | None`; define `EMPTY_SESSION` initial value constant
- [X] T005 Implement `interview-ui/client.py` — define `APIError(Exception)` with `message: str` and `status_code: int | None` fields; implement `InterviewAPIClient` class with a shared `httpx.AsyncClient` instance (base URL from `BACKEND_URL` env var, default `http://localhost:8000`); implement all four async methods from `specs/002-minimal-interview-ui/contracts/api-client.md`: `create_session()`, `submit_answer()`, `get_answer_result()`, `get_session_summary()`; all methods raise `APIError` on non-2xx responses or network failures; expose a module-level `client = InterviewAPIClient()` singleton

**Checkpoint**: `from interview_ui.state import EMPTY_SESSION, SessionState` imports cleanly; `from interview_ui.client import client, APIError` imports cleanly.

---

## Phase 3: User Story 1 — Start An Interview (Priority: P1) 🎯 MVP

**Goal**: A user opens the app, sees a focused start screen, fills in role/difficulty/question count, clicks Start, and the first question appears.

**Independent Test**: Open `http://localhost:7860`, enter `"Backend Engineer"` / `"mid"` / `5`, click Start, verify the start panel is hidden and a question card is visible with question text. No prior state needed.

### Tests for User Story 1

- [X] T006 [P] [US1] Create `interview-ui/tests/test_client.py` — write `respx`-mocked tests for `InterviewAPIClient.create_session()`: success case (HTTP 201 → returns `SessionCreatedData`); 422 response → raises `APIError` with correct `status_code=422`; 500 response → raises `APIError`; network timeout → raises `APIError` with `status_code=None`

- [X] T007 [P] [US1] Create `interview-ui/tests/test_app.py` — stub file with one async test for the `start_interview` handler (to be added in T009): mock `InterviewAPIClient`, call handler with valid inputs, assert returned `SessionState` has `session_id` set and `len(questions) > 0`, assert start panel visibility output is `gr.update(visible=False)`

### Implementation for User Story 1

- [X] T008 [US1] Create `interview-ui/app.py` — scaffold a `gr.Blocks(theme=..., css=...)` app; build the **start panel** with: `gr.Textbox` for role (label "Job Role", placeholder "e.g. Backend Engineer"), `gr.Dropdown` for difficulty (choices `["junior", "mid", "senior"]`, value `"mid"`), `gr.Slider` for question count (min 1, max 10, step 1, value 5), `gr.Button("Start Interview")`, `gr.Markdown` for error display (hidden by default); add `gr.State(value=EMPTY_SESSION)` for session state; import `client` from `interview_ui.client`
- [X] T009 [US1] Wire `start_interview` async event handler in `interview-ui/app.py` — on button click: validate inputs, call `await client.create_session(role, difficulty, question_count)`, on success populate `SessionState` from response, make start panel `visible=False` and question panel `visible=True`; on `APIError` show error in the error markdown component and keep start panel visible with inputs preserved

**Checkpoint**: `uv run interview-ui/app.py` opens at `http://localhost:7860`; filling out the form and clicking Start creates a session and transitions the view to show the first question.

---

## Phase 4: User Story 2 — Answer Questions And See Results (Priority: P2)

**Goal**: A user can navigate between questions, type an answer, submit it, see "Evaluating…" while the backend processes, and then see the score and feedback when the evaluation completes.

**Independent Test**: Start a session (T009 must work), submit an answer for Q1, verify answer panel shows "Evaluating…", wait up to 10 s, verify score and feedback appear. Navigate to Q2 (if multi-question session) and verify it is unanswered.

### Tests for User Story 2

- [X] T010 [P] [US2] Extend `interview-ui/tests/test_client.py` — add `respx`-mocked tests for `submit_answer()` (202 → `AnswerAcceptedData`; 404 → `APIError`; 422 → `APIError`; 5xx → `APIError`); `get_answer_result()` with each status value (`pending_evaluation`, `in_progress`, `completed` with evaluation payload, `failed` with `failureReason`); `get_session_summary()` (200 → `SessionSummaryData`; 404 → `APIError`)
- [X] T011 [P] [US2] Extend `interview-ui/tests/test_app.py` — add async handler tests for `submit_answer`: (a) multi-question session → `current_idx` advances to next unanswered; (b) single-question session → `current_idx` stays at 0, submit button disabled; add test for `poll_tick`: (a) non-terminal answer → state updated with completed evaluation; (b) all answers terminal → handler returns no-op updates without calling client

### Implementation for User Story 2

- [X] T012 [US2] Build **question view panel** in `interview-ui/app.py` (hidden initially, `visible=True` after session start): `gr.Markdown` for question position indicator (e.g. "Question 2 of 5"), `gr.Markdown` for question type badge, `gr.Markdown` for question text; previous/next `gr.Button` controls that update `current_idx` in state and refresh the displayed question; question nav buttons disabled when at boundaries or question has no adjacent unanswered question
- [X] T013 [US2] Build **answer and evaluation panel** in `interview-ui/app.py`: `gr.Textbox` (lines=6, placeholder "Type your answer…") for answer text; `gr.Button("Submit Answer")` with `interactive=False` while submission is in flight or answer already submitted; `gr.Markdown` evaluation status display ("Evaluating…" spinner or final result); evaluation result card components: score `gr.Number`, feedback `gr.Markdown`, strengths `gr.Markdown`, improvements `gr.Markdown`; audit details in a `gr.Accordion` (schema/rubric/prompt/model versions)
- [X] T014 [US2] Wire `submit_answer` async event handler in `interview-ui/app.py`: on click call `await client.submit_answer(session_id, question_id, answer_text)`, add `AnswerData(status="pending_evaluation")` to `state["answers"]`; if session has >1 question advance `current_idx` to `get_next_unanswered_idx(state)` immediately; if single-question session keep focus on current question and disable Submit; on `APIError` show error and preserve answer text in textbox
- [X] T015 [US2] Wire `gr.Timer(value=5)` polling in `interview-ui/app.py`: attach `poll_tick` async handler to `timer.tick`; handler reads `get_non_terminal_answer_ids(state)` and calls `await client.get_answer_result()` for each; on `status == "completed"` update `AnswerData.evaluation` in state and refresh evaluation panel components; on `status == "failed"` update `AnswerData.status` and render failure message; short-circuit immediately with no-op updates when `state["session_id"]` is `None` or non-terminal list is empty
- [X] T016 [US2] Add **end-of-session summary** render in `interview-ui/app.py`: when `poll_tick` detects all answers are in terminal states, call `await client.get_session_summary(session_id)`, hide per-question panels, show summary panel with all questions + submitted answers + scores + feedback in a `gr.Dataframe` or sequential `gr.Markdown` blocks

**Checkpoint**: Full interview flow works end-to-end via the UI: start session → answer all questions → see evaluations appear one by one → see summary panel.

---

## Phase 5: User Story 3 — Stay Focused In A Modern Interface (Priority: P3)

**Goal**: The UI applies the Gradio Soft theme with custom CSS overrides so the layout feels polished, minimal, and readable on both desktop and mobile widths.

**Independent Test**: Open the app at both desktop (1280 px) and mobile (375 px) viewport widths; verify start panel, question card, answer textarea, and evaluation panel are all fully visible and usable; verify consistent visual language (cards, spacing, typography) across all states.

### Implementation for User Story 3

- [X] T017 [US3] Create `interview-ui/theme.py` — define `THEME = gr.themes.Soft()` and `CUSTOM_CSS` string constant with rules for: `.interview-container { max-width: 840px; margin: 0 auto; }` layout constraint; `.question-card`, `.eval-card` card panel styles (background, border-radius, box-shadow, padding); primary accent override to dark-neutral hex; `@media (max-width: 640px)` responsive rule reducing padding; loading indicator styles for ".evaluating-spinner" state
- [X] T018 [US3] Apply theme in `interview-ui/app.py` — pass `THEME` and `CUSTOM_CSS` to `gr.Blocks(theme=THEME, css=CUSTOM_CSS)`; attach `elem_id` and `elem_classes` to key components (`"question-card"`, `"eval-card"`, `"interview-container"`); add `gr.Markdown("⏳ Evaluating your answer…", visible=False, elem_classes=["evaluating-spinner"])` that becomes visible on submit and hidden when evaluation card renders; add `gr.Markdown("⚙️ Creating your interview session…")` inline loading indicator on Start button click

**Checkpoint**: All three interview states (start, question/answer, evaluation) look visually consistent; card panels have visible separation from the background; layout fits within 840 px centred column on desktop and stacks cleanly on mobile.

---

## Phase 6: Docker

**Purpose**: Containerise the UI so it runs alongside the existing backend via `docker compose`.

- [X] T019 [P] Create `docker/Dockerfile.ui` — multi-stage build: `builder` stage installs `gradio`, `httpx`, `pydantic` from `pyproject.toml` into a `Python 3.12-slim` base; `final` stage creates non-root user `appuser`, copies installed packages and `interview-ui/` source, sets `EXPOSE 7860`, sets `CMD ["uv", "run", "interview-ui/app.py"]`
- [X] T020 Update `docker/compose.yml` — add `ui` service: `build.context: .`, `build.dockerfile: docker/Dockerfile.ui`, `ports: ["7860:7860"]`, `environment: [BACKEND_URL=http://api:8000, UI_HOST=0.0.0.0, UI_PORT=7860]`, `depends_on: [api]`, `networks: [app-network]`

**Checkpoint**: `docker compose build ui` completes without errors; `docker compose up ui` starts Gradio on port 7860 and logs no import errors.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T021 Run `uv sync` from repo root — verify lock file updates cleanly, `gradio` is present, `nicegui` is absent; run `uv run python -c "from interview_ui.app import demo"` to confirm no import errors
- [X] T022 Run full test suite — `uv run -m pytest interview-ui/tests/ -v --tb=short`; fix any assertion failures before proceeding; confirm all `test_client.py` and `test_app.py` tests pass
- [X] T023 [P] Build Docker image and verify — `docker compose build ui`; inspect image with `docker run --rm <image> python -c "import gradio"` to confirm deps present
- [X] T024 Full stack smoke test — `docker compose up`; open `http://localhost:7860` in browser; complete one full interview (fill start form → submit session → answer all questions → view evaluation results → view summary); verify no console errors and no unhandled exceptions in compose logs

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 completion — **BLOCKS all user story phases**
- **Phase 3 (US1)**: Depends on Phase 2 — tests (T006, T007) and implementation (T008, T009) can start concurrently after Foundational
- **Phase 4 (US2)**: Depends on Phase 3 implementation complete (T008, T009) — tests (T010, T011) can run in parallel with implementation tasks (T012–T016)
- **Phase 5 (US3)**: Depends on Phase 4 complete — theme applies on top of existing layout
- **Phase 6 (Docker)**: Can begin after Phase 2 (Dockerfile only needs the module to exist); T020 (compose.yml) after T019
- **Phase 7 (Polish)**: Depends on Phases 1–6 all complete

### User Story Dependencies

| Story | Can start after | Integration needed |
|-------|----------------|-------------------|
| US1 (P1) | Phase 2 | None — self-contained start flow |
| US2 (P2) | US1 complete (session state must exist) | Uses `SessionState` populated by US1 handler |
| US3 (P3) | US2 complete | Applies CSS/theme on top of all panels |

### Within Each User Story

- Tests (T006/T007, T010/T011) should be written before or alongside implementation — they are marked `[P]` because they share no file dependencies with implementation tasks
- State and client modules (T004, T005) before any handler task
- Layout tasks (T008, T012, T013) before wiring handlers (T009, T014, T015)
- Core handlers before end-of-session summary (T016 depends on T015 logic being stable)

---

## Parallel Execution Examples

### Phase 1 — all three tasks can run together

```
T001  (pyproject.toml)
T002  (env.example)      ← parallel
T003  (.py stubs)        ← parallel
```

### Phase 2 — sequential (state.py before client.py for import clarity)

```
T004  (state.py)
  └── T005  (client.py, imports from state.py)
```

### Phase 3 — tests and implementation in parallel

```
T006  (test_client.py stub)   ← parallel with T007, T008
T007  (test_app.py stub)      ← parallel with T006, T008
T008  (app.py layout)
  └── T009  (start_interview handler, depends on T008)
```

### Phase 4 — tests parallel to implementation

```
T010  (extend test_client.py) ← parallel with T011, T012, T013
T011  (extend test_app.py)    ← parallel with T010, T012, T013
T012  (question panel layout)
T013  (answer panel layout)
  ├── T014  (submit handler, depends on T012 + T013)
  │     └── T015  (timer + poll_tick, depends on T014)
  │           └── T016  (summary render, depends on T015)
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (Setup)
2. Complete Phase 2 (Foundational — blocks everything)
3. Complete Phase 3 (US1)
4. **STOP and VALIDATE**: `uv run interview-ui/app.py` → start a session → first question visible
5. Deploy or demo the start-session experience

### Incremental Delivery

1. Setup + Foundational → T001–T005
2. US1 complete → T006–T009 → **MVP: session creation works** ✓
3. US2 complete → T010–T016 → **Full interview loop works** ✓
4. US3 complete → T017–T018 → **Polished visual experience** ✓
5. Docker → T019–T020 → **Deployable** ✓
6. Polish → T021–T024 → **Verified and smoke-tested** ✓

---

## Task Summary

| Phase | Tasks | Parallel? |
|-------|-------|-----------|
| Phase 1: Setup | T001–T003 | T002, T003 parallel |
| Phase 2: Foundational | T004–T005 | Sequential |
| Phase 3: US1 (P1) | T006–T009 | T006, T007, T008 parallel |
| Phase 4: US2 (P2) | T010–T016 | T010, T011, T012, T013 parallel |
| Phase 5: US3 (P3) | T017–T018 | T017 then T018 |
| Phase 6: Docker | T019–T020 | T019 parallel; T020 after T019 |
| Phase 7: Polish | T021–T024 | T023 parallel |
| **Total** | **24 tasks** | |

| User Story | Tasks | Count |
|------------|-------|-------|
| US1 — Start Interview | T006, T007, T008, T009 | 4 |
| US2 — Answer + Results | T010, T011, T012, T013, T014, T015, T016 | 7 |
| US3 — Modern Interface | T017, T018 | 2 |
| Cross-cutting/Infra | T001–T005, T019–T024 | 11 |
