# Quickstart: Minimal Interview UI

**Date**: 2026-03-15 | **Plan**: [plan.md](./plan.md)

---

## Prerequisites

- Python 3.12 and `uv` installed
- The FastAPI backend running (locally or via Docker)
- A `.env` file at the repo root (copy `.env.example` if it does not exist)

---

## 1. Local Development (against a locally running API)

### Step 1 — Back-end must be running first

```bash
# Option A: Run the full stack in Docker
cd /home/parzival/projects/AI-Interview-Evaluation
docker compose -f docker/compose.yml up -d

# Option B: Run the API directly
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 2 — Configure the UI environment

The `.env` file at repo root is shared between the backend and the UI. Add:

```dotenv
# UI configuration
BACKEND_URL=http://localhost:8000
UI_PORT=7860
```

If running inside Docker Compose, `BACKEND_URL` should be `http://api:8000` (set automatically in `docker/compose.yml`).

### Step 3 — Install dependencies

```bash
# From the repo root (uv installs into the shared .venv)
uv sync
```

### Step 4 — Run the UI

```bash
uv run interview-ui/app.py
```

The Gradio interface is now accessible at [http://localhost:7860](http://localhost:7860).  
The UI connects to the backend at `BACKEND_URL` (defaults to `http://localhost:8000`).

---

## 2. Docker Compose (full stack, all services)

After adding the `ui` service to `docker/compose.yml`:

```bash
cd /home/parzival/projects/AI-Interview-Evaluation

# Build all images (includes the new ui image)
docker compose -f docker/compose.yml build

# Start all services
docker compose -f docker/compose.yml up -d

# Tail UI logs
docker compose -f docker/compose.yml logs ui -f
```

| Service | Internal URL | Exposed port |
|---------|--------------|--------------|
| FastAPI API | `http://api:8000` | 8000 |
| Gradio UI | `http://ui:7860` | **7860** |
| PostgreSQL | `postgres://db:5432` | 5432 |
| Redis | `redis://redis:6379` | 6379 |

Open [http://localhost:7860](http://localhost:7860) in a browser to use the interview UI.

---

## 3. Running Tests

```bash
# All tests (backend + UI)
uv run -m pytest

# UI layer only
uv run -m pytest interview-ui/tests/ -v

# Backend only
uv run -m pytest tests/ -v
```

---

## 4. Interview Workflow (End-to-End)

1. **Open** [http://localhost:7860](http://localhost:7860)
2. **Fill in** the start form: Role (e.g., "Backend Engineer"), Difficulty, number of questions
3. **Click** "Start Interview" — the backend generates questions; the first question appears
4. **Type** your answer in the text area
5. **Click** "Submit Answer"
   - If there are more questions: the UI advances to the next question immediately
   - If it is the last (or only) question: a "Evaluating…" indicator appears
6. **Wait** — every 5 seconds the UI polls for evaluation results
7. **Read** the evaluation score, feedback, strengths, and improvements when they appear
8. **Navigate** between questions using the question nav row to review completed answers

---

## 5. Environment Variable Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_URL` | `http://localhost:8000` | FastAPI backend base URL |
| `UI_PORT` | `7860` | Port the Gradio server listens on |
| `UI_HOST` | `0.0.0.0` | Host binding |

---

## 6. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| "Failed to connect to backend" on start | API not running or wrong `BACKEND_URL` | Check `docker ps` / confirm `BACKEND_URL` |
| Questions never appear after "Start Interview" | LLM timeout or API key missing | Check `docker compose logs api` |
| Evaluation stays "Evaluating…" indefinitely | Worker not running | Check `docker compose logs worker`; ensure migrations are applied |
| Gradio UI shows blank page | Port conflict on 7860 | Set `UI_PORT=7861` in `.env` |
