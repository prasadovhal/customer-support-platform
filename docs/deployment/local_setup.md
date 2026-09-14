# Local Development Setup

## Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Runtime |
| Poetry | 1.7+ | Dependency management |
| Docker Desktop | Latest | PostgreSQL + Redis |
| Ollama | Latest | Local LLM serving |

## 1. Clone and install dependencies

```bash
git clone <repo>
cd customer-support-platform
poetry install --with dev
```

## 2. Start infrastructure

```bash
docker compose up db redis -d
```

Wait for health checks to pass (`docker compose ps`).

## 3. Configure environment

```bash
cp .env.example .env
# Edit .env — at minimum set:
#   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/customer_support
#   REDIS_URL=redis://localhost:6379/0
#   JWT_SECRET_KEY=$(openssl rand -hex 32)
```

For local dev, replace `db` and `redis` service names with `localhost` in `.env`.

## 4. Run database migrations

```bash
poetry run alembic upgrade head
```

## 5. Start the API

```bash
poetry run uvicorn app.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`.

## 6. (Optional) Start Ollama for LLM

```bash
docker compose --profile llm up ollama -d
ollama pull llama3.2
```

## 7. Run tests

```bash
# Unit tests (no DB required)
poetry run pytest tests/unit/ -q

# Integration tests (requires running DB)
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/customer_support_test \
  poetry run pytest tests/integration/ -q
```

## Common issues

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Ensure `PYTHONPATH=src` or run via `poetry run` |
| DB connection refused | Run `docker compose up db -d` and wait for healthcheck |
| JWT decode error in tests | Ensure `JWT_SECRET_KEY` env var is set |
| Ollama timeout | Check `OLLAMA_BASE_URL` points to running Ollama instance |
