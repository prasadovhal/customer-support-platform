#!/bin/sh
# Entrypoint shared by api, worker, and beat containers.
# Only the api container runs migrations (RUN_MIGRATIONS=true).
set -e

if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
    echo "[entrypoint] Running database migrations..."
    alembic upgrade head
fi

echo "[entrypoint] Starting application..."
exec "$@"
