# Stage 1: builder — export dependencies via poetry
FROM python:3.11-slim AS builder

WORKDIR /build

RUN pip install --no-cache-dir poetry

COPY pyproject.toml ./
COPY poetry.lock* ./

RUN poetry export -f requirements.txt --without-hashes --without dev -o requirements.txt


# Stage 2: runtime — lean production image
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install compiled dependencies
COPY --from=builder /build/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ /app/src/

# Non-root user for security
RUN groupadd --system nonroot && useradd --system --gid nonroot nonroot
USER nonroot

ENV PYTHONPATH=/app/src

EXPOSE 8000
