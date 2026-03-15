# Research: Minimal Interview UI

**Phase**: 0 | **Date**: 2026-03-15 | **Plan**: [plan.md](./plan.md)

All research items originate from unknowns surfaced during Technical Context analysis. Every item below is resolved; no NEEDS CLARIFICATION markers remain.

---

## 1. UI Framework Selection: Gradio vs. Alternatives

**Decision**: Gradio 5.x  
**Rationale**: The user explicitly selected Gradio. Gradio 5 (released late 2024, stable in 2026) ships with a full `gr.Blocks` layout API, `gr.State` for per-session in-memory state, `gr.Timer` for periodic polling, built-in theming (`gr.themes.Soft`, `gr.themes.Monochrome`, or custom CSS overrides), and native support for `async def` event handlers. This makes it a natural Python-native fit over the existing FastAPI + Python environment. The entire UI is one or two Python files, requiring no JavaScript, no build step, and no separate frontend runtime.

**Alternatives considered**:
- **NiceGUI**: Already listed in `pyproject.toml`. Rejected — user explicitly chose Gradio; nicegui will be removed as an unused dependency.
- **Streamlit**: No `gr.Timer`-equivalent without manual threading hacks; less suitable for async polling patterns.
- **Raw HTML/HTMX served by FastAPI**: Adds HTML templating complexity and diverges from the "all Python" goal.

---

## 2. HTTP Client: httpx Sync vs. Async

**Decision**: `httpx.AsyncClient` with `async def` Gradio event handlers  
**Rationale**: `httpx>=0.28.0` is already a project dependency. Gradio 5 fully supports `async def` functions as event handlers and uses an internal asyncio event loop. Using `httpx.AsyncClient` inside `async def` handlers gives true non-blocking I/O, which is important during the polling tick (a sync call would block Gradio's loop). The client is wrapped in a thin `client.py` module that manages a single shared `AsyncClient` instance, opened on startup and closed on shutdown, which avoids per-request connection overhead.

**Alternatives considered**:
- **aiohttp**: Would also work but httpx is already present; no reason to add a second async HTTP library.
- **requests (sync)**: Would block Gradio's event loop during polling; rejected.

---

## 3. Async Evaluation Polling Strategy

**Decision**: `gr.Timer(value=5)` always active during an interview session; fires a polling function every 5 seconds that refreshes all answers with non-terminal status (`pending_evaluation` or `in_progress`)  
**Rationale**: Gradio 5's `gr.Timer` component fires a `.tick` event at a configurable interval (seconds). The tick handler receives `gr.State` and can update multiple output components. This is the correct Gradio-native mechanism — no threads, no `time.sleep`, no manual asyncio scheduling. The timer runs at the Gradio component level, not the OS level, so it respects Gradio's queue and does not interfere with other user interactions.

**Non-blocking vs. blocking behaviour**:
- **≥2 questions in session**: Submit immediately advances `current_question_idx` to the next unanswered question. Evaluation status for past questions is updated asynchronously on the next timer tick. This satisfies FR-008 (navigate between questions) and FR-005 (immediate submission acknowledgement).
- **1-question session**: After submit, the UI remains on the question view and renders a "Evaluating…" spinner visible in the evaluation panel. The next timer tick (≤5 s) that finds `status == completed` will render the full evaluation. A `gr.Markdown` loading indicator is shown; the submit button is disabled during polling.

**Timer lifecycle**: Timer `.tick` is connected to a handler that short-circuits (returns no-ops) when `session_id` is `None` or all answers are in terminal states, avoiding unnecessary API calls.

**Alternatives considered**:
- **Streaming / WebSocket**: Overkill; the backend does not expose a streaming endpoint; polling every 5 s meets SC-003.
- **JavaScript in Gradio's `head`**: Rejected — avoids adding JS to a Python-first project.

---

## 4. UI State Management

**Decision**: `gr.State` Pydantic-dict holding `SessionState` (serialised as dict for Gradio compatibility)  
**Rationale**: `gr.State` is Gradio's first-class mechanism for per-session mutable state. It persists across event handler calls within the same browser session and is scoped per connection, which is correct for a single-user interview. State is stored as a plain `dict` (or a Pydantic model serialised to `dict`) rather than a class instance, because Gradio serialises/deserialises `gr.State` values and handles plain dicts reliably.

**State shape** (defined in `state.py`):
```python
SessionState(TypedDict):
    session_id: int | None
    questions: list[QuestionData]  # from POST /sessions response
    current_idx: int               # which question is currently shown
    answers: dict[int, AnswerData] # keyed by question_id
```

---

## 5. Theming and "Sleek Modern" Appearance

**Decision**: `gr.themes.Soft()` base theme with a `custom_css` override block for card-style panels, a constrained max-width, and a neutral monochrome colour palette  
**Rationale**: Gradio 5's theme system accepts a Python `Theme` subclass and a `css` string. `gr.themes.Soft()` provides clean rounded inputs and good default typography. The custom CSS targets Gradio's generated class names to: constrain layout to 840 px centred max width, render question and evaluation blocks as distinct cards with subtle shadows, and apply a dark-neutral primary accent. No external assets are needed.

**Alternatives considered**:
- `gr.themes.Monochrome()`: Good but slightly too stark for an evaluation context where coloured score indicators are useful.
- Full custom theme from `gr.Theme(...)`: More control but more boilerplate; the Soft base with CSS overrides achieves the same result with less code.

---

## 6. Dependency Changes Required

| Change | Target file | Notes |
|--------|-------------|-------|
| Add `gradio>=5.0` to `[project.dependencies]` | `pyproject.toml` | Primary UI dependency |
| Remove `nicegui>=3.8.0` from `[project.dependencies]` | `pyproject.toml` | Unused; user chose Gradio |
| Add `respx>=0.21` to `[project.optional-dependencies].dev` | `pyproject.toml` | httpx mock router for unit tests |
| Add `BACKEND_URL=http://localhost:8000` | `.env.example` / `.env` | Configures which FastAPI instance the UI calls |
| Add `ui` service on port 7860 | `docker/compose.yml` | Runs the Gradio app in Docker |
| New `docker/Dockerfile.ui` | `docker/` | Lightweight image for the UI |

---

## 7. Testing Approach for the UI Layer

**Decision**: Unit tests with `respx` to mock httpx; no Selenium/browser automation  
**Rationale**: The only logic in the UI layer is in `client.py` (HTTP calls) and a handful of pure helper functions in `state.py` (e.g., "which questions are still pending?"). These are testable without a browser. Gradio's event handlers delegate to `client.py`, so testing `client.py` in isolation covers the meaningful behaviour. Full browser automation (Playwright/Selenium) is disproportionate for a thin UI and is excluded from the minimal scope.

**Test file layout**:
- `interview-ui/tests/test_client.py` — mock httpx with `respx`; assert correct URLs, headers, and payload shapes; assert error branches raise correctly.
- `interview-ui/tests/test_app.py` — call Gradio event handler functions directly (they are plain `async def` functions); pass a mock `client` fixture; assert state transitions are correct.

---

## 8. Docker + Local Run Strategy

**Decision**: `uv run interview-ui/app.py` locally; `ui` Docker service in `compose.yml`  
**Rationale**: The app is a standard Python script. Locally it runs with `uv run interview-ui/app.py` (uses the project venv). In Docker it is a separate `ui` service that connects to the `api` service via the internal `app-network` using `http://api:8000` as `BACKEND_URL`. The Docker image is a second multi-stage build (`Dockerfile.ui`) that installs only what the UI needs.

---

## Resolution Summary

| # | Unknown | Resolved |
|---|---------|---------|
| 1 | UI framework | Gradio 5.x |
| 2 | HTTP client | `httpx.AsyncClient` |
| 3 | Polling strategy | `gr.Timer(value=5)`, non-blocking advance when ≥2 questions |
| 4 | State management | `gr.State` dict, `SessionState` TypedDict in `state.py` |
| 5 | Theming | `gr.themes.Soft()` + custom CSS |
| 6 | Dependency changes | gradio added, nicegui removed, respx added to dev |
| 7 | Testing | `respx` httpx mock; handler tests are plain async functions |
| 8 | Run strategy | `uv run interview-ui/app.py` / Docker `ui` service |
