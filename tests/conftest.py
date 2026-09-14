from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ---------------------------------------------------------------------------
# Minimal test settings — must be set BEFORE any app imports that call
# get_settings() so pydantic-settings resolves the required fields.
# ---------------------------------------------------------------------------
_TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/customer_support_test",
)
_TEST_JWT_SECRET = "test-secret-key-for-unit-tests-only"

os.environ.setdefault("DATABASE_URL", _TEST_DATABASE_URL)
os.environ.setdefault("JWT_SECRET_KEY", _TEST_JWT_SECRET)
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DEBUG", "true")

from app.core.config import get_settings  # noqa: E402 — must follow env setup
from app.db.base import Base  # noqa: E402
from app.main import app  # noqa: E402


# ---------------------------------------------------------------------------
# Session-scoped event loop — required so session-scoped async fixtures
# (create_tables) share the same loop as per-test fixtures.
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Settings fixture
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def settings():
    """Return a Settings instance configured for testing."""
    get_settings.cache_clear()
    return get_settings()


# ---------------------------------------------------------------------------
# Async test DB engine / session
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def test_engine(settings):
    """Create a test async engine scoped to the whole test session."""
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
    )
    return engine


@pytest_asyncio.fixture(scope="session")
async def create_tables(test_engine):
    """Create all tables at the start of the test session and drop them after.

    Skips gracefully if the database is not reachable (e.g. Docker not running).
    """
    import pytest
    try:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        pytest.skip(f"Database not reachable — skipping integration tests: {exc}")
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture()
async def db_session(test_engine, create_tables) -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession that rolls back after each test."""
    session_factory = async_sessionmaker(
        bind=test_engine,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )
    async with session_factory() as session:
        async with session.begin():
            yield session
            await session.rollback()


# ---------------------------------------------------------------------------
# HTTP client fixture
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture()
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Return an AsyncClient wired to the FastAPI app with the test DB session."""
    from app.db.session import get_db

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
