# ADR-007 — Async Processing: Redis + Celery

**Status:** Accepted  
**Date:** 2026-09-07  
**Deciders:** Engineering Lead  
**Supersedes:** —  
**Superseded by:** —

---

## Context

The platform requires reliable asynchronous processing for operations that must not block the synchronous API response path:

- Approval notification dispatch to human agents.
- Customer notification emails (refund processed, escalation confirmed, verification code).
- Knowledge base document ingestion, chunking, and embedding.
- Re-indexing on embedding model change.
- Approval timeout checking (scheduled, recurring).
- Evaluation job execution (retrieval eval, agent eval, ML eval).
- Analytics and business metric computation.
- Dead-letter handling for persistently failing jobs.

Key requirements from FR-011, §15 (Async Processing Requirements):
- At-least-once delivery for important jobs.
- Idempotent consumers for state-changing jobs.
- Retries with bounded backoff.
- Failure tracking and dead-letter handling.
- Queue-depth monitoring.
- The synchronous API must return before async work completes.

---

## Decision Drivers

| Driver | Weight | Notes |
|---|---|---|
| At-least-once delivery | High | Important jobs must not be silently dropped |
| Idempotent consumers | High | Retry must not cause duplicate business actions |
| Retry with backoff | High | Transient failures must not lose jobs |
| Dead-letter queue | High | Persistent failures must be captured |
| Python-native | High | Entire stack is Python |
| Operational simplicity | High | Redis already in stack for caching |
| Queue-depth monitoring | Medium | Operations must be able to observe backlogs |
| Scheduled / periodic tasks | Medium | Approval timeout check needs a scheduler |
| Self-hostable | High | Project principle |
| Cost | Medium | Redis already required — no extra infra |

---

## Considered Options

### Option A — Redis + Celery

Redis as message broker; Celery as the task queue and worker framework. Celery Beat for scheduled tasks.

**Pros:**
- Celery is the most mature Python async task library.
- Redis is already in the stack for caching and rate limiting — no additional service.
- Built-in retry with exponential backoff (`autoretry_for`, `max_retries`, `countdown`).
- Dead-letter queue via `task_reject_on_worker_lost` + DLQ routing.
- Celery Beat handles the approval timeout scheduler without a separate cron service.
- Rich monitoring: Flower dashboard, Prometheus exporter.
- Widely understood — large community, extensive documentation.

**Cons:**
- Redis is not a true message broker — no guaranteed message ordering across partitions, limited to at-most-once delivery by default.
- At-least-once delivery requires acknowledgement + `acks_late=True` configuration.
- Redis Streams (more durable) require different Celery configuration vs. Redis Lists.
- Task routing and prioritization require explicit configuration.

### Option B — RabbitMQ + Celery

RabbitMQ as the AMQP broker; Celery as the worker framework.

**Pros:**
- True message broker: persistent queues, guaranteed delivery, message acknowledgement native.
- Better message ordering guarantees.
- Dead-letter exchange (DLX) is a native RabbitMQ concept.
- Better fit for Celery's native AMQP primitives.

**Cons:**
- Adds RabbitMQ as a new service (ops overhead: setup, monitoring, backup).
- Higher operational complexity than Redis for V1 needs.
- Redis is already required — running both adds service sprawl.

### Option C — Redis Queues (RQ)

Python-native task queue using Redis. Simpler API than Celery.

**Pros:**
- Simpler than Celery — less configuration.
- Redis-native.

**Cons:**
- Fewer production features: limited retry configuration, no built-in Beat scheduler, weaker monitoring.
- Smaller community than Celery.
- Would require a separate scheduler for approval timeout checks.

### Option D — Kafka + custom consumer

Apache Kafka as the message broker with custom consumer code.

**Pros:**
- True at-least-once (and exactly-once with transactions) delivery.
- High throughput, persistent log.
- Replay capability for debugging.

**Cons:**
- Massive operational overhead for V1 scale.
- Requires Zookeeper or KRaft, schema registry, consumer group management.
- No Python-native task abstraction — must write consumer code from scratch.
- Overkill: V1 message volumes are trivially low.

### Option E — Temporal Workers

Use Temporal (from ADR-005 Option C) for async tasks in addition to workflows.

**Cons:**
- Already rejected in ADR-005 for workflow orchestration due to operational complexity.
- Would add Temporal server as another service.

---

## Decision

**Use Redis as broker + Celery as worker framework**, with Celery Beat for scheduled tasks.

Configuration choices to ensure at-least-once delivery and idempotency:

```python
# celery_config.py
CELERY_BROKER_URL = "redis://redis:6379/1"        # DB 1 for tasks (DB 0 for cache)
CELERY_RESULT_BACKEND = "redis://redis:6379/2"    # DB 2 for results
CELERY_TASK_ACKS_LATE = True                       # at-least-once: ack after completion
CELERY_TASK_REJECT_ON_WORKER_LOST = True           # re-queue on worker crash
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_TRACK_STARTED = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1              # one task at a time per worker (safer for idempotency)
```

**Dead-letter queue:**
Route tasks that exhaust retries to a `dead_letter` queue. A monitoring alert fires when this queue is non-empty.

**Scheduled tasks (Celery Beat):**
```python
CELERY_BEAT_SCHEDULE = {
    "check-approval-timeouts": {
        "task": "workers.approval.check_timeouts",
        "schedule": 900.0,    # every 15 minutes
    },
    "check-verification-expiry": {
        "task": "workers.verification.check_expiry",
        "schedule": 300.0,    # every 5 minutes
    },
}
```

---

## Rationale

**Why Redis over RabbitMQ:**
Redis is already required for caching and rate limiting. Adding RabbitMQ for at-most-once-vs-at-least-once delivery guarantees is not warranted at V1 scale — the gap is closed by `acks_late=True` and idempotent consumers. Two services instead of one is the wrong trade at V1.

**Why Celery over RQ:**
Celery provides built-in retry with exponential backoff, Celery Beat for scheduling, priority queues, task routing, and a monitoring ecosystem (Flower). RQ would require building these capabilities.

**Why not Kafka:**
V1 message volumes do not justify Kafka's operational complexity. Kafka's strengths (high throughput, log replay, exactly-once) are not needed at this scale.

---

## Queue Structure

```
Queue               Priority    Workers    Tasks
──────────────────────────────────────────────────────────
critical            High        2          execute_refund, execute_cancellation,
                                           execute_account_change
approvals           High        2          send_approval_notification,
                                           check_approval_timeouts
notifications       Normal      2          send_customer_notification,
                                           send_verification_challenge
ingestion           Low         1          ingest_document, reindex_knowledge_base
evaluation          Low         1          run_retrieval_eval, run_agent_eval,
                                           run_ml_eval
analytics           Low         1          compute_business_metrics
dead_letter         —           Manual     All exhausted tasks
```

---

## Idempotency Contract

Every state-changing Celery task must follow this pattern:

```python
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(TransientError,),
    acks_late=True,
    reject_on_worker_lost=True,
)
def execute_refund(self, approval_id: str, idempotency_key: str):
    # 1. Check idempotency key
    if idempotency_key_exists(idempotency_key):
        return {"status": "already_processed"}

    # 2. Mark as processing (atomic with check above, using DB transaction)
    with db.transaction():
        insert_idempotency_key(idempotency_key, status="processing")

    try:
        # 3. Execute business logic
        result = do_refund(approval_id)

        # 4. Mark complete
        update_idempotency_key(idempotency_key, status="completed", result=result)
        return result

    except Exception as exc:
        # 5. On failure: idempotency key remains "processing" → safe to retry
        raise self.retry(exc=exc)
```

---

## Consequences

**Positive:**
- Docker Compose stack gains no new services — Redis already present.
- `acks_late=True` + idempotent consumers provide at-least-once safety.
- Celery Beat eliminates need for a separate cron service for approval timeout and verification expiry checks.
- Queue-depth monitoring available via Redis `LLEN` + Flower dashboard + Prometheus exporter.
- Task retry and dead-letter handling are configuration, not code.

**Negative / Trade-offs:**
- Redis is not a true message broker — message persistence is limited (Redis RDB/AOF configuration required for durability, not just caching defaults).
- Redis restart without persistence loses in-flight queued tasks — mitigated by `acks_late=True` (tasks re-queued if worker crashes) and Redis AOF persistence for the task DB.
- Celery Beat is a single point of failure for scheduled tasks — acceptable for V1; for production, Beat should run with a lock (e.g., `redbeat` distributed lock scheduler).

---

## Redis Configuration Notes

Two separate Redis databases must be used to avoid operational confusion:

```
Redis DB 0 — Cache (short-lived: policy cache, rate limits, session data)
Redis DB 1 — Celery broker (task queue — must use AOF persistence)
Redis DB 2 — Celery results backend
```

The task queue database (DB 1) must use AOF (`appendonly yes`) persistence to avoid losing queued tasks on restart. The cache database (DB 0) can use RDB or no persistence.

---

## Review Triggers

Revisit this ADR if:
- Task volume grows to where Redis becomes a bottleneck (unlikely at V1 scale).
- Exactly-once delivery semantics become a hard requirement (upgrade to RabbitMQ or Kafka).
- Celery Beat reliability issues arise under production load (upgrade to `redbeat` or Temporal).
- Multi-region deployment requires distributed task routing.
