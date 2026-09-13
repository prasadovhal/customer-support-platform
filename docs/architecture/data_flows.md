# End-to-End Data Flows — Enterprise Customer Support AI Platform

**Document:** End-to-End Data Flows  
**Version:** 1.0  
**Status:** Draft  
**Derived from:** System Architecture V1.0, Use Case Specifications V1.0  
**Part of:** System Architecture Series (Step 3 of 5)

---

## 1. Purpose and Scope

This document defines how data moves through the platform end-to-end for every major flow. It covers:

- Data entering the system (inputs and their schemas)
- Transformations at each component boundary
- What is written to which store at each step
- Data exiting the system (response, notification, audit record)
- Asynchronous continuation flows
- Supporting infrastructure flows (ingestion, approval timeout, evaluation)

These diagrams are the primary input to API contract design, database schema decisions, and integration design.

---

## 2. Notation

```
─────►   Synchronous call (waits for response)
- - -►   Asynchronous message (fire-and-forget / queued)
═════►   Data written to store
◄─────   Response returned
[data]   Payload at this point in the flow
{store}  Data store (PostgreSQL, Redis, Vector Store)
```

**Participants used across diagrams:**

| Short Name | Full Name |
|---|---|
| C | Customer |
| API | Support API (FastAPI) |
| AG | Agent Service |
| BM25 | BM25 index (lexical retrieval) |
| VS | Vector Store (pgvector) |
| RR | Reranker |
| LLM | LLM Abstraction → Ollama → model |
| PG | PostgreSQL |
| RD | Redis |
| WK | Worker Service (Celery) |
| EP | Email Provider |
| HA | Human Support Agent |
| OT | OpenTelemetry Collector |

---

## 3. Flow 1 — Simple FAQ (UC-01)

The baseline synchronous flow: retrieval + grounded generation, no tool calls, no auth required.

### 3.1 Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    participant C as Customer
    participant API as Support API
    participant AG as Agent Service
    participant BM25 as BM25 Index
    participant VS as Vector Store
    participant RR as Reranker
    participant LLM as LLM (Ollama)
    participant PG as PostgreSQL
    participant OT as OpenTelemetry

    C->>API: POST /api/v1/conversations/{id}/messages<br/>{message, conversation_id, channel, timestamp}

    API->>API: Auth middleware (optional for FAQ)<br/>Rate limit check<br/>Request validation (Pydantic)<br/>Idempotency check

    API->>PG: Load conversation history<br/>(last 10 turns verbatim + summary if exists)
    PG-->>API: [conversation_messages, summary_state]

    API->>AG: Forward request + conversation context<br/>{message, history, conversation_id, customer_id}

    AG->>AG: Input Guardrail Layer 1<br/>(rule-based: injection patterns, length)

    AG->>LLM: Intent classification call<br/>{message, recent_context}<br/>[prompt_version: intent_v1.2]
    LLM-->>AG: {intent: "faq", confidence: 0.92,<br/>  requires_customer_data: false}

    AG->>AG: Build retrieval query from message + intent

    par Hybrid Retrieval
        AG->>BM25: BM25 query(text)<br/>{query_text, top_k: 20}
        BM25-->>AG: [{doc_id, chunk_id, score, text}, ...]

        AG->>VS: ANN search(embedding, filters)<br/>{query_vector, category_filter,<br/>  effective_date_filter, top_k: 20}
        VS-->>AG: [{chunk_id, score, text, metadata}, ...]
    end

    AG->>AG: Hybrid fusion (RRF)<br/>Merge BM25 + dense → Top 20 candidates

    AG->>RR: Rerank(query, chunks)<br/>{query_text, candidates[20]}
    RR-->>AG: [{chunk_id, score, text, doc_id,<br/>  doc_version, source_metadata}, ...]<br/>Top 5 reranked chunks

    AG->>AG: Context Builder<br/>Assemble: system_prompt + history<br/>+ retrieved_chunks + current_message<br/>Check: fits within context budget

    AG->>LLM: Generation call<br/>{assembled_context}<br/>[model: llama3.2, prompt_version: support_v2.1]
    LLM-->>AG: {response_text, usage: {tokens_in, tokens_out}}

    AG->>AG: Structured output parse + validate (Pydantic)<br/>{response, sources_cited, groundedness_signal}

    AG->>AG: Output Guardrail Layer 5<br/>PII masking, safety filter, HTML escaping

    AG->>PG: Write conversation turn<br/>{message_id, conversation_id, role: "assistant",<br/>  content, retrieved_doc_ids, prompt_version,<br/>  model_version, groundedness_score, latency}
    PG-->>AG: [written: message_id]

    AG-->>API: {response_text, sources, conversation_id}
    API-->>C: 200 OK<br/>{response, sources, conversation_id, message_id}

    AG--)OT: Trace span: full interaction<br/>{interaction_id, intent, retrieval_scores,<br/>  reranker_scores, model, tokens,<br/>  groundedness, latency_ms per stage}
```

### 3.2 Data Written Per Step

| Step | Store | Data Written |
|---|---|---|
| 1 | API logs | Request received, request_id |
| PG load | PostgreSQL | Read only |
| BM25 | In-memory index | Read only |
| VS | Vector Store | Read only |
| PG write | PostgreSQL | `conversation_messages`: role, content, retrieved_doc_ids, prompt_version, model_version, groundedness_score, latency |
| OTel | OTel backend | Full trace span with all metadata |

### 3.3 Data Transformations

```
Raw message (text)
      │
      ▼ [Intent classification]
{intent, confidence, requires_customer_data}
      │
      ▼ [Retrieval query construction]
{query_text, query_vector, metadata_filters}
      │
      ├──► BM25 → [{doc_id, chunk_id, bm25_score, text}]
      └──► Dense → [{chunk_id, dense_score, text, metadata}]
                │
                ▼ [Hybrid fusion RRF]
      [{chunk_id, fused_score, text, source_metadata}] × 20
                │
                ▼ [Reranker]
      [{chunk_id, rerank_score, text, source_metadata}] × 5
                │
                ▼ [Context assembly]
      {system_prompt + history + chunks + message} (token budget checked)
                │
                ▼ [LLM]
      {response_text, usage}
                │
                ▼ [Output guardrails]
      {response_text_clean, sources_cited}
```

---

## 4. Flow 2 — Order Status (UC-02)

Authenticated customer reads order data through tool call. No writes to business data.

### 4.1 Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    participant C as Customer
    participant API as Support API
    participant AG as Agent Service
    participant LLM as LLM (Ollama)
    participant PG as PostgreSQL
    participant OT as OpenTelemetry

    C->>API: POST /api/v1/conversations/{id}/messages<br/>{message: "Where is my order #5001?",<br/>  conversation_id, customer_id, timestamp}<br/>Authorization: Bearer {token}

    API->>API: Auth middleware: validate JWT<br/>Extract: customer_id, session_id, scopes
    API->>API: Rate limit check (by customer_id)
    API->>API: Request validation

    API->>PG: Load conversation history
    PG-->>API: [history]

    API->>AG: {message, history, customer_id, conversation_id}

    AG->>AG: Input Guardrail Layer 1

    AG->>LLM: Intent classification<br/>{message, context}
    LLM-->>AG: {intent: "order_status", confidence: 0.96,<br/>  extracted: {order_id: "5001"}}

    AG->>AG: Workflow: order_status_workflow<br/>Load from PostgreSQL if resuming mid-flow

    Note over AG: Tool Dispatcher — Step 1: Parse tool request
    AG->>AG: Tool: get_order<br/>Args: {order_id: "5001", customer_id: "C-123"}

    Note over AG: Tool Dispatcher — Steps 2–5: Validate
    AG->>AG: Layer 2: Schema validation ✓<br/>Layer 3: Authorization check<br/>→ customer_id matches token ✓<br/>→ scope: read_orders ✓<br/>Layer 3: Risk: LOW → direct execute

    AG->>PG: SELECT order + items + tracking<br/>WHERE order_id='5001'<br/>AND customer_id='C-123'
    PG-->>AG: {order_id, status: "shipped",<br/>  items: [...], tracking_number: "1Z999...",<br/>  carrier: "UPS", estimated_delivery: "2026-09-09",<br/>  shipped_at: "2026-09-06"}

    AG->>AG: Authorization check:<br/>order.customer_id == request.customer_id ✓

    AG->>PG: Write tool_call audit record<br/>{tool: "get_order", args_hash, result_summary,<br/>  authorized: true, latency_ms}

    AG->>AG: Build context: order data + message

    AG->>LLM: Generation call<br/>{context: order_data + message + history}
    LLM-->>AG: {response: "Your order #5001 shipped on...<br/>  Tracking: 1Z999... (UPS). Estimated delivery: Sep 9."}

    AG->>AG: Structured output validate<br/>Output guardrails: PII mask tracking details per config

    AG->>PG: Write conversation turn<br/>{message_id, content, tool_calls: ["get_order"],<br/>  model_version, prompt_version, latency}

    AG-->>API: {response, conversation_id}
    API-->>C: 200 OK {response, message_id}

    AG--)OT: Trace: intent, tool_call, auth_result,<br/>order_id (masked), latency per stage
```

### 4.2 Authorization Data Flow

```
JWT token  ──────►  Auth middleware  ──────►  {customer_id, scopes, session_id}
                                                          │
                                                          ▼
                                              Tool Dispatcher
                                              scope check: read_orders ✓
                                                          │
                                                          ▼
                                              PostgreSQL query
                                              WHERE customer_id = token.customer_id
                                              (DB-level ownership enforcement)
                                                          │
                                                          ▼
                                              Agent-level check:
                                              result.customer_id == token.customer_id
                                              (double-check, defense in depth)
```

---

## 5. Flow 3 — Refund Request (UC-04)

The most complex synchronous→asynchronous flow. Two distinct phases: the synchronous API turn (ends with approval requested), and the asynchronous approval + execution continuation.

### 5.1 Phase 1 — Synchronous: Request to Approval Pending

```mermaid
sequenceDiagram
    autonumber
    participant C as Customer
    participant API as Support API
    participant AG as Agent Service
    participant LLM as LLM (Ollama)
    participant PG as PostgreSQL
    participant RD as Redis
    participant WK as Worker (Celery)
    participant OT as OpenTelemetry

    C->>API: POST /api/v1/conversations/{id}/messages<br/>{message: "I want a refund for order 5001",<br/>  customer_id, conversation_id}<br/>Bearer {token}

    API->>API: Auth + rate limit + validation
    API->>PG: Load history
    PG-->>API: [history]
    API->>AG: {message, history, customer_id}

    AG->>AG: Input Guardrail Layer 1

    AG->>LLM: Intent classification
    LLM-->>AG: {intent: "refund_request", confidence: 0.94,<br/>  extracted: {order_id: "5001"}}

    AG->>AG: Tool: get_order(order_id="5001", customer_id="C-123")
    Note over AG: Tool Dispatcher: schema ✓, auth ✓, risk=LOW

    AG->>PG: SELECT order WHERE id='5001' AND customer_id='C-123'
    PG-->>AG: {order_id: "5001", status: "delivered",<br/>  total: 149.99, items: [...],<br/>  delivered_at: "2026-09-01",<br/>  customer_id: "C-123"}

    AG->>AG: Tool: check_refund_policy(order_id, product_category)
    AG->>PG: SELECT policy WHERE type='refund'<br/>  AND category='electronics'<br/>  AND effective_from <= order_date<br/>  AND (effective_to IS NULL OR effective_to >= order_date)
    PG-->>AG: {policy_id: "P-88", version: "2.1",<br/>  return_window_days: 30,<br/>  eligible_statuses: ["delivered"],<br/>  restocking_fee_pct: 0}

    AG->>AG: Eligibility reasoning:<br/>delivered_at=Sep 1, today=Sep 7 → 6 days < 30 ✓<br/>status=delivered ✓<br/>no restocking fee<br/>refund_amount = 149.99

    AG->>AG: Tool Dispatcher: issue_refund<br/>Risk classification: HIGH<br/>→ APPROVAL GATE (do not execute)

    AG->>PG: INSERT approval_requests<br/>{id: "AR-001",<br/>  action: "issue_refund",<br/>  order_id: "5001",<br/>  customer_id: "C-123",<br/>  amount: 149.99,<br/>  currency: "USD",<br/>  policy_id: "P-88",<br/>  policy_version: "2.1",<br/>  eligibility_basis: "within_return_window",<br/>  conversation_id: "CONV-99",<br/>  state: "pending_approval",<br/>  requested_at: "2026-09-07T10:15:00Z",<br/>  sla_deadline: "2026-09-08T18:00:00Z",<br/>  idempotency_key: "refund-5001-CONV-99-001"}
    PG-->>AG: {approval_id: "AR-001"}

    AG->>PG: UPDATE conversation_workflow_state<br/>{conversation_id, pending_approval_id: "AR-001",<br/>  workflow: "refund_request", state: "pending_approval"}

    AG->>RD: LPUSH celery_queue "send_approval_notification"<br/>{approval_id: "AR-001",<br/>  queue: "human_agent_approval",<br/>  priority: "normal"}

    AG->>AG: Generate customer response<br/>(no LLM call needed — templated approval notification)

    AG->>PG: Write conversation turn<br/>{content: "Your refund request...",<br/>  workflow_state: "pending_approval",<br/>  approval_id: "AR-001"}

    AG-->>API: {response: "I've submitted your refund request...<br/>  A support specialist will review it within<br/>  4 business hours. Reference: AR-001"}
    API-->>C: 200 OK {response, approval_reference: "AR-001"}

    AG--)OT: Trace: intent, eligibility_result,<br/>policy_version, approval_id, latency
    
    Note over WK: (async, separate process)
    RD--)WK: Dequeue: send_approval_notification {AR-001}
    WK->>PG: SELECT approval_request WHERE id='AR-001'
    PG-->>WK: [approval request details]
    WK->>WK: Format notification for human agent queue
    WK->>PG: INSERT human_agent_notifications<br/>{approval_id, queue: "refunds", priority, created_at}
    WK--)OT: Worker task trace: task_id, approval_id, latency
```

### 5.2 Phase 2 — Asynchronous: Human Decision to Execution

```mermaid
sequenceDiagram
    autonumber
    participant HA as Human Agent
    participant API as Support API
    participant WK as Worker (Celery)
    participant PG as PostgreSQL
    participant RD as Redis
    participant EP as Email Provider
    participant OT as OpenTelemetry

    Note over HA: Human agent reviews approval in agent portal

    HA->>API: POST /api/v1/approvals/AR-001/decision<br/>{decision: "approved",<br/>  reason: "Within return window, valid request",<br/>  agent_id: "HA-007"}<br/>Bearer {agent_token}

    API->>API: Auth: validate agent JWT<br/>Check scope: approve_refunds ✓
    API->>PG: SELECT approval_request WHERE id='AR-001'
    PG-->>API: {state: "pending_approval", amount: 149.99, ...}

    API->>PG: UPDATE approval_requests<br/>SET state='approved',<br/>    decided_by='HA-007',<br/>    decided_at='2026-09-07T11:30:00Z',<br/>    decision_reason='Within return window...',<br/>    policy_version='2.1'<br/>WHERE id='AR-001' AND state='pending_approval'
    PG-->>API: {rows_updated: 1}

    API->>PG: INSERT approval_audit_log<br/>{approval_id: "AR-001",<br/>  event: "approved",<br/>  actor_id: "HA-007",<br/>  actor_role: "support_agent",<br/>  timestamp, reason,<br/>  policy_version: "2.1"}

    API->>RD: LPUSH celery_queue "execute_refund"<br/>{approval_id: "AR-001",<br/>  idempotency_key: "exec-AR-001-v1"}
    API-->>HA: 200 OK {approval_id, state: "approved"}

    Note over WK: Worker picks up execute_refund task
    RD--)WK: Dequeue: execute_refund {AR-001}

    WK->>PG: SELECT * FROM approval_requests WHERE id='AR-001'
    PG-->>WK: {state: "approved", order_id: "5001",<br/>  amount: 149.99, idempotency_key: "exec-AR-001-v1"}

    WK->>PG: SELECT idempotency_keys<br/>WHERE key='exec-AR-001-v1'
    PG-->>WK: {exists: false}

    WK->>PG: INSERT idempotency_keys<br/>{key: "exec-AR-001-v1",<br/>  created_at, status: "processing"}

    Note over WK: Execute the actual refund tool
    WK->>PG: UPDATE orders SET refund_status='processing'<br/>WHERE id='5001'
    WK->>PG: INSERT refund_transactions<br/>{order_id: "5001",<br/>  amount: 149.99,<br/>  currency: "USD",<br/>  approval_id: "AR-001",<br/>  initiated_at: now(),<br/>  status: "processing"}
    PG-->>WK: {transaction_id: "RT-5501"}

    Note over WK: (Simulated external payment processor call)
    WK->>WK: issue_refund(order_id, amount, transaction_id)
    WK-->>WK: {success: true, external_ref: "PAY-REF-99"}

    WK->>PG: UPDATE refund_transactions<br/>SET status='completed',<br/>    external_ref='PAY-REF-99',<br/>    completed_at=now()<br/>WHERE id='RT-5501'

    WK->>PG: UPDATE orders<br/>SET refund_status='refunded', refunded_at=now()<br/>WHERE id='5001'

    WK->>PG: UPDATE approval_requests<br/>SET state='executed', executed_at=now()<br/>WHERE id='AR-001'

    WK->>PG: UPDATE idempotency_keys<br/>SET status='completed', result_ref='RT-5501'<br/>WHERE key='exec-AR-001-v1'

    WK->>RD: LPUSH celery_queue "send_customer_notification"<br/>{customer_id: "C-123",<br/>  conversation_id: "CONV-99",<br/>  template: "refund_processed",<br/>  data: {amount: 149.99, ref: "RT-5501",<br/>         expected_days: "3-5 business days"}}

    RD--)WK: Dequeue: send_customer_notification
    WK->>EP: Send email<br/>{to: customer_email (PII - masked in logs),<br/>  template: "refund_processed",<br/>  amount: "$149.99",<br/>  reference: "RT-5501"}
    EP-->>WK: {delivered: true}

    WK->>PG: INSERT conversation_messages<br/>{conversation_id: "CONV-99",<br/>  role: "system",<br/>  content: "Refund of $149.99 processed. Ref: RT-5501.",<br/>  created_at: now()}

    WK--)OT: Worker trace: task_chain, approval_id,<br/>transaction_id, latency, outcome
```

### 5.3 Approval Timeout Flow

```mermaid
sequenceDiagram
    autonumber
    participant SCHED as Celery Beat (scheduler)
    participant WK as Worker (Celery)
    participant PG as PostgreSQL
    participant RD as Redis
    participant OT as OpenTelemetry

    Note over SCHED: Runs every 15 minutes
    SCHED->>WK: check_approval_timeouts task

    WK->>PG: SELECT * FROM approval_requests<br/>WHERE state = 'pending_approval'<br/>  AND sla_deadline < now()
    PG-->>WK: [{approval_id: "AR-002",<br/>   order_id: "5002",<br/>   customer_id: "C-456",<br/>   conversation_id: "CONV-88",<br/>   sla_deadline: "2026-09-07T09:00:00Z"}]

    Note over WK: For each timed-out approval:

    WK->>PG: UPDATE approval_requests<br/>SET state='timeout',<br/>    timed_out_at=now()<br/>WHERE id='AR-002' AND state='pending_approval'
    PG-->>WK: {rows_updated: 1}

    WK->>PG: INSERT approval_audit_log<br/>{approval_id: "AR-002",<br/>  event: "timeout",<br/>  timestamp: now()}

    Note over WK: Create escalation ticket (never auto-approve)
    WK->>RD: LPUSH celery_queue "create_ticket"<br/>{trigger: "approval_timeout",<br/>  approval_id: "AR-002",<br/>  conversation_id: "CONV-88",<br/>  customer_id: "C-456",<br/>  priority_hint: "P1",<br/>  idempotency_key: "ticket-timeout-AR-002"}

    WK->>RD: LPUSH celery_queue "send_customer_notification"<br/>{customer_id: "C-456",<br/>  template: "approval_timeout",<br/>  data: {ticket_ref: "pending",<br/>         action: "refund",<br/>         next_steps: "..."}}

    WK--)OT: Trace: timeout_check, count_timed_out,<br/>approval_ids, tickets_created
```

### 5.4 Data Written — Refund Flow Summary

| Phase | Store | Table / Key | Data |
|---|---|---|---|
| Sync (approval gate) | PostgreSQL | `approval_requests` | Full approval record, policy version, SLA deadline |
| Sync (approval gate) | PostgreSQL | `conversation_workflow_state` | Pending approval ID, workflow state |
| Sync (approval gate) | PostgreSQL | `conversation_messages` | Customer-facing response |
| Sync (approval gate) | Redis | Celery queue | `send_approval_notification` task |
| Async (notification) | PostgreSQL | `human_agent_notifications` | Approval in agent queue |
| Human decision | PostgreSQL | `approval_requests` | Decision, actor, timestamp, reason |
| Human decision | PostgreSQL | `approval_audit_log` | Full audit trail |
| Human decision | Redis | Celery queue | `execute_refund` task |
| Execution | PostgreSQL | `idempotency_keys` | Execution idempotency key |
| Execution | PostgreSQL | `refund_transactions` | Refund record + external ref |
| Execution | PostgreSQL | `orders` | Refund status + timestamp |
| Execution | PostgreSQL | `approval_requests` | State → executed |
| Execution | Redis | Celery queue | `send_customer_notification` task |
| Execution | Email Provider | (external) | Customer notification (email) |
| Execution | PostgreSQL | `conversation_messages` | System confirmation message |
| All phases | OTel backend | Trace spans | Full distributed trace |

---

## 6. Flow 4 — High-Value Cancellation (UC-05)

Identical approval pattern to UC-04 with one critical difference: the high-value threshold and high-risk category list are loaded from the policy store at runtime, not from code or prompts.

### 6.1 Policy Store Load

```mermaid
sequenceDiagram
    autonumber
    participant AG as Agent Service
    participant PG as PostgreSQL
    participant RD as Redis

    Note over AG: After order is retrieved, before executing cancellation

    AG->>RD: GET policy:cancellation:thresholds (cache)
    RD-->>AG: {cache_miss}

    AG->>PG: SELECT value FROM policies<br/>WHERE type='cancellation_threshold'<br/>  AND effective_from <= now()<br/>  AND (effective_to IS NULL OR effective_to > now())<br/>ORDER BY effective_from DESC LIMIT 1
    PG-->>AG: {policy_id: "P-44", version: "1.3",<br/>  high_value_threshold: 200.00,<br/>  currency: "USD",<br/>  high_risk_categories: ["jewelry","electronics_premium",<br/>                          "appliances_large"]}

    AG->>RD: SET policy:cancellation:thresholds {data} EX 300
    Note over AG: Cached for 5 minutes<br/>(short TTL — policy can change)

    AG->>AG: Apply threshold:<br/>order_total=850.00 > 200.00 → HIGH VALUE<br/>product_category="appliances_large" → HIGH RISK CATEGORY<br/>→ Both conditions met → REQUIRES APPROVAL<br/>(policy_version="1.3" recorded in approval request)
```

### 6.2 Key Difference from UC-04

```
UC-04 Refund:    Refund always requires approval (hard rule)
UC-05 Cancel:    Threshold loaded from policy store at runtime
                 ┌──────────────────────────────────────────────────┐
                 │  order_total > policy.high_value_threshold        │
                 │  OR                                              │
                 │  product_category IN policy.high_risk_categories  │
                 │  → requires approval                             │
                 │                                                  │
                 │  order_total <= threshold                         │
                 │  AND product_category NOT IN high_risk           │
                 │  → direct execution (out of scope for this UC)   │
                 └──────────────────────────────────────────────────┘

Fail-safe: If policy store is unavailable → treat as HIGH VALUE → require approval
```

---

## 7. Flow 5 — Account / Security Change (UC-06)

Three-phase flow: current-session auth → re-verification through original channel → approval + execution.

### 7.1 Phase 1 — Request and Re-verification Challenge

```mermaid
sequenceDiagram
    autonumber
    participant C as Customer
    participant API as Support API
    participant AG as Agent Service
    participant LLM as LLM (Ollama)
    participant PG as PostgreSQL
    participant RD as Redis
    participant WK as Worker (Celery)

    C->>API: POST /api/v1/conversations/{id}/messages<br/>{message: "I need to change my email address to new@example.com"}<br/>Bearer {token}

    API->>API: Auth: validate JWT → customer_id="C-123"
    API->>AG: {message, customer_id, history}

    AG->>LLM: Intent classification
    LLM-->>AG: {intent: "account_change",<br/>  change_type: "email_change",<br/>  requested_value: "new@example.com"}

    Note over AG: SEC-011: Chat session alone is INSUFFICIENT
    Note over AG: Re-verification required through original channel

    AG->>AG: Tool: get_customer(customer_id="C-123")
    AG->>PG: SELECT email, phone, verification_channels<br/>FROM customers WHERE id='C-123'
    PG-->>AG: {email: "o***@example.com" (masked),<br/>  phone: "***-***-4321" (masked),<br/>  verification_channels: ["email", "sms"]}

    AG->>AG: Determine re-verification method:<br/>email_change → verify through CURRENT registered email<br/>(not the new email, not the current chat session)

    AG->>PG: INSERT verification_requests<br/>{id: "VR-001",<br/>  customer_id: "C-123",<br/>  change_type: "email_change",<br/>  requested_value_hash: SHA256("new@example.com"),<br/>  channel: "email",<br/>  code: random_6_digit (stored hashed),<br/>  code_hash: BCRYPT(code),<br/>  expires_at: now() + 15min,<br/>  conversation_id: "CONV-77",<br/>  state: "pending",<br/>  attempts: 0}
    PG-->>AG: {verification_id: "VR-001"}

    AG->>PG: UPDATE conversation_workflow_state<br/>{pending_verification_id: "VR-001",<br/>  workflow: "email_change",<br/>  state: "pending_reverification"}

    AG->>RD: LPUSH celery_queue "send_verification_challenge"<br/>{verification_id: "VR-001",<br/>  customer_id: "C-123",<br/>  channel: "email",<br/>  code_for_delivery: "847291"}

    AG-->>API: {response: "To protect your account, we've sent<br/>  a verification code to your registered email<br/>  o***@example.com. Please enter the code here.<br/>  It expires in 15 minutes."}
    API-->>C: 200 OK {response}

    Note over WK: (async — delivers verification code)
    RD--)WK: Dequeue: send_verification_challenge
    WK->>WK: Format verification email<br/>(one-time code only, no account details)
    WK->>EP: Send to customer original email<br/>{to: customer_email,<br/>  code: "847291",<br/>  expiry: "15 minutes",<br/>  action: "email address change"}
    EP-->>WK: {delivered: true}
    WK->>PG: UPDATE verification_requests<br/>SET code_sent_at=now()<br/>WHERE id='VR-001'
```

### 7.2 Phase 2 — Customer Submits Code

```mermaid
sequenceDiagram
    autonumber
    participant C as Customer
    participant API as Support API
    participant AG as Agent Service
    participant LLM as LLM (Ollama)
    participant PG as PostgreSQL
    participant RD as Redis

    C->>API: POST /api/v1/conversations/{id}/messages<br/>{message: "847291"}<br/>Bearer {token}

    API->>AG: {message: "847291", customer_id, history}

    AG->>PG: SELECT workflow_state<br/>WHERE conversation_id='CONV-77'
    PG-->>AG: {state: "pending_reverification",<br/>  pending_verification_id: "VR-001"}

    Note over AG: Active verification → handle as code submission<br/>(not intent classification)

    AG->>AG: Tool: verify_code(verification_id="VR-001", code="847291")

    AG->>PG: SELECT * FROM verification_requests<br/>WHERE id='VR-001' AND state='pending'
    PG-->>AG: {code_hash, expires_at, attempts, customer_id}

    AG->>AG: Check: now() < expires_at ✓<br/>Check: attempts < 3 ✓<br/>Check: BCRYPT.verify("847291", code_hash) ✓

    AG->>PG: UPDATE verification_requests<br/>SET state='verified',<br/>    verified_at=now()<br/>WHERE id='VR-001'

    AG->>PG: INSERT approval_requests<br/>{id: "AR-010",<br/>  action: "email_change",<br/>  customer_id: "C-123",<br/>  change_type: "email_change",<br/>  new_value_hash: SHA256("new@example.com"),<br/>  verification_id: "VR-001",<br/>  verification_method: "email",<br/>  conversation_id: "CONV-77",<br/>  state: "pending_approval",<br/>  requested_at: now(),<br/>  sla_deadline: now() + 4h,<br/>  idempotency_key: "acct-change-VR-001"}

    AG->>PG: UPDATE conversation_workflow_state<br/>{state: "pending_approval",<br/>  pending_approval_id: "AR-010",<br/>  pending_verification_id: null}

    AG->>RD: LPUSH celery_queue "send_approval_notification"<br/>{approval_id: "AR-010", queue: "account_security"}

    AG-->>API: {response: "Identity verified. Your email change<br/>  request has been submitted for review.<br/>  A specialist will process it within 4 hours.<br/>  Reference: AR-010"}
    API-->>C: 200 OK
```

### 7.3 Failed Re-verification

```
Customer submits wrong code:
    ├─ attempts < 3 → increment attempts, return error
    └─ attempts >= 3 → state='failed', deny workflow

Customer does not respond (timeout):
    └─ Celery Beat: check expired verification_requests
       → state='expired'
       → Notify customer: "Verification expired. Please restart the request."
       → No escalation required (customer can retry)

Suspected account takeover:
    → Skip re-verification entirely
    → Immediate escalation to security queue
    → Create high-priority ticket
    → Do not reveal detection criteria
```

---

## 8. Flow 6 — Human Escalation (UC-11)

Handover of the full conversation to a human agent with complete context package.

### 8.1 Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    participant AG as Agent Service
    participant PG as PostgreSQL
    participant RD as Redis
    participant WK as Worker (Celery)
    participant HA as Human Agent Portal
    participant OT as OpenTelemetry

    Note over AG: Escalation trigger detected<br/>(any: agent can't resolve, customer requests human,<br/>  policy requires escalation, max clarifications reached)

    AG->>PG: SELECT full conversation context<br/>{messages, tool_calls, retrieved_docs,<br/>  workflow_state, approval_state, guardrail_events}
    PG-->>AG: [complete context package]

    AG->>AG: Assemble escalation package:<br/>{customer_id, conversation_id,<br/>  escalation_reason: "agent_cannot_resolve",<br/>  conversation_summary: LLM-generated summary,<br/>  message_history: [...],<br/>  retrieved_docs: [{doc_id, version, relevance_score}],<br/>  tool_calls: [{tool, args_hash, result_summary, timestamp}],<br/>  attempted_actions: [...],<br/>  failure_reasons: [...],<br/>  policy_signals: {policy_version, threshold_applied},<br/>  quality_signals: {groundedness_scores, guardrail_events},<br/>  pending_workflow: {approval_id: null or "AR-xxx"}}

    AG->>RD: LPUSH celery_queue "create_ticket"<br/>{trigger: "escalation",<br/>  escalation_package: (above),<br/>  priority_hint: "P1",<br/>  idempotency_key: "esc-CONV-77-001"}

    AG->>PG: UPDATE conversation_workflow_state<br/>SET state='escalated',<br/>    escalated_at=now(),<br/>    escalation_reason='agent_cannot_resolve'

    AG->>PG: INSERT conversation_messages<br/>{role: "assistant",<br/>  content: "I'm connecting you with a support specialist...",<br/>  metadata: {escalated: true}}

    Note over WK: Async ticket creation
    RD--)WK: Dequeue: create_ticket (escalation)

    WK->>PG: Check idempotency_key 'esc-CONV-77-001'
    PG-->>WK: {exists: false}

    WK->>WK: ML-001: classify ticket category + priority<br/>{input: escalation_package.summary + reason}<br/>→ {category: "order_issue", priority: "P1",<br/>    model_version: "classifier_v2.3"}

    WK->>PG: INSERT support_tickets<br/>{id: "TK-9901",<br/>  customer_id: "C-123",<br/>  conversation_id: "CONV-77",<br/>  category: "order_issue",<br/>  priority: "P1",<br/>  escalation_reason: "agent_cannot_resolve",<br/>  context_ref: "CONV-77",<br/>  status: "open",<br/>  assigned_queue: "tier2_support",<br/>  ml_model_version: "classifier_v2.3",<br/>  created_at: now(),<br/>  idempotency_key: "esc-CONV-77-001"}

    WK->>PG: INSERT idempotency_keys<br/>{key: "esc-CONV-77-001", result_ref: "TK-9901"}

    WK->>HA: Notify human agent portal<br/>{ticket_id: "TK-9901",<br/>  priority: "P1",<br/>  queue: "tier2_support",<br/>  customer_id: "C-123" (masked in notification),<br/>  conversation_link: "/conversations/CONV-77"}

    WK->>RD: LPUSH celery_queue "send_customer_notification"<br/>{template: "escalation_confirmed",<br/>  ticket_ref: "TK-9901",<br/>  expected_response: "within 2 business hours"}

    WK--)OT: Worker trace: ticket_id, category, priority,<br/>ml_model_version, latency
```

---

## 9. Flow 7 — Knowledge Base Ingestion Pipeline

How Markdown knowledge articles become searchable indexed chunks.

### 9.1 Ingestion Pipeline

```mermaid
sequenceDiagram
    autonumber
    participant ADM as Administrator
    participant API as Support API
    participant RD as Redis
    participant WK as Worker (Celery)
    participant PG as PostgreSQL
    participant VS as Vector Store
    participant OT as OpenTelemetry

    ADM->>API: POST /api/v1/knowledge/ingest<br/>{document_path: "kb/returns/policy_v3.md",<br/>  category: "returns",<br/>  effective_from: "2026-09-01",<br/>  effective_to: null,<br/>  version: "3.0"}

    API->>API: Auth: admin role required
    API->>RD: LPUSH celery_queue "ingest_document"<br/>{doc_path, category, effective_from,<br/>  effective_to, version,<br/>  idempotency_key: "ingest-returns-v3"}
    API-->>ADM: 202 Accepted {job_id: "JOB-55"}

    RD--)WK: Dequeue: ingest_document

    WK->>PG: Check: idempotency_key 'ingest-returns-v3'
    PG-->>WK: {exists: false}

    WK->>WK: Step 1 — Parse Markdown<br/>Extract: title, sections, metadata,<br/>  headings, links, effective dates

    WK->>WK: Step 2 — Chunk<br/>Strategy: recursive character split<br/>{chunk_size: 512 tokens,<br/>  overlap: 64 tokens,<br/>  respect_headings: true}<br/>→ 8 chunks produced

    WK->>PG: INSERT knowledge_documents<br/>{id: "DOC-301",<br/>  path: "kb/returns/policy_v3.md",<br/>  category: "returns",<br/>  version: "3.0",<br/>  effective_from: "2026-09-01",<br/>  effective_to: null,<br/>  title: "Return Policy",<br/>  chunk_count: 8,<br/>  ingested_at: now()}

    WK->>PG: INSERT knowledge_chunks (batch)<br/>[{id: "CK-3001", doc_id: "DOC-301",<br/>   chunk_index: 0, text: "...",<br/>   token_count: 498,<br/>   chunk_version: "v3.0-0"},<br/>  ... × 8]

    WK->>WK: Step 3 — Embed<br/>{model: "bge-m3", version: "1.2.0",<br/>  batch_size: 8}<br/>→ 8 vectors of dim=1024

    WK->>VS: Upsert chunk vectors (batch)<br/>[{chunk_id: "CK-3001",<br/>   vector: [...1024 floats],<br/>   metadata: {doc_id, category, effective_from,<br/>               effective_to, chunk_version,<br/>               doc_version}},<br/>  ... × 8]
    VS-->>WK: {upserted: 8}

    WK->>PG: INSERT embedding_metadata (batch)<br/>[{chunk_id: "CK-3001",<br/>   embedding_model: "bge-m3",<br/>   embedding_version: "1.2.0",<br/>   embedding_dim: 1024,<br/>   index_version: "IX-007",<br/>   embedded_at: now()},<br/>  ... × 8]

    WK->>PG: UPDATE knowledge_documents<br/>SET indexed_at=now(),<br/>    index_version='IX-007'<br/>WHERE id='DOC-301'

    WK->>PG: INSERT idempotency_keys<br/>{key: "ingest-returns-v3", result_ref: "DOC-301"}

    WK->>RD: LPUSH celery_queue "trigger_retrieval_evaluation"<br/>{changed_docs: ["DOC-301"],<br/>  evaluation_dataset: "retrieval_eval.jsonl",<br/>  note: "ingestion-triggered re-eval"}

    WK--)OT: Trace: doc_id, chunk_count, embed_model,<br/>embed_version, index_version, latency

    Note over WK: Evaluation worker runs retrieval eval<br/>Results compared to baseline<br/>If regression detected → alert
```

### 9.2 Re-indexing on Embedding Model Change

```
Embedding model updated (e.g., bge-m3 v1.2.0 → v1.3.0)
    │
    ▼
Admin triggers: POST /api/v1/knowledge/reindex
    │
    ▼
Worker: full_reindex task
    ├─ SELECT all knowledge_chunks WHERE indexed_with_model != 'bge-m3-v1.3.0'
    ├─ Re-embed all chunks with new model
    ├─ Upsert new vectors to Vector Store
    ├─ Update embedding_metadata with new model + version
    └─ Trigger retrieval evaluation (required before promotion)
    
Promotion blocked until:
    └─ Retrieval Recall@5 relative regression ≤ 5% vs. baseline
```

---

## 10. Flow 8 — Webhook: Order Event

External order system notifies the platform of order state changes.

### 10.1 Sequence Diagram

```mermaid
sequenceDiagram
    autonumber
    participant OS as Order System (External)
    participant API as Support API
    participant RD as Redis
    participant WK as Worker (Celery)
    participant PG as PostgreSQL
    participant OT as OpenTelemetry

    OS->>API: POST /api/v1/webhooks/orders<br/>Headers: X-Signature: HMAC-SHA256(payload, secret)<br/>{event_id: "EVT-8821",<br/>  event_type: "order.status_updated",<br/>  order_id: "5001",<br/>  new_status: "shipped",<br/>  shipped_at: "2026-09-07T08:00:00Z",<br/>  tracking_number: "1Z999AA10123456784",<br/>  carrier: "UPS"}

    API->>API: Step 1: Verify signature<br/>HMAC-SHA256(payload, webhook_secret) == X-Signature?
    API->>API: Step 2: Check idempotency<br/>SELECT FROM idempotency_keys WHERE key='EVT-8821'
    PG-->>API: {exists: false}

    API->>PG: INSERT idempotency_keys<br/>{key: "EVT-8821",<br/>  event_type: "order.status_updated",<br/>  received_at: now(),<br/>  status: "queued"}

    API->>RD: LPUSH celery_queue "process_order_event"<br/>{event_id: "EVT-8821",<br/>  event_type: "order.status_updated",<br/>  payload: {order_id, new_status, tracking_number, ...}}

    API-->>OS: 200 OK {received: true, event_id: "EVT-8821"}
    Note over API: Fast 200 response to prevent OS retry

    RD--)WK: Dequeue: process_order_event

    WK->>PG: UPDATE orders<br/>SET status='shipped',<br/>    shipped_at='2026-09-07T08:00:00Z',<br/>    tracking_number='1Z999AA1...',<br/>    carrier='UPS'<br/>WHERE id='5001'

    WK->>PG: INSERT order_events<br/>{order_id: "5001",<br/>  event_id: "EVT-8821",<br/>  event_type: "status_updated",<br/>  old_status: "processing",<br/>  new_status: "shipped",<br/>  payload: {...},<br/>  processed_at: now()}

    WK->>PG: Check: any open conversations for order 5001?
    PG-->>WK: [{conversation_id: "CONV-99",<br/>   state: "pending_approval",<br/>   pending_approval_id: "AR-001"}]

    Note over WK: Order now shipped — check if pending approval<br/>is still valid (shipping-address-change window closed)
    WK->>PG: SELECT * FROM approval_requests WHERE id='AR-001'
    PG-->>WK: {action: "issue_refund", state: "pending_approval"}
    Note over WK: Refund approval unaffected by shipping event<br/>(different action type — no state change needed)

    WK->>PG: UPDATE idempotency_keys<br/>SET status='completed'<br/>WHERE key='EVT-8821'

    WK--)OT: Trace: event_id, event_type, order_id,<br/>processing_latency

    Note over OS: If OS retries EVT-8821:
    OS->>API: POST /api/v1/webhooks/orders {event_id: "EVT-8821", ...}
    API->>PG: SELECT FROM idempotency_keys WHERE key='EVT-8821'
    PG-->>API: {exists: true, status: "completed"}
    API-->>OS: 200 OK {received: true, event_id: "EVT-8821"}
    Note over API: No duplicate processing — idempotency key exists
```

---

## 11. Flow 9 — Evaluation Pipeline (Offline)

How the retrieval and agent evaluation datasets are run and results compared to baseline.

### 11.1 Retrieval Evaluation

```mermaid
sequenceDiagram
    autonumber
    participant DS as Data Scientist
    participant API as Support API
    participant WK as Worker (Celery)
    participant PG as PostgreSQL
    participant BM25 as BM25 Index
    participant VS as Vector Store
    participant RR as Reranker
    participant OT as OpenTelemetry

    DS->>API: POST /api/v1/evaluation/retrieval/run<br/>{dataset: "retrieval_eval.jsonl",<br/>  dataset_version: "v1.2",<br/>  retrieval_config: {strategy: "hybrid+reranker",<br/>    bm25_weight: 0.4, dense_weight: 0.6,<br/>    top_k: 5},<br/>  compare_to_baseline: true}

    API->>WK: Enqueue: run_retrieval_evaluation
    API-->>DS: 202 Accepted {eval_job_id: "EJ-007"}

    WK->>PG: Load evaluation dataset<br/>{query, expected_doc_ids}[] from retrieval_eval.jsonl
    PG-->>WK: [{query_id, query_text, relevant_doc_ids[]}] × N

    loop For each query in dataset
        WK->>BM25: BM25 query(query_text, top_k=20)
        BM25-->>WK: [{doc_id, chunk_id, score}]

        WK->>VS: ANN search(query_vector, top_k=20)
        VS-->>WK: [{chunk_id, score, metadata}]

        WK->>WK: Hybrid fusion → Top 20

        WK->>RR: Rerank(query, candidates)
        RR-->>WK: [{chunk_id, score}] × Top 5

        WK->>WK: Compute metrics:<br/>{Recall@5, Precision@5, MRR, nDCG@5}
    end

    WK->>WK: Aggregate metrics:<br/>{mean_recall_at_5, mean_precision_at_5,<br/>  mrr, ndcg_at_5,<br/>  per_category_breakdown, failure_cases[]}

    WK->>PG: SELECT baseline_metrics<br/>FROM evaluation_results<br/>WHERE dataset_version='v1.2'<br/>  AND is_baseline=true
    PG-->>WK: {baseline_recall_at_5: 0.82, ...}

    WK->>WK: Compare to baseline:<br/>relative_regression = (baseline - current) / baseline<br/>0.82 → 0.79: regression = 3.7% < 5% threshold ✓<br/>Result: PASS

    WK->>PG: INSERT evaluation_results<br/>{eval_job_id: "EJ-007",<br/>  dataset: "retrieval_eval.jsonl",<br/>  dataset_version: "v1.2",<br/>  retrieval_config: {...},<br/>  embedding_model_version: "bge-m3-v1.2.0",<br/>  index_version: "IX-007",<br/>  recall_at_5: 0.79,<br/>  precision_at_5: ...,<br/>  mrr: ...,<br/>  ndcg_at_5: ...,<br/>  baseline_comparison: {regression_pct: 3.7, result: "PASS"},<br/>  failure_cases: [...],<br/>  evaluated_at: now(),<br/>  is_baseline: false}

    WK--)DS: Evaluation complete notification<br/>{eval_job_id, result: "PASS", recall_at_5: 0.79,<br/>  regression_pct: 3.7, report_url: "/eval/EJ-007"}

    WK--)OT: Trace: eval_job_id, dataset_version,<br/>config, metrics_summary, pass_fail
```

---

## 12. Cross-Cutting Data Flows

### 12.1 PII Masking Flow

PII is masked at write time for logs and traces, and at read time for display contexts.

```
Data enters system (customer message, tool result)
    │
    ├─► Agent processing context (PII present — needed for tools)
    │
    └─► At output boundary:
         ├─ Logs / OTel traces → PII Registry applied → mask before write
         │    {customer_email: "p***@example.com",
         │     customer_phone: "***-***-4321",
         │     address: "[REDACTED]"}
         │
         ├─ Audit records → PII Registry applied → store hashes + masked values
         │    {customer_id: "C-123" (keep — operational),
         │     email_hash: SHA256(email),
         │     email_masked: "p***@example.com"}
         │
         └─ Response to customer → no cross-customer PII ever included

PII Registry (stored in PostgreSQL):
    ├─ customer_name: mask as "J*** D***"
    ├─ email: mask as "p***@domain.com"
    ├─ phone: mask as "***-***-NNNN"
    ├─ address: REDACTED
    ├─ payment_tokens: REDACTED
    └─ order contents: keep (not PII per policy)
```

### 12.2 Idempotency Check Flow

```
Inbound request / event / task
    │
    ▼
Compute idempotency key
    │ Key derivation:
    ├─ API requests:   hash(customer_id + action + order_id + conversation_id)
    ├─ Webhooks:       event_id (provided by sender)
    ├─ Worker tasks:   "task_type-source_id-version"
    └─ Refund exec:    "exec-{approval_id}-v1"
    │
    ▼
PostgreSQL: SELECT FROM idempotency_keys WHERE key=?
    ├─ EXISTS (status=completed)
    │     → Return cached result / 200 OK / skip processing
    │
    └─ NOT EXISTS
          → INSERT key (status=processing)
          → Execute operation
          → UPDATE key (status=completed, result_ref=X)
```

### 12.3 Observability Data Flow

Every interaction produces a structured trace. All services emit to the same OTel collector.

```
All Services
    │ OpenTelemetry SDK (auto-instrumentation + manual spans)
    ▼
OTel Collector
    │
    ├──► Traces backend (Jaeger / Tempo — ADR-010)
    │         └─ Full distributed trace per interaction_id
    │
    ├──► Metrics backend (Prometheus / Grafana — ADR-010)
    │         ├─ api_request_latency_ms (p50, p95, p99)
    │         ├─ agent_step_latency_ms per step
    │         ├─ retrieval_recall_at_5 (from eval runs)
    │         ├─ llm_tokens_in / llm_tokens_out
    │         ├─ tool_call_success_rate per tool
    │         ├─ approval_pending_count
    │         ├─ escalation_rate
    │         └─ automation_rate
    │
    └──► Logs backend (Loki / Elasticsearch — ADR-010)
              ├─ Structured JSON logs
              ├─ PII masked before write
              └─ Level: INFO for normal, ERROR for failures
```

---

## 13. Data Flow Summary — Writes Per Flow

| Flow | PostgreSQL Tables Written | Redis | Vector Store | External |
|---|---|---|---|---|
| UC-01 FAQ | `conversation_messages` | — | Read only | — |
| UC-02 Order Status | `conversation_messages`, `tool_calls` | — | — | — |
| UC-04 Refund (sync) | `approval_requests`, `conversation_workflow_state`, `conversation_messages` | Celery queue | — | — |
| UC-04 Refund (async exec) | `refund_transactions`, `orders`, `approval_requests`, `approval_audit_log`, `idempotency_keys`, `conversation_messages` | Celery queue | — | Email |
| UC-05 Cancellation | same as UC-04 + policy store read | Celery queue | — | — |
| UC-06 Account Change | `verification_requests`, `conversation_workflow_state`, `approval_requests`, `approval_audit_log`, `customers` | Celery queue | — | Email |
| UC-11 Escalation | `conversation_workflow_state`, `conversation_messages`, `support_tickets`, `idempotency_keys` | Celery queue | — | Agent portal |
| UC-12 Ticket | `support_tickets`, `idempotency_keys` | — | — | Agent portal |
| Approval timeout | `approval_requests`, `approval_audit_log`, `support_tickets`, `idempotency_keys` | Celery queue | — | Email |
| Webhook (order) | `orders`, `order_events`, `idempotency_keys` | — | — | — |
| KB Ingestion | `knowledge_documents`, `knowledge_chunks`, `embedding_metadata`, `idempotency_keys` | Celery queue | Chunk vectors upserted | — |
| Retrieval eval | `evaluation_results` | — | Read only | — |

---

## 14. Next Steps

```
Data Flows V1.0 (this document)
         ↓
ADRs — priority order for implementation:
  ADR-001 PostgreSQL (schema derived from flows above)
  ADR-007 Redis + Celery (queue shapes defined above)
  ADR-009 OAuth + JWT (auth flows defined above)
  ADR-005 Workflow Orchestration (state machine derived above)
  ADR-002 Vector Store (query patterns defined above)
         ↓
Database Schema Design
  (tables, constraints, indexes derived from §13 write summary)
         ↓
API Contract Design
  (endpoints, request/response schemas from flows above)
         ↓
Phase 6: Backend Foundation
```

**Key implementation constraints derived from these flows:**

1. `approval_requests` and `conversation_workflow_state` must be in the same PostgreSQL transaction when creating an approval.
2. All Celery tasks processing approvals must check idempotency before any write.
3. The webhook endpoint must respond `200 OK` before enqueuing — never block on processing.
4. Re-verification codes must be stored hashed (bcrypt), never plaintext.
5. Embedding metadata must be inserted atomically with vector store upsert — use a two-phase write with rollback capability.
6. The policy store cache TTL (Redis) must be short (≤ 5 minutes) — policy changes must propagate quickly.
