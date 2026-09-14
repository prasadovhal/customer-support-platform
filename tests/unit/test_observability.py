"""Unit tests for Phase 13 observability components."""
from __future__ import annotations

import pytest
from prometheus_client import REGISTRY, CollectorRegistry


# ── Metrics definitions ───────────────────────────────────────────────────────

def test_all_metrics_registered():
    """All expected metric names must exist in the default Prometheus registry."""
    from app.observability.metrics import (
        AGENT_CALLS, AGENT_LATENCY,
        APPROVAL_OUTCOMES,
        HTTP_REQUEST_DURATION, HTTP_REQUESTS,
        LLM_CALLS, LLM_LATENCY,
        ML_INFERENCES, ML_LATENCY,
        RAG_LATENCY, RAG_RETRIEVALS,
    )
    # prometheus_client strips _total from Counter names internally; check base names
    expected_names = {
        "http_requests",
        "http_request_duration_seconds",
        "agent_calls",
        "agent_latency_seconds",
        "llm_calls",
        "llm_latency_seconds",
        "rag_retrievals",
        "rag_retrieval_latency_seconds",
        "ml_inferences",
        "ml_inference_latency_seconds",
        "approval_outcomes",
    }
    registered = {m.name for m in REGISTRY.collect()}
    for name in expected_names:
        assert name in registered, f"Expected metric '{name}' not found in registry"


def test_http_requests_counter_increments():
    from app.observability.metrics import HTTP_REQUESTS

    before = _read_counter(HTTP_REQUESTS, method="GET", path="/test", status_code="200")
    HTTP_REQUESTS.labels(method="GET", path="/test", status_code="200").inc()
    after = _read_counter(HTTP_REQUESTS, method="GET", path="/test", status_code="200")
    assert after == before + 1.0


def test_agent_calls_counter_increments():
    from app.observability.metrics import AGENT_CALLS

    before = _read_counter(AGENT_CALLS, intent="return_refund", outcome="success")
    AGENT_CALLS.labels(intent="return_refund", outcome="success").inc()
    after = _read_counter(AGENT_CALLS, intent="return_refund", outcome="success")
    assert after == before + 1.0


def test_llm_calls_counter_tracks_errors():
    from app.observability.metrics import LLM_CALLS

    before = _read_counter(LLM_CALLS, model="llama3.2", outcome="error")
    LLM_CALLS.labels(model="llama3.2", outcome="error").inc()
    after = _read_counter(LLM_CALLS, model="llama3.2", outcome="error")
    assert after == before + 1.0


def test_rag_retrievals_counter():
    from app.observability.metrics import RAG_RETRIEVALS

    before = _read_counter(RAG_RETRIEVALS, strategy="bm25+dense+reranked", outcome="success")
    RAG_RETRIEVALS.labels(strategy="bm25+dense+reranked", outcome="success").inc()
    after = _read_counter(RAG_RETRIEVALS, strategy="bm25+dense+reranked", outcome="success")
    assert after == before + 1.0


def test_approval_outcomes_counter_per_action():
    from app.observability.metrics import APPROVAL_OUTCOMES

    before_auto = _read_counter(APPROVAL_OUTCOMES, action="issue_refund", outcome="auto_approve")
    before_pend = _read_counter(APPROVAL_OUTCOMES, action="issue_refund", outcome="approval_required")

    APPROVAL_OUTCOMES.labels(action="issue_refund", outcome="auto_approve").inc()
    APPROVAL_OUTCOMES.labels(action="issue_refund", outcome="auto_approve").inc()
    APPROVAL_OUTCOMES.labels(action="issue_refund", outcome="approval_required").inc()

    assert _read_counter(APPROVAL_OUTCOMES, action="issue_refund", outcome="auto_approve") == before_auto + 2.0
    assert _read_counter(APPROVAL_OUTCOMES, action="issue_refund", outcome="approval_required") == before_pend + 1.0


def test_ml_inferences_no_model_label():
    from app.observability.metrics import ML_INFERENCES

    before = _read_counter(ML_INFERENCES, task="category", outcome="no_model")
    ML_INFERENCES.labels(task="category", outcome="no_model").inc()
    assert _read_counter(ML_INFERENCES, task="category", outcome="no_model") == before + 1.0


# ── Path normalisation ────────────────────────────────────────────────────────

def test_normalise_path_replaces_uuid():
    from app.observability.middleware import _normalise_path

    raw = "/api/v1/conversations/550e8400-e29b-41d4-a716-446655440000/messages"
    assert _normalise_path(raw) == "/api/v1/conversations/{id}/messages"


def test_normalise_path_leaves_clean_paths():
    from app.observability.middleware import _normalise_path

    assert _normalise_path("/api/v1/health") == "/api/v1/health"


def test_normalise_path_multiple_uuids():
    from app.observability.middleware import _normalise_path

    raw = "/api/v1/customers/550e8400-e29b-41d4-a716-446655440000/orders/6ba7b810-9dad-11d1-80b4-00c04fd430c8"
    result = _normalise_path(raw)
    assert result == "/api/v1/customers/{id}/orders/{id}"


# ── Tracing helpers (no-op when OTel not configured) ──────────────────────────

@pytest.mark.asyncio
async def test_trace_agent_noop_without_otel():
    """trace_agent should be a transparent no-op if OTel is not configured."""
    from app.observability.tracing import trace_agent

    ran = False
    async with trace_agent(conversation_id="test-123", intent="greeting"):
        ran = True
    assert ran


@pytest.mark.asyncio
async def test_trace_rag_noop_without_otel():
    from app.observability.tracing import trace_rag

    ran = False
    async with trace_rag(query="return policy", strategy="bm25"):
        ran = True
    assert ran


@pytest.mark.asyncio
async def test_trace_llm_noop_without_otel():
    from app.observability.tracing import trace_llm

    ran = False
    async with trace_llm(model="llama3.2"):
        ran = True
    assert ran


@pytest.mark.asyncio
async def test_trace_propagates_exceptions():
    """Exceptions inside a trace context manager must propagate outward."""
    from app.observability.tracing import trace_agent

    with pytest.raises(ValueError, match="boom"):
        async with trace_agent(conversation_id="test-123"):
            raise ValueError("boom")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _read_counter(metric, **labels) -> float:
    """Read current value of a labelled counter from the registry."""
    for sample in metric.collect()[0].samples:
        if sample.labels == labels:
            return sample.value
    return 0.0
