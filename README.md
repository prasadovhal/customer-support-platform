# Enterprise Customer Support AI Platform

Production-grade AI/ML platform combining classical ML, hybrid RAG, agentic workflows, policy-governed tool use, human-in-the-loop approvals, observability, and CI/CD — built to demonstrate Principal Data Scientist / Principal Applied AI engineering.

## Architecture

```
Customer Request
      │
      ▼
FastAPI (REST API)
      │
      ▼
LangGraph Agent Workflow
 ├── Intent Classification  ← ML model (scikit-learn) + keyword fallback
 ├── Hybrid RAG Retrieval   ← BM25 + dense embeddings + cross-encoder reranker
 ├── Policy Engine          ← stateless rule evaluation (refund / cancel / account)
 ├── Approval Workflow      ← human-in-the-loop for high-risk actions
 └── LLM Generation         ← Ollama (llama3.2) with retry + circuit breaker
      │
      ▼
Response + Observability (Prometheus metrics, OTel traces, structured logs)
```

## Tech stack

| Layer | Technology |
|---|---|
| API | FastAPI, Pydantic v2, Uvicorn |
| Database | PostgreSQL 15 + pgvector |
| Queue / Cache | Redis, Celery |
| Agent workflow | LangGraph |
| LLM serving | Ollama (llama3.2) |
| Embeddings | sentence-transformers (bge-base-en) |
| Retrieval | BM25 (rank-bm25) + dense + cross-encoder reranker |
| ML models | scikit-learn (intent, priority, routing, escalation) |
| Observability | Prometheus, OpenTelemetry, Jaeger, loguru |
| Auth | JWT (OAuth2 password + refresh flow) |
| CI/CD | GitHub Actions (lint → typecheck → unit → integration → docker build) |
| Containerisation | Docker, docker-compose |

## Quick start

```bash
# 1. Install dependencies
poetry install --with dev

# 2. Start infrastructure
docker compose up db redis -d

# 3. Configure environment
cp .env.example .env   # then edit JWT_SECRET_KEY and DB/Redis URLs for local dev

# 4. Run migrations
poetry run alembic upgrade head

# 5. Start API
poetry run uvicorn app.main:app --reload --port 8000
```

See `docs/deployment/local_setup.md` for the full setup guide.

## Full stack (Docker)

```bash
docker compose up                          # API + worker + beat + db + redis
docker compose --profile llm up            # + Ollama LLM
docker compose --profile observability up  # + Jaeger tracing UI
```

## Running tests

```bash
# Unit tests (158 tests, no external services)
poetry run pytest tests/unit/ -q

# Integration tests (43 tests, requires running Postgres)
TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/customer_support_test \
  poetry run pytest tests/integration/ -q
```

## Key components

### Agent workflow (`src/app/agent/`)

LangGraph state machine: `classify_intent → retrieve_knowledge → handle_action → generate_response`

- Intent classified by ML model with keyword-heuristic fallback
- Hybrid RAG: BM25 + dense retrieval fused with RRF, optionally reranked
- Policy engine gates high-risk actions before LLM can proceed
- OllamaClient has 3-attempt exponential-backoff retry + circuit breaker

### Policy engine (`src/app/policy/`)

Stateless `PolicyEngine.evaluate(PolicyContext) → PolicyDecision`. Outcomes:
- `auto_approve` — within threshold for customer segment
- `approval_required` — above threshold, creates `ApprovalRequest` for human review
- `denied` — policy hard-reject (e.g. order too old, wrong status)

### Approval workflow (`src/app/api/v1/approvals.py`)

Full lifecycle: `pending_approval → approved / denied / timeout`. Celery Beat expires stale approvals every 15 minutes. Agents require explicit scope (`approve:refunds`, `approve:cancellations`).

### Observability (`src/app/observability/`)

- **Prometheus metrics**: HTTP, agent, LLM, RAG, ML inference, approval outcome counters/histograms
- **OTel tracing**: async context manager helpers for agent, RAG, LLM spans (no-op without Jaeger)
- **Structured logs**: loguru JSON with request ID propagation

### Evaluation platform (`src/app/evaluation/`)

- Retrieval metrics: Recall@K, Precision@K, MRR, nDCG@K
- Groundedness: context coverage, token F1, doc-ID hit rate
- Regression gate: blocks CI if metrics degrade > 5% from baseline
- `EvaluationPlatform` class orchestrates all three for unified reports

### Resilience (`src/app/core/resilience.py`)

- `with_retry` decorator: tenacity-backed exponential backoff, configurable exceptions
- `CircuitBreaker`: CLOSED → OPEN → HALF_OPEN state machine, recovery timeout
- Applied to all external I/O (LLM, future external APIs)

## CI/CD (`.github/workflows/ci.yml`)

```
lint (ruff) ──┐
              ├──► unit tests ──► integration tests (pgvector service)
typecheck ────┘        └──► eval gate
docker build (independent, layer-cached)
```

## Repository structure

```
src/app/
├── agent/          # LangGraph workflow, LLM client, tools
├── api/v1/         # FastAPI routes (conversations, messages, approvals, …)
├── core/           # config, exceptions, resilience
├── db/             # SQLAlchemy engine, session, base
├── evaluation/     # retrieval metrics, groundedness, eval platform
├── experiments/    # experiment registry for A/B comparisons
├── ml/             # intent/priority/routing/escalation classifiers
├── models/         # SQLAlchemy ORM models
├── observability/  # Prometheus metrics, middleware, OTel tracing
├── policy/         # stateless policy engine and defaults
├── rag/            # chunker, embedder, retriever, reranker, pipeline
├── schemas/        # Pydantic request/response models
├── security/       # JWT, password hashing, dependencies
└── workers/        # Celery app, task definitions
```

## Docs

- `docs/adr/` — 13 Architecture Decision Records
- `docs/architecture/` — system architecture and data flows
- `docs/deployment/local_setup.md` — developer setup guide
- `docs/runbooks/on_call.md` — incident response playbook
