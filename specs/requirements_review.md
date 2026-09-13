# Requirements Review: Acme Store Customer Support AI Platform

**Reviewed by:** Senior Product + AI Systems Architect
**Document version reviewed:** 1.0 (Draft)
**Review date:** 2026-09-03

---

## Part 1 — Requirements Review Report

---

### Issue 001

**Requirement/Section:** FR-013 — Human Approval ("high-value cancellation")
**Issue:** "High-value" is undefined. There is no dollar threshold, no order-count threshold, and no product-category rule. Any implementation team will invent a number.
**Why it matters:** The approval trigger is the heart of the human-in-the-loop guarantee for financial actions. If the threshold is wrong, expensive cancellations are auto-approved, or every $5 cancellation blocks a human.
**Recommended clarification:** Define the threshold explicitly — e.g., `order_total > $200 OR contains [electronics, appliances]`. Make it configurable at runtime (stored in policy store, not hardcoded). Specify whether the threshold applies to the refund amount or the order total.
**Priority:** Critical

---

### Issue 002

**Requirement/Section:** FR-013 — Human Approval (SLA for approver response)
**Issue:** No SLA is defined for how long the system waits for human approval. There is no specification of what happens if the approver never responds: auto-reject, auto-escalate, notify customer, timeout with callback?
**Why it matters:** Approval workflows that hang indefinitely produce invisible failures. Customers with pending refunds have no recourse if the queue stalls. This is a reliability and trust issue.
**Recommended clarification:** Define approval SLA (e.g., 4 business hours), define the timeout action (auto-reject with customer notification + ticket, or escalate to supervisor), and define the customer communication cadence during the wait.
**Priority:** Critical

---

### Issue 003

**Requirement/Section:** UC-06 — Account/Security Change ("Authentication")
**Issue:** The use case mentions "Authentication + policy + approval" but the identity re-verification method is completely undefined. There is no requirement specifying whether this means re-entering a password, OTP, security question, or out-of-band verification. This is the most security-critical flow in the system.
**Why it matters:** Without specifying re-verification, the implementation may inadvertently allow account takeover via a support chat session. An attacker who gains access to a customer session could change the email address to their own.
**Recommended clarification:** Specify the identity re-verification protocol for each change type. At minimum: email change requires OTP to original email + human approval. Address change after shipment requires original payment method verification. Define what "strong authentication" means in operational terms.
**Priority:** Critical

---

### Issue 004

**Requirement/Section:** Section 29 — Success Criteria / Section 19 — Performance Requirements
**Issue:** No SLOs (Service Level Objectives) are defined. The document says "measure latency" but sets no thresholds. There is no availability target (99.9%? 99.95%?), no P95 latency budget, no error rate budget.
**Why it matters:** A production AI system without SLOs cannot be operated. You cannot set alerts, cannot define incident thresholds, and cannot tell whether the system is performing acceptably or degrading.
**Recommended clarification:** Define at minimum: API P95 latency target (e.g., <3s for synchronous flows), end-to-end agent P95 target (e.g., <8s), availability SLO (e.g., 99.5% for this v1 system), maximum error rate before alert. Even rough targets give architecture direction.
**Priority:** Critical

---

### Issue 005

**Requirement/Section:** EVAL-006 — Quality Gates ("Material quality regressions should block promotion")
**Issue:** "Material" is undefined. A 1% drop in Recall@5 may or may not be material depending on baseline. Without a numeric threshold, this gate is unenforceable.
**Why it matters:** CI/CD quality gates that are qualitative rather than quantitative are not gates — they are opinions. Teams will argue about whether a regression is "material" instead of having automated enforcement.
**Recommended clarification:** Define specific numeric regression thresholds per metric tier (e.g., Recall@5 drop >5% from baseline blocks promotion; groundedness drop >3% blocks promotion). Define the evaluation dataset size required for the gate to be statistically valid.
**Priority:** Critical

---

### Issue 006

**Requirement/Section:** LLM-002 — "Use Ollama as the initial local/self-hosted LLM serving layer" vs. Section 21 Deployment Architecture
**Issue:** Contradiction. LLM-002 specifies Ollama for local development. Section 21 shows a cloud deployment target with containers. There is no specified migration path from Ollama dev to cloud inference in production. It is unclear whether Ollama is only for dev, or if a self-hosted Ollama instance is also the production inference layer.
**Why it matters:** The architecture of the LLM serving layer is fundamentally different depending on this answer. Local Ollama has very different latency, throughput, reliability, and cost profiles than a cloud-hosted model API. Tool-calling reliability also varies significantly across models and serving environments.
**Recommended clarification:** State explicitly: "Ollama is development-only. Production will use [X: cloud API / self-hosted vLLM / managed inference]." Or: "Ollama is also the initial production serving layer, running on [hardware spec], and migration to cloud inference is a future experiment."
**Priority:** Critical

---

### Issue 007

**Requirement/Section:** FR-002 — Conversation Handling ("Maintain sufficient multi-turn context")
**Issue:** "Sufficient" is undefined. No maximum turn count, no context window management strategy, no specification of what happens when the conversation exceeds the LLM's context limit (truncation? summarization? embedding-based retrieval of prior turns?).
**Why it matters:** Production conversations can be long. Without a strategy, the system either silently loses context (causing incoherent responses) or fails when the token limit is exceeded.
**Recommended clarification:** Define the maximum turns to preserve verbatim, the summarization strategy for older turns, and the maximum total context length. Specify how the conversation memory interacts with the retrieved knowledge context (the combined prompt must fit in the model's context window).
**Priority:** High

---

### Issue 008

**Requirement/Section:** FR-005 — Grounded Responses ("must be grounded in retrieved information")
**Issue:** "Grounded" has no numeric definition. There is no groundedness threshold for passing evaluation, no specification of how groundedness is measured in production (real-time check vs. offline evaluation), and no handling of partial grounding (some claims supported, some not).
**Why it matters:** Groundedness is the primary quality contract with customers. Without a measurable definition, you cannot assert whether the system is meeting this requirement.
**Recommended clarification:** Define groundedness measurement method (LLM-as-judge with attribution scoring, NLI entailment, or citation coverage). Define the minimum groundedness score for an acceptable response. Define the runtime action when a generated response fails the groundedness check (regenerate once, then abstain, or always abstain after failed check).
**Priority:** High

---

### Issue 009

**Requirement/Section:** Section 14 — Asynchronous Processing (message broker specification)
**Issue:** Section 6 mentions "cache/message broker where required" and Section 14 mentions background jobs. No message broker technology is specified, no delivery guarantees are defined (at-least-once vs. exactly-once), no dead-letter queue requirement exists, and no queue depth monitoring is specified.
**Why it matters:** The choice of message broker (e.g., Redis Streams, Celery+Redis, PostgreSQL-backed queue) directly affects job delivery guarantees, ordering, retry behavior, and whether refund or cancellation jobs can be safely retried without double-execution.
**Recommended clarification:** Specify the message broker technology or shortlist. Define delivery guarantee required (at-least-once with idempotency is minimum for financial jobs). Define dead-letter queue requirement and alerting threshold for queue depth.
**Priority:** High

---

### Issue 010

**Requirement/Section:** Section 16 / Section 17 — Data Requirements (embedding model)
**Issue:** The embedding model for the RAG pipeline is never specified. There is no requirement for which embedding model to use, how embeddings are stored alongside documents, or what happens when the embedding model is changed (requiring full re-indexing of the knowledge base).
**Why it matters:** The embedding model determines retrieval quality and is a foundational architectural decision. Changing it mid-project requires full re-indexing, re-evaluation, and potentially breaking changes to stored vectors.
**Recommended clarification:** Specify the initial embedding model (e.g., `nomic-embed-text` via Ollama for local, or a benchmark of 2-3 options). Define the embedding versioning strategy — vector records must store which embedding model version produced them, so re-indexing can be triggered selectively.
**Priority:** High

---

### Issue 011

**Requirement/Section:** SEC requirements — No rate limiting
**Issue:** There is no rate limiting requirement anywhere in the document. The system exposes an API that triggers LLM inference (expensive) and customer data lookups. Without rate limiting, a single malicious or broken client can exhaust resources or generate runaway inference costs.
**Why it matters:** This is both a security control (DoS protection) and a cost control (inference cost runaway). It is also a reliability control (protecting downstream services from overload).
**Recommended clarification:** Add a rate limiting requirement specifying limits per customer, per API key, and per IP. Define the behavior on rate limit breach (HTTP 429, retry-after header, graceful message to customer).
**Priority:** High

---

### Issue 012

**Requirement/Section:** SEC requirements — No data retention or privacy policy
**Issue:** The system processes customer names, emails, addresses, order histories, and payment-adjacent information. There is no requirement for data retention period, no right-to-deletion (GDPR/CCPA) requirement, and no PII field classification.
**Why it matters:** Conversation logs, tool call results, and audit trails accumulate indefinitely. Storing PII in log streams without retention limits is a compliance and data breach risk, even with synthetic data in development.
**Recommended clarification:** Define retention policy for conversation logs, audit records, and evaluation traces. Define PII fields (customer email, name, address, payment info) and their handling rules (masking in logs, encryption at rest, deletion workflow). Even if regulatory compliance is out of scope for v1, the architecture must not foreclose it.
**Priority:** High

---

### Issue 013

**Requirement/Section:** FR-012 vs. FR-013 — Escalation vs. Approval (workflow boundary overlap)
**Issue:** Escalation (FR-012) means handing off to a human. Approval (FR-013) means getting a yes/no decision while the agent may continue. These are different workflows but the document does not specify: (a) Can the conversation continue while an approval is pending? (b) Does approval failure automatically trigger escalation? (c) If an approval is pending and the customer sends another message, what happens?
**Why it matters:** Without defining these interaction states, the implementation will have undefined behavior in the most sensitive workflows (refunds, cancellations, account changes). State machine design requires these transitions to be explicit.
**Recommended clarification:** Draw the state machine for approval-pending interactions. Define: pending_approval → customer_message → [pause and explain / queue message / escalate]. Define: pending_approval → timeout → [auto-reject + notify + escalate]. Define: approval_denied → [notify customer + offer alternatives / auto-escalate].
**Priority:** High

---

### Issue 014

**Requirement/Section:** FR-014 — Tool Permission Model ("allowed caller")
**Issue:** Every tool must define "allowed caller" but the only caller described is "the agent." The document does not address whether tools can be called by: evaluation harness (for testing), background workers, administrators (for manual operations), or other services via the API.
**Why it matters:** If the evaluation harness calls tools against production data, this is a security gap. If background workers can call high-risk tools without an approval workflow, this bypasses the human-in-the-loop requirement.
**Recommended clarification:** Enumerate valid callers per tool and specify the authentication/authorization mechanism for each. Evaluation tools should target a sandboxed environment, not production data. Background workers calling write tools must carry an approval token provenance.
**Priority:** High

---

### Issue 015

**Requirement/Section:** FR-016 — Guardrails ("must not rely solely on an LLM prompt")
**Issue:** The requirement correctly mandates non-LLM guardrails but does not specify what the non-LLM layer consists of. Are these regex-based pattern matchers? A fine-tuned classifier? A rule engine? An allow-list of permitted tool calls? The requirement identifies the problem but provides no direction.
**Why it matters:** Guardrail architecture is a distinct engineering problem. An LLM-only guardrail will fail against sufficiently creative adversarial input. Without specifying the non-LLM mechanism, implementation teams will default to prompt-only guards.
**Recommended clarification:** Specify the layers: (1) rule-based input filtering (regex/keyword for known injection patterns); (2) structural validation of tool arguments (schema enforcement before execution); (3) LLM-based classifier as a secondary layer for semantic attacks; (4) output filtering before response delivery. Each layer must be independently testable.
**Priority:** High

---

### Issue 016

**Requirement/Section:** EVAL-001 — ("Use the provided... datasets")
**Issue:** The evaluation datasets are referenced but not described. There is no specification of: how many golden QA examples exist, who authored the golden answers, how the retrieval evaluation dataset was constructed (ground truth relevance labels), what schema the agent evaluation dataset uses, or how these datasets will be maintained and versioned.
**Why it matters:** Evaluation is described as "first-class engineering" but the datasets that make it possible are treated as black boxes. Poorly constructed golden datasets will produce misleading evaluation results and false confidence.
**Recommended clarification:** Document each evaluation dataset: size, schema, construction methodology, ground truth labeling process, update frequency, version control location, and contamination prevention policy (ensure evaluation data was not used in knowledge base construction).
**Priority:** High

---

### Issue 017

**Requirement/Section:** Section 23 — Human-in-the-Loop ("policy-driven")
**Issue:** The policy is described as "policy-driven" but the policy storage, versioning, and runtime management are not specified. Who can modify the escalation policy? Where is it stored (database? config file? admin UI?)? Can it be changed without redeployment? How are policy changes audited?
**Why it matters:** Runtime-configurable policy is essential for a production support platform (e.g., increasing the high-value threshold during a sale event). If policy is hardcoded, changes require deployment, introducing latency and risk.
**Recommended clarification:** Define a policy store (database table, admin-managed) with versioning and audit log. Define who can modify policy (admin role only). Define whether policy changes take effect immediately or at the next interaction.
**Priority:** High

---

### Issue 018

**Requirement/Section:** LLM-003 — Model Selection ("Where resources permit")
**Issue:** "Where resources permit" is a vague qualifier that makes this requirement non-actionable. No hardware specification, no minimum GPU VRAM, and no benchmark timeline is given.
**Why it matters:** Model benchmarking is a significant engineering effort (infrastructure, evaluation, analysis). Without resource specifications, it cannot be planned or scoped.
**Recommended clarification:** Specify the available hardware (e.g., "single consumer GPU with 8-24GB VRAM"), the number of candidate models to benchmark (2-3 is stated, list the candidates), and the benchmark timeline. If resources are genuinely unknown, make model selection a scoped discovery spike with a defined output.
**Priority:** High

---

### Issue 019

**Requirement/Section:** FR-017 — Ambiguous Requests ("ambiguity materially affects the answer")
**Issue:** "Materially affects" is undefined. There is no specification of how the system determines when to ask a clarification vs. proceeding with the most probable interpretation. There is also no maximum clarification turn limit specified.
**Why it matters:** Over-clarification degrades customer experience (constant questions). Under-clarification produces wrong actions. Without a definition and a turn limit, the system can enter infinite clarification loops.
**Recommended clarification:** Define the confidence threshold below which clarification is triggered. Define the maximum number of clarification turns before escalation (suggest: 2). Specify that clarification questions must be single, specific, and present options where possible rather than open-ended.
**Priority:** Medium

---

### Issue 020

**Requirement/Section:** Section 25 — Monitoring and Drift (ML drift thresholds)
**Issue:** Drift monitoring is listed but no alerting thresholds or response procedures are defined. "Monitor classification performance" does not specify when drift becomes actionable.
**Why it matters:** Drift monitoring without alert thresholds is observability theater. The value of drift monitoring is triggering retraining, investigation, or rollback.
**Recommended clarification:** Define drift detection method (PSI, KL divergence, or rolling metric comparison). Define alert threshold per metric. Define the response procedure (who gets alerted, what the SLA for investigation is).
**Priority:** Medium

---

### Issue 021

**Requirement/Section:** FR-004 — Knowledge Retrieval (experimentation with retrieval)
**Issue:** The requirement mentions "support experimentation" with multiple retrieval strategies, but there is no specification of the A/B testing or shadow evaluation infrastructure. Running retrieval experiments in production without a framework is risky.
**Why it matters:** Experimenting with chunking or reranking on live traffic can degrade response quality unpredictably. Without an offline evaluation framework as a prerequisite, experiments cannot be safely evaluated.
**Recommended clarification:** Specify that retrieval experiments are run offline first (using the retrieval evaluation dataset), then promoted with an evaluation gate, not directly on live traffic. Define the offline → online experiment promotion criteria.
**Priority:** Medium

---

### Issue 022

**Requirement/Section:** OBS-004 — Tool observability ("avoiding unnecessary sensitive data in logs")
**Issue:** "Unnecessary" is undefined. There is no specification of which fields are PII, which must be masked in logs, and which can be logged in plain text. This creates inconsistent implementations that may log PII in some paths and miss it in others.
**Why it matters:** Inconsistent PII logging is a compliance and breach risk. Developers will make different judgment calls without a clear standard.
**Recommended clarification:** Define a PII field registry (customer email, name, address, payment token) and specify the masking rule for each (e.g., email → `****@domain.com`, address → city+country only). Apply this registry uniformly across all logging paths.
**Priority:** Medium

---

### Issue 023

**Requirement/Section:** FR-008 — Product Information ("Combine with knowledge-base information where required")
**Issue:** The combination logic between structured product data (from the database/tool) and unstructured KB information (from RAG) is undefined. When both are retrieved, which takes precedence? How are conflicts resolved (e.g., KB says product has 1-year warranty, but product database says 2-year)?
**Why it matters:** Conflicting information between structured data and KB documents will produce incoherent or incorrect responses. The agent needs a defined priority order.
**Recommended clarification:** Define the authority hierarchy: structured product data from the database takes precedence for factual attributes (warranty period, specs, price). KB documents take precedence for policies and procedures. Conflicts must trigger escalation rather than agent synthesis.
**Priority:** Medium

---

### Issue 024

**Requirement/Section:** Section 26 — Continuous Improvement ("Production failures should become evaluation cases")
**Issue:** No feedback mechanism is specified. There is no requirement for a customer feedback signal (thumbs up/down, CSAT survey), no agent feedback interface (flagging AI responses for review), and no pipeline for converting failures into evaluation data.
**Why it matters:** The continuous improvement loop is described but has no implementation path. Without a feedback capture mechanism, the loop starts with "interaction" but has no connection to "feedback."
**Recommended clarification:** Specify the feedback capture mechanism: (a) customer feedback (post-interaction CSAT, inline rating); (b) agent feedback (flag-for-review interface); (c) automated failure detection (tool call failures, escalation events). Define the pipeline from flagged interaction to labeled evaluation example.
**Priority:** Medium

---

### Issue 025

**Requirement/Section:** Section 21 — Deployment ("Cloud/provider selection will be made later")
**Issue:** Several architecture decisions depend on cloud provider: vector DB as a managed service vs. self-hosted, message broker technology, container orchestration, secrets management, networking, and TLS termination. Deferring this decision means the architecture cannot be fully specified.
**Why it matters:** Architecture decisions are not cloud-neutral at this level of detail. Choosing a local Qdrant vs. Pinecone vs. pgvector has different operational, cost, and scaling implications.
**Recommended clarification:** Either make a provisional cloud-provider decision with a stated assumption (e.g., "assuming self-hosted on a single Linux VM for v1, AWS ECS for v2"), or enumerate the cloud-agnostic constraints (must support: PostgreSQL, container runtime, self-hosted vector DB, Redis-compatible broker) and note provider selection as a pending ADR.
**Priority:** Medium

---

### Issue 026

**Requirement/Section:** REL-002 / REL-001 — No circuit breaker, no chaos testing requirement
**Issue:** Bounded retries with backoff (REL-002) are necessary but not sufficient. Without circuit breakers, a failing downstream service (LLM inference, vector DB) will be retried until all threads are exhausted. No chaos engineering requirement means failure paths are specced but never validated.
**Why it matters:** Without circuit breakers, retry storms cause cascading failures. Without chaos testing, the graceful degradation claimed by REL-004/005 is untested.
**Recommended clarification:** Add REL-007 (Circuit breaker pattern required for LLM, vector DB, and database calls). Add a testing requirement for chaos/failure injection to validate degradation paths (can be in Section 22 Testing Requirements).
**Priority:** Medium

---

### Issue 027

**Requirement/Section:** Section 18 — Database Requirements (no backup/recovery spec)
**Issue:** PostgreSQL is the primary operational data store but there is no RPO (Recovery Point Objective) or RTO (Recovery Time Objective) requirement, no backup frequency requirement, and no data migration strategy.
**Why it matters:** A production database without a backup policy is a single point of failure for all operational data. Even for a v1 system, defining RPO/RTO focuses the infrastructure design.
**Recommended clarification:** Add a database reliability requirement: backup frequency (e.g., daily full + WAL archiving), RPO target (e.g., <1 hour), RTO target (e.g., <4 hours). Even if the v1 system accepts higher risk, the requirement should acknowledge this explicitly.
**Priority:** Medium

---

### Issue 028

**Requirement/Section:** FR-003 — Intent Understanding (intent taxonomy versioning)
**Issue:** The intent list is provided but there is no requirement for intent taxonomy versioning, for handling out-of-taxonomy intents gracefully, or for how the taxonomy evolves over time as new support scenarios emerge.
**Why it matters:** Intent classifiers trained on a fixed taxonomy will degrade as real-world requests drift. New product categories or policy changes generate new intents that the model won't recognize.
**Recommended clarification:** Define the intent taxonomy as a versioned artifact. Specify the process for adding new intents (data collection → model update → evaluation → deployment). Define the fallback behavior for unrecognized intents.
**Priority:** Low

---

### Issue 029

**Requirement/Section:** LLM-001 — Model Abstraction (prompt management missing)
**Issue:** LLM-001 requires a model abstraction layer but there is no requirement for prompt management: prompt versioning, prompt registry, A/B testing of prompts, or prompt rollback. Prompts are first-class artifacts in an LLM system but are treated implicitly here.
**Why it matters:** Without prompt versioning, changes to prompts are untraceable. EVAL-005 requires rerunning evaluations after prompt changes — this is only possible if prompts are versioned and retrievable.
**Recommended clarification:** Add a prompt management requirement: prompts must be versioned (e.g., stored in database or version control with semantic versioning), each generated output must record the prompt version used (linked to LLM-004 configuration traceability), and prompt changes must trigger regression evaluation before promotion.
**Priority:** Low

---

### Issue 030

**Requirement/Section:** Section 22 — Testing Requirements (LLM output sanitization missing)
**Issue:** If the system renders LLM output in any web context (customer-facing UI, agent dashboard), LLM-generated content could contain HTML/JavaScript if the model is manipulated. No requirement exists for output sanitization before rendering.
**Why it matters:** LLM outputs rendered unsanitized in a browser context are an XSS vector. This is especially relevant if the system ever exposes a web interface.
**Recommended clarification:** Add a security requirement: all LLM-generated text must be treated as untrusted content and HTML-escaped before rendering in any web context. This is independent of guardrails — it is a defense-in-depth output layer.
**Priority:** Low

---

## Part 2 — Requirements Gaps

The following information is missing and must be resolved before architecture can begin on the indicated components.

| Gap | Blocking Component | Required Before |
|---|---|---|
| High-value threshold definition | Approval workflow, cancellation tool | UC-05 architecture |
| Approval SLA and timeout actions | Human approval state machine | UC-04, UC-05, UC-06 architecture |
| Identity re-verification method for UC-06 | Account security tool | UC-06 architecture |
| API latency SLOs (P95 targets) | API layer, LLM serving, caching | All component sizing |
| Evaluation quality gate thresholds | CI/CD pipeline, regression suite | EVAL-005, EVAL-006 |
| LLM serving strategy (dev vs. production) | Inference infrastructure | All LLM-dependent components |
| Embedding model selection and versioning | Vector DB, RAG pipeline | FR-004, Section 17 |
| Message broker technology | Async job infrastructure | Section 14, refund/cancel workflows |
| Approval request delivery mechanism | Human agent interface | FR-013 |
| Policy store technology and management | Human-in-the-loop, guardrails | Section 23, FR-016 |
| Feedback capture mechanism | Continuous improvement loop | Section 26 |
| Cloud/infra provider decision | Deployment, vector DB, secrets | Section 21 |
| PII field registry and masking rules | Logging, audit, OBS-004 | SEC-007, OBS-004 |
| Conversation context overflow strategy | Agent context management | FR-002 |
| Groundedness threshold and measurement method | Evaluation, runtime check | FR-005, EVAL-003 |
| Adversarial evaluation dataset | Guardrail evaluation | EVAL-004, UC-10 |
| Evaluation dataset schemas and sizes | All EVAL requirements | EVAL-001 through EVAL-006 |
| Rate limiting policy | API security | SEC-001 |
| Clarification turn limit | Ambiguity workflow | UC-08 |
| Data retention and privacy policy | Log storage, audit records | SEC requirements, GDPR |

---

## Part 3 — Use Case Specification Draft

Each specification follows: Actor → Trigger → Preconditions → Inputs → Decision Logic → Retrieval Requirements → Tool Requirements → Approval Requirements → Output → Failure Paths → Audit Requirements → Evaluation Criteria → KPI Linkage.

---

### UC-01 — Simple FAQ

**Actor:** Customer (authenticated or anonymous)
**Trigger:** Customer asks a factual question answerable from the knowledge base (e.g., "What are your shipping times?", "Do you offer price matching?")
**Preconditions:** Knowledge base is indexed; RAG pipeline is operational; no customer-specific data required
**Inputs:** `customer_id` (optional), `conversation_id`, `channel`, `message`, `timestamp`

**Decision Logic:**
1. Intent classifier identifies FAQ intent with high confidence
2. System determines no customer-specific tool call is required
3. Hybrid retrieval (semantic + lexical) queries knowledge base
4. Reranker scores and selects top-K chunks
5. LLM generates response grounded exclusively in retrieved content
6. Runtime groundedness check validates response against source chunks
7. If groundedness below threshold: regenerate once; on second failure, abstain and offer escalation
8. Source attribution attached to response

**Retrieval Requirements:** Hybrid search (semantic + BM25); top-K configurable; minimum relevance score threshold (to be calibrated by retrieval evaluation); chunk-level metadata preserved

**Tool Requirements:** None

**Approval Requirements:** None

**Output:** Grounded text response; source attribution (document title, section, version, effective date); conversation ID; groundedness indicator

**Failure Paths:**
- KB unavailable → static safe fallback message + escalation offered
- No relevant documents retrieved (score below threshold) → abstain, offer escalation, flag KB gap
- LLM timeout → retry once with reduced context; fallback to "I cannot answer right now" + escalation
- Groundedness check fails after retry → abstain with explanation

**Audit Requirements:** Interaction ID; retrieved document IDs and relevance scores; LLM model ID and version; prompt version; response text; source citations; groundedness score

**Evaluation Criteria:** Recall@5, Precision@5, MRR, nDCG against retrieval evaluation dataset; groundedness score ≥ defined threshold; answer correctness against golden QA dataset; P95 latency; abstention rate on out-of-scope questions

**KPI Linkage:** FCR (customer resolved without agent); CSAT; automation rate; AHT reduction

---

### UC-02 — Order Status

**Actor:** Customer (authenticated with verified session)
**Trigger:** Customer asks about their order (e.g., "Where is my order?", "When will order #5023 arrive?")
**Preconditions:** Customer is authenticated; order exists in database; customer owns the order; order tool operational
**Inputs:** `customer_id` (required), `conversation_id`, `message`, `order_id` (explicit or extracted from NER), `timestamp`

**Decision Logic:**
1. Intent: order status
2. Extract `order_id` from message; if absent, query most recent open orders for customer
3. Authorization check: verify `order.customer_id == session.customer_id` — hard block if mismatch, log security event
4. Execute `get_order_tool` with `{customer_id, order_id}`
5. Parse status, items, tracking number, estimated delivery
6. If order is delayed or status is anomalous (lost, returned unexpectedly), offer escalation path
7. Generate response from structured order data (no RAG needed for status itself)
8. Optional: if customer asks follow-up shipping policy question, trigger retrieval for shipping policy KB

**Retrieval Requirements:** Optional; only if customer asks shipping policy follow-up; not required for core order status display

**Tool Requirements:**
- `get_order_tool`: `{customer_id, order_id}` → `{status, items[], tracking_number, carrier, estimated_delivery, shipping_address_masked}`; risk: LOW (read-only); authorization: customer session; PII: address masked in logs

**Approval Requirements:** None (read-only)

**Output:** Order status summary; estimated delivery date; tracking number (not hyperlink unless verified); item list; order total

**Failure Paths:**
- Order not found → ask for order ID, offer to list recent orders
- Authorization failure (order belongs to different customer) → hard refuse, log security event, do not reveal order exists
- Tool timeout → retry once with backoff; if still failing: "I can't retrieve your order right now, please try again shortly" + offer escalation
- No order ID extractable after clarification attempt → escalate

**Audit Requirements:** `customer_id`, `order_id` accessed; authorization check result; tool call arguments and result (address masked); agent decision trace; interaction ID

**Evaluation Criteria:** Correct tool selected; correct `customer_id`/`order_id` extraction; authorization check always executed; no cross-customer data leakage; response accuracy vs. expected order fixture; P95 latency

**KPI Linkage:** FCR; AHT reduction; automation rate for order status queries

---

### UC-03 — Return Policy

**Actor:** Customer (authenticated or anonymous)
**Trigger:** Customer asks about return eligibility or process (e.g., "Can I return this item?", "What's the return window?", "How do I return a damaged product?")
**Preconditions:** Return policy documents exist and are indexed in KB; if order-specific: customer is authenticated and order tool is operational
**Inputs:** `customer_id` (optional), `conversation_id`, `message`, `order_id` (optional), `product_id` (optional), `timestamp`

**Decision Logic:**
1. Intent: return policy
2. Sub-classify: general policy question vs. order-specific return eligibility question
3. For general policy: RAG retrieval from return policy KB documents
4. For order-specific: retrieve policy KB + call `get_order_tool` (purchase date, product category, order status)
5. Match retrieved policy version to order date (temporal validity — policy at time of purchase applies, not current policy)
6. Apply eligibility rules: return window elapsed?, product category eligible?, order status eligible?
7. If eligible: return instructions + note that return initiation is a separate action (may trigger UC-04)
8. If ineligible: explain reason with policy citation; offer escalation for exceptions
9. Conflicting signals between KB and order data → escalate, do not synthesize

**Retrieval Requirements:** Hybrid retrieval from return policy documents; temporal validity filter (policy effective date ≤ purchase date); product-specific policy documents if product_id available; chunk metadata must include policy version and effective date range

**Tool Requirements:**
- `get_order_tool` (if order-specific): `{customer_id, order_id}` → `{purchase_date, product_category, order_status, items[]}`; risk: LOW; authorization: customer session
- `get_product_tool` (optional): `{product_id}` → `{category, warranty_period, special_return_conditions}`; risk: LOW; public product data

**Approval Requirements:** None (read-only policy explanation); return initiation routes to UC-04

**Output:** Policy explanation grounded in KB; eligibility determination (if order-specific); return process steps; source attribution with policy version and effective date

**Failure Paths:**
- Policy document not found → abstain, escalate to human, flag KB gap
- Order tool unavailable → answer general policy only; explicitly note that order-specific eligibility cannot be confirmed
- Policy version mismatch (purchase pre-dates KB records) → escalate; do not apply current policy to historical order
- Conflicting policies (general vs. product-specific) → escalate; do not synthesize

**Audit Requirements:** Retrieved policy document IDs and versions; order data accessed; temporal validity logic trace; eligibility decision with reasoning

**Evaluation Criteria:** Policy accuracy vs. golden QA; correct policy version applied based on purchase date; groundedness: every eligibility claim traceable to retrieved document; abstention on conflicting evidence; no fabricated conditions

**KPI Linkage:** FCR; return rate policy compliance; customer satisfaction with policy clarity; reduction in agent escalations for basic return policy questions

---

### UC-04 — Refund Request

**Actor:** Customer (authenticated)
**Trigger:** Customer explicitly requests a refund for a completed or returned order
**Preconditions:** Customer is authenticated; order exists and belongs to customer; refund policy in KB; human approval workflow operational; `create_refund_tool` accessible
**Inputs:** `customer_id` (required), `conversation_id`, `order_id`, `refund_reason`, `refund_amount_requested` (or "full order"), `timestamp`

**Decision Logic:**
1. Intent: refund request
2. Authenticate customer; verify session
3. Retrieve order via `get_order_tool` — confirm ownership, order status, and items
4. Retrieve refund/return policy via RAG (temporal validity: policy at purchase date)
5. Evaluate eligibility: return window, product category, prior refund history, order status
6. Calculate eligible refund amount (full or partial, per policy)
7. If ineligible: explain with policy citation; offer exception escalation (UC-11)
8. If eligible: generate approval request package containing order details, eligibility assessment, policy citation, refund amount, customer history summary
9. Submit approval request to human approval queue (FR-013 — ALL refunds require approval)
10. Notify customer: "Your refund request has been received and is pending review. Reference: [ticket_id]. Expected response within [SLA]."
11. On approval decision (async): if approved → execute `create_refund_tool`; notify customer; if denied → notify customer with reason; offer escalation

**Retrieval Requirements:** Refund and return policy documents (temporal validity enforced); product-specific policies if applicable

**Tool Requirements:**
- `get_order_tool`: {customer_id, order_id} → order details; risk: LOW; read-only
- `create_approval_request_tool`: {request_type: "refund", order_id, amount, eligibility_assessment, policy_citations, customer_id}; risk: MEDIUM (creates pending action); audit: full
- `create_refund_tool`: {approval_token, order_id, refund_amount, reason, customer_id}; risk: HIGH (financial write); requires: valid approval token; idempotency key: `order_id + refund_type`; audit: complete; only callable post-approval
- `notify_customer_tool`: {customer_id, message_type, content, channel}; risk: LOW

**Approval Requirements:**
- All refunds require human approval regardless of amount
- Approval package must include: order summary, eligibility assessment, policy document citations, calculated amount, customer refund history
- Approval SLA: [UNDEFINED — must be specified]
- Timeout action: [UNDEFINED — must be specified]
- Approver role: `support_agent` or `support_supervisor`

**Output:** Immediate: refund request confirmation with ticket ID and expected SLA; Async after approval: approval/denial notification with next steps

**Failure Paths:**
- Order not found or not owned by customer: refuse with explanation
- Policy document unavailable: abstain, create ticket, escalate
- Not eligible per policy: explain with citation, offer escalation for exceptions
- Approval timeout: notify customer, escalate to supervisor, maintain ticket
- `create_refund_tool` failure after approval: retry with idempotency key; on persistent failure: create incident ticket; do not double-refund
- Duplicate refund request on same order: idempotency check returns existing ticket ID

**Audit Requirements:** Customer ID; order ID; eligibility assessment with reasoning; policy documents referenced with versions; approval request ID; approver identity, timestamp, decision; refund execution result; idempotency key

**Evaluation Criteria:** Correct eligibility determination on test fixtures; approval workflow always triggered (never bypassed in any code path); correct refund amount calculation; no double refunds (idempotency); correct policy version applied; failure handling prevents incomplete state

**KPI Linkage:** Refund processing time (from request to resolution); refund accuracy rate; agent time per refund approval; customer satisfaction with refund process

---

### UC-05 — High-Value Cancellation

**Actor:** Customer (authenticated)
**Trigger:** Customer requests to cancel an order; order value or type meets the high-value threshold (threshold currently undefined — see Issue 001)
**Preconditions:** Customer is authenticated; order exists in database; order is in a cancellable state (pending or processing); high-value threshold policy is defined and loaded; cancellation policy in KB
**Inputs:** `customer_id` (required), `conversation_id`, `order_id`, `cancellation_reason`, `timestamp`

**Decision Logic:**
1. Intent: order cancellation
2. Retrieve order via `get_order_tool` — check ownership, status, and total value
3. If order is shipped/delivered: cannot cancel; redirect to return/refund flow (UC-03, UC-04)
4. Check order value against high-value threshold [threshold must be defined before implementation]
5. Retrieve cancellation policy via RAG — check cancellation window, restocking fees, refund terms
6. If high-value: build approval request package; submit to human approval queue; notify customer of pending review
7. If below threshold (policy gap: auto-approval path not fully specified): follow cancellation policy rules
8. After approval: execute `cancel_order_tool`; trigger refund initiation per policy
9. Notify fulfillment system (side effect)
10. Notify customer with confirmation and refund timeline

**Retrieval Requirements:** Cancellation policy (temporal validity); refund terms for cancelled orders; product-specific cancellation conditions

**Tool Requirements:**
- `get_order_tool`: ownership and status verification; risk: LOW
- `create_approval_request_tool`: {request_type: "high_value_cancellation", order_id, order_value, reason}; risk: MEDIUM; audit: full
- `cancel_order_tool`: {approval_token, order_id, reason}; risk: HIGH (write, triggers fulfillment); side effects: order status update, refund initiation, fulfillment notification; idempotency key: `order_id`; audit: complete
- `notify_customer_tool`: risk: LOW

**Approval Requirements:**
- Required when order_value > [UNDEFINED threshold — must be defined]
- Approval package must include: order value, items, customer order history, reason, policy assessment
- What constitutes a "high-value" order must be defined before this UC can be implemented

**Output:** If pending approval: confirmation with ticket ID and SLA; After approval: cancellation confirmation with refund amount and timeline; If order cannot be cancelled: explanation and alternative (return/refund path)

**Failure Paths:**
- Order already shipped: redirect to return flow; do not cancel
- Order already cancelled (idempotency): return existing cancellation confirmation
- Approval denied: notify customer with reason; offer alternatives (keep order, return after delivery)
- `cancel_order_tool` failure after approval: retry with idempotency key; escalate if persistent; fulfillment notification failure: separate retry mechanism, do not block customer response
- High-value threshold config unavailable: fail safe → treat as high-value, require approval

**Audit Requirements:** Order value at time of cancellation request; threshold version applied; approval chain complete; cancellation execution result with timestamp; fulfillment notification status

**Evaluation Criteria:** Correct threshold determination (including edge cases at boundary); approval always triggered for high-value orders; no cancellation executed before approval; idempotency enforced; correct policy applied for refund terms; shipped order correctly redirected

**KPI Linkage:** Cancellation rate by order value tier; revenue impact of reviewed cancellations; refund processing speed; agent time per high-value cancellation review

---

### UC-06 — Account / Security Change

**Actor:** Customer (authenticated + identity re-verified)
**Trigger:** Customer requests a sensitive account modification: email address change, password reset via agent, MFA settings change, billing/shipping address change post-shipment, security question update
**Preconditions:** Customer is authenticated; identity re-verification mechanism is operational [mechanism is undefined — see Issue 003]; account change policy exists in KB; human approval workflow operational
**Inputs:** `customer_id` (required), `conversation_id`, `change_type` (email / address / mfa / security), `new_value` (masked), `verification_evidence`, `timestamp`

**Decision Logic:**
1. Intent: account/security change
2. Identify change type; classify risk level (email > mfa > address)
3. Initiate identity re-verification appropriate to change type [method undefined — must be specified per change type]
4. If re-verification fails: hard refuse; log security event with customer_id and IP; after N failures notify security team and consider temporary account lock
5. If re-verification passes: retrieve account change policy via RAG
6. Build approval request for human review
7. Submit to human approval queue (all account security changes require approval — FR-013)
8. Notify customer of pending review
9. After approval: execute `account_change_tool`
10. Send confirmation to the ORIGINAL contact method (never to the new email, to prevent account takeover)

**Retrieval Requirements:** Account security policy documents; identity verification requirements per change type

**Tool Requirements:**
- `verify_identity_tool`: [UNDEFINED METHOD]; output: {verified: bool, method, timestamp}; risk: HIGH; logs: method and outcome only, never credentials
- `get_customer_tool`: {customer_id} → current account state; risk: LOW; authorization: customer session
- `create_approval_request_tool`: {request_type: "account_security_change", change_type, customer_id, verification_method, verification_timestamp}; risk: MEDIUM; audit: full
- `account_change_tool`: {approval_token, customer_id, change_type, new_value}; risk: CRITICAL (security-sensitive write); requires: valid approval token + identity verification token; audit: mandatory; idempotency key: `customer_id + change_type + request_id`
- `notify_customer_tool`: must target original contact method, not new value

**Approval Requirements:**
- All account security changes require human approval
- Approver must confirm identity verification evidence is present
- Approver role: `support_supervisor` or above (higher than standard refund approvals)

**Output:** Pending verification confirmation; after verification: pending approval notification; after approval: change confirmation via original channel

**Failure Paths:**
- Identity verification fails: hard refuse; security event logged; N consecutive failures trigger account security flag
- Suspicious pattern (multiple change attempts across session or IP): escalate to security team immediately
- Approval denied: maintain current account state; notify customer; log reason
- `account_change_tool` failure: retry with idempotency; if persistent: escalate; original state preserved (fail-safe: no partial change)
- Original channel notification failure: block execution until notification can be delivered (notification is a prerequisite for UC-06 execution)

**Audit Requirements:** Identity verification method and outcome; change type; old and new values (both masked); approval chain complete with timestamps; execution result; original channel notification confirmation; security events

**Evaluation Criteria:** Identity verification always completed before approval request; approval always required; original channel notification always sent before considering change complete; no account takeover path through adversarial inputs; correct high-risk routing (supervisor-level approval)

**KPI Linkage:** Account security incident rate; account takeover fraud rate; customer friction for legitimate changes (legitimate change success rate and time-to-complete)

---

### UC-07 — Product Troubleshooting

**Actor:** Customer (authenticated or anonymous)
**Trigger:** Customer reports a product issue or asks how to use a feature (e.g., "My device won't turn on", "How do I configure the Wi-Fi on the router?", "The item I received is damaged")
**Preconditions:** Product troubleshooting guides exist in KB; product information accessible; clarification workflow operational
**Inputs:** `customer_id` (optional), `conversation_id`, `message`, `product_id` (optional, extractable), `timestamp`

**Decision Logic:**
1. Intent: product troubleshooting
2. Extract product identifier from message (NER, explicit mention, or context)
3. If product unclear after extraction attempt: ask one specific clarification question (e.g., "Which product are you having trouble with — can you share the model name or order number?")
4. Retrieve product troubleshooting guides via hybrid search using symptom description + product filter
5. If additional diagnostic information needed (error codes, symptoms): ask targeted clarification (maximum 2 clarification turns before escalation)
6. Present troubleshooting steps grounded in KB, numbered, one stage at a time
7. If steps do not resolve: offer next escalation options (human agent, warranty claim, return)
8. If product defect or damage suspected: offer return/refund path (UC-03/UC-04) or warranty process
9. Do NOT generate troubleshooting steps that are not grounded in retrieved KB content

**Retrieval Requirements:** Product-specific troubleshooting guides; product documentation (specs, compatibility); known issues and resolutions; hybrid retrieval: symptom-based semantic search + product category filter; chunk metadata must include product scope

**Tool Requirements:**
- `get_product_tool` (if product_id known): {product_id} → {name, category, warranty_period, known_issues_flag}; risk: LOW; public product data
- `create_ticket_tool` (if unresolved): {customer_id, conversation_id, category: "troubleshooting", product_id, summary}; risk: LOW

**Approval Requirements:** None for troubleshooting guidance; return/warranty flows handled by UC-03/UC-04

**Output:** Grounded troubleshooting steps with source attribution; targeted clarification questions when needed; escalation path if unresolved; ticket reference if created

**Failure Paths:**
- Product not found in KB: acknowledge gap; escalate to human; flag KB gap for improvement
- No troubleshooting guide for reported symptom: acknowledge; create ticket for human follow-up; do not fabricate steps
- Issue too complex after 2 clarification turns: escalate to human with all symptoms captured
- LLM generates ungrounded or potentially dangerous instructions: guardrail must intercept; substitute with "I need to connect you with a specialist"

**Audit Requirements:** Product accessed; KB documents retrieved and scored; clarification questions asked; resolution outcome (resolved / escalated / ticket created); symptom description captured

**Evaluation Criteria:** Correct product identification; groundedness of troubleshooting steps (every step traceable to retrieved document); no fabricated technical instructions; appropriate clarification questions (specific, not generic); escalation triggered after maximum clarification turns; safety check on generated instructions

**KPI Linkage:** FCR for troubleshooting; CSAT for troubleshooting interactions; KB coverage rate; escalation rate; product return rate reduction attributable to successful troubleshooting

---

### UC-08 — Ambiguous Request

**Actor:** Customer (authenticated or anonymous)
**Trigger:** Intent classifier returns confidence below threshold, or multiple intents score within a defined confidence band of each other (e.g., "cancel" could be cancel-order or cancel-account)
**Preconditions:** Intent classification operational; clarification workflow supported; conversation context maintained
**Inputs:** `customer_id` (optional), `conversation_id`, `message`, `timestamp`

**Decision Logic:**
1. Intent classification returns: confidence < threshold, OR top-2 intents within [confidence_gap] of each other
2. Identify the specific ambiguity dimension (not generic): "Are you asking about returning an item for a refund, or do you want to cancel an upcoming order?"
3. Present concrete options rather than open-ended "can you clarify?" questions
4. Store `pending_context` with conversation state and ambiguous message
5. On customer response: resolve to single intent; route to appropriate flow
6. If second response also ambiguous: offer a second clarification or present structured options (numbered list)
7. After maximum clarification turns (to be defined, suggest: 2): escalate to human with full context
8. Do NOT proceed to tool calls or sensitive actions while intent is unresolved

**Retrieval Requirements:** None during clarification phase; full retrieval after disambiguation

**Tool Requirements:** None during clarification phase; post-disambiguation tools determined by resolved intent

**Approval Requirements:** Determined by resolved intent; no approval triggered before intent is resolved

**Output:** Single, specific clarification question with concrete options; on resolution: confirmation of understood intent before proceeding

**Failure Paths:**
- Customer continues to give ambiguous responses after 2 attempts: escalate to human with full conversation
- Customer is in an escalating emotional state: prioritize escalation over clarification
- System cannot formulate a specific clarification question: escalate rather than ask generic question

**Audit Requirements:** Original ambiguous message; confidence scores for top intents; clarification question(s) asked; customer response(s); final resolved intent (or escalation reason)

**Evaluation Criteria:** Ambiguity detection accuracy (true positive rate on ambiguous test cases; false positive rate on clear test cases); specificity of clarification questions (human-scored); one-turn resolution rate; no incorrect routing after successful disambiguation; escalation triggered at correct turn limit

**KPI Linkage:** First-message resolution rate; AHT for ambiguous interactions; escalation rate from ambiguity

---

### UC-09 — Unanswerable Request

**Actor:** Customer (authenticated or anonymous)
**Trigger:** Customer asks a question the system cannot answer: out of supported scope, in-scope but KB gap, requires unavailable data, or exceeds agent authorization
**Preconditions:** Intent has been attempted and failed resolution; retrieval has been attempted where applicable
**Inputs:** `customer_id` (optional), `conversation_id`, `message`, `timestamp`

**Decision Logic:**
1. Intent is identified but resolution fails (or intent confidence too low for any known intent)
2. Classify unanswerability reason:
   - Out of scope: topic is not a supported customer support topic
   - KB gap: topic is in scope but no relevant documents retrieved (score below threshold)
   - Unauthorized: requires customer-specific data but customer is not authenticated or data is unavailable
   - Policy requires human judgment: the question requires case-by-case evaluation
3. Do NOT fabricate an answer; do NOT hallucinate policy
4. Generate honest, professional explanation of limitation (without exposing system architecture or prompts)
5. Offer specific alternatives: human escalation, ticket creation, link to self-service resources (if available)
6. If KB gap: internally flag the unresolved query for KB improvement workflow

**Retrieval Requirements:** Retrieval was attempted and returned insufficient results (below confidence threshold)

**Tool Requirements:**
- `create_ticket_tool` (optional): to track unanswerable request for KB improvement analysis; risk: LOW
- Internal: `flag_kb_gap` (internal event, not a customer-facing tool)

**Approval Requirements:** None

**Output:** Honest explanation of limitation appropriate to reason; specific alternatives offered; ticket reference if created

**Failure Paths:**
- System hallucinates instead of abstaining: critical guardrail failure — groundedness check must catch this
- System enters clarification loop on an unanswerable question: cap at 2 clarification turns, then abstain
- Escalation unavailable when offered: acknowledge and provide alternative contact method

**Audit Requirements:** Unanswerability reason classified; retrieval results (or absence); KB gap flag raised; alternative options offered; customer response to alternatives

**Evaluation Criteria:** Abstention rate on test cases with no KB support (must be high); hallucination rate on unanswerable queries (must be zero); correct unanswerability reason classification; appropriate alternative offered; no system internals exposed in response

**KPI Linkage:** KB coverage rate (derived from unanswerable query volume and reasons); escalation rate; customer satisfaction on unresolved interactions; KB improvement velocity

---

### UC-10 — Adversarial Request

**Actor:** Adversarial user (authenticated session may be legitimate, stolen, or fake)
**Trigger:** Input contains prompt injection patterns, jailbreak attempts, policy bypass instructions, social engineering, or requests designed to circumvent agent constraints
**Preconditions:** Guardrail system operational; multi-layer detection active (not LLM-only per FR-016); security event logging operational
**Inputs:** `customer_id` (may be stolen), `conversation_id`, `message` (adversarial content), `timestamp`

**Decision Logic:**
1. Input passes through Layer 1: rule-based filter (regex/keyword patterns for known injection signatures: "ignore previous instructions", "pretend you are", "for testing purposes", "as an administrator", "system:", etc.)
2. If Layer 1 triggers: immediate safe refusal; no tool calls; log security event
3. If Layer 1 passes: input proceeds to Layer 2: structural validation (is the message asking for something within the tool permission model?)
4. Layer 3: LLM safety classifier (secondary check, not the only check) — classifies adversarial intent
5. If any layer triggers: safe refusal; do not reveal which layer triggered; do not reveal system prompt; do not engage with the premise of the adversarial request
6. Log: classification reason, all layers that triggered, customer/session info, full message
7. If N adversarial attempts from same session: flag account, rate limit, consider session termination
8. False positive path: if a legitimate customer is incorrectly blocked, provide human escalation path

**Retrieval Requirements:** None; adversarial requests do not proceed to retrieval

**Tool Requirements:**
- No tools executed for confirmed adversarial inputs
- `log_security_event` (internal): {event_type, customer_id, session_id, message_hash, detection_layer, timestamp}; risk: INTERNAL; must not log raw adversarial content in detail to prevent poisoning log analysis systems

**Approval Requirements:** None; immediate refusal

**Output:** Safe, professional refusal: "I can help you with questions about your orders, returns, and account. Is there something specific I can help you with today?" — no apology, no engagement with adversarial premise, no system details

**Failure Paths:**
- Guardrail bypass (adversarial succeeds): security incident; tool calls executed must be idempotent and logged; post-incident review required
- False positive (legitimate customer blocked): human escalation path must always be available; false positive events logged for guardrail calibration
- Repeated adversarial attempts: progressive response (first: polite redirect; second: firm redirect; third: session flag + human escalation)

**Audit Requirements:** Detection layer that triggered; adversarial pattern type; customer/session info; message hash (not full content to prevent log poisoning); security event type; subsequent session actions; false positive flags

**Evaluation Criteria:** Adversarial detection rate against labeled adversarial test dataset; false positive rate against legitimate request test set (must be < defined threshold); no tool execution on adversarial inputs; no system prompt leakage in any refusal response; consistent refusal regardless of framing (jailbreaks that vary prompt structure must all be caught)

**KPI Linkage:** Security incident rate; fraud prevention rate; false positive rate (customer experience impact of over-blocking); guardrail calibration quality

---

### UC-11 — Human Escalation

**Actor:** Customer (authenticated); Human Support Agent
**Trigger:** Agent determines escalation is necessary (cannot safely resolve, safety condition, information unavailable, policy requires escalation) OR customer explicitly requests a human agent
**Preconditions:** Human support queue operational; ticket system operational; context serialization mechanism available; human agent notification mechanism defined
**Inputs:** `customer_id`, `conversation_id`, `escalation_trigger` (agent-determined or customer-requested), `timestamp`

**Decision Logic:**
1. Determine escalation trigger (one of the conditions in Section 23)
2. Compile escalation package:
   - Full conversation history (all turns)
   - Retrieved KB documents with relevance scores
   - All tool calls and results (with PII handling — masking applied)
   - Attempted actions and failure reasons
   - Agent's natural-language assessment of the issue
   - Relevant customer data snapshot (from last tool call, not re-queried)
   - Classification: issue type, priority (from ML-001), sentiment
3. Create escalation ticket with the full context package attached
4. Route to appropriate agent queue based on issue category and priority
5. Notify customer: "You're being connected to a support specialist. Your reference number is [ticket_id]. Estimated wait: [queue_estimate]."
6. Human agent receives context package — must be able to continue without re-asking questions already answered
7. After human resolution: record outcome, resolution type, resolution notes; close ticket; trigger CSAT survey
8. If issue would have been resolvable by agent: flag for improvement analysis

**Retrieval Requirements:** None at escalation time (context already gathered); KB context from prior retrieval preserved in escalation package

**Tool Requirements:**
- `create_ticket_tool`: {customer_id, conversation_id, escalation_reason, priority, category, context_package}; risk: LOW; audit: creation, assignment, resolution
- `notify_customer_tool`: {customer_id, ticket_id, message, estimated_wait}; risk: LOW
- `assign_to_queue_tool`: {ticket_id, queue_id, priority}; risk: LOW; routing logic driven by category + priority

**Approval Requirements:** None for escalation itself; if prior approval was pending, include in escalation package

**Output:** Customer: escalation confirmation with ticket ID and estimated wait; Human agent: full context package in agent interface

**Failure Paths:**
- Human queue unavailable: notify customer of delay; set expectations; provide callback reference; do not silently fail
- Context serialization failure: escalate with partial context; flag for review; do not block escalation on serialization failure
- Ticket system unavailable: retry with exponential backoff; provide customer with fallback contact (email/phone) if ticket creation fails after retries
- Queue routing failure: default to general queue rather than failing

**Audit Requirements:** Escalation trigger reason; context package contents (document list, not full text); queue routing decision; human agent assignment; time to first human response; resolution outcome; CSAT result

**Evaluation Criteria:** Context completeness in escalation package (all required fields present); correct queue routing (category match); customer notification timeliness (< N seconds after trigger); human agent able to continue without re-asking already-answered questions (human evaluation); escalation trigger correctly classified

**KPI Linkage:** Escalation rate (overall and by intent type); AHT for escalated interactions; CSAT for escalated interactions; first escalation resolution rate; cost per escalated interaction vs. automated interaction

---

### UC-12 — Ticket Creation

**Actor:** Agent (automated trigger); Customer (explicit request); Human Agent (manual creation)
**Trigger:** Automatic resolution fails; human escalation occurs; policy requires tracking; customer explicitly requests a ticket; long-running action is deferred; audit trail is required for a policy-sensitive action
**Preconditions:** Ticket database (PostgreSQL) operational; ML classification models operational (ML-001); agent caller is authorized to create tickets
**Inputs:** `customer_id`, `conversation_id`, `ticket_type` (auto-classified or specified), `priority_override` (optional), `issue_description` (extracted or provided), `linked_order_id` (optional), `linked_product_id` (optional), `timestamp`

**Decision Logic:**
1. Determine ticket creation trigger and creator identity (agent / customer request / human agent)
2. Check idempotency: if ticket already exists for `conversation_id` + `ticket_type`, return existing ticket ID
3. Extract ticket metadata:
   - Category: ML classifier (ML-001) from conversation context; fallback: "general"
   - Priority: ML classifier (ML-001); fallback: "medium"
   - Sentiment: ML classifier (ML-001); fallback: "neutral"
   - Escalation prediction: ML classifier (ML-001)
4. Generate ticket summary from conversation context (LLM-generated, bounded length)
5. Attach artifacts: conversation history reference, retrieved KB document IDs, tool call results (PII masked), approval status (if applicable)
6. Record ML model version used for each classification field (ML-003)
7. Create ticket record in PostgreSQL
8. Apply routing rules: by category, priority, agent availability
9. Confirm ticket creation to customer with ticket ID and expected SLA [SLA must be defined]
10. Emit ticket creation event for async observability pipeline

**Retrieval Requirements:** None for ticket creation; prior retrieval context attached as artifact reference

**Tool Requirements:**
- `create_ticket_tool`: {customer_id, conversation_id, category, priority, sentiment, escalation_flag, summary, artifact_refs[], linked_order_id, linked_product_id, creator_type, ml_model_versions{}}; risk: LOW; idempotency key: `conversation_id + ticket_type`; audit: creation timestamp, creator identity, ML versions used

**Approval Requirements:** None for standard ticket creation; high-priority tickets may trigger supervisor notification (policy-defined)

**Output:** Ticket ID; creation confirmation to customer with expected resolution SLA; routing assignment; ticket reference for all subsequent interactions

**Failure Paths:**
- Database unavailable: retry with exponential backoff; if persistent, log to durable fallback store; do not lose ticket data
- ML classification fails: fallback to category="general", priority="medium"; flag ticket for manual review; do not block ticket creation on ML failure
- Duplicate request (same conversation): idempotency check returns existing ticket ID without creating duplicate
- Ticket creation fails after retries: log error with full context; notify customer of follow-up via alternate channel; never silently drop

**Audit Requirements:** Ticket ID; creation timestamp; creator identity (agent/customer/human-agent); category and priority with ML model ID and version; conversation artifacts attached (by reference, not by copy); agent assignment; all subsequent state changes (status updates, reassignments, resolution)

**Evaluation Criteria:** Category classification accuracy vs. labeled test set (ML-002 metrics); priority prediction accuracy; duplicate prevention (idempotency enforced across all creation paths); artifact attachment completeness; correct routing; ML model version recorded; resolution SLA tracked

**KPI Linkage:** Ticket volume and distribution by category and priority; ML classification accuracy in production vs. held-out evaluation set; resolution time by category and priority; cost per ticket; KB gap identification rate from ticket analysis; drift in classification distribution (ML-004)

---

## Part 4 — Architecture Readiness Assessment

### What Can Begin Now

The following components have sufficient specification to begin architecture design:

| Component | Basis |
|---|---|
| API layer design (request/response schema) | FR-001, FR-002, INT-001 |
| Intent classification pipeline | FR-003, ML-001, ML-002 |
| PostgreSQL schema (customers, orders, products, tickets, conversations) | Section 18, Section 16 |
| Tool permission framework skeleton | FR-014, FR-015 |
| Basic RAG pipeline (retrieval, reranking, chunking) | FR-004, Section 17 |
| Observability schema (interaction traces) | OBS-001, OBS-002 |
| Evaluation framework structure | EVAL-001 through EVAL-006 |
| Classical ML pipeline (classification, versioning) | ML-001 through ML-004 |
| Audit record schema | Section 24 |
| Security controls: auth, authorization, secret management | SEC-001 through SEC-007 |

### What Cannot Begin Without Gap Resolution

| Component | Blocking Gap | Issue # |
|---|---|---|
| Human approval workflow | Approval SLA and timeout action undefined | 002 |
| High-value cancellation (UC-05) | Dollar threshold undefined | 001 |
| Account security change (UC-06) | Identity re-verification method undefined | 003 |
| LLM serving architecture | Dev vs. production Ollama strategy undefined | 006 |
| RAG pipeline embedding layer | Embedding model not selected | 010 |
| Async job infrastructure | Message broker technology not specified | 009 |
| Guardrail implementation | Non-LLM layer not specified | 015 |
| CI/CD evaluation gates | Quality gate thresholds undefined | 005 |
| Deployment architecture | Cloud provider deferred | 025 |
| Continuous improvement loop | Feedback capture mechanism undefined | 024 |
| SLO-based alerting | No SLO targets defined | 004 |

### Summary Verdict

**Architecture readiness: Partial — approximately 60% of required decisions are specifiable today.**

The document demonstrates Principal-level thinking on structure, traceability, and evaluation first-class status. The core functional, observability, and ML requirements are well-scoped. The critical gaps are concentrated in three areas:

1. **Human approval workflow mechanics** (SLA, timeout, state machine) — blocks UC-04, UC-05, UC-06
2. **Security-sensitive UCs** (identity re-verification for account changes) — blocks the highest-risk flow
3. **Infrastructure decisions** (LLM serving, embedding model, message broker) — block all components that depend on them

Resolving Issues 001 through 006 (all marked Critical) unblocks approximately 80% of the architecture. The remaining High and Medium issues should be resolved in a second pass before implementation begins but do not block the initial architecture design.

---

*Review complete. No modifications were made to `requirements.md`. All findings are documented above for discussion and resolution before architecture design proceeds.*
