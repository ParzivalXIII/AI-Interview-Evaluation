# Quickstart: Async Interview Evaluation Engine

## Goal

Run the API, PostgreSQL, Redis, and ARQ workers locally so the end-to-end interview workflow can be exercised.

## Prerequisites

- Docker and Docker Compose available on Linux
- `uv` installed for local Python dependency management
- An OpenRouter API key for model access

## Environment Variables

Create a local `.env` file with values equivalent to the following:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/interview_eval
REDIS_URL=redis://redis:6379/0
OPENROUTER_API_KEY=your-key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-4.1-mini
QUESTION_PROMPT_VERSION=v1
EVALUATION_PROMPT_VERSION=v1
EVALUATION_SCHEMA_VERSION=v1
RUBRIC_VERSION=v1
```

## Local Setup

1. Install project dependencies.

```bash
uv sync
```

1. Start infrastructure services.

```bash
docker compose -f docker/compose.yml up -d db redis
```

1. Apply database migrations.

```bash
uv run alembic upgrade head
```

1. Start the FastAPI application.

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

1. Start the ARQ evaluation worker process.

```bash
uv run arq app.workers.main.WorkerSettings
```

1. Optional: run the full containerized stack.

```bash
docker compose -f docker/compose.yml up --build
```

## Smoke Test Flow

1. Create a session.

```bash
curl -X POST http://localhost:8000/sessions \
  -H 'Content-Type: application/json' \
  -d '{"role":"backend engineer","difficulty":"mid","questionCount":3}'
```

1. Poll the session until it becomes `ready` and capture a returned `questionId`.

```bash
curl http://localhost:8000/sessions/<sessionId>
```

1. Submit an answer.

```bash
curl -X POST http://localhost:8000/sessions/<sessionId>/answers \
  -H 'Content-Type: application/json' \
  -d '{"questionId":"<questionId>","answerText":"My candidate answer"}'
```

1. Poll for the evaluation result.

```bash
curl http://localhost:8000/sessions/<sessionId>/answers/<answerId>
```

1. Retrieve the full session summary.

```bash
curl http://localhost:8000/sessions/<sessionId>/summary
```

## Test Strategy

- Unit tests mock LangChain and OpenRouter responses.
- Integration tests run against PostgreSQL and Redis.
- Contract tests validate API schemas and worker job payloads.
- End-to-end tests exercise session creation, answer submission, worker evaluation, and result retrieval.
