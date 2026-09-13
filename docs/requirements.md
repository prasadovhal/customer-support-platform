# Requirements — Enterprise Customer Support AI/ML Platform

**Project:** Acme Store Customer Support AI/ML Platform  
**Version:** 1.0  
**Date:** 2026-01-01  
**Status:** Approved  

---

## Table of Contents

1. [Business Context](#1-business-context)
2. [Stakeholders](#2-stakeholders)
3. [Current-State Workflow](#3-current-state-workflow)
4. [Pain-Point Analysis](#4-pain-point-analysis)
5. [Future-State Workflow](#5-future-state-workflow)
6. [Functional Requirements](#6-functional-requirements)
7. [Non-Functional Requirements](#7-non-functional-requirements)
8. [AI / ML Requirements](#8-ai--ml-requirements)
9. [Safety Requirements](#9-safety-requirements)
10. [Out of Scope](#10-out-of-scope)
11. [Assumptions and Constraints](#11-assumptions-and-constraints)
12. [Success Criteria](#12-success-criteria)

---

## 1. Business Context

### 1.1 Company

Acme Store is a mid-to-large e-commerce retailer selling consumer electronics (laptops, smartphones, tablets, audio, wearables, networking equipment, home appliances, gaming peripherals, accessories). It serves four customer segments — Standard, Premium, Business, and Enterprise — each with different service-level expectations and policy entitlements.

### 1.2 Problem Statement

Acme's support operation does not scale. As the customer base and SKU catalogue grow, the number of inbound support requests grows proportionally — but agent headcount and knowledge currency cannot keep pace. The result:

- Agents spend the majority of handle time looking up information (customer records, order status, policy documents) rather than resolving issues.
- Response quality is inconsistent: different agents apply different policy interpretations.
- High-volume, repetitive queries (order status, return windows, shipping ETAs) consume time that should be reserved for complex escalations.
- SLA targets are missed in peak seasons because staffing elasticity is insufficient.
- New-agent ramp time is long because policy and product knowledge is tribal.

### 1.3 Opportunity

AI/ML can address each failure mode:

| Failure Mode | AI/ML Solution |
|---|---|
| Lookup time dominates handle time | Automated retrieval: customer record, order, KB article |
| Inconsistent policy interpretation | RAG grounded in authoritative KB with version control |
| Repetitive queries consume agent capacity | Intent classification + automated resolution for low-risk actions |
| SLA misses at peak | AI-first triage routes and partially resolves before agent involvement |
| Slow agent ramp | Suggested responses surfaced directly in the agent UI |

### 1.4 Goals

- Reduce average handle time (AHT) by ≥ 30% within 12 months of production.
- Increase first-contact resolution (FCR) rate by ≥ 20%.
- Reduce cost per ticket by ≥ 25%.
- Maintain or improve CSAT score (target ≥ 4.2 / 5.0).
- Achieve ≥ 80% of routine queries (order status, return policy, shipping ETAs) resolvable without agent involvement.

### 1.5 Non-Goals

- This system does not replace human agents for complex, nuanced, or high-risk interactions.
- This system does not perform autonomous financial transactions above defined risk thresholds without human approval.
- This system is not a general-purpose chatbot — scope is limited to Acme Store customer support.
- Multi-language support is deferred to a future phase (English only in v1).
- Real-time voice channel integration is out of scope for v1.

---

## 2. Stakeholders

### 2.1 Stakeholder Map

| Stakeholder | Role | Primary Concern | Success Metric |
|---|---|---|---|
| End customers | Service consumers | Fast, correct, easy resolution | CSAT ≥ 4.2, resolution time < 5 min |
| Support agents | Front-line resolvers | Context at fingertips, less lookup | AHT reduction ≥ 30% |
| Support managers | Team leads | SLA compliance, queue health | FCR ≥ 80% routine, SLA compliance ≥ 95% |
| Business leadership | Executive sponsors | ROI, CSAT, scalability | Cost per ticket ↓ 25%, CSAT stable |
| Engineering | Builders and operators | Reliability, maintainability, security | Uptime ≥ 99.9%, MTTR < 30 min |
| Data Science / AI | Model owners | Performance, feedback loops, experimentation | Eval metrics meet thresholds |
| Compliance / Legal | Risk oversight | Data privacy, safe action limits | Zero unauthorized PII exposures |

### 2.2 Customer Personas

**Persona 1 — Alex (Standard, Self-Serve)**  
Profile: Consumer buyer. Buys electronics occasionally. Comfortable with self-service. Wants instant answers for order status and return questions. Frustrated by wait times and inconsistent answers.  
Key interactions: Order status lookups, return initiation, shipping tracking.

**Persona 2 — Maria (Premium, High-Value)**  
Profile: Frequent shopper with premium membership. Expects priority handling and personalized service. Unwilling to repeat account details. Values speed and consistency.  
Key interactions: Priority queue routing, personalized recommendations, refund disputes.

**Persona 3 — David (Business, Procurement)**  
Profile: SMB procurement manager. Places bulk orders. Needs invoices, purchase orders, order modification. Has a named account manager. Tolerates slightly longer resolution for complex issues if progress is visible.  
Key interactions: Bulk order management, invoicing, order modification after placement.

**Persona 4 — Enterprise IT Lead (Enterprise, Regulated)**  
Profile: Large-company IT department. Strict compliance requirements. Needs audit trails, security assurances, and SLA contracts. Very sensitive to data handling and policy compliance.  
Key interactions: Compliance questions, security incident reporting, SLA tracking.

---

## 3. Current-State Workflow

### 3.1 Inbound Request Flow

```
Customer submits request
  │
  ├── Email
  ├── Chat widget
  └── Phone (out of scope for AI v1)
        │
        ▼
Support queue (FIFO, manual priority assignment)
        │
        ▼
Agent picks up ticket
  │
  ├── Searches CRM for customer record (manual, ~2 min)
  ├── Searches order management for relevant order (manual, ~2 min)
  ├── Searches KB for applicable policy (manual, ~3 min)
  ├── Formulates response (manual, ~3 min)
  └── Resolves or escalates (manual judgment)
        │
        ▼
Resolution recorded in ticketing system (manual, ~1 min)
```

**Average handle time: 11–15 minutes per ticket**

### 3.2 Escalation Flow

```
Agent cannot resolve
  │
  ▼
Manual escalation flag set
  │
  ▼
Senior agent or specialist assigned (queue delay: 30–120 min)
  │
  ▼
Specialist reviews context (may need to re-read entire thread: ~5 min)
  │
  ▼
Specialist resolves or escalates to policy/legal/finance team
```

**Escalation rate: ~22% of tickets**  
**Escalation resolution time: 2–48 hours**

---

## 4. Pain-Point Analysis

| Pain Point | Impact | Root Cause |
|---|---|---|
| Manual customer/order lookup consumes 40% of AHT | High | No context pre-loaded for agent |
| Inconsistent policy answers across agents | High | No authoritative, versioned policy surfacing |
| Agents unaware of order-specific exceptions | Medium | KB not linked to order state |
| Queue backlogs during peak seasons | High | Staffing cannot elastically scale |
| Escalation context loss (re-read whole thread) | Medium | No structured hand-off summary |
| Agents answering questions already in KB | High | Knowledge discovery is search-box only, no suggestions |
| High new-agent ramp time (6–8 weeks) | Medium | Policy and product knowledge is not surfaced in context |
| Agents manually creating ticket records | Low-Medium | No automation; relies on agent discipline |
| Refund/return policy disputes due to misapplication | Medium | Agent applied wrong policy version or customer segment |
| No audit trail for high-risk actions | High | Manual actions not systematically logged |

---

## 5. Future-State Workflow

### 5.1 AI-First Resolution Path

```
Customer submits request
        │
        ▼
Support API ingests message
        │
        ▼
Intelligence Layer
  ├── Intent Classifier  →  categorize intent + priority
  ├── Entity Extractor   →  customer_id, order_id, product_id
  ├── RAG Retrieval      →  fetch relevant KB articles
  ├── CRM Tool           →  fetch customer record + tier
  └── Order Tool         →  fetch order state
        │
        ▼
Agent (LLM) generates response
        │
        ▼
Risk Classifier
  ├── Low risk   → auto-send response
  ├── Medium risk → response queued for agent review (soft approval)
  └── High risk  → route to human approval gate
        │
        ▼
Outcome recorded (ticket created, action logged, conversation closed)
        │
        ▼
Evaluation & Observability pipeline captures result
```

### 5.2 Human-in-the-Loop Path (High-Risk)

```
AI Agent proposes high-risk action
        │
        ▼
Human approval queue surfaced in agent UI
  ├── Agent sees: context, proposed action, policy citation
  └── Agent approves / modifies / rejects
        │
        ▼
If approved → AI executes action via tool call
If rejected → AI reformulates or escalates further
        │
        ▼
Action logged with approver identity, timestamp, reason
```

### 5.3 Agent-Assist Path (Complex Queries)

```
AI cannot resolve with high confidence
        │
        ▼
AI generates context summary + suggested response draft
        │
        ▼
Human agent receives pre-loaded context:
  - Customer profile
  - Order details
  - KB articles retrieved
  - Draft response
        │
        ▼
Agent edits draft and sends (AHT target: < 4 min)
```

---

## 6. Functional Requirements

### FR-01 — Request Ingestion

**The system must:**
- FR-01.1: Accept inbound support requests via REST API (JSON payload).
- FR-01.2: Support multi-turn conversations with session context maintained.
- FR-01.3: Accept asynchronous events (order shipped, refund processed) for proactive outreach.
- FR-01.4: Validate and sanitize all incoming message content before processing.

### FR-02 — Intent Classification

**The system must:**
- FR-02.1: Classify each inbound message into one of the supported intent categories.
- FR-02.2: Assign a priority tier (P0 critical / P1 high / P2 medium / P3 low) to each request.
- FR-02.3: Handle multi-intent messages by identifying the primary and secondary intents.
- FR-02.4: Return intent confidence scores alongside the classification result.
- FR-02.5: Support the following intent classes:

| Intent | Description |
|---|---|
| check_order_status | Customer asking about an order's current state |
| initiate_return | Customer wants to start a return |
| check_return_policy | Customer asking about return windows/rules |
| request_refund | Customer requesting a refund |
| check_refund_status | Customer asking about a pending refund |
| track_shipment | Customer asking for shipping/delivery status |
| report_damaged_item | Customer reporting a damaged product |
| account_issue | Authentication, account access, profile problems |
| billing_issue | Payment, invoice, charge disputes |
| product_question | Pre-purchase or post-purchase product information |
| technical_support | Device, app, or software troubleshooting |
| escalation_request | Customer explicitly requesting human agent |
| out_of_scope | Request outside Acme Store support domain |

### FR-03 — Knowledge Retrieval

**The system must:**
- FR-03.1: Embed and index all 90 knowledge base articles in a vector store.
- FR-03.2: Retrieve the top-k most relevant articles for a given query using hybrid retrieval (dense + sparse).
- FR-03.3: Apply metadata filters (category, product_scope, customer_segment, effective dates) to restrict retrieval to applicable policies.
- FR-03.4: Distinguish between current and historical policy versions and surface the correct version for the query date context.
- FR-03.5: Rerank retrieved results before passing to the language model.
- FR-03.6: Return source citations (document_id, title, section) with every retrieval-backed response.

### FR-04 — Customer Data Retrieval

**The system must:**
- FR-04.1: Look up customer records by customer_id, email, or phone.
- FR-04.2: Return customer tier/segment, account status, contact preferences, and loyalty flags.
- FR-04.3: Enforce access control: the system may only retrieve customer data for the authenticated session.
- FR-04.4: Never expose PII in logs or external outputs.

### FR-05 — Order Data Retrieval

**The system must:**
- FR-05.1: Look up orders by order_id, associated customer_id, or product_id.
- FR-05.2: Return order status, line items, amounts, shipping state, and delivery dates.
- FR-05.3: Surface order-specific exceptions (e.g., damaged shipment flag, warranty claim in progress).
- FR-05.4: Validate that the requesting customer owns the queried order before returning data.

### FR-06 — Response Generation

**The system must:**
- FR-06.1: Generate responses grounded in retrieved KB articles and/or structured data.
- FR-06.2: Refuse to answer questions where no grounding evidence is found (rather than hallucinate).
- FR-06.3: Adapt response tone and detail level to customer segment (Standard vs. Enterprise).
- FR-06.4: Generate responses in under 5 seconds (p95) for synchronous interactions.
- FR-06.5: Apply response templates for high-frequency, low-risk query types (order status, shipping ETA).
- FR-06.6: Include policy citations and applicable document IDs in responses requiring policy justification.

### FR-07 — Ticket Management

**The system must:**
- FR-07.1: Automatically create a support ticket for every inbound request that does not resolve in the first message.
- FR-07.2: Populate ticket fields: customer_id, category, priority, channel, issue summary, intent.
- FR-07.3: Update ticket status as the conversation progresses (open → in_progress → resolved / escalated).
- FR-07.4: Attach conversation transcript and retrieved context to the ticket record.
- FR-07.5: Allow agents to modify AI-assigned priority and category.

### FR-08 — Action Execution (Tool Use)

**The system must:**
- FR-08.1: Execute approved actions via typed tool calls with structured arguments.
- FR-08.2: Support the following tools:

| Tool | Description | Risk Tier |
|---|---|---|
| get_customer_profile | Retrieve customer record | Low |
| get_order_status | Retrieve order details | Low |
| get_order_history | Retrieve all orders for a customer | Low |
| get_shipment_tracking | Retrieve shipping carrier tracking | Low |
| search_knowledge_base | Retrieve KB articles | Low |
| create_support_ticket | Create a new ticket | Low |
| update_ticket_status | Change ticket state | Low |
| initiate_return | Start return process | Medium |
| process_refund | Issue a refund | High |
| cancel_order | Cancel an order | High |
| modify_shipping_address | Change shipping address post-shipment | High |
| change_account_email | Change customer email address | High |
| override_policy | Apply policy exception | High |
| escalate_to_human | Route to human agent | Low |
| send_notification | Send email/SMS to customer | Medium |

- FR-08.3: Log every tool call with: tool name, arguments, response, latency, and invoking agent step.
- FR-08.4: Retry transient tool failures up to 3 times with exponential backoff before surfacing an error.
- FR-08.5: Never execute a High-risk tool without human approval (see Safety Requirements).

### FR-09 — Escalation

**The system must:**
- FR-09.1: Detect when a query exceeds the AI system's resolution capability and route to a human agent.
- FR-09.2: Detect explicit escalation requests from customers ("let me speak to a human").
- FR-09.3: Generate a structured hand-off summary before routing: customer context, order details, conversation summary, recommended next action.
- FR-09.4: Route escalations to the correct agent queue based on issue category and customer segment.
- FR-09.5: Preserve full conversation history and tool call logs for the receiving human agent.

### FR-10 — Audit and Logging

**The system must:**
- FR-10.1: Record every agent decision step: intent classification, retrieval query, documents retrieved, tool calls, response generated.
- FR-10.2: Persist audit logs immutably for ≥ 90 days.
- FR-10.3: Log approver identity and timestamp for every human-approved high-risk action.
- FR-10.4: Produce a replay-safe audit trail: given a conversation ID, full agent reasoning can be reconstructed.

### FR-11 — Asynchronous Event Processing

**The system must:**
- FR-11.1: Consume order lifecycle events (shipped, delayed, delivered, cancelled) from an event queue.
- FR-11.2: Trigger proactive customer notifications for relevant events (e.g., order delayed beyond ETA).
- FR-11.3: Process events idempotently — duplicate events must not trigger duplicate notifications.

---

## 7. Non-Functional Requirements

### NFR-01 — Latency

| Operation | Target (p50) | Target (p95) | Hard Limit |
|---|---|---|---|
| Intent classification | < 200 ms | < 500 ms | 1 s |
| Knowledge retrieval (top-5) | < 300 ms | < 800 ms | 2 s |
| Full response generation (LLM) | < 2 s | < 5 s | 10 s |
| Tool call round-trip (read) | < 300 ms | < 800 ms | 2 s |
| Tool call round-trip (write) | < 500 ms | < 1.5 s | 3 s |
| End-to-end API response | < 3 s | < 7 s | 15 s |

Streaming responses must begin emitting tokens within 1 second of request receipt.

### NFR-02 — Availability

- System SLA: **99.9% uptime** (≤ 8.7 hours downtime per year).
- Planned maintenance windows must not overlap peak support hours (9 AM–6 PM local customer time).
- The system must degrade gracefully: if the LLM inference service is unavailable, fall back to agent-assist mode (surface retrieved context to human agent) rather than returning errors to customers.
- The knowledge retrieval layer must remain available independently of the LLM layer.

### NFR-03 — Scalability

- The system must handle **10× peak load** without manual intervention (horizontal auto-scaling).
- Baseline load: 500 concurrent conversations.
- Peak load target: 5,000 concurrent conversations.
- Knowledge base indexing must complete within 10 minutes for a corpus of up to 10,000 articles.
- Database queries must remain under SLA at 10× ticket volume (50,000 tickets).

### NFR-04 — Reliability

- Mean time to recovery (MTTR) for P0 incidents: **< 30 minutes**.
- Mean time between failures (MTBF): **> 720 hours** (30 days).
- All state (conversations, tickets, audit logs) must be persisted durably — in-memory state loss must not result in data loss.
- Exactly-once semantics required for ticket creation and action execution tools.
- Circuit breakers required on all external integrations (LLM API, CRM, order management).

### NFR-05 — Security

- All API endpoints must require authentication (JWT / OAuth 2.0).
- Customer data access must be scoped to the authenticated session — cross-customer data access must be impossible by design.
- All data in transit must use TLS 1.2 or higher.
- All data at rest must be encrypted (AES-256 or equivalent).
- Secrets (API keys, credentials) must never appear in logs, responses, or source code.
- PII (email addresses, phone numbers, addresses) must be masked in all log output.
- The system must pass OWASP Top 10 assessment before production launch.
- Prompt injection attacks must be detected and blocked (see Safety Requirements).

### NFR-06 — Maintainability

- All components must be containerized (Docker) and deployable via a single command.
- System configuration must be environment-variable driven (no hard-coded values in source).
- Knowledge base updates must be deployable without a full system restart (online re-indexing).
- Model upgrades must be deployable via configuration change (model name/version), not code changes.
- Every component must have a health endpoint (`GET /health`).
- API schema must be versioned (URL-based: `/api/v1/`, `/api/v2/`).

### NFR-07 — Observability

The system must emit:

| Signal Type | Required Metrics |
|---|---|
| Latency | p50, p95, p99 per endpoint and per agent step |
| Error rate | 4xx and 5xx rates, by endpoint and by error type |
| Throughput | Requests/second, conversations/minute |
| AI quality | Retrieval hit rate, response confidence, hallucination flag rate |
| Business | Resolution rate, escalation rate, CSAT (when captured), AHT |
| Infrastructure | CPU, memory, disk I/O, GPU utilization (inference) |

All metrics must be queryable via a time-series database. Dashboards must exist for: real-time queue health, AI quality trends, and incident investigation. Alerts must fire within 2 minutes of threshold breach.

### NFR-08 — Cost

- LLM inference cost per resolved ticket must not exceed **$0.05** at steady state.
- Retrieval (vector DB) cost must not exceed **$0.005** per query.
- Infrastructure cost must scale sub-linearly with ticket volume (target: 0.7× cost for 2× volume via batching and caching).
- Caching must be applied for identical or near-identical retrieval queries (TTL: 5 minutes).
- Model selection must be tiered: smaller/cheaper models for simple intents, larger models for complex reasoning.

---

## 8. AI / ML Requirements

### AIR-01 — Intent Classification

| Metric | Target | Minimum Acceptable |
|---|---|---|
| Overall accuracy | ≥ 90% | ≥ 85% |
| Precision (per class, weighted) | ≥ 88% | ≥ 80% |
| Recall (per class, weighted) | ≥ 88% | ≥ 80% |
| out_of_scope precision | ≥ 95% | ≥ 90% |
| Latency (p95) | < 500 ms | < 1 s |

Evaluated on: `data/evaluation/classification_eval.csv` (200 labeled examples).

### AIR-02 — Knowledge Retrieval

| Metric | Target | Minimum Acceptable |
|---|---|---|
| Recall@5 | ≥ 90% | ≥ 80% |
| Precision@3 | ≥ 85% | ≥ 75% |
| MRR (Mean Reciprocal Rank) | ≥ 0.85 | ≥ 0.75 |
| NDCG@5 | ≥ 0.88 | ≥ 0.78 |
| Latency (p95) | < 800 ms | < 2 s |

The retrieval system must correctly resolve:
- Overlapping policy conflicts (return policies narrowed by product category or customer segment).
- Temporal policy questions (historical vs. current version).
- Multi-hop questions requiring two or more articles combined.

Evaluated on: `data/evaluation/retrieval_eval.jsonl` (100 retrieval scenarios).

### AIR-03 — Answer Correctness

| Metric | Target | Minimum Acceptable |
|---|---|---|
| Correctness (human-eval or LLM-eval) | ≥ 85% | ≥ 75% |
| Faithfulness (grounded in retrieved docs) | ≥ 90% | ≥ 85% |
| Citation accuracy (document_id match) | ≥ 90% | ≥ 85% |
| Refusal rate on unanswerable questions | ≥ 95% | ≥ 88% |

Evaluated on: `data/evaluation/golden_qa.jsonl` (70 hand-crafted QA pairs).

### AIR-04 — Hallucination Control

- The system must **never** fabricate order details, customer data, policy terms, or refund amounts.
- Hallucination rate on factual claims (verifiable against KB or structured data) must be **< 1%**.
- When the system is uncertain, it must express uncertainty explicitly rather than fabricate a confident answer.
- Responses citing non-existent document IDs must not reach the customer — a citation validator must run post-generation.

### AIR-05 — Tool / Action Accuracy

| Metric | Target | Minimum Acceptable |
|---|---|---|
| Tool selection accuracy | ≥ 92% | ≥ 85% |
| Argument extraction correctness | ≥ 90% | ≥ 82% |
| Tool call success rate (no execution error) | ≥ 97% | ≥ 93% |
| Human approval escalation accuracy | ≥ 98% | ≥ 95% |

Evaluated on: `data/evaluation/agent_eval.jsonl` (50 tool-calling scenarios).

### AIR-06 — Agent End-to-End Success

| Metric | Target | Minimum Acceptable |
|---|---|---|
| Fully autonomous resolution rate (routine queries) | ≥ 80% | ≥ 70% |
| Correct escalation rate (should-escalate cases) | ≥ 95% | ≥ 90% |
| False escalation rate (should-resolve cases) | ≤ 10% | ≤ 15% |
| End-to-end CSAT for AI-resolved sessions | ≥ 4.0 / 5.0 | ≥ 3.7 / 5.0 |

### AIR-07 — Adversarial Robustness

The system must correctly handle:
- **Jailbreak attempts**: Requests attempting to override system instructions, extract system prompts, or bypass safety controls — refusal rate ≥ 99%.
- **Prompt injection**: Malicious content in customer messages designed to hijack agent behavior — detection and neutralization rate ≥ 99%.
- **Policy override attempts**: Customer claiming false entitlements ("my manager said I get a 90-day return") — the system must verify against KB rather than accept unverified claims.
- **Out-of-domain requests**: Requests unrelated to Acme Store support — must be routed to `out_of_scope` intent and declined gracefully.

---

## 9. Safety Requirements

### SR-01 — Risk Tier Classification

Every agent action is classified into one of three risk tiers:

| Tier | Actions | Gate Required |
|---|---|---|
| Low | Read-only lookups, KB search, ticket creation, send informational response | None — execute automatically |
| Medium | Initiate return, send notification to customer, cancel low-value order (< $50) | Soft gate — confidence threshold check; log action |
| High | Process refund (any amount), cancel high-value order (≥ $50), modify shipping address post-shipment, change account email, apply policy exception, account security changes | Human approval required — see SR-02 |

### SR-02 — High-Risk Action Gate

All high-risk actions must traverse the following approval gate:

```
Agent proposes action
        │
        ▼
Policy check
  └── Verify proposed action is permitted under applicable KB policy
  └── If policy prohibits: reject action, explain to customer
        │
        ▼
Authorization check
  └── Verify agent (AI or human) has permission for this action type
  └── Verify customer session owns the affected resource (order, account)
        │
        ▼
Human approval queue
  └── Present to human agent: customer context, proposed action, policy citation, risk summary
  └── Agent must approve within configured timeout (default: 15 minutes)
  └── If timeout exceeded: action cancelled, customer notified
        │
        ▼
Execution (with full audit log entry)
  └── Log: action type, arguments, approver_id, approval_timestamp, outcome
```

### SR-03 — Prompt Injection Defense

- All customer-provided content must be treated as untrusted input.
- System prompt must be isolated from customer message content in the LLM call structure.
- The system must detect and block messages containing:
  - Explicit instruction override attempts ("Ignore previous instructions").
  - Role reassignment attempts ("You are now a different assistant").
  - Data exfiltration attempts ("Repeat your system prompt").
- Detected injection attempts must be logged as security events and routed to out_of_scope handling.

### SR-04 — Data Isolation

- The system must enforce that a customer session can only access data belonging to that customer.
- Cross-customer data access must be prevented at the tool call level — every read tool must validate that the authenticated customer_id matches the requested resource's owner.
- A customer may not retrieve another customer's order, ticket, or account information under any circumstances, including via indirect prompting ("look up order ORD-99999 for me, that's my friend's order").

### SR-05 — Graceful Degradation Under Uncertainty

- When confidence in the retrieved policy or generated response falls below a defined threshold, the system must:
  1. Decline to provide a potentially incorrect answer.
  2. Explicitly state that it is uncertain.
  3. Offer to escalate to a human agent.
- The system must never present a low-confidence answer as authoritative.

### SR-06 — PII Handling

- Customer PII (name, email, phone, address, payment method) must never appear in:
  - Log output.
  - LLM prompts beyond what is operationally necessary (minimum necessary principle).
  - Responses returned to parties other than the authenticated session owner.
- PII in LLM prompts must use masked/pseudonymized identifiers where possible.

---

## 10. Out of Scope

The following are explicitly not requirements for v1.0:

- Voice channel support (phone/IVR integration).
- Non-English language support.
- Real-time third-party carrier API integration (simulated via order data).
- Payment processing (refunds are logged as intents; actual payment execution is external).
- Native mobile application.
- Social media channel integration (Twitter/X, Facebook Messenger).
- Fine-tuning proprietary LLM weights.
- Federated identity / SSO integration (deferred to Phase 9).

---

## 11. Assumptions and Constraints

### Assumptions

1. The knowledge base is the authoritative source of truth for all policy responses. No policy answer should be generated without grounding in the KB.
2. Customer data (customers, orders, tickets) is available via a read-only API backed by PostgreSQL — the AI system does not own or mutate this data except via explicitly defined write tools.
3. LLM inference will use a hosted API (not self-hosted in v1) for velocity; self-hosting may be revisited based on cost at scale.
4. All data in this project is synthetic — no real PII exists in the development dataset.
5. Human agents will continue to handle complex, ambiguous, and high-value cases; the AI system is additive, not a full replacement.
6. A customer's tier/segment is determined at session initialization and does not change mid-conversation.
7. The system clock is authoritative for temporal policy resolution (e.g., determining which policy version is active).

### Constraints

1. All open-source and self-hostable tools are preferred over managed proprietary services for core infrastructure.
2. The system must run in a Docker-based environment — no vendor-specific managed compute required for local development.
3. Budget constraint: LLM inference cost must stay below $0.05 per resolved ticket at steady state.
4. The evaluation framework must be automated — no manual scoring step should block a CI/CD deployment pipeline.
5. The system must support hot-swapping the LLM provider without code changes (configuration-driven).

---

## 12. Success Criteria

The platform is considered successful when all of the following are true in production:

| Criterion | Target | Measurement Method |
|---|---|---|
| AHT reduction | ≥ 30% vs. baseline | Ticket analytics (agent_time_spent) |
| FCR improvement | ≥ 20% vs. baseline | Ticket re-open rate |
| Autonomous resolution rate | ≥ 80% for routine queries | AI resolution flag in ticket system |
| CSAT (AI-resolved sessions) | ≥ 4.0 / 5.0 | Post-session survey |
| Retrieval quality (Recall@5) | ≥ 90% | Automated evaluation pipeline |
| Answer correctness | ≥ 85% | Golden QA evaluation pipeline |
| Hallucination rate | < 1% | Faithfulness eval (automated) |
| Tool accuracy | ≥ 92% | Agent eval pipeline |
| Jailbreak refusal rate | ≥ 99% | Adversarial eval suite |
| System uptime | ≥ 99.9% | Infrastructure monitoring |
| P95 end-to-end latency | < 7 s | API gateway metrics |
| Cost per resolved ticket | < $0.05 | LLM usage billing + infrastructure cost |

---

*Document maintained by: Engineering and Data Science teams*  
*Next review: Before Phase 4 (System Architecture) begins*
