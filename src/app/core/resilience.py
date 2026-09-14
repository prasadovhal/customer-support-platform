from __future__ import annotations

import functools
import time
from dataclasses import dataclass
from typing import Any, Callable

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.exceptions import ServiceUnavailableError


@dataclass
class RetryConfig:
    max_attempts: int = 3
    wait_min_seconds: float = 0.5
    wait_max_seconds: float = 10.0
    reraise: bool = True


def with_retry(
    config: RetryConfig | None = None,
    exceptions: tuple = (Exception,),
) -> Callable:
    cfg = config if config is not None else RetryConfig()

    def decorator(fn: Callable) -> Callable:
        retrying = retry(
            stop=stop_after_attempt(cfg.max_attempts),
            wait=wait_exponential(
                min=cfg.wait_min_seconds,
                max=cfg.wait_max_seconds,
            ),
            retry=retry_if_exception_type(exceptions),
            reraise=cfg.reraise,
        )
        return retrying(fn)

    return decorator


_CLOSED = "closed"
_OPEN = "open"
_HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        name: str = "circuit",
    ) -> None:
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._name = name
        self._state: str = _CLOSED
        self._failure_count: int = 0
        self._last_failure_time: float | None = None

    def is_open(self) -> bool:
        if self._state == _OPEN:
            if (
                self._last_failure_time is not None
                and time.monotonic() - self._last_failure_time >= self._recovery_timeout
            ):
                self._state = _HALF_OPEN
                return False
            return True
        return False

    def record_success(self) -> None:
        self._failure_count = 0
        self._last_failure_time = None
        self._state = _CLOSED

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self._failure_threshold:
            self._state = _OPEN

    def __call__(self, fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if self.is_open():
                raise ServiceUnavailableError(
                    f"Circuit breaker '{self._name}' is open."
                )
            try:
                result = await fn(*args, **kwargs)
            except Exception:
                self.record_failure()
                raise
            self.record_success()
            return result

        return wrapper
