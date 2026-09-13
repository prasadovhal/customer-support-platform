# Architecture Decision Records

This directory contains all Architecture Decision Records (ADRs) for the Enterprise Customer Support AI Platform.

Every significant architectural decision is documented here: what was decided, what was considered, why, and what the trade-offs are.

---

## ADR Format

Each ADR contains:

```
Status         — Proposed / Accepted / Deprecated / Superseded
Context        — What problem required a decision
Decision Drivers — What criteria mattered and their weight
Considered Options — Alternatives evaluated with pros/cons
Decision       — What was chosen and how to implement it
Rationale      — Why this over the alternatives
Consequences   — Trade-offs: positive, negative, risks
Review Triggers — Conditions that should prompt revisiting
```

---

## Index

### Accepted

| ADR | Title | Unblocks |
|---|---|---|
| [ADR-001](ADR-001-postgresql-primary-database.md) | PostgreSQL as Primary Relational Database | Database schema, all data layer work |
| [ADR-002](ADR-002-vector-store-pgvector.md) | Vector Store: pgvector (V1 Baseline) | RAG pipeline, embedding pipeline |
| [ADR-003](ADR-003-hybrid-retrieval-rrf.md) | Hybrid Retrieval: BM25 + Dense with RRF | Phase 9 RAG pipeline, retrieval evaluation |
| [ADR-004](ADR-004-reranker-cross-encoder.md) | Reranker: Cross-Encoder MiniLM-L-6-v2 | Phase 9 reranking layer, groundedness improvement |
| [ADR-005](ADR-005-workflow-orchestration-langgraph.md) | Workflow Orchestration: LangGraph | Agent implementation, approval workflows |
| [ADR-006](ADR-006-embedding-model-bge-base.md) | Embedding Model: BAAI/bge-base-en-v1.5 | Phase 9 dense retrieval, pgvector indexing |
| [ADR-007](ADR-007-async-processing-redis-celery.md) | Async Processing: Redis + Celery | Worker service, approval notifications, ingestion |
| [ADR-009](ADR-009-authentication-oauth2-jwt.md) | Authentication: OAuth 2.0 + JWT | API layer, tool authorization, service identity |
| [ADR-010](ADR-010-observability-otel-prometheus-grafana.md) | Observability: OTel + Prometheus + Grafana + Jaeger | Phase 20 observability stack |
| [ADR-011](ADR-011-cloud-provider-aws.md) | Cloud Provider: AWS (+ Hetzner for GPU) | Phase 26 cloud deployment |
| [ADR-012](ADR-012-iac-opentofu.md) | Infrastructure as Code: OpenTofu | Phase 26 IaC modules |
| [ADR-013](ADR-013-production-llm-serving-vllm.md) | Production LLM Serving: vLLM | Phase 26 GPU serving layer |

### Proposed (Pending Benchmarking)

| ADR | Title | Confirmed After |
|---|---|---|
| [ADR-008](ADR-008-llm-model-selection-llama31.md) | LLM Model: Llama 3.1 8B (proposed baseline) | LLM-003 domain benchmarking (Phase 11) |

---

## Decision Order

ADRs are ordered by when the decision must be made, not when they were written:

```
Before Phase 6 (Backend):     ADR-001, ADR-009
Before Phase 7 (Database):    ADR-001, ADR-002
Before Phase 11 (Agent):      ADR-005, ADR-007
Before Phase 9 (RAG):         ADR-003, ADR-004, ADR-006
Before Phase 8/11 (LLM):      ADR-008, ADR-013
Before Phase 20 (Observability): ADR-010
Before Phase 26 (Cloud):      ADR-011, ADR-012
```

---

## Traceability

Every ADR links to:
- The requirement section that drove it.
- The use cases it enables.
- The implementation phase it unblocks.

| ADR | Key Requirements | Use Cases Enabled |
|---|---|---|
| ADR-001 | §19 Database, REL-003, FR-013 | All |
| ADR-002 | FR-004, EMB-001, EMB-002 | UC-01, UC-03, UC-07 |
| ADR-003 | FR-004, EVAL-002, EMB-001 | UC-01, UC-03, UC-07, UC-10 |
| ADR-004 | FR-004, FR-005, EVAL-002 | UC-01, UC-03, UC-07 |
| ADR-005 | FR-013, FR-012, LLM-001 | UC-04, UC-05, UC-06, UC-11 |
| ADR-006 | FR-004, EMB-001, EMB-002 | UC-01, UC-03, UC-07 |
| ADR-007 | §15 Async Processing, FR-011 | UC-04, UC-05, UC-06, UC-11, UC-12 |
| ADR-008 | LLM-001, LLM-002, LLM-003 | All (UC-01 through UC-12) |
| ADR-009 | SEC-001, SEC-002, SEC-003, SEC-004 | UC-02, UC-04, UC-05, UC-06 |
| ADR-010 | OBS-001–005, SEC-007 | All |
| ADR-011 | §23 Deployment, REL-001–007 | All (production) |
| ADR-012 | §23 Deployment (open-source principle) | All (production) |
| ADR-013 | LLM-004, REL-007, §21 SLOs | All (production) |
