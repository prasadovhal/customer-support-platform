# On-Call Runbook

## Alerts and responses

### API latency > 2s (p95)

1. Check `http_request_duration_seconds` histogram in Prometheus/Grafana
2. Identify slow paths via `path` label
3. Check if LLM is the bottleneck: `llm_latency_seconds` histogram
4. Check DB: slow query log in Postgres (`pg_stat_statements`)
5. Mitigation: LLM calls have 3-retry exponential backoff; if Ollama is down the agent returns the fallback response automatically

### API error rate > 1%

1. Check `http_requests_total{status_code=~"5.."}` counter
2. Check application logs (structured JSON via loguru)
3. Common causes: DB pool exhaustion, Redis unavailable, LLM timeout

### Worker queue depth growing

1. Check Redis: `redis-cli llen celery` (default queue)
2. Check worker logs: `docker compose logs worker --tail=100`
3. Scale workers: `docker compose up --scale worker=4 -d`

### Approval SLA breached

1. The `expire_stale_approvals` Celery Beat task runs every 15 minutes
2. Check beat logs: `docker compose logs beat --tail=50`
3. Manual trigger: `docker compose exec worker celery -A app.workers.celery_app call app.workers.tasks.expire_stale_approvals`

### Database disk > 80%

1. Check table sizes: `SELECT pg_size_pretty(pg_total_relation_size(relid)), relname FROM pg_catalog.pg_statio_user_tables ORDER BY pg_total_relation_size(relid) DESC;`
2. Likely cause: `knowledge_chunks` (embedding vectors) or `conversation_messages`
3. Archive old conversations older than 90 days if needed

## Circuit breaker states

The LLM client uses a circuit breaker (`app.core.resilience.CircuitBreaker`):
- **CLOSED**: normal operation
- **OPEN**: LLM unreachable — agent returns fallback response automatically
- **HALF_OPEN**: recovering — next request tests connectivity

Monitor `llm_calls_total{outcome="error"}` to detect circuit breaker activation.

## Graceful degradation

| Component down | System behaviour |
|---|---|
| Ollama (LLM) | Agent returns: "I'm sorry, I wasn't able to process your request. A support agent will follow up." |
| pgvector (RAG) | RAG retrieval skipped; LLM responds without context |
| Redis | Celery workers stop; API continues; rate limiting disabled |
| PostgreSQL | API returns 503 on all DB-dependent endpoints |

## Key metrics to watch

| Metric | Alert threshold |
|---|---|
| `http_request_duration_seconds{quantile="0.95"}` | > 2.0s |
| `agent_calls_total{outcome="fallback"}` / total | > 5% |
| `llm_calls_total{outcome="error"}` / total | > 2% |
| `rag_retrievals_total{outcome="error"}` / total | > 1% |
| `approval_outcomes_total{outcome="approval_required"}` | monitor for spikes |
