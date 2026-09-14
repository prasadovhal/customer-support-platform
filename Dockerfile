# Stage 1: builder — resolve locked deps into a requirements.txt
FROM python:3.11-slim AS builder

WORKDIR /build

RUN pip install --no-cache-dir "poetry==2.3.4"

COPY pyproject.toml poetry.lock* ./

# Install into an in-project venv, then freeze exact pinned versions.
# We copy only the tiny requirements.txt to the runtime stage — never the
# multi-GB .venv — so the runner never needs to hold both in disk at once.
RUN poetry config virtualenvs.in-project true && \
    poetry install --without dev --no-root && \
    poetry run pip freeze > requirements.txt


# Stage 2: runtime — lean production image
FROM python:3.11-slim AS runtime

WORKDIR /app

# System deps needed at runtime (libpq for psycopg2-binary, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy only the pinned requirements list (a few KB) from the builder stage.
# Re-install with --no-cache-dir to keep the runtime layer as small as possible.
COPY --from=builder /build/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Application source and Alembic migrations
COPY src/ /app/src/
COPY alembic.ini /app/alembic.ini
COPY alembic/ /app/alembic/

# Entrypoint script (runs migrations then execs CMD)
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Non-root user for security
RUN groupadd --system nonroot && useradd --system --gid nonroot nonroot
USER nonroot

ENV PYTHONPATH=/app/src

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
