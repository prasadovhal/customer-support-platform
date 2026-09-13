# ADR-009 — Authentication and Authorization: OAuth 2.0 + JWT

**Status:** Accepted  
**Date:** 2026-09-07  
**Deciders:** Engineering Lead  
**Supersedes:** —  
**Superseded by:** —

---

## Context

The platform has three distinct authentication contexts, each with different trust and scope requirements:

**1. Customer authentication**
Customers interact via the API to submit messages, check orders, and initiate sensitive actions (refunds, account changes). The system must verify identity before any customer-specific data is accessed or modified.

**2. Human support agent authentication**
Human agents access the platform to handle escalations and submit approval decisions for high-risk actions (refunds, cancellations, account changes). These users have elevated permissions and their actions are audited.

**3. Service-to-service authentication**
The Worker Service (Celery) calls internal APIs and tools to execute approved actions. The Evaluation harness calls agent and retrieval APIs in sandboxed mode. These callers must have scoped, verifiable identities — not shared secrets embedded in code.

**Key constraints from requirements:**
- SEC-001: Authentication required for all API access.
- SEC-002: Role- and action-based authorization enforced.
- SEC-003: Least privilege — each caller gets only required permissions.
- SEC-004: No hard-coded secrets.
- FR-014: Tool authorization enforced by application logic, not the LLM.
- SEC-011: Chat session alone is insufficient for high-risk account changes (separate re-verification required).

---

## Decision Drivers

| Driver | Weight | Notes |
|---|---|---|
| Industry standard / interoperability | High | Must work with enterprise clients and tooling |
| Stateless verification | High | API is horizontally scalable — no session store for auth |
| Scoped permissions | High | customer / agent / service / eval each need different scopes |
| Service-to-service support | High | Worker and eval harness need machine identity |
| Token expiry and revocation | High | Short-lived access tokens; refresh for human sessions |
| Secret management | High | No hard-coded credentials anywhere |
| Python ecosystem support | High | FastAPI native OAuth2 support via python-jose / PyJWT |
| Self-hostable for V1 | Medium | Auth server can be lightweight for V1 |
| Open-source | High | Project principle |

---

## Considered Options

### Option A — OAuth 2.0 + JWT (Access + Refresh Tokens)

OAuth 2.0 authorization framework with JWT access tokens. FastAPI has native `OAuth2PasswordBearer` and JWT validation support. For V1, a lightweight embedded auth service issues tokens; in production, can be replaced by an external IdP.

**Pros:**
- Industry standard — every enterprise integration team knows it.
- JWT: stateless verification on every API node (no DB lookup per request).
- Scopes: fine-grained permission control (`read:orders`, `approve:refunds`, etc.).
- Refresh tokens: human sessions stay alive; access tokens expire quickly (15 min).
- Service-to-service: Client Credentials flow gives workers machine identity.
- FastAPI `Depends(oauth2_scheme)` integrates cleanly with dependency injection.

**Cons:**
- JWT revocation is not instant — must wait for token expiry or maintain a revocation list.
- Requires an auth server (lightweight for V1, external IdP for production).
- Token management (refresh, rotation) adds client complexity.

### Option B — API Keys Only

Simple static API keys per client, validated on each request.

**Pros:**
- Simple to implement and understand.
- No token expiry management.

**Cons:**
- No scoped permissions — all keys have the same access or require per-key ACLs.
- Key rotation is manual and disruptive.
- No standard service-to-service identity.
- Does not support human agent sessions with re-authentication.
- Not suitable for the customer-facing flow where per-user identity is required.

### Option C — Session-Based (Server-Side Sessions)

Server manages session state; client holds a session cookie.

**Pros:**
- Instant revocation (delete session from store).
- Simpler client implementation.

**Cons:**
- Requires a shared session store (Redis) that every API node reads from — adds latency and coupling.
- Stateful — conflicts with horizontal scaling goal.
- Not standard for API-first platforms (APIs are called programmatically, not browser-session-based).
- Does not naturally support service-to-service auth.

### Option D — mTLS (Mutual TLS) for service-to-service

Each service holds a client certificate; services verify each other's certs.

**Pros:**
- Strong cryptographic identity for services.
- No token management.

**Cons:**
- Certificate management complexity for V1.
- Does not address human user authentication.
- Requires PKI infrastructure.
- Overlaps with JWT for service-to-service — not necessary to combine both.

---

## Decision

**Use OAuth 2.0 with JWT access tokens** for all three authentication contexts.

- **Customer access:** Password grant (or authorization code for browser-based) → short-lived JWT (15 min) + refresh token (7 days).
- **Human agent access:** Password grant → short-lived JWT (60 min) + refresh token (8 hours, matching shift length).
- **Service-to-service (Worker, Eval):** Client Credentials flow → short-lived JWT (5 min, auto-refreshed).

For V1, use a **lightweight embedded auth module** (FastAPI + PyJWT + PostgreSQL for user store). This is replaceable by an external IdP (Keycloak, Auth0, Okta) in production without changing the API contract, since the JWT format and scopes remain the same.

---

## Token Design

### JWT Claims Structure

```json
{
  "sub": "C-123",
  "type": "customer",
  "scopes": ["read:own_orders", "read:own_customer", "submit:support_messages"],
  "session_id": "sess-abc",
  "iat": 1725696000,
  "exp": 1725696900,
  "iss": "support-platform-auth"
}
```

### Scope Definitions

| Scope | Granted to | Permits |
|---|---|---|
| `read:own_orders` | Customer | get_order where order.customer_id == sub |
| `read:own_customer` | Customer | get_customer where id == sub |
| `submit:support_messages` | Customer | POST /conversations/{id}/messages |
| `read:all_orders` | Human Agent | get_order (any customer) |
| `read:all_customers` | Human Agent | get_customer (any) |
| `approve:refunds` | Human Agent | POST /approvals/{id}/decision (refund actions) |
| `approve:cancellations` | Human Agent | POST /approvals/{id}/decision (cancellation actions) |
| `approve:account_changes` | Human Agent | POST /approvals/{id}/decision (account change actions) |
| `admin:policy` | Administrator | Policy CRUD |
| `admin:knowledge` | Administrator | Knowledge base ingest/manage |
| `service:execute_tools` | Worker | Tool execution (post-approval) |
| `service:read_all` | Worker | Read any customer/order for async tasks |
| `eval:sandbox` | Eval Harness | All reads; write only to sandboxed test data |

### Flow by Actor

```
Customer:
  POST /auth/token {grant_type: password, username, password}
  → {access_token (15 min JWT), refresh_token (7 days)}
  → API calls: Authorization: Bearer {access_token}
  → On expiry: POST /auth/refresh → new access_token

Human Agent:
  POST /auth/token {grant_type: password, username, password}
  → {access_token (60 min), refresh_token (8 hours)}

Worker (Service):
  POST /auth/token {grant_type: client_credentials, client_id, client_secret}
  → {access_token (5 min)} — refreshed automatically before expiry
  → client_id/secret: from environment variables (never hard-coded)

Eval Harness:
  client_credentials → access_token with eval:sandbox scope
  → tool calls routed to test data only
```

---

## FastAPI Integration

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def get_current_customer(token: str = Depends(oauth2_scheme)) -> TokenPayload:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["RS256"])
        if payload["type"] != "customer":
            raise HTTPException(status_code=403)
        return TokenPayload(**payload)
    except JWTError:
        raise HTTPException(status_code=401)

async def require_scope(required_scope: str):
    def checker(token_payload: TokenPayload = Depends(get_current_customer)):
        if required_scope not in token_payload.scopes:
            raise HTTPException(status_code=403, detail="Insufficient scope")
        return token_payload
    return checker

# Usage in route:
@router.post("/conversations/{id}/messages")
async def post_message(
    id: str,
    body: MessageRequest,
    user: TokenPayload = Depends(require_scope("submit:support_messages"))
):
    ...
```

---

## Authorization Beyond Authentication

Authentication verifies identity. Authorization is enforced separately:

```
JWT verified (identity) → scope check (capability) → ownership check (resource)

Example: customer C-123 requests order O-5001:
  1. JWT valid, sub=C-123, scope includes read:own_orders ✓
  2. DB query: SELECT * FROM orders WHERE id='O-5001' AND customer_id='C-123'
     (ownership enforced at DB level, not just application level)
  3. If result empty → 404 (do not reveal existence of other customers' orders)
```

This double enforcement (scope + DB-level ownership) is architecture principle P-02: authorization is enforced by application logic, not delegated to the LLM.

---

## Re-verification Distinction (SEC-011)

OAuth JWT authentication establishes the current session identity. It does **not** satisfy re-verification for high-risk account changes.

```
Current session token (JWT) = "who are you right now"
Re-verification (email/SMS code) = "prove you control the original registered channel"

High-risk changes require BOTH:
  1. Valid JWT (current session auth)
  2. Successful re-verification through original channel (UC-06 flow)
```

A customer holding a valid JWT must still complete re-verification before an account change approval request is created.

---

## Secret Management

Per SEC-004, no secrets are hard-coded:

| Secret | V1 (local) | Production |
|---|---|---|
| JWT signing key (RS256 private key) | `.env` file | Cloud secret manager |
| Worker client_secret | `.env` file | Cloud secret manager |
| Eval harness client_secret | `.env` file | Cloud secret manager |
| User passwords | Hashed (bcrypt) in PostgreSQL | Same |

`.env.example` contains variable names only, never real values. `.env` is in `.gitignore`.

For production, RS256 (asymmetric) is preferred over HS256 (symmetric): the private key signs tokens (auth server only); the public key verifies tokens (any API node). This avoids distributing a shared secret across all API instances.

---

## Consequences

**Positive:**
- Stateless JWT verification: no per-request DB lookup for auth.
- Scopes enable fine-grained least-privilege per actor type.
- Client Credentials flow gives Worker and Eval Harness verifiable machine identities.
- FastAPI's OAuth2 support makes route protection a one-line dependency.
- Replaceable by external IdP without changing API contracts.

**Negative / Trade-offs:**
- JWT revocation is not immediate — 15-minute window for customer tokens.
  - Mitigation: short expiry (15 min) + maintain a revocation list in Redis for compromised tokens.
- Requires a minimal auth server for V1 — adds code to maintain.
  - Mitigation: this is replaced by Keycloak/Auth0/Okta in production; V1 implementation is ~200 lines of FastAPI code.
- RS256 key rotation requires re-issuing all active tokens — planned rotation procedure needed.

---

## Review Triggers

Revisit this ADR if:
- An external IdP (Keycloak, Auth0, Okta) is adopted — update implementation, keep scope design.
- mTLS is required for service-to-service (compliance requirement).
- Token revocation latency becomes a security concern (upgrade to opaque tokens + introspection).
- Multi-tenant architecture requires tenant-scoped claims.
