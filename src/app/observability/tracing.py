"""Lightweight OTel span helpers for the agent, RAG, and ML hot paths.

Each helper is an async context manager that:
  - Creates a child span under the active trace (no-op if tracing is disabled).
  - Sets standard span attributes.
  - Records exceptions and marks the span as ERROR on failure.

Usage::

    async with trace_agent(conversation_id="abc", intent="return_refund"):
        result = await run_agent(...)

    async with trace_rag(query="return policy", strategy="bm25+dense"):
        chunks = await pipeline.query(...)
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional


def _get_tracer():
    try:
        from opentelemetry import trace
        return trace.get_tracer("customer_support.observability")
    except Exception:
        return None


@asynccontextmanager
async def trace_agent(
    conversation_id: str,
    intent: Optional[str] = None,
) -> AsyncGenerator[None, None]:
    tracer = _get_tracer()
    if tracer is None:
        yield
        return

    with tracer.start_as_current_span("agent.workflow") as span:
        span.set_attribute("conversation.id", conversation_id)
        if intent:
            span.set_attribute("agent.intent", intent)
        try:
            yield
        except Exception as exc:
            span.record_exception(exc)
            try:
                from opentelemetry.trace import StatusCode
                span.set_status(StatusCode.ERROR, str(exc))
            except Exception:
                pass
            raise


@asynccontextmanager
async def trace_rag(
    query: str,
    strategy: str = "hybrid",
) -> AsyncGenerator[None, None]:
    tracer = _get_tracer()
    if tracer is None:
        yield
        return

    with tracer.start_as_current_span("rag.retrieval") as span:
        span.set_attribute("rag.query_length", len(query))
        span.set_attribute("rag.strategy", strategy)
        try:
            yield
        except Exception as exc:
            span.record_exception(exc)
            raise


@asynccontextmanager
async def trace_llm(
    model: str,
    conversation_id: Optional[str] = None,
) -> AsyncGenerator[None, None]:
    tracer = _get_tracer()
    if tracer is None:
        yield
        return

    with tracer.start_as_current_span("llm.chat") as span:
        span.set_attribute("llm.model", model)
        if conversation_id:
            span.set_attribute("conversation.id", conversation_id)
        try:
            yield
        except Exception as exc:
            span.record_exception(exc)
            raise


@asynccontextmanager
async def trace_ml(task: str) -> AsyncGenerator[None, None]:
    tracer = _get_tracer()
    if tracer is None:
        yield
        return

    with tracer.start_as_current_span("ml.inference") as span:
        span.set_attribute("ml.task", task)
        try:
            yield
        except Exception as exc:
            span.record_exception(exc)
            raise
