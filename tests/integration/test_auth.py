"""Integration tests for POST /auth/token and POST /auth/refresh."""
from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.integration.conftest import _customer_token

pytestmark = pytest.mark.asyncio


class TestLogin:
    async def test_login_returns_tokens(self, async_client: AsyncClient, make_customer):
        customer = await make_customer(email="alice@test.com", password="Secret99!")

        resp = await async_client.post(
            "/api/v1/auth/token",
            json={"username": "alice@test.com", "password": "Secret99!"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"
        assert body["expires_in"] > 0

    async def test_login_wrong_password_returns_401(
        self, async_client: AsyncClient, make_customer
    ):
        await make_customer(email="bob@test.com", password="RealPass1!")
        resp = await async_client.post(
            "/api/v1/auth/token",
            json={"username": "bob@test.com", "password": "WrongPass!"},
        )
        assert resp.status_code == 401

    async def test_login_unknown_email_returns_401(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/auth/token",
            json={"username": "nobody@test.com", "password": "whatever"},
        )
        assert resp.status_code == 401

    async def test_login_suspended_account_returns_401(
        self, async_client: AsyncClient, make_customer
    ):
        await make_customer(
            email="suspended@test.com", password="Pass123!", status="suspended"
        )
        resp = await async_client.post(
            "/api/v1/auth/token",
            json={"username": "suspended@test.com", "password": "Pass123!"},
        )
        assert resp.status_code == 401


class TestRefresh:
    async def test_refresh_returns_new_tokens(
        self, async_client: AsyncClient, make_customer
    ):
        customer = await make_customer(email="charlie@test.com", password="Pass123!")

        login = await async_client.post(
            "/api/v1/auth/token",
            json={"username": "charlie@test.com", "password": "Pass123!"},
        )
        refresh_token = login.json()["refresh_token"]

        resp = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["access_token"] != login.json()["access_token"]

    async def test_refresh_with_invalid_token_returns_401(
        self, async_client: AsyncClient
    ):
        resp = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "not.a.real.token"},
        )
        assert resp.status_code == 401
