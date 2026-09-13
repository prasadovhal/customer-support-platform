# System Architecture — Enterprise Customer Support AI Platform

**Document:** System Architecture  
**Version:** 1.0  
**Status:** Draft  
**Derived from:** Requirements V1.1, Use Case Specifications V1.0  
**Supersedes:** Conceptual sketch in `specs/enterprise_customer_support_ai_phases.md` §Phase 4

---

## 1. Purpose and Scope

This document defines the system architecture of the Acme Store Customer Support AI Platform. It covers:

- System context and external actors
- Logical component architecture (layers and responsibilities)
- Synchronous and asynchronous request flows
- Trust boundaries and security boundaries
- Failure boundaries and degradation paths
- Approval workflow architecture
- Data architecture
- Deployment architecture
- Open architecture decisions (ADR index)

This document describes the **what** and **why** of the architecture. Technology choices open for decision are deferred to ADRs. Implementation detail belongs in component-level design documents.

---

## 2. Architecture Principles

These principles are derived directly from requirements and use-case specifications and constrain every architectural decision.

| # | Principle | Source |
|---|---|---|
| P-01 | **Agent output is untrusted.** LLM responses are parsed and validated before any action is executed. | FR-013, Phase 13 |
| P-02 | **Authorization is enforced outside the LLM.** The agent recommends actions; application logic authorizes them. | FR-014, SEC-002 |
| P-03 | **Policy is externalized.** Thresholds, category lists, and SLAs live in a policy store — not in prompts or code. | FR-013, §20 |
| P-04 | **Untrusted content cannot become instructions.** Messages, retrieved documents, and tool outputs are treated as data in the context, never as system instructions. | SEC-005 |
| P-05 | **Approval state is durable.** Pending approvals survive service restarts. A new customer message cannot bypass or invalidate a pending approval. | FR-013 |
| P-06 | **Every state-changing operation is idempotent.** Retries, at-least-once delivery, and duplicate webhooks must not cause duplicate business actions. | REL-003, FR-011 |
| P-07 | **Failures are explicit.** No silent swallowing of errors. Every failure produces an observable signal and a safe response. | REL-006 |
| P-08 | **Evaluation is a first-class concern.** The system is designed to be measurable. Every component that affects quality exposes measurable signals. | §11 (EVAL) |
| P-09 | **Defense in depth.** Security controls are layered and independently testable. No single bypass point exists. | FR-016 |
| P-10 | **Single-agent baseline.** Multi-agent orchestration is a future experiment, not a baseline assumption. | Requirements §1 |

---

## 3. System Context

### 3.1 Actors

| Actor | Role | Trust Level |
|---|---|---|
| Customer | Submits support requests via API | Low (untrusted input) |
| Human Support Agent | Handles escalations, approves sensitive actions | Medium (internal, authenticated) |
| Administrator | Manages policy, configuration, users | High (internal, role-limited) |
| Data Scientist / ML Engineer | Runs evaluation, experiments, monitors models | High (internal, role-limited) |
| Background Worker / System Service | Performs authorized async operations | Medium (service identity, scoped permissions) |

### 3.2 External Systems

| System | Interaction | Direction |
|---|---|---|
| Email provider | Re-verification challenges (UC-06), customer notifications | Outbound |
| Carrier / shipping API | Tracking data retrieval (UC-02) | Inbound to platform (optional integration) |
| CRM / Order system | Order and customer data (simulated in V1 by internal tools) | Internal |
| Observability backend | Traces, metrics, logs | Outbound |

### 3.3 Context Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                        INTERNET                              │
│                                                              │
│   Customer ──HTTPS──────────────────────────┐               │
│                                             ▼               │
│                                  ┌─────────────────────┐    │
│   Human Support Agent ──────────▶│                     │    │
│                                  │  Customer Support   │    │
│   Administrator ────────────────▶│   AI Platform       │◀── Carrier API
│                                  │                     │    │
│   Data Scientist / ML ──────────▶│                     │───▶ Email Provider
│                                  └─────────────────────┘    │
│                                             │               │
│                                             ▼               │
│                                  Observability Backend       │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. Logical Architecture — Containers

The platform is decomposed into six logical containers. Each container has a single primary responsibility, independent scalability, and an explicit interface boundary.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PLATFORM BOUNDARY                           │
│                                                                     │
│  ┌──────────────┐     ┌──────────────────────────────────────────┐  │
│  │   Support    │────▶│              Agent Service               │  │
│  │   API        │     │  (Orchestration · RAG · Tools · Guards)  │  │
│  │  (FastAPI)   │◀────│                                          │  │
│  └──────┬───────┘     └───────────────────┬──────────────────────┘  │
│         │                                 │                         │
│         │              ┌──────────────────┼──────────────┐          │
│         │              ▼                  ▼              ▼          │
│         │       ┌─────────────┐  ┌──────────────┐  ┌──────────┐    │
│         │       │  PostgreSQL │  │  Vector Store│  │  Redis   │    │
│         │       │ (runtime DB)│  │  (RAG index) │  │(cache/   │    │
│         │       └─────────────┘  └──────────────┘  │ broker)  │    │
│         │                                           └────┬─────┘    │
│         │                                               │           │
│         │                                               ▼           │
│         │                                    ┌──────────────────┐   │
│         └───────────────────────────────────▶│  Worker Service  │   │
│                                              │  (Celery)        │   │
│                                              └──────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                   LLM Serving (Ollama / dev)                  │   │
│  │              Open-weight model — selected via ADR             │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │          OpenTelemetry Collector + Observability Backend      │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

### Container Responsibilities

#### Support API (FastAPI)
- Entry point for all synchronous customer requests.
- Authentication and session validation.
- Rate limiting and request validation.
- Idempotency handling for state-changing requests.
- Webhook ingestion and signature verification.
- Routes synchronous requests to Agent Service.
- Enqueues async work to Redis → Worker.
- Health and readiness endpoints.

#### Agent Service
- Stateful workflow orchestration per conversation.
- Intent classification.
- Context assembly (conversation history + retrieval + tool results).
- Retrieval pipeline orchestration (hybrid BM25 + dense, reranking).
- LLM prompt construction and invocation through abstraction layer.
- Structured output parsing and validation.
- Tool dispatch with authorization checks.
- Guardrail enforcement (all 5 layers).
- Approval workflow state management.
- Escalation and ticket triggers.

#### PostgreSQL
- System of record for all transactional data.
- Customers, products, orders, conversations, messages.
- Agent execution traces, tool calls.
- Approval state (durable, survives restarts).
- Support tickets.
- Policy store (versioned, auditable).
- Idempotency keys.
- Embedding/chunk metadata (document ID, model version, chunk version).

#### Vector Store (pgvector initially — ADR pending)
- Stores dense vector embeddings of knowledge base chunks.
- Supports ANN similarity search.
- Filtered search by document category, effective date, product scope.
- Embedding metadata linked to source documents in PostgreSQL.

#### Redis
- Celery message broker (task queue).
- Short-lived caching (conversation context cache, rate limit counters).
- NOT used as primary source of truth for transactional data.

#### Worker Service (Celery)
- Async document ingestion and embedding.
- Approval notification dispatch.
- Email/re-verification channel delivery.
- Long-running evaluation jobs.
- Analytics and reporting jobs.
- Knowledge base re-indexing.
- Idempotent consumers for all state-changing jobs.

#### LLM Serving (Ollama in dev — production via ADR)
- Serves the selected open-weight model.
- Accessed through an LLM abstraction interface; application code is not tied to Ollama directly.
- Production serving is a separate ADR decision.

#### Observability Stack
- OpenTelemetry collector receives traces, metrics, and logs from all services.
- Captures: request traces, agent steps, tool calls, retrieval results, LLM calls, latency, errors, workflow state.
- Backend: selected via ADR (Jaeger, Grafana, or equivalent).

---

## 5. Component Architecture

### 5.1 Support API Layer

```
Inbound Request
      │
      ▼
┌──────────────────────────────────────────────────┐
│                  Support API                      │
│                                                   │
│  ┌──────────────┐    ┌─────────────────────────┐  │
│  │  Auth        │    │  Rate Limiter            │  │
│  │  Middleware  │───▶│  (by customer/IP/cred)   │  │
│  └──────────────┘    └─────────────┬─────────────┘  │
│                                    │                │
│  ┌─────────────────────────────────▼────────────┐  │
│  │           Request Router                      │  │
│  │  ┌───────────┐  ┌──────────┐  ┌───────────┐  │  │
│  │  │Conversation│  │ Tickets  │  │ Webhooks  │  │  │
│  │  │ Messages  │  │ Customers│  │ Health    │  │  │
│  │  └─────┬──────┘  └────┬─────┘  └─────┬────┘  │  │
│  └────────┼──────────────┼───────────────┼───────┘  │
│           │              │               │           │
│  ┌────────▼──────────────▼───────────────▼───────┐  │
│  │          Idempotency Handler                   │  │
│  │  (deduplicate state-changing requests)         │  │
│  └────────────────────────┬───────────────────────┘  │
└───────────────────────────┼──────────────────────────┘
                            │
               ┌────────────┴─────────────┐
               ▼                          ▼
         Agent Service              Worker Queue
       (synchronous path)          (async path)
```

**Key API endpoints:**

```
POST   /api/v1/conversations                  Create conversation
POST   /api/v1/conversations/{id}/messages    Submit message (main support flow)
GET    /api/v1/conversations/{id}             Get conversation state

GET    /api/v1/customers/{id}                 Customer lookup (admin/agent)
GET    /api/v1/orders/{id}                    Order lookup (admin/agent)

POST   /api/v1/tickets                        Manual ticket creation
GET    /api/v1/tickets/{id}                   Get ticket status
PATCH  /api/v1/tickets/{id}                   Update ticket (human agent)

POST   /api/v1/approvals/{id}/decision        Human agent approval decision
GET    /api/v1/approvals/{id}                 Get approval state

POST   /api/v1/webhooks/orders                Order event webhook

GET    /health                                Liveness
GET    /ready                                 Readiness
```

---

### 5.2 Agent Layer

The Agent layer is the core intelligence layer. It is invoked synchronously by the API for each message turn.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Agent Service                            │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  INPUT GUARDRAILS (Layer 1: rule-based)                  │   │
│  └─────────────────────────┬────────────────────────────────┘   │
│                            │                                    │
│  ┌─────────────────────────▼────────────────────────────────┐   │
│  │  Intent Classifier                                        │   │
│  │  ├─ Versioned intent taxonomy                            │   │
│  │  ├─ Confidence scoring                                   │   │
│  │  └─ Low-confidence detection → UC-08 / UC-09             │   │
│  └─────────────────────────┬────────────────────────────────┘   │
│                            │                                    │
│  ┌─────────────────────────▼────────────────────────────────┐   │
│  │  Context Builder                                          │   │
│  │  ├─ Last 10 turns verbatim (from PostgreSQL)             │   │
│  │  ├─ Summarized history (if > 10 turns)                   │   │
│  │  ├─ Retrieved knowledge (from retrieval pipeline)        │   │
│  │  ├─ Tool results (from prior turns)                      │   │
│  │  └─ Pending workflow state (approvals, verifications)    │   │
│  └─────────────────────────┬────────────────────────────────┘   │
│                            │                                    │
│  ┌─────────────────────────▼────────────────────────────────┐   │
│  │  Retrieval Pipeline                                       │   │
│  │  ├─ BM25 (lexical)                                       │   │
│  │  ├─ Dense vector search (ANN)                            │   │
│  │  ├─ Hybrid fusion                                        │   │
│  │  └─ Reranker (cross-encoder) → Top-K                     │   │
│  └─────────────────────────┬────────────────────────────────┘   │
│                            │                                    │
│  ┌─────────────────────────▼────────────────────────────────┐   │
│  │  Workflow State Machine (LangGraph — ADR-005)             │   │
│  │  ├─ Workflow graph per intent                            │   │
│  │  ├─ State persisted in PostgreSQL (durable)              │   │
│  │  ├─ Handles branching, retries, human-in-loop            │   │
│  │  └─ Approval and re-verification sub-workflows           │   │
│  └─────────────────────────┬────────────────────────────────┘   │
│                            │                                    │
│  ┌─────────────────────────▼────────────────────────────────┐   │
│  │  LLM Abstraction Layer                                    │   │
│  │  ├─ Model-agnostic interface                             │   │
│  │  ├─ Versioned prompt registry                            │   │
│  │  ├─ Structured output request                            │   │
│  │  └─ Retry on invalid structured output (bounded)         │   │
│  └─────────────────────────┬────────────────────────────────┘   │
│                            │                                    │
│  ┌─────────────────────────▼────────────────────────────────┐   │
│  │  Structured Output Validator (Pydantic)                   │   │
│  │  ├─ Schema validation                                    │   │
│  │  ├─ Type checking                                        │   │
│  │  └─ Invalid output → retry or fallback                   │   │
│  └─────────────────────────┬────────────────────────────────┘   │
│                            │                                    │
│  ┌─────────────────────────▼────────────────────────────────┐   │
│  │  Tool Dispatcher                                          │   │
│  │  ├─ Authorization check (outside LLM)                    │   │
│  │  ├─ Argument validation (schema + business policy)       │   │
│  │  ├─ Risk classification check                            │   │
│  │  ├─ High-risk actions → approval gate (not direct exec)  │   │
│  │  └─ Audit record written                                 │   │
│  └─────────────────────────┬────────────────────────────────┘   │
│                            │                                    │
│  ┌─────────────────────────▼────────────────────────────────┐   │
│  │  OUTPUT GUARDRAILS (Layer 5: output validation)           │   │
│  │  ├─ PII masking                                          │   │
│  │  ├─ Safety content filter                               │   │
│  │  └─ Groundedness check (optional runtime)               │   │
│  └─────────────────────────┬────────────────────────────────┘   │
│                            │                                    │
│                       Response                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 5.3 Retrieval Pipeline

```
Customer Query
      │
      ▼
┌──────────────────────────────────────────────────────────┐
│                  Retrieval Pipeline                       │
│                                                          │
│  ┌──────────────┐         ┌──────────────────────────┐   │
│  │  BM25        │         │  Dense Vector Search      │   │
│  │  (lexical)   │         │  (ANN via Vector Store)   │   │
│  │              │         │  with metadata filters:   │   │
│  │  Good for:   │         │  - category               │   │
│  │  - SKUs      │         │  - effective_date         │   │
│  │  - order IDs │         │  - product_scope          │   │
│  │  - exact     │         │                           │   │
│  │    policy    │         │                           │   │
│  │    terms     │         │                           │   │
│  └──────┬───────┘         └────────────┬──────────────┘   │
│         │                              │                  │
│         └──────────────┬───────────────┘                  │
│                        ▼                                  │
│              Hybrid Fusion (RRF or weighted)              │
│                        │                                  │
│                        ▼                                  │
│              Top-20 candidate chunks                      │
│                        │                                  │
│                        ▼                                  │
│              ┌─────────────────────┐                      │
│              │  Cross-Encoder      │                      │
│              │  Reranker           │  (ADR-004)           │
│              │  (open-source)      │                      │
│              └──────────┬──────────┘                      │
│                         │                                 │
│                         ▼                                 │
│              Top-5 chunks with source metadata            │
│              (document_id, version, score, provenance)    │
└──────────────────────────────────────────────────────────┘
```

**Retrieval is the primary candidate for experimentation (Phase 22):**

```
Experiment axis 1: BM25 vs Dense vs Hybrid vs Hybrid+Reranker
Experiment axis 2: Chunking strategy (size, overlap, semantic)
Experiment axis 3: Embedding model selection
Experiment axis 4: Reranker model selection
```

---

### 5.4 Tool Layer

All tools follow the contract defined in FR-014. The Tool Dispatcher enforces authorization before any tool executes.

```
Agent Decision (structured output)
          │
          ▼
┌──────────────────────────────────────────────────────────┐
│                   Tool Dispatcher                         │
│                                                          │
│  Step 1: Parse tool name and arguments from agent output │
│  Step 2: Validate schema (Pydantic)                      │
│  Step 3: Check caller authorization (role + scope)       │
│  Step 4: Check risk classification                       │
│  Step 5: Check business policy (e.g., ownership)         │
│  Step 6: Write audit record (pre-execution)              │
│  Step 7: Execute (or gate if high-risk)                  │
│  Step 8: Write audit record (post-execution, with result)│
└──────────────────────────────────────────────────────────┘
          │
          ▼
┌──────────────────────────────────────────────────────────┐
│                      Tool Registry                        │
│                                                          │
│  Read tools (low risk — direct execution):               │
│  ├─ get_customer(customer_id)                            │
│  ├─ get_order(order_id)                                  │
│  ├─ get_tracking(order_id)                               │
│  └─ get_product(product_id)                              │
│                                                          │
│  Policy tools (low risk — direct execution):             │
│  ├─ check_refund_policy(order_id, product_id)            │
│  └─ check_cancellation_policy(order_id)                  │
│                                                          │
│  Write tools — medium risk (direct + audit):             │
│  ├─ create_ticket(data, idempotency_key)                 │
│  └─ update_ticket(ticket_id, data)                       │
│                                                          │
│  Write tools — HIGH RISK (approval gate, never direct):  │
│  ├─ issue_refund(order_id, amount, reason)               │
│  ├─ cancel_order(order_id, reason)                       │
│  └─ update_customer(customer_id, field, value)           │
│                                                          │
│  Verification tools:                                     │
│  ├─ send_verification(customer_id, channel, type)        │
│  └─ verify_code(customer_id, code)                       │
└──────────────────────────────────────────────────────────┘
```

**High-risk tool execution gate:**

```
Agent requests high-risk tool
         │
         ▼
Authorization check (passed)
         │
         ▼
Approval request created in PostgreSQL
         │
         ▼
Customer notified (async)
         │
         ▼
Agent returns (synchronous turn complete)
         │ (async)
         ▼
Human approval decision received via API
         │
     ┌───┴────┐
     ▼        ▼
  Approved  Denied / Timeout
     │        │
  Execute  Notify + Ticket
  tool
```

---

### 5.5 Data Layer

```
┌───────────────────────────────────────────────────────────────────┐
│                         PostgreSQL                                │
│                                                                   │
│  Runtime / Transactional:                                         │
│  ├─ customers                                                     │
│  ├─ products                                                      │
│  ├─ orders                                                        │
│  ├─ support_tickets                                               │
│  ├─ conversations                                                 │
│  ├─ conversation_messages                                         │
│  ├─ agent_executions                                              │
│  └─ tool_calls                                                    │
│                                                                   │
│  Workflow State (durable):                                        │
│  ├─ approval_requests (state, actor, timestamps, policy_version)  │
│  ├─ verification_requests (state, channel, expiry)               │
│  └─ conversation_workflow_state (pending intents, open approvals) │
│                                                                   │
│  Policy Store (versioned, auditable):                             │
│  ├─ policies (type, value, effective_from, effective_to)          │
│  ├─ policy_audit_log (actor, timestamp, old_value, new_value)     │
│  └─ intent_taxonomy_versions                                      │
│                                                                   │
│  Idempotency:                                                     │
│  └─ idempotency_keys (key, created_at, result_reference)          │
│                                                                   │
│  RAG Metadata:                                                    │
│  ├─ knowledge_documents (id, category, version, effective_dates)  │
│  ├─ knowledge_chunks (id, doc_id, text, chunk_version)            │
│  └─ embedding_metadata (chunk_id, model_id, model_version,        │
│                          index_version, embedding_dim)            │
│                                                                   │
│  ML Model Registry:                                               │
│  └─ model_versions (name, version, artifact_path, metrics)        │
└───────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────┐
│                       Vector Store                                │
│                    (pgvector — ADR-002)                           │
│                                                                   │
│  ├─ chunk_embeddings (chunk_id → vector)                          │
│  └─ Metadata for filtered search:                                 │
│       category, effective_date, product_scope, doc_version        │
│                                                                   │
│  Embedding model and index version tracked in PostgreSQL.         │
│  Model change → controlled re-indexing required.                  │
└───────────────────────────────────────────────────────────────────┘
```

---

### 5.6 Async Worker Layer

```
┌────────────────────────────────────────────────────────────────┐
│                     Worker Service (Celery)                     │
│                                                                │
│  Knowledge Ingestion Queue:                                    │
│  └─ ingest_document → parse → chunk → embed → index           │
│                                                                │
│  Notification Queue:                                           │
│  ├─ send_approval_notification (to human agent queue)         │
│  ├─ send_customer_notification (email / channel)              │
│  └─ send_verification_challenge (re-verification)             │
│                                                                │
│  Evaluation Queue:                                             │
│  ├─ run_retrieval_evaluation (golden dataset)                  │
│  ├─ run_agent_evaluation                                       │
│  └─ run_ml_evaluation                                          │
│                                                                │
│  Analytics Queue:                                              │
│  └─ compute_business_metrics (CSAT, FCR, AHT, automation rate)│
│                                                                │
│  Approval Timeout Queue:                                       │
│  └─ check_approval_timeout → create_ticket → notify_customer  │
│                                                                │
│  All workers:                                                  │
│  ├─ idempotent (idempotency key checked before processing)     │
│  ├─ retry with exponential backoff                             │
│  ├─ dead-letter queue for persistent failures                  │
│  └─ observability: task ID, latency, retry count, failure      │
└────────────────────────────────────────────────────────────────┘
```

---

### 5.7 Guardrail Architecture

All 5 layers are independently testable per FR-016.

```
Input
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 1 — Rule-based Input Checks                      │
│  ├─ Pattern matching: injection keywords, forbidden      │
│  │   patterns, system override attempts                  │
│  ├─ Field validation: length, encoding, content type     │
│  └─ PII detection in output-bound fields                 │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 2 — Structural Validation                        │
│  ├─ Tool argument schema validation (Pydantic)          │
│  ├─ Workflow state transition validation                 │
│  └─ No unauthorized state jumps                         │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 3 — Policy and Permission Checks                 │
│  ├─ Role-based authorization per tool                   │
│  ├─ Customer ownership checks (order, account)          │
│  ├─ Risk classification → route or gate                 │
│  └─ Policy threshold enforcement (from policy store)    │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 4 — Semantic / LLM-based Classification          │
│  ├─ High-risk intent classification                     │
│  ├─ Adversarial content detection                       │
│  └─ Applied where rule-based is insufficient            │
└───────────────────────┬─────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────┐
│  Layer 5 — Output Validation                            │
│  ├─ PII masking before delivery                         │
│  ├─ Safety content filter                               │
│  ├─ HTML/script escaping for web rendering (SEC-012)    │
│  └─ Optional: runtime groundedness check                │
└───────────────────────┬─────────────────────────────────┘
                        │
                       Output
```

---

## 6. Request Flows

### 6.1 Synchronous Path — Simple FAQ (UC-01)

```
Customer
    │  POST /api/v1/conversations/{id}/messages
    ▼
Support API
    ├─ Auth middleware
    ├─ Rate limiter
    ├─ Request validation
    └─ Forward to Agent Service
              │
              ▼
         Agent Service
              ├─ Input guardrails (Layer 1)
              ├─ Intent classification → FAQ
              ├─ Context builder (history + retrieval)
              ├─ Retrieval pipeline
              │    ├─ BM25 + Dense → Top 20
              │    └─ Reranker → Top 5
              ├─ LLM prompt construction (versioned prompt)
              ├─ LLM call → Ollama → open-weight model
              ├─ Structured output parse + validate
              ├─ Output guardrails (Layer 5)
              └─ Response
              │
              ▼
         Support API
              │
              ▼
         Customer response

Async (fire-and-forget):
    └─ Trace written to OpenTelemetry
    └─ Conversation turn persisted to PostgreSQL
```

### 6.2 Synchronous → Async Path — Refund Request (UC-04)

```
Customer
    │  POST /api/v1/conversations/{id}/messages ("I want a refund")
    ▼
Support API → Agent Service
              ├─ Intent: refund_request
              ├─ Auth check (customer ownership of order)
              ├─ Order tool → get_order()
              ├─ Policy check → check_refund_policy()
              ├─ Eligibility: eligible
              ├─ Refund amount calculated
              ├─ Tool Dispatcher: issue_refund = HIGH RISK
              │    └─ Authorization: passed
              │    └─ Approval gate: CREATE APPROVAL REQUEST
              │         ├─ Write to PostgreSQL: approval_requests
              │         └─ Enqueue: send_approval_notification (Worker)
              ├─ Response to customer: "Approval required, expect 4 business hours"
              └─ Return (synchronous turn complete)

[Async — Worker]
    └─ send_approval_notification → Human agent notified

[Async — Human Agent]
    │  POST /api/v1/approvals/{id}/decision {"decision": "approved"}
    ▼
Support API → Approval Service
              ├─ Auth: human agent role verified
              ├─ Update approval_requests in PostgreSQL → approved
              ├─ Enqueue: execute_refund task (Worker)
              └─ Return

[Async — Worker]
    └─ execute_refund
         ├─ Check approval state (idempotency)
         ├─ issue_refund(order_id, amount)
         └─ send_customer_notification("Refund processed")
```

### 6.3 Webhook Path — Order Event

```
Order System
    │  POST /api/v1/webhooks/orders
    ▼
Support API
    ├─ Verify webhook signature (HMAC)
    ├─ Check event_id in idempotency_keys (duplicate check)
    ├─ If duplicate → 200 OK, no processing
    └─ If new → record event_id → enqueue to Worker

[Worker]
    └─ Process order event
         ├─ Update order state in PostgreSQL
         ├─ If approval pending → check if state change affects approval
         └─ Notify relevant workflows
```

---

## 7. Trust Boundaries

```
┌─────────────────────────────────────────────────────────────────┐
│  TRUST BOUNDARY 1 — INTERNET / PLATFORM                        │
│                                                                 │
│  All inbound traffic crosses here.                              │
│  Controls: TLS, authentication, rate limiting, input guardrails │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  TRUST BOUNDARY 2 — API / INTERNAL SERVICES              │  │
│  │                                                           │  │
│  │  Service-to-service calls require service identity.       │  │
│  │  Controls: service auth tokens, network policy            │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  TRUST BOUNDARY 3 — LLM OUTPUT                     │  │  │
│  │  │                                                     │  │  │
│  │  │  LLM output is UNTRUSTED.                           │  │  │
│  │  │  Controls: structured output parsing, Pydantic      │  │  │
│  │  │  validation, retry on invalid, action gate          │  │  │
│  │  │                                                     │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  TRUST BOUNDARY 4 — RETRIEVED CONTENT              │  │  │
│  │  │                                                     │  │  │
│  │  │  KB documents and tool outputs are UNTRUSTED        │  │  │
│  │  │  as INSTRUCTIONS.                                   │  │  │
│  │  │  Controls: context segregation, prompt structure,   │  │  │
│  │  │  Layer 1 + Layer 4 guardrails on retrieved content  │  │  │
│  │  │                                                     │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                                                           │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  TRUST BOUNDARY 5 — TOOL EXECUTION                 │  │  │
│  │  │                                                     │  │  │
│  │  │  Tool calls are authorized by application logic,   │  │  │
│  │  │  not by LLM decision alone.                        │  │  │
│  │  │  Controls: Tool Dispatcher, authorization checks,   │  │  │
│  │  │  risk classification, approval gate for high-risk   │  │  │
│  │  │                                                     │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Failure Boundaries and Degradation

### 8.1 Failure Boundary Map

| Component | Failure | Degradation Behavior | Circuit Breaker |
|---|---|---|---|
| LLM Serving | Unavailable / timeout | Return safe fallback response; escalate if repeated | Yes |
| Vector Store | Unavailable | Fall back to BM25-only retrieval | Yes |
| BM25 index | Unavailable | Fall back to vector-only retrieval | No (in-process) |
| Reranker | Unavailable | Return hybrid results without reranking | No |
| PostgreSQL | Unavailable | Fail safe; no writes; alert | Yes |
| Redis | Unavailable | Degrade: in-process cache for short-lived data; async jobs pause | Yes |
| External email | Unavailable | Retry with backoff; if persistent → ticket for manual follow-up | No |
| Approval system | Unavailable (DB) | Cannot create approval; return error; create manual ticket | — |
| Tool call | Error / timeout | Retry once with backoff; surface failure explicitly; escalate | No (per-call) |
| Policy store | Unavailable | Fail safe: treat action as high-risk; require approval | — |

### 8.2 Circuit Breaker Candidates (REL-007)

```
LLM Inference ──────────► Circuit Breaker ──► Fallback: safe refusal + ticket
Vector Store ────────────► Circuit Breaker ──► Fallback: BM25-only
PostgreSQL ──────────────► Circuit Breaker ──► Fallback: read-only / reject writes
Redis / Celery ──────────► Circuit Breaker ──► Fallback: synchronous processing for short tasks
```

### 8.3 Failure Injection Test Cases

These scenarios must be tested explicitly (Phase 27):

1. LLM unavailable mid-conversation.
2. Vector store unavailable — verifies BM25 fallback.
3. PostgreSQL unavailable — verifies no silent data loss.
4. Redis unavailable — verifies async queue degrades gracefully.
5. Duplicate webhook delivered twice.
6. Invalid LLM structured output — verifies retry and fallback.
7. Malformed tool arguments from LLM — verifies Layer 2 guardrail.
8. Approval timeout — verifies ticket creation and no auto-approval.
9. Policy store unavailable — verifies fail-safe (treat as high-risk).
10. Worker crash mid-job — verifies at-least-once re-delivery.

---

## 9. Approval Workflow Architecture

Approval is a first-class durable workflow, not a UI pattern or in-memory state.

```
┌────────────────────────────────────────────────────────────────────┐
│                    Approval Workflow                               │
│                                                                    │
│  Storage: PostgreSQL (approval_requests table)                     │
│  Worker: Celery (approval timeout check, notification dispatch)    │
│                                                                    │
│  States:                                                           │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                                                              │  │
│  │  action_requested                                            │  │
│  │       ↓                                                      │  │
│  │  policy_check (policy version recorded)                      │  │
│  │       ↓                                                      │  │
│  │  approval_required                                           │  │
│  │       ↓                                                      │  │
│  │  pending_approval ←──── customer_new_message (safe handling) │  │
│  │       ├── approved ──► execute_action ──► complete           │  │
│  │       ├── denied ───► notify_customer ──► alternatives       │  │
│  │       └── timeout ──► create_ticket ───► notify_customer     │  │
│  │                        (never auto-approve on timeout)       │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  Durability requirements:                                          │
│  ├─ State survives API/agent service restarts                      │
│  ├─ New customer message does NOT invalidate pending state         │
│  ├─ Approval decision is idempotent (duplicate POST handled)       │
│  └─ Timeout checked by scheduled Celery task                      │
│                                                                    │
│  Audit record:                                                     │
│  ├─ action, order_id, customer_id, amount (PII masked in logs)    │
│  ├─ policy version and threshold applied                          │
│  ├─ approval request timestamp                                    │
│  ├─ decision (approver, timestamp, reason)                        │
│  └─ execution result                                              │
└────────────────────────────────────────────────────────────────────┘
```

---

## 10. Data Architecture

### 10.1 Data Separation

```
┌──────────────────────────────────────────────────────────────────┐
│  Runtime Transactional Data     →  PostgreSQL                    │
│  (customers, orders, tickets, conversations, approvals)          │
├──────────────────────────────────────────────────────────────────┤
│  Vector Index                   →  Vector Store (pgvector/ADR)   │
│  (chunk embeddings + metadata)                                   │
├──────────────────────────────────────────────────────────────────┤
│  Cache / Broker                 →  Redis                         │
│  (short-lived context, rate limits, task queue)                  │
├──────────────────────────────────────────────────────────────────┤
│  Knowledge Base (source)        →  File system / object store    │
│  (Markdown articles)            →  Ingested via Worker pipeline  │
├──────────────────────────────────────────────────────────────────┤
│  Evaluation Datasets            →  File system (JSONL, CSV)      │
│  (golden QA, retrieval eval,    →  Separate from runtime data    │
│   agent eval, classification)       (no contamination)          │
├──────────────────────────────────────────────────────────────────┤
│  ML Model Artifacts             →  File system / model registry  │
│  (scikit-learn models, embeddings)                               │
├──────────────────────────────────────────────────────────────────┤
│  Traces / Metrics / Logs        →  OpenTelemetry → Backend       │
└──────────────────────────────────────────────────────────────────┘
```

### 10.2 Source Authority Hierarchy (FR-008)

```
Structured operational data (PostgreSQL)
  └─ Authoritative for: order state, prices, specs, warranty facts
  
Knowledge base documents (Vector Store + file system)
  └─ Authoritative for: policies, procedures, troubleshooting

Conflict between sources → surface conflict, do not silently resolve
```

### 10.3 Embedding Versioning (EMB-002)

Every embedded chunk is traceable to:
- Embedding model name and version
- Embedding configuration (dimensions, pooling)
- Source document ID and version
- Chunk version and chunking parameters
- Index version

Model change → full re-indexing required → retrieval re-evaluation required before promotion.

---

## 11. Deployment Architecture

### 11.1 Logical Deployment Layout

```
Internet
    │
    ▼ HTTPS / TLS termination
┌───────────────────────────────────────────────────────────────┐
│                      Application Tier                         │
│                                                               │
│   ┌──────────────────────┐   ┌───────────────────────────┐   │
│   │   Support API        │   │   Worker Service           │   │
│   │   (FastAPI)          │   │   (Celery)                 │   │
│   │   - Stateless        │   │   - Stateless              │   │
│   │   - Horizontally     │   │   - Horizontally           │   │
│   │     scalable         │   │     scalable               │   │
│   └──────────────────────┘   └───────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
    │                                   │
    ▼                                   ▼
┌───────────────────────────────────────────────────────────────┐
│                       Data Tier                               │
│                                                               │
│   ┌───────────┐  ┌──────────────┐  ┌────────────────────┐   │
│   │PostgreSQL │  │ Vector Store │  │       Redis         │   │
│   │           │  │ (pgvector)   │  │                     │   │
│   │ Primary + │  │              │  │                     │   │
│   │ Replica   │  │              │  │                     │   │
│   └───────────┘  └──────────────┘  └────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────┐
│                      LLM Inference Tier                       │
│                                                               │
│   ┌───────────────────────────────────────────────────────┐   │
│   │  Ollama (dev) / Production Serving (ADR-004)          │   │
│   │  Open-weight model (selected via benchmarking)        │   │
│   └───────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────┘
    │
    ▼
┌───────────────────────────────────────────────────────────────┐
│                    Observability                               │
│   OpenTelemetry Collector → Backend (ADR pending)             │
└───────────────────────────────────────────────────────────────┘
```

### 11.2 Local Development Stack (Docker Compose)

```yaml
services:
  api:        FastAPI support API
  worker:     Celery worker
  postgres:   PostgreSQL (runtime DB + pgvector)
  redis:      Redis (broker + cache)
  ollama:     Ollama (LLM serving)
  otel:       OpenTelemetry collector
```

Single command: `docker compose up`

### 11.3 Environment Requirements

| Requirement | V1 Baseline |
|---|---|
| Linux containers | Required |
| PostgreSQL | Required |
| Self-hosted vector store | Required |
| Async processing (Redis + Celery) | Required |
| Secret management | Required (env vars locally; cloud secret manager in production) |
| TLS termination | Required |
| Persistent storage | Required (PostgreSQL, vector index) |
| Cloud provider | ADR pending — cost, OSS compatibility, container support |

---

## 12. Observability Architecture

Every interaction produces a structured trace linking all components.

```
Trace: interaction_id (unique per message turn)
    ├─ span: api_request (latency, auth, rate_limit)
    ├─ span: intent_classification (intent, confidence, model_version)
    ├─ span: retrieval
    │    ├─ span: bm25 (latency, result_count)
    │    ├─ span: dense_search (latency, result_count, embedding_model)
    │    └─ span: reranker (latency, input_count, output_count)
    ├─ span: context_build (token_count, turns_included, summary_used)
    ├─ span: llm_call (model, prompt_version, latency, tokens_in, tokens_out)
    ├─ span: structured_output_validation (valid/invalid, retry_count)
    ├─ span: tool_dispatch (tool_name, args_valid, authorized, risk_level)
    │    └─ span: tool_execution (latency, success/failure)
    ├─ span: guardrails (layer, triggered/passed)
    └─ span: response_delivery (latency)

Attributes always present:
    conversation_id, customer_id (masked), interaction_id,
    model_version, prompt_version, embedding_model_version,
    policy_version, workflow_state, outcome
```

**Business metrics (OBS-005):**

```
CSAT                → from customer feedback events
FCR                 → from ticket re-open / re-contact detection
AHT                 → from conversation duration
Automation rate     → resolved without human / total
Escalation rate     → escalated / total
Cost per interaction → LLM tokens × cost rate + infra cost
```

---

## 13. Architecture Decision Records — Index

The following decisions are open or require formal ADR documentation.

| ADR | Decision | Status |
|---|---|---|
| ADR-001 | PostgreSQL as primary relational database | Decided; ADR to document |
| ADR-002 | Vector database: pgvector vs. Qdrant vs. Weaviate | Open |
| ADR-003 | Hybrid retrieval strategy and fusion method | Open (pending benchmarking) |
| ADR-004 | Reranker model selection | Open (pending benchmarking) |
| ADR-005 | Workflow orchestration: LangGraph vs. alternatives | Open |
| ADR-006 | Embedding model selection | Open (pending benchmarking) |
| ADR-007 | Async broker and worker: Redis + Celery | Decided; ADR to document |
| ADR-008 | LLM model selection and serving architecture | Open (pending benchmarking) |
| ADR-009 | OAuth 2.0 + JWT for authentication | Decided; ADR to document |
| ADR-010 | Observability backend (Jaeger / Grafana / other) | Open |
| ADR-011 | Cloud provider and deployment target | Open |
| ADR-012 | Infrastructure as Code: OpenTofu vs. Terraform | Open |
| ADR-013 | Production LLM serving (Ollama vs. vLLM vs. other) | Open (post-benchmarking) |

---

## 14. Architecture Trade-offs

### Single-agent vs. Multi-agent

**Decision:** Single-agent baseline (P-10).

| Factor | Single-Agent | Multi-Agent |
|---|---|---|
| Complexity | Lower | Higher (orchestration, inter-agent auth) |
| Debugging | Simpler (one trace) | Harder (distributed) |
| Latency | Lower | Higher (round-trips) |
| Capability ceiling | Sufficient for V1 UCs | Needed for very parallel workflows |

Multi-agent is a Phase 22 experiment, not a baseline assumption.

### pgvector vs. Dedicated Vector Database

**Decision pending ADR-002.**

| Factor | pgvector | Dedicated (Qdrant/Weaviate) |
|---|---|---|
| Operational complexity | Low (one database) | Higher (additional service) |
| Filtering | Good for moderate complexity | Better for complex multi-field filters |
| Scale | Moderate (millions of vectors) | Higher scale ceiling |
| Cost | Lower (shared infra) | Higher (separate service) |
| V1 suitability | Sufficient (~100 articles) | Overkill for V1 |

### Sync vs. Async for Approval

**Decision:** Approval is asynchronous with durable state in PostgreSQL.

Synchronous approval would require blocking the customer's connection for up to 4 business hours, which is not viable. The async path requires durable state (PostgreSQL, not Redis) to survive restarts and correctly handle new customer messages during the pending period.

### LLM Abstraction Layer

**Decision:** Application code targets an LLM interface, not Ollama directly.

This enables:
- Model benchmarking without application changes.
- Production serving swap without refactoring.
- Unit testing with mock LLM.

---

## 15. Requirements Traceability

| Requirement | Architecture Component |
|---|---|
| FR-001 (query submission) | Support API — POST /conversations/{id}/messages |
| FR-002 (context management) | Context Builder — 10-turn verbatim + summary |
| FR-003 (intent taxonomy) | Intent Classifier — versioned taxonomy in PostgreSQL |
| FR-004 (knowledge retrieval) | Retrieval Pipeline — hybrid BM25 + dense + reranker |
| FR-005 (grounded responses) | LLM Abstraction + Output Guardrails Layer 5 |
| FR-006/007 (customer/order tools) | Tool Registry — get_customer, get_order, get_tracking |
| FR-008 (source authority) | Data Architecture §10.2 |
| FR-011 (ticket creation) | Worker Service — create_ticket with idempotency |
| FR-012 (human escalation) | Agent Layer + Worker — escalation context package |
| FR-013 (human approval) | Approval Workflow Architecture §9 |
| FR-014 (tool permission model) | Tool Dispatcher — 8-step authorization flow |
| FR-015 (argument validation) | Tool Dispatcher + Guardrail Layer 2 |
| FR-016 (guardrails) | Guardrail Architecture §5.7 — 5 layers |
| ML-001–004 | Worker Service — ML inference + model registry in PostgreSQL |
| LLM-001 (model abstraction) | LLM Abstraction Layer |
| LLM-002 (Ollama dev) | Local Docker Compose stack |
| EVAL-001–006 | Worker Service evaluation queues + PostgreSQL model registry |
| OBS-001–005 | Observability Architecture §12 |
| SEC-001–012 | Trust Boundaries §7 + Guardrail Architecture §5.7 |
| REL-001–007 | Failure Boundaries §8 |

---

## 16. Next Steps

```
System Architecture V1.0 (this document)
         ↓
Sequence Diagrams (UC-04, UC-05, UC-06 — complex approval flows)
         ↓
ADRs (ADR-001 through ADR-013, prioritized by build order)
         ↓
Repository and Component Design
         ↓
Phase 6: Backend Foundation (FastAPI API layer)
         ↓
Phase 7: Database and Data Layer (PostgreSQL schema, migrations)
```

Priority ADRs before implementation begins:
1. ADR-001 (PostgreSQL) — unblock DB schema work.
2. ADR-007 (Redis + Celery) — unblock async worker design.
3. ADR-009 (OAuth) — unblock auth layer.
4. ADR-005 (Workflow orchestration) — unblock agent implementation.
5. ADR-002 (Vector store) — unblock RAG pipeline.
