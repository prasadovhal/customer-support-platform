"""LangFuse tracing integration for the agent, RAG, and LLM hot paths.

Provides a lazy-initialised singleton Langfuse client and span helpers.
All helpers are no-ops when LANGFUSE_ENABLED=false or when keys are absent,
so the application degrades gracefully without any code changes at call sites.

Trace hierarchy per agent call:
    Trace: agent_invocation  (session_id = conversation_id)
      ├─ Span: classify_intent
      ├─ Span: retrieve_knowledge
      ├─ Span: handle_action        (only when actionable intent)
      └─ Generation: llm_generate   (model, prompt, response, latency)
"""
from __future__ import annotations

import threading
from typing import Any, Optional

from loguru import logger

_lock = threading.Lock()
_client: Any = None  # Langfuse | None
_initialised = False


def get_langfuse() -> Any:
    """Return the singleton Langfuse client, or None if disabled/unavailable."""
    global _client, _initialised
    if _initialised:
        return _client
    with _lock:
        if _initialised:
            return _client
        try:
            from app.core.config import get_settings

            cfg = get_settings()
            if not cfg.LANGFUSE_ENABLED:
                _initialised = True
                return None
            if not cfg.LANGFUSE_PUBLIC_KEY or not cfg.LANGFUSE_SECRET_KEY:
                logger.warning(
                    "LangFuse enabled but LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY not set — tracing disabled"
                )
                _initialised = True
                return None

            from langfuse import Langfuse

            _client = Langfuse(
                public_key=cfg.LANGFUSE_PUBLIC_KEY,
                secret_key=cfg.LANGFUSE_SECRET_KEY,
                host=cfg.LANGFUSE_HOST,
            )
            logger.info(f"LangFuse tracing enabled → {cfg.LANGFUSE_HOST}")
        except ImportError:
            logger.warning("langfuse package not installed — tracing disabled")
        except Exception as exc:
            logger.warning(f"LangFuse initialisation failed: {exc}")
        finally:
            _initialised = True
    return _client


def create_trace(
    name: str,
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    input_data: Optional[dict] = None,
    metadata: Optional[dict] = None,
) -> Any:
    """Create a new LangFuse trace and return it (or None)."""
    lf = get_langfuse()
    if lf is None:
        return None
    try:
        kwargs: dict[str, Any] = {"name": name}
        if session_id:
            kwargs["session_id"] = session_id
        if user_id:
            kwargs["user_id"] = user_id
        if input_data:
            kwargs["input"] = input_data
        if metadata:
            kwargs["metadata"] = metadata
        return lf.trace(**kwargs)
    except Exception as exc:
        logger.debug(f"LangFuse create_trace failed: {exc}")
        return None


def create_span(
    trace: Any,
    name: str,
    input_data: Optional[Any] = None,
    output_data: Optional[Any] = None,
    metadata: Optional[dict] = None,
    level: str = "DEFAULT",
) -> Any:
    """Create a child span on an existing trace (or None if trace is None)."""
    if trace is None:
        return None
    try:
        kwargs: dict[str, Any] = {"name": name}
        if input_data is not None:
            kwargs["input"] = input_data
        if output_data is not None:
            kwargs["output"] = output_data
        if metadata:
            kwargs["metadata"] = metadata
        return trace.span(**kwargs)
    except Exception as exc:
        logger.debug(f"LangFuse create_span failed: {exc}")
        return None


def end_span(
    span: Any, output_data: Optional[Any] = None, metadata: Optional[dict] = None
) -> None:
    """End a span with optional output and metadata."""
    if span is None:
        return
    try:
        kwargs: dict[str, Any] = {}
        if output_data is not None:
            kwargs["output"] = output_data
        if metadata:
            kwargs["metadata"] = metadata
        span.end(**kwargs)
    except Exception as exc:
        logger.debug(f"LangFuse end_span failed: {exc}")


def log_generation(
    trace: Any,
    name: str,
    model: str,
    input_messages: list[dict],
    output: str,
    latency_ms: int,
    metadata: Optional[dict] = None,
) -> None:
    """Log an LLM generation event on a trace."""
    if trace is None:
        return
    try:
        gen_kwargs: dict[str, Any] = {
            "name": name,
            "model": model,
            "input": input_messages,
            "output": output,
            "metadata": {
                "latency_ms": latency_ms,
                **(metadata or {}),
            },
        }
        trace.generation(**gen_kwargs)
    except Exception as exc:
        logger.debug(f"LangFuse log_generation failed: {exc}")


def update_trace_output(
    trace: Any, output_data: Any, metadata: Optional[dict] = None
) -> None:
    """Update a trace's output after all spans are complete."""
    if trace is None:
        return
    try:
        kwargs: dict[str, Any] = {"output": output_data}
        if metadata:
            kwargs["metadata"] = metadata
        trace.update(**kwargs)
    except Exception as exc:
        logger.debug(f"LangFuse update_trace failed: {exc}")


def flush() -> None:
    """Flush all pending LangFuse events to the cloud."""
    lf = get_langfuse()
    if lf is None:
        return
    try:
        lf.flush()
    except Exception as exc:
        logger.debug(f"LangFuse flush failed: {exc}")
