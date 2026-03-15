# AI-Interview-Evaluation Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-15

## Active Technologies
- Python 3.12 + NiceGUI, httpx, Pydantic, pytest, existing FastAPI backend API (002-minimal-interview-ui)
- No UI-owned persistent storage; ephemeral UI state in process/browser, backend continues using PostgreSQL and Redis (002-minimal-interview-ui)
- Python 3.12 + `gradio>=5.0`, `httpx>=0.28.0` (already in project), `pydantic>=2.9.0` (already in project) (002-minimal-interview-ui)
- No new storage — live session state held in `gr.State` (browser-scoped, in-memory) (002-minimal-interview-ui)

- Python 3.12 + FastAPI, Pydantic, SQLModel, SQLAlchemy, Alembic, Redis, ARQ, LangChain, OpenAI-compatible chat client configuration, Uvicorn (001-async-interview-evaluation)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.12: Follow standard conventions

## Recent Changes
- 002-minimal-interview-ui: Added Python 3.12 + `gradio>=5.0`, `httpx>=0.28.0` (already in project), `pydantic>=2.9.0` (already in project)
- 002-minimal-interview-ui: Added Python 3.12 + NiceGUI, httpx, Pydantic, pytest, existing FastAPI backend API

- 001-async-interview-evaluation: Added Python 3.12 + FastAPI, Pydantic, SQLModel, SQLAlchemy, Alembic, Redis, ARQ, LangChain, OpenAI-compatible chat client configuration, Uvicorn

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
