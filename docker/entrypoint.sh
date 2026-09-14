#!/bin/sh
# Entrypoint for the API container.
# Runs Alembic migrations before starting the server so the schema is always
# up-to-date without a separate migration step in docker-compose.
set -e

echo "[entrypoint] Running database migrations..."
alembic upgrade head

echo "[entrypoint] Starting application..."
exec "$@"
