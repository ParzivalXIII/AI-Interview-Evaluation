#!/bin/sh
set -e

# Run Alembic migrations then start the requested process
if [ "$1" = "api" ]; then
    echo "Running database migrations..."
    uv run alembic upgrade head
    echo "Starting API server..."
    exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
elif [ "$1" = "worker" ]; then
    echo "Starting ARQ evaluation worker..."
    exec uv run arq app.workers.main.WorkerSettings
else
    exec "$@"
fi
