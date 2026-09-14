# Stage 1: builder — install deps into an in-project virtualenv
FROM python:3.11-slim AS builder

WORKDIR /build

RUN pip install --no-cache-dir "poetry==2.3.4"

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.in-project true && \
    poetry install --without dev --no-root


# Stage 2: runtime — lean production image
FROM python:3.11-slim AS runtime

WORKDIR /app

# System deps needed at runtime (libpq for psycopg2-binary, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy the pre-built virtualenv from builder
COPY --from=builder /build/.venv /app/.venv

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

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app/src

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
