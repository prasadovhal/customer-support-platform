from __future__ import annotations

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestHealthEndpoint:
    async def test_health_returns_200(self, async_client: AsyncClient) -> None:
        response = await async_client.get("/api/v1/health")
        assert response.status_code == 200

    async def test_health_returns_ok_status(self, async_client: AsyncClient) -> None:
        response = await async_client.get("/api/v1/health")
        body = response.json()
        assert body["status"] == "ok"

    async def test_health_returns_service_name(self, async_client: AsyncClient) -> None:
        response = await async_client.get("/api/v1/health")
        body = response.json()
        assert "service" in body
        assert isinstance(body["service"], str)
        assert len(body["service"]) > 0

    async def test_health_returns_version(self, async_client: AsyncClient) -> None:
        response = await async_client.get("/api/v1/health")
        body = response.json()
        assert "version" in body


class TestReadyEndpoint:
    async def test_ready_returns_200_when_db_available(
        self, async_client: AsyncClient, db_session
    ) -> None:
        """When the test DB is reachable the /ready endpoint should return 200.

        Note: Redis may not be running in CI — we patch the Redis check so the
        test focuses only on DB connectivity which we can guarantee.
        """
        import unittest.mock as mock

        with mock.patch("app.api.v1.health.aioredis") as mock_redis:
            mock_client = mock.AsyncMock()
            mock_client.ping = mock.AsyncMock(return_value=True)
            mock_client.aclose = mock.AsyncMock()
            mock_redis.from_url.return_value = mock_client

            response = await async_client.get("/api/v1/ready")

        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ready"

    async def test_ready_returns_503_when_redis_unavailable(
        self, async_client: AsyncClient, db_session
    ) -> None:
        """When Redis is down the /ready endpoint must return 503."""
        import unittest.mock as mock

        with mock.patch("app.api.v1.health.aioredis") as mock_redis:
            mock_client = mock.AsyncMock()
            mock_client.ping = mock.AsyncMock(
                side_effect=Exception("Connection refused")
            )
            mock_client.aclose = mock.AsyncMock()
            mock_redis.from_url.return_value = mock_client

            response = await async_client.get("/api/v1/ready")

        assert response.status_code == 503
