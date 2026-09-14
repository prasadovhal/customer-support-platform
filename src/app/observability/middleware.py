"""ASGI middleware that records HTTP metrics and emits structured access logs."""
from __future__ import annotations

import time
from typing import Awaitable, Callable

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.observability.metrics import HTTP_REQUEST_DURATION, HTTP_REQUESTS

# Paths we never want to appear in metric label cardinality
_SKIP_METRIC_PATHS = frozenset({"/metrics", "/health", "/ready"})

# Collapse path parameters so label cardinality stays bounded:
# /api/v1/conversations/550e.../messages  →  /api/v1/conversations/{id}/messages
_PARAM_SEGMENTS = frozenset({
    # UUID-shaped (8-4-4-4-12 hex groups or 32 hex chars)
})


def _normalise_path(path: str) -> str:
    """Replace UUID path segments with {id} to bound label cardinality."""
    import re

    _UUID_RE = re.compile(
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
        re.IGNORECASE,
    )
    return _UUID_RE.sub("{id}", path)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Record Prometheus HTTP metrics and emit a structured access log line."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        start = time.perf_counter()

        response = await call_next(request)

        duration = time.perf_counter() - start
        method = request.method
        path = _normalise_path(request.url.path)
        status = str(response.status_code)
        request_id = response.headers.get("X-Request-ID", "")

        # Record Prometheus metrics (skip noisy infra endpoints)
        if path not in _SKIP_METRIC_PATHS:
            HTTP_REQUESTS.labels(method=method, path=path, status_code=status).inc()
            HTTP_REQUEST_DURATION.labels(method=method, path=path).observe(duration)

        # Structured access log
        logger.bind(
            request_id=request_id,
            method=method,
            path=path,
            status_code=int(status),
            duration_ms=round(duration * 1000, 1),
        ).info(f"{method} {path} → {status} ({duration * 1000:.1f}ms)")

        return response
