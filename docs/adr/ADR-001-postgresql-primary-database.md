# ADR-001 — PostgreSQL as Primary Relational Database

**Status:** Accepted  
**Date:** 2026-09-07  
**Deciders:** Engineering Lead  
**Supersedes:** —  
**Superseded by:** —

---

## Context

The platform requires a primary data store for all transactional runtime data: customers, products, orders, conversations, support tickets, approval state, policy store, audit logs, idempotency keys, and ML/embedding metadata.

The data model is relational: orders reference customers, tickets reference conversations, approval records reference orders and policy versions. Referential integrity and transactional consistency are critical — particularly for the approval workflow, where an approval record and workflow state must be written atomically, and for idempotency keys, where a duplicate check and insert must be atomic.

The store also needs to support: complex filtered queries (policy by effective date, orders by customer, approvals by state and SLA deadline), migrations as schema evolves, and efficient read access for tool calls within agent response latency budgets.

---

## Decision Drivers

| Driver | Weight | Notes |
|---|---|---|
| ACID transactions | High | Approval + workflow state atomic writes |
| Referential integrity | High | Customer→Order→Ticket→Approval chains |
| Operational complexity | High | Minimize services for V1 |
| Python ecosystem maturity | High | SQLAlchemy, asyncpg, Alembic |
| JSON support | Medium | Agent execution traces, tool call payloads |
| Full-text search | Low | BM25 handled separately |
| pgvector extension | Medium | Potential to co-locate vector index for V1 |
| Open-source / self-hostable | High | Project principle |
| Cost | Medium | Local dev + cloud deployment |

---

## Considered Options

| Option | ACID | Relational | Python ecosystem | Self-hosted | Notes |
|---|---|---|---|---|---|
| **PostgreSQL** | Full | Yes | Excellent | Yes | pgvector extension available |
| MySQL / MariaDB | Full | Yes | Good | Yes | Weaker JSON, no vector extension |
| SQLite | File-level | Yes | Good | Yes (embedded) | Not suitable for multi-service |
| MongoDB | Document-level | No | Good | Yes | Schema flexibility not needed; no relational integrity |
| CockroachDB | Full (distributed) | Yes | Good | Yes | Overkill for V1 scale |

---

## Decision

**Use PostgreSQL** as the sole primary relational database for all transactional and operational data.

Use the **pgvector** extension within the same PostgreSQL instance for vector storage in V1 (deferred to ADR-002 for detailed vector store evaluation).

Use **SQLAlchemy** (async) as the ORM / query builder, **asyncpg** as the async driver, and **Alembic** for schema migrations.

---

## Rationale

**Why PostgreSQL over MySQL/MariaDB:**
- pgvector extension eliminates the need for a separate vector database in V1.
- Superior JSON handling (JSONB) for agent execution traces and policy store values.
- More expressive SQL (window functions, CTEs, lateral joins) useful for evaluation queries.
- Stronger community tooling in the Python ML/AI ecosystem (pgvector, pgai).

**Why not MongoDB:**
- The data model is inherently relational (customers → orders → tickets → approvals). Document flexibility adds complexity without benefit.
- Referential integrity cannot be enforced at the database level, requiring application-level enforcement for every operation.
- ACID transactions across collections are more limited.

**Why not SQLite:**
- Not suitable for multi-service deployment (API + Worker both writing concurrently).
- No pgvector extension.

---

## Consequences

**Positive:**
- Single database service reduces operational complexity.
- pgvector allows starting RAG without a dedicated vector database.
- Alembic provides a disciplined migration path as schema evolves.
- Full ACID transactions support the approval + workflow state atomic write requirement.
- Rich query capability handles policy-by-date and SLA-deadline queries natively.

**Negative / Trade-offs:**
- PostgreSQL is not horizontally write-scalable without additional tooling (Citus, read replicas only for reads).
- Vector search performance in pgvector degrades at very large scale (millions of vectors with complex filters) compared to dedicated stores — acceptable for V1 (~100 KB documents → ~1,000 chunks).
- Single point of failure without a replica — mitigated by RPO < 1 hour / RTO < 4 hours backup requirement (§19 of requirements).

**Risks and Mitigations:**
- Vector search at scale: mitigated by ADR-002 (vector store can be migrated if benchmarking shows pgvector insufficient).
- Connection pooling under load: mitigated by PgBouncer or SQLAlchemy connection pool configuration.
- Schema drift: mitigated by Alembic with enforced migration discipline (no direct DDL changes).

---

## Schema Responsibilities

PostgreSQL owns the following logical domains:

```
Runtime data:       customers, products, orders, order_events
Support workflow:   support_tickets, conversations, conversation_messages
Agent runtime:      agent_executions, tool_calls
Approval workflow:  approval_requests, approval_audit_log, verification_requests
Policy store:       policies, policy_audit_log, intent_taxonomy_versions
Infrastructure:     idempotency_keys, conversation_workflow_state
RAG metadata:       knowledge_documents, knowledge_chunks, embedding_metadata
ML registry:        model_versions, evaluation_results
```

Vector embeddings (chunk_id → vector) live in the pgvector extension within the same instance but are logically treated as a separate concern (see ADR-002).

---

## Review Triggers

Revisit this ADR if:
- Vector search performance benchmarks show pgvector insufficient for the retrieval quality or latency targets.
- Write throughput requirements exceed single-primary PostgreSQL capacity.
- A requirement for distributed/multi-region data emerges.
