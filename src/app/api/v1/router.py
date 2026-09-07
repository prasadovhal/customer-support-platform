from __future__ import annotations

from fastapi import APIRouter

from app.api.v1 import (
    approvals,
    auth,
    conversations,
    customers,
    health,
    messages,
    orders,
    tickets,
    webhooks,
)

v1_router = APIRouter()

# Health / readiness — no prefix so they sit at /health and /ready
v1_router.include_router(health.router)

# Auth
v1_router.include_router(auth.router)

# Domain resources
v1_router.include_router(conversations.router)
v1_router.include_router(messages.router)
v1_router.include_router(tickets.router)
v1_router.include_router(customers.router)
v1_router.include_router(orders.router)
v1_router.include_router(approvals.router)
v1_router.include_router(webhooks.router)
