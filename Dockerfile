# Stage 1: builder — export pinned requirements via poetry
FROM python:3.11-slim AS builder

WORKDIR /build

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock* ./

RUN poetry export -f requirements.txt --without-hashes --without dev -o requirements.txt


# Stage 2: runtime — lean production image
FROM python:3.11-slim AS runtime

WORKDIR /app

# System deps needed at runtime (libpq for psycopg2-binary, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

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
