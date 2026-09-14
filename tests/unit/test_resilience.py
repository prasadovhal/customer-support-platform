from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core.exceptions import ServiceUnavailableError
from app.core.resilience import CircuitBreaker, RetryConfig, with_retry

pytestmark = pytest.mark.asyncio

_NO_WAIT = RetryConfig(max_attempts=3, wait_min_seconds=0.0, wait_max_seconds=0.0)


# ── with_retry ────────────────────────────────────────────────────────────────


async def test_with_retry_succeeds_on_third_attempt():
    call_count = 0

    @with_retry(config=_NO_WAIT)
    async def flaky() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("not yet")
        return "ok"

    result = await flaky()
    assert result == "ok"
    assert call_count == 3


async def test_with_retry_raises_after_max_attempts():
    call_count = 0

    @with_retry(config=_NO_WAIT)
    async def always_fails() -> None:
        nonlocal call_count
        call_count += 1
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        await always_fails()

    assert call_count == 3


async def test_with_retry_no_retry_on_success():
    call_count = 0

    @with_retry(config=_NO_WAIT)
    async def succeeds() -> str:
        nonlocal call_count
        call_count += 1
        return "done"

    result = await succeeds()
    assert result == "done"
    assert call_count == 1


async def test_with_retry_only_retries_matching_exceptions():
    call_count = 0

    @with_retry(config=_NO_WAIT, exceptions=(ValueError,))
    async def wrong_exc() -> None:
        nonlocal call_count
        call_count += 1
        raise TypeError("not retried")

    with pytest.raises(TypeError):
        await wrong_exc()

    assert call_count == 1


# ── CircuitBreaker ────────────────────────────────────────────────────────────


async def test_circuit_breaker_starts_closed():
    cb = CircuitBreaker(failure_threshold=3)
    assert cb.is_open() is False


async def test_circuit_breaker_opens_after_threshold():
    cb = CircuitBreaker(failure_threshold=3)
    for _ in range(3):
        cb.record_failure()
    assert cb.is_open() is True


async def test_circuit_breaker_transitions_to_half_open_after_timeout():
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
    for _ in range(3):
        cb.record_failure()
    assert cb.is_open() is True

    # Advance monotonic clock past recovery_timeout
    with patch(
        "app.core.resilience.time.monotonic", return_value=cb._last_failure_time + 31.0
    ):
        assert cb.is_open() is False


async def test_circuit_breaker_resets_after_success():
    cb = CircuitBreaker(failure_threshold=3)
    for _ in range(3):
        cb.record_failure()
    assert cb.is_open() is True

    @cb
    async def ok_fn() -> str:
        return "ok"

    # Manually force half_open so we can call through
    cb._state = "half_open"
    result = await ok_fn()
    assert result == "ok"
    assert cb.is_open() is False
    assert cb._failure_count == 0


async def test_circuit_breaker_raises_when_open():
    cb = CircuitBreaker(failure_threshold=2)
    cb.record_failure()
    cb.record_failure()
    assert cb.is_open() is True

    @cb
    async def fn() -> str:
        return "should not reach"

    with pytest.raises(ServiceUnavailableError):
        await fn()


async def test_circuit_breaker_record_success_resets_failure_count():
    cb = CircuitBreaker(failure_threshold=5)
    cb.record_failure()
    cb.record_failure()
    assert cb._failure_count == 2

    cb.record_success()
    assert cb._failure_count == 0
    assert cb._last_failure_time is None
    assert cb.is_open() is False


async def test_circuit_breaker_wraps_async_fn_and_records_failure():
    cb = CircuitBreaker(failure_threshold=3)

    @cb
    async def bad_fn() -> None:
        raise RuntimeError("fail")

    with pytest.raises(RuntimeError):
        await bad_fn()

    assert cb._failure_count == 1


async def test_circuit_breaker_wraps_async_fn_and_records_success():
    cb = CircuitBreaker(failure_threshold=3)

    @cb
    async def good_fn() -> str:
        return "value"

    result = await good_fn()
    assert result == "value"
    assert cb._failure_count == 0
    assert cb.is_open() is False
