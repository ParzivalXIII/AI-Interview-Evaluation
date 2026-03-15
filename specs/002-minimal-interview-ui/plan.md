# Implementation Plan: Minimal Interview UI

**Branch**: `002-minimal-interview-ui` | **Date**: 2026-03-15 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/002-minimal-interview-ui/spec.md`

## Summary

Build a minimal Gradio 5 web UI that lets a user start an interview session, read each generated question, type and submit answers, and view LLM evaluation results as they arrive. The UI is a thin Python client: all business logic stays in the existing FastAPI backend. The UI communicates exclusively through the existing REST endpoints via `httpx.AsyncClient`. Async evaluation results are surfaced by a `gr.Timer` that polls the result endpoint every 5 seconds. When a session has two or more questions the UI advances immediately to the next question after each submission (non-blocking); for single-question sessions a spinner holds focus until the evaluation result arrives.

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: `gradio>=5.0`, `httpx>=0.28.0` (already in project), `pydantic>=2.9.0` (already in project)  
**Storage**: No new storage — live session state held in `gr.State` (browser-scoped, in-memory)  
**Testing**: `pytest`, `pytest-asyncio`, `respx` (httpx mock router for unit tests)  
**Target Platform**: Browser, served by Gradio's built-in ASGI server (port 7860)  
**Project Type**: Web UI — thin client over existing web-service  
**Performance Goals**: Submit acknowledgement visible within 2 seconds of user action; evaluation result reflected within one 5-second poll tick after it becomes available  
**Constraints**: Zero business logic in UI code; no direct DB or Redis access; no new API endpoints required; `nicegui` dependency removed from `pyproject.toml`  
**Scale/Scope**: Single-user session per browser tab; no authentication; 1–10 questions per session

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Backend-First Scope | ✅ PASS | UI contains zero evaluation, scoring, or prompt logic. All computation stays in the FastAPI + ARQ backend. |
| II. Structured Traceable Evaluation | ✅ PASS | UI renders evaluation payloads (score, feedback, strengths, improvements, schema/rubric/prompt/model versions) verbatim from the API — no reinterpretation. |
| III. Safety and Fairness | ✅ PASS | UI introduces no scoring criteria or filtering. It displays exactly what the backend returns. |
| IV. Testable LLM Integration | ✅ PASS | `client.py` is a thin httpx wrapper with no LLM logic. It can be fully tested by mocking httpx calls with `respx`. |
| V. Simplicity and Observability | ✅ PASS | Single `interview-ui/` directory, no new data stores, no additional worker processes. Gradio's built-in logging is sufficient. |

**Gate result**: All principles pass. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/002-minimal-interview-ui/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
├── contracts/
│   └── api-client.md   ← Phase 1 output — HTTP contract the UI consumes
└── tasks.md             ← Phase 2 output (created by /speckit.tasks)
```

### Source Code (repository root)

```text
interview-ui/               ← NEW: Gradio UI package
├── __init__.py
├── app.py                  ← Gradio Blocks app, entry point (uv run interview-ui/app.py)
├── client.py               ← httpx.AsyncClient wrapper for FastAPI backend
├── state.py                ← Pydantic data models mirroring API response shapes (read-only)
├── theme.py                ← Gradio Theme + custom CSS constants
└── tests/
    ├── __init__.py
    ├── test_client.py      ← API client unit tests, mocked with respx
    └── test_app.py         ← Gradio event-handler integration smoke tests

docker/
├── Dockerfile.ui           ← NEW: lightweight image for the Gradio UI service
└── compose.yml             ← MODIFIED: add `ui` service on port 7860

pyproject.toml              ← MODIFIED: add gradio>=5.0, remove nicegui>=3.8.0, add respx to dev deps
.env / .env.example         ← MODIFIED: add BACKEND_URL=http://localhost:8000
```

**Structure Decision**: Single `interview-ui/` directory at repo root (the project's `pyproject.toml` already lists `interview-ui/tests` in `testpaths`, confirming this layout was anticipated). No `src/` nesting — the package is simple enough to lay flat. Source code and tests colocated inside `interview-ui/` for discoverability.
