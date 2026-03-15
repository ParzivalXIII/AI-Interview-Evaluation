# AI Interview Evaluation Engine

A backend service that simulates technical interviews and evaluates candidate responses using large language models.

## Architecture

```
Gradio UI  (localhost:7860)
  │
  └─► FastAPI (localhost:8000)
        │
        ├── POST /sessions              → Synchronously generates questions via LLM
        ├── POST /sessions/{id}/answers  → Accepts answer, queues async evaluation via ARQ
        ├── GET  /sessions/{id}/answers/{aid} → Poll evaluation status and structured result
        └── GET  /sessions/{id}/summary  → Full session history
              │
              ├── PostgreSQL + SQLModel  (persistence)
              ├── Redis + ARQ            (async evaluation queue)
              └── OpenRouter / LangChain (LLM)
```

**Stack**: Gradio · FastAPI · PostgreSQL + SQLModel · Redis + ARQ · LangChain · OpenRouter · Docker

## Quick Start

### 1. Prerequisites

- Docker & Docker Compose
- `uv` ([install](https://docs.astral.sh/uv/getting-started/installation/))
- OpenRouter API key

### 2. Environment

```bash
cp .env.example .env
# Edit .env and set OPENROUTER_API_KEY
```

### 3. Run with Docker Compose

```bash
docker compose -f docker/compose.yml up --build
```

This starts:

| Service | URL |
|---------|-----|
| Gradio UI | `http://localhost:7860` |
| FastAPI | `http://localhost:8000` |
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |

### 4. Run locally (without Docker)

```bash
# Start infrastructure
docker compose -f docker/compose.yml up -d db redis

# Install dependencies
uv sync

# Apply migrations
uv run alembic upgrade head

# Start API
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start worker (separate terminal)
uv run arq app.workers.main.WorkerSettings
```

## Smoke Test

```bash
# 1. Create a session (returns questions immediately)
curl -s -X POST http://localhost:8000/sessions \
  -H 'Content-Type: application/json' \
  -d '{"role":"backend engineer","difficulty":"mid","questionCount":3}' | jq

# 2. Submit an answer (use sessionId/questionId from step 1)
curl -s -X POST http://localhost:8000/sessions/<sessionId>/answers \
  -H 'Content-Type: application/json' \
  -d '{"questionId":<questionId>,"answerText":"My answer text"}' | jq

# 3. Poll for evaluation result
curl -s http://localhost:8000/sessions/<sessionId>/answers/<answerId> | jq

# 4. Get full session summary
curl -s http://localhost:8000/sessions/<sessionId>/summary | jq
```

## Project Structure

```
app/
├── api/            # Routes, schemas, dependencies, error utils
├── core/           # Config, database, queue, logging, constants
├── contracts/      # Prompt templates, output schemas, rubrics
├── models/         # SQLModel table models
├── repositories/   # Data access layer
├── services/       # Business logic orchestration
└── workers/        # ARQ async evaluation worker

interview-ui/       # Gradio frontend
├── app.py          # Blocks app — start, interview, and summary panels
├── client.py       # Async HTTP client wrapping the FastAPI backend
├── state.py        # SessionState TypedDicts and helper functions
├── theme.py        # Gradio Soft theme and custom CSS
└── tests/          # Unit tests (pytest + respx)

alembic/versions/   # Database migrations (001 → 003)
docker/             # Dockerfiles and compose
tests/              # Unit, integration, API, contract tests
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | — |
| `REDIS_URL` | Redis connection string | — |
| `OPENROUTER_API_KEY` | OpenRouter API key | — |
| `OPENROUTER_BASE_URL` | LLM provider base URL | `https://openrouter.ai/api/v1` |
| `OPENROUTER_MODEL` | Model identifier | `openai/gpt-4.1-mini` |
| `QUESTION_PROMPT_VERSION` | Prompt version tag for questions | `v1` |
| `EVALUATION_PROMPT_VERSION` | Prompt version tag for evaluation | `v1` |
| `EVALUATION_SCHEMA_VERSION` | Result schema version tag | `v1` |
| `RUBRIC_VERSION` | Evaluation rubric version tag | `v1` |
| `BACKEND_URL` | FastAPI base URL (used by the UI) | `http://localhost:8000` |
| `UI_HOST` | Gradio server bind address | `0.0.0.0` |
| `UI_PORT` | Gradio server port | `7860` |

## API Reference

Full OpenAPI spec: `specs/001-async-interview-evaluation/contracts/interview-api.yaml`

Interactive docs (when running): `http://localhost:8000/docs`

## Health Check

```bash
curl http://localhost:8000/health
```