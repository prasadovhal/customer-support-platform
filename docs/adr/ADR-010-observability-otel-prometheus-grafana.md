# ADR-010 — Observability Backend

**Status:** Accepted  
**Date:** 2026-09-13  
**Deciders:** Engineering Lead  
**Supersedes:** —  
**Superseded by:** —

---

## Context

The platform requires end-to-end observability across six instrumented layers:

1. **API layer** — request latency, error rate, status codes, rate limit events
2. **Agent execution** — intent classification, tool selection, approval decisions, workflow state transitions
3. **LLM calls** — model/version, prompt version, token counts, latency, retry count
4. **Retrieval** — query, Recall@K, chunk IDs retrieved, reranker latency, source attribution
5. **Tool calls** — tool name, arguments (PII-masked), result, latency, success/failure
6. **Background workers** — queue depth, task latency, retry count, DLQ events

Requirements OBS-001 through OBS-005 define what must be observable. SEC-007 requires that security-sensitive actions are auditable. The instrumentation layer is already defined: OpenTelemetry (OTel) is already in pyproject.toml as `opentelemetry-api`, `opentelemetry-sdk`, and integrations for FastAPI, SQLAlchemy, Redis, Celery, and httpx.

The decision here is the **observability backend** — where traces, metrics, and logs are shipped to, stored, and visualized.

---

## Decision Drivers

| Driver | Weight | Notes |
|---|---|---|
| Open-source / self-hostable | High | Project principle |
| OTel native / compatible | High | Already instrumented with OTel SDK |
| Trace storage and query | High | Must inspect agent steps, LLM calls, tool call chains |
| Metrics storage and alerting | High | SLO monitoring, drift detection (§27) |
| Cost | High | No per-seat or per-GB SaaS billing |
| AI telemetry support | Medium | Custom spans for LLM/RAG-specific attributes |
| Deployment complexity | Medium | Must run in docker-compose for local dev |

---

## Considered Options

| Option | Traces | Metrics | Logs | OTel native | Self-hosted | Cost |
|---|---|---|---|---|---|---|
| Datadog | Yes | Yes | Yes | Yes (exporter) | No | High (per-host) |
| Honeycomb | Yes | Limited | No | Yes (exporter) | No | Medium (per event) |
| New Relic | Yes | Yes | Yes | Yes (exporter) | No | Medium |
| Grafana Cloud | Yes | Yes | Yes | Yes | Partly (limits) | Low (free tier limited) |
| **OTel Collector + Prometheus + Grafana + Jaeger** | Yes | Yes | Yes (Loki) | Native | Full | Zero |
| Uptrace (self-hosted) | Yes | Limited | No | Yes | Yes | Zero |

---

## Decision

Use a **self-hosted OpenTelemetry stack**:

| Component | Role | Technology |
|---|---|---|
| **OTel Collector** | Receive, process, and export telemetry | `otelcol-contrib` |
| **Prometheus** | Metrics storage and alerting | Prometheus v2 |
| **Grafana** | Dashboards for metrics, traces, and logs | Grafana OSS |
| **Jaeger** | Distributed trace storage and UI | Jaeger all-in-one (dev), Jaeger + Cassandra (prod) |
| **Loki** | Log aggregation (optional, Phase 20) | Grafana Loki |

### Telemetry Flow

```
Application (OTel SDK)
      │
      ▼
OTel Collector (OTLP receiver)
      ├── Traces → Jaeger (OTLP/gRPC)
      ├── Metrics → Prometheus (Prometheus scrape endpoint)
      └── Logs → Loki (OTLP/HTTP)

Grafana
  ├── Datasource: Prometheus  (metrics dashboards, SLO panels)
  ├── Datasource: Jaeger      (trace explorer, agent step visualization)
  └── Datasource: Loki        (log correlation)
```

### Custom AI Telemetry Spans

Beyond standard OTel instrumentation, the following custom spans are required:

```
llm.chat
  attributes: model, prompt_version, token_count_input, token_count_output,
              latency_ms, retry_count, finish_reason

retrieval.query
  attributes: query_text (truncated), retrieval_strategy, n_candidates,
              recall_at_k, chunk_ids[], latency_ms, reranker_used

tool.call
  attributes: tool_name, caller_type, args_schema_valid, latency_ms,
              success, error_type (PII masked per SEC-009)

agent.step
  attributes: step_type, intent, workflow_state, action_selected,
              requires_approval, escalated
```

### docker-compose Integration

The observability stack is included in `docker-compose.yml` as named services: `otel-collector`, `prometheus`, `grafana`, `jaeger`. This allows `docker compose up` to start the full observability stack alongside the API and workers (Phase 23 requirement).

---

## Rationale

**Why self-hosted over SaaS (Datadog, Honeycomb):**  
SaaS observability solutions charge per host, per event, or per GB — costs that accumulate rapidly during development and benchmarking (Phase 21 runs hundreds of evaluation queries). The self-hosted stack has zero incremental cost. The project principle of open-source/self-hostable applies equally to observability infrastructure.

**Why OTel Collector as an intermediary:**  
The OTel Collector decouples the application from the backend. Adding a new backend (e.g., migrating from Jaeger to Tempo) requires only a Collector configuration change, not application code changes. It also enables telemetry sampling, attribute filtering (PII masking before export), and fan-out to multiple backends.

**Why Jaeger over Tempo:**  
Both are valid. Jaeger was chosen because the `opentelemetry-exporter-jaeger` library is already in pyproject.toml, reducing the delta for Phase 20 implementation. Tempo is the preferred long-term backend for large-scale deployments and is a straightforward migration path.

**Why Prometheus over InfluxDB or VictoriaMetrics:**  
Prometheus is the standard metrics backend for the Kubernetes/Docker ecosystem and has the most complete Grafana integration. The OTel SDK already includes a Prometheus exporter via `opentelemetry-exporter-prometheus`.

---

## Consequences

**Positive:**
- Zero incremental cost; all components are Apache 2.0 or AGPLv3 licensed.
- OTel Collector provides a centralized PII scrubbing point before telemetry reaches storage — supporting SEC-009.
- Grafana unified dashboards correlate metrics, traces, and logs in a single UI.
- SLO dashboards (API availability ≥ 99.5%, P95 latency < 3s) are native Prometheus/Grafana constructs.
- Custom AI spans give visibility into retrieval quality, LLM behavior, and agent decisions that SaaS tools would require additional configuration to capture.

**Negative / Trade-offs:**
- Self-hosted observability requires operational maintenance (storage growth, retention configuration, alertmanager setup).
- Jaeger all-in-one is not production-grade at high trace volume; Cassandra backend or migration to Grafana Tempo is needed for Phase 26.
- docker-compose observability stack adds ~1.5GB of RAM overhead in development.

**Risks and Mitigations:**
- Storage overflow from high trace/metric volume: mitigated by configuring OTel Collector sampling (10% for non-error traces in production) and Prometheus retention policy (30 days).
- Alertmanager configuration complexity: mitigated by starting with recording rules only (no paging) in Phase 20; alerting thresholds added in Phase 27.

---

## Review Triggers

Revisit this ADR if:
- Phase 26 cloud deployment reveals that self-hosted observability storage costs exceed managed alternatives at production scale.
- Grafana Tempo matures to the point where it offers a clear operational advantage over Jaeger for this use case.
- A compliance or audit requirement emerges that requires SLA-backed trace retention.
