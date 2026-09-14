"""Prometheus metric definitions for the customer support platform.

All metrics use a shared default registry.  Import from this module wherever
you need to record observations — do not create new metric objects elsewhere.
"""
from __future__ import annotations

from prometheus_client import Counter, Histogram, REGISTRY  # noqa: F401 — re-exported

# ── HTTP layer ────────────────────────────────────────────────────────────────

HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests handled",
    labelnames=["method", "path", "status_code"],
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    labelnames=["method", "path"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# ── Agent workflow ────────────────────────────────────────────────────────────

AGENT_CALLS = Counter(
    "agent_calls_total",
    "Total support agent workflow invocations",
    labelnames=["intent", "outcome"],  # outcome: success | fallback
)

AGENT_LATENCY = Histogram(
    "agent_latency_seconds",
    "End-to-end agent workflow latency in seconds",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
)

# ── LLM calls ─────────────────────────────────────────────────────────────────

LLM_CALLS = Counter(
    "llm_calls_total",
    "Total calls made to the LLM backend",
    labelnames=["model", "outcome"],  # outcome: success | error
)

LLM_LATENCY = Histogram(
    "llm_latency_seconds",
    "LLM response latency in seconds",
    labelnames=["model"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 20.0, 30.0, 60.0],
)

# ── RAG retrieval ─────────────────────────────────────────────────────────────

RAG_RETRIEVALS = Counter(
    "rag_retrievals_total",
    "Total RAG knowledge retrieval calls",
    labelnames=["strategy", "outcome"],  # outcome: success | error
)

RAG_LATENCY = Histogram(
    "rag_retrieval_latency_seconds",
    "RAG retrieval latency in seconds",
    labelnames=["strategy"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

# ── ML inference ──────────────────────────────────────────────────────────────

ML_INFERENCES = Counter(
    "ml_inferences_total",
    "Total ML model inference calls",
    labelnames=["task", "outcome"],  # outcome: success | error | no_model
)

ML_LATENCY = Histogram(
    "ml_inference_latency_seconds",
    "ML inference latency in seconds",
    labelnames=["task"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25],
)

# ── Approval workflow ─────────────────────────────────────────────────────────

APPROVAL_OUTCOMES = Counter(
    "approval_outcomes_total",
    "Approval requests by policy outcome",
    labelnames=[
        "action",
        "outcome",
    ],  # outcome: auto_approve | approval_required | denied
)
