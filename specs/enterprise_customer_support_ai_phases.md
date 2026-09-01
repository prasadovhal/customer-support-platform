# Enterprise Customer Support AI/ML Platform

## Overall journey

```text
Business Problem
      ↓
Data Strategy
      ↓
Requirements
      ↓
System Architecture
      ↓
Data Engineering
      ↓
Classical ML
      ↓
RAG
      ↓
Agent + Skills
      ↓
Workflow Orchestration
      ↓
Enterprise Integrations
      ↓
Evaluation
      ↓
Guardrails + Security
      ↓
Observability
      ↓
Reliability
      ↓
Docker
      ↓
CI/CD
      ↓
Cloud Deployment
      ↓
Production Monitoring
      ↓
Experimentation
      ↓
Continuous Improvement
      ↓
Business Impact
```

We'll use **open-source/self-hostable tools wherever practical**, and we'll make technology choices based on requirements rather than forcing a particular framework.

---

# PHASE 0 — Project Definition

### Objective

Define exactly what we're building and why.

### Business

**Acme Store** is a fictional e-commerce company with:

- customers
- products
- orders
- support tickets
- support agents
- knowledge base
- CRM/order/payment systems

### Core problem

Acme wants to improve:

- support efficiency
- customer experience
- resolution rate
- consistency
- scalability

without compromising:

- correctness
- security
- reliability
- safety

### AI/ML opportunity

```text
Customer Support
       │
 ┌─────┼──────────────┐
 ▼     ▼              ▼
ML    GenAI       Automation
 │      │              │
 │      ├── RAG        ├── Tools
 │      ├── Agents     ├── Workflows
 │      └── Skills     └── Actions
 │
 ├── Classification
 ├── Priority
 └── Routing
```

### Deliverables

- Problem statement
- Project charter
- Scope
- Goals
- Non-goals
- Assumptions
- Success criteria

---

# PHASE 1 — Customer & Business Discovery

Before architecture, understand the business.

### Stakeholders

**Customers**

Want:

- fast answers
- correct answers
- easy resolution

**Support agents**

Want:

- customer context
- order information
- relevant knowledge
- suggested responses
- automation

**Support managers**

Want:

- lower AHT
- higher FCR
- SLA compliance
- quality

**Business leadership**

Want:

- lower cost
- higher CSAT
- scalable support
- measurable ROI

**Engineering**

Want:

- secure
- reliable
- maintainable
- observable systems

**Data Science / AI**

Want:

- measurable model performance
- experimentation
- evaluation
- feedback loops

### Current workflow

```text
Customer
 ↓
Support channel
 ↓
Human agent
 ├── Find customer
 ├── Find order
 ├── Search KB
 ├── Check policy
 ├── Resolve
 └── Escalate if necessary
```

### Deliverables

- Customer personas
- Stakeholder map
- Current-state workflow
- Pain-point analysis
- Future-state workflow
- Business requirements

---

# PHASE 2 — Data Strategy

This is already defined substantially.

We'll create:

| Dataset | Initial size | Format |
|---|---:|---|
| Knowledge articles | ~100 | Markdown |
| FAQ questions | ~300 | JSONL |
| Golden QA | ~200 | JSONL |
| Customers | 1,000 | CSV + PostgreSQL |
| Products | 100 | CSV + PostgreSQL |
| Orders | 5,000 | CSV + PostgreSQL |
| Support tickets | 1,000 | CSV + PostgreSQL |
| Conversations | 300 | JSONL + PostgreSQL |

### Knowledge base

```text
shipping/
returns/
refunds/
payments/
products/
account/
troubleshooting/
orders/
warranty/
security/
```

We'll deliberately include:

- overlapping documents
- exceptions
- temporal versions
- product-specific rules
- customer-segment rules
- ambiguous information
- irrelevant information

This makes retrieval genuinely challenging.

### Data provenance

Every document has:

```text
document_id
source
source_type
source_url
license
version
effective_from
effective_to
```

### Synthetic enterprise data

Customers → Orders → Products → Tickets → Conversations must remain relationally consistent.

### Data quality

Validate:

- IDs
- foreign keys
- dates
- business rules
- nulls
- distributions
- duplicate records

### Data Cards

For every major dataset:

- purpose
- source
- generation method
- schema
- assumptions
- limitations
- biases
- intended use
- version
- generation seed

### Deliverables

```text
data/
├── raw/
├── processed/
├── structured/
├── database/
├── evaluation/
├── data_cards/
└── schemas/
```

---

# PHASE 3 — Requirements Engineering

Now translate business needs into technical requirements.

## Functional requirements

The system should:

- receive support requests
- identify intent
- retrieve relevant knowledge
- retrieve customer information
- retrieve order information
- generate responses
- create tickets
- perform approved actions
- escalate to humans
- record actions
- process asynchronous events

## Non-functional requirements

Define:

- latency
- availability
- scalability
- reliability
- security
- maintainability
- observability
- cost

## AI requirements

Define:

- retrieval quality
- answer correctness
- hallucination tolerance
- tool accuracy
- agent success
- escalation accuracy

## Safety requirements

High-risk operations require:

```text
Agent
 ↓
Policy check
 ↓
Authorization
 ↓
Human approval
 ↓
Execution
```

### Deliverable

`docs/requirements.md`

---

# PHASE 4 — System Architecture

Now we design the complete system.

Initial conceptual architecture:

```text
                       CUSTOMER
                           │
                           ▼
                    ┌─────────────┐
                    │ Support API │
                    └──────┬──────┘
                           │
                           ▼
                   ┌───────────────┐
                   │ Intelligence  │
                   │     Layer     │
                   └───────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
             ML           RAG         Agent
              │            │            │
              │            │         Skills
              │            │         Tools
              │            │       Workflows
              └────────────┼────────────┘
                           ▼
                       Decision
                           │
                    ┌──────┴──────┐
                    ▼             ▼
               Automation      Human
                              approval
                    │             │
                    └──────┬──────┘
                           ▼
                        Outcome
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
          Evaluation   Observability  Analytics
```

We'll design:

- component architecture
- data flow
- API boundaries
- trust boundaries
- failure boundaries
- synchronous vs asynchronous paths
- security boundaries

### Deliverables

- Architecture diagram
- Data-flow diagram
- Sequence diagrams
- Deployment architecture
- Threat model

---

# PHASE 5 — Architecture Decision Records

Every meaningful decision gets an ADR.

Examples:

```text
ADR-001 PostgreSQL
ADR-002 Vector database
ADR-003 Hybrid retrieval
ADR-004 Reranking
ADR-005 LangGraph
ADR-006 Skills architecture
ADR-007 Async processing
ADR-008 OAuth
ADR-009 Webhooks
ADR-010 Observability
ADR-011 Deployment
```

Each ADR:

```text
Problem
 ↓
Options
 ↓
Evaluation criteria
 ↓
Decision
 ↓
Trade-offs
 ↓
Consequences
```

This becomes excellent material for system-design interviews.

---

# PHASE 6 — Backend Foundation

Build the API layer.

We'll use **FastAPI** initially.

Examples:

```text
POST /api/v1/conversations
POST /api/v1/messages

GET /api/v1/customers/{id}
GET /api/v1/orders/{id}

POST /api/v1/tickets
GET /api/v1/tickets/{id}

GET /health
GET /ready
```

Learn/practice:

- REST
- HTTP
- Pydantic
- dependency injection
- validation
- error handling
- middleware
- API versioning
- authentication boundaries
- request IDs

### Deliverable

A clean, tested backend service.

---

# PHASE 7 — Database & Data Layer

Use PostgreSQL as the transactional system.

Tables:

```text
customers
products
orders
support_tickets
conversations
conversation_messages
agent_executions
tool_calls
```

Learn:

- schema design
- relationships
- indexes
- constraints
- transactions
- migrations
- connection pooling

We'll keep the vector store conceptually separate.

---

# PHASE 8 — Classical ML

This is important for your **Principal DS identity**.

Build models for:

### Intent classification

```text
Ticket → Intent
```

### Category classification

```text
Ticket → Category
```

### Priority prediction

```text
Ticket → P0/P1/P2/P3
```

### Routing

```text
Ticket → Support Team
```

### Escalation prediction

```text
Ticket → P(escalation)
```

Start with appropriate baselines:

```text
Rules
 ↓
Logistic Regression
 ↓
Tree-based model
```

Evaluate with:

- precision
- recall
- F1
- macro F1
- confusion matrix
- calibration
- class-specific metrics

For priority, pay particular attention to P0/P1 recall.

---

# PHASE 9 — RAG Knowledge Pipeline

Now we use the ~100 articles.

Pipeline:

```text
Markdown
 ↓
Parse
 ↓
Metadata
 ↓
Chunk
 ↓
Embed
 ↓
Index
 ↓
Retrieve
```

We'll experiment with:

### Baseline

Keyword/BM25.

### Dense

Embedding-based retrieval.

### Hybrid

```text
BM25
 +
Dense
```

### Reranking

```text
Hybrid
 ↓
Top 20
 ↓
Cross Encoder
 ↓
Top 5
```

We won't assume one approach is best.

We'll **measure it**.

---

# PHASE 10 — RAG Evaluation

Use the ~200 golden QA dataset.

Measure:

### Retrieval

- Recall@K
- Precision@K
- MRR
- NDCG

### Context

- relevance
- precision
- recall

### Generation

- correctness
- completeness
- faithfulness
- groundedness

### Regression

Every change should be evaluated against the golden set.

Eventually:

```text
Git commit
 ↓
Evaluation
 ↓
Metrics
 ↓
Threshold
 ├── PASS → continue
 └── FAIL → block
```

This becomes an **evaluation gate** in CI/CD.

---

# PHASE 11 — Agent Architecture

Now we finally build the agent.

The agent will not be a giant prompt.

It will use:

```text
Agent
 ├── Skills
 ├── Tools
 ├── Memory
 ├── Policies
 ├── Workflow
 └── Guardrails
```

Example request:

> "My package hasn't arrived. Can I get a refund?"

Agent:

```text
Intent
 ↓
Skill
 ↓
Order lookup
 ↓
Policy retrieval
 ↓
Eligibility
 ↓
Decision
 ↓
Response/action
```

---

# PHASE 12 — Agent Skills

Now we create the skills you asked about earlier.

Potential skills:

```text
skills/
├── knowledge_search/
├── order_status/
├── return_eligibility/
├── refund/
├── troubleshooting/
├── ticket_management/
├── customer_lookup/
└── escalation/
```

Each skill defines:

```text
Purpose
Inputs
Outputs
Tools
Preconditions
Guardrails
Failure handling
Evaluation
```

Important distinction:

```text
Tool
= capability

Skill
= reusable capability + instructions + rules

Agent
= decides when/how to use capabilities
```

---

# PHASE 13 — Structured Outputs

Agent decisions should become machine-readable.

For example:

```text
AgentDecision
├── intent
├── confidence
├── action
├── requires_human
├── reasoning_metadata
└── tool_request
```

Use:

- Pydantic
- JSON Schema
- validation
- retry on invalid output

The LLM should not directly control critical business operations.

---

# PHASE 14 — Workflow Orchestration

Use a workflow/state-machine approach.

Example:

```text
Request
 ↓
Classify
 ↓
Retrieve
 ↓
Reason
 ↓
Tool
 ↓
Policy check
 ↓
Human approval?
 ├── No → Execute
 └── Yes → Approval → Execute
 ↓
Respond
```

We'll handle:

- branching
- retries
- state
- checkpoints
- failures
- human-in-the-loop
- timeouts

This is where **LangGraph** can be evaluated against alternatives rather than assumed automatically.

---

# PHASE 15 — Enterprise Tools & Integrations

Simulate enterprise systems.

Tools:

```text
get_customer()
get_order()
get_order_status()
get_tracking()
check_refund_policy()
create_ticket()
update_ticket()
issue_refund()
```

We'll create mock services first.

Later:

```text
Agent
 ↓
HTTP API
 ↓
External service
```

Learn:

- API contracts
- authentication
- timeouts
- retries
- rate limits
- error handling
- schema validation

---

# PHASE 16 — OAuth & Security

Implement enterprise authentication.

Understand:

```text
OAuth 2.0
JWT
Access tokens
Refresh tokens
Scopes
Roles
Service authentication
```

We'll distinguish:

```text
Customer authorization
Agent authorization
Service-to-service authorization
```

And enforce authorization **outside the LLM**.

---

# PHASE 17 — Webhooks & Event-Driven Architecture

Example:

```text
Order System
     │
     │ order.updated
     ▼
Webhook API
     │
     ▼
Validate signature
     │
     ▼
Check event ID
     │
     ▼
Process
```

Learn:

- webhook signatures
- event IDs
- retries
- duplicate delivery
- replay protection
- idempotency
- event ordering

Critical rule:

> Same event received twice must not cause the business action twice.

---

# PHASE 18 — Background Jobs

Move long-running work off the request path.

```text
API
 ↓
Queue
 ↓
Worker
 ↓
Task
```

Possible tasks:

- document ingestion
- embedding
- evaluation
- CRM synchronization
- email/notification
- long agent workflows

Learn:

- retries
- backoff
- task states
- failure handling
- idempotent workers
- dead-letter concepts

---

# PHASE 19 — Guardrails & Human-in-the-Loop

Define action risk levels.

### Low risk

```text
Search KB
Get order status
Get tracking
Create ticket
```

### Medium risk

```text
Update ticket
Cancel low-value order
```

### High risk

```text
Refund
Change account information
Override policy
Security changes
High-value cancellation
```

High-risk actions:

```text
Agent
 ↓
Policy
 ↓
Authorization
 ↓
Human approval
 ↓
Execution
```

The LLM should **never bypass these controls**.

---

# PHASE 20 — Observability

Instrument the entire system.

Trace:

```text
Request
 ↓
Agent
 ├── Retrieval
 │    └── DB
 ├── LLM
 ├── Skill
 └── Tool
      └── External API
```

Capture:

- latency
- errors
- tool calls
- retrieval
- token usage
- cost
- workflow state
- escalation
- outcomes

Use OpenTelemetry as the vendor-neutral instrumentation layer.

---

# PHASE 21 — AI Evaluation Platform

Now combine everything we've learned.

Evaluation layers:

```text
                    Evaluation
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
      ML              RAG              Agent
        │               │                │
     F1/AUC        Retrieval          Task success
                   Answer quality     Tool accuracy
                                      Policy compliance
```

Also measure:

- hallucination
- groundedness
- regression
- safety
- latency
- cost

And connect them to business metrics.

---

# PHASE 22 — Experimentation

This is a major Principal DS component.

Examples:

### Retrieval

```text
Dense
vs
BM25
vs
Hybrid
vs
Hybrid + reranker
```

### Agent

```text
RAG-only
vs
RAG + tools
vs
Agentic workflow
```

### ML

```text
Rules
vs
Logistic Regression
vs
Tree model
```

For every experiment:

```text
Hypothesis
 ↓
Methodology
 ↓
Dataset
 ↓
Baseline
 ↓
Experiment
 ↓
Metrics
 ↓
Statistical analysis
 ↓
Conclusion
 ↓
Decision
```

---

# PHASE 23 — Docker & Local Production Environment

Containerize:

```text
FastAPI
Worker
PostgreSQL
Redis
Vector DB
Observability
```

Run locally through:

```bash
docker compose up
```

We want a reproducible environment.

---

# PHASE 24 — Testing

Testing will happen at multiple levels.

### Unit

Individual functions.

### Integration

Database/API/tool integration.

### Workflow

Agent workflow.

### RAG

Retrieval and answer tests.

### Evaluation

Golden dataset.

### Reliability

Retries, failures, duplicate events.

### Security

Authentication/authorization.

### Load

Concurrent requests.

We'll deliberately **break the system** and verify recovery.

---

# PHASE 25 — CI/CD

GitHub:

```text
Developer
 ↓
Git push
 ↓
GitHub Actions
 ├── lint
 ├── type checks
 ├── unit tests
 ├── integration tests
 ├── evaluation
 ├── security checks
 └── Docker build
       ↓
     Deploy
```

Important:

**AI evaluation becomes part of CI/CD.**

A retrieval change that destroys quality should be able to fail the pipeline.

---

# PHASE 26 — Cloud Deployment

We'll deploy the complete system.

Target architecture:

```text
Internet
   ↓
HTTPS
   ↓
Application
   ├── API
   └── Worker
        │
        ├── PostgreSQL
        ├── Redis
        └── Vector DB
```

We'll learn:

- networking
- environment variables
- secrets
- containers
- databases
- TLS
- logging
- monitoring
- scaling

We will choose the actual cloud/provider later based on cost, open-source compatibility and availability.

---

# PHASE 27 — Production Reliability

Introduce realistic failures.

Examples:

```text
LLM unavailable
Database unavailable
Redis unavailable
CRM timeout
Webhook duplicated
Worker crashes
Invalid LLM output
Malformed tool arguments
Rate limit
Network timeout
```

Design:

- retries
- backoff
- timeouts
- circuit breakers where appropriate
- idempotency
- graceful degradation
- fallback
- alerting

---

# PHASE 28 — Cost & Performance Optimization

Measure:

```text
Latency
Throughput
CPU
Memory
LLM inference
Embedding
Database
Network
```

Optimize:

- caching
- retrieval
- model selection
- prompt size
- batching
- asynchronous processing
- database indexes

Then calculate:

> **Cost per support interaction**

---

# PHASE 29 — Production Monitoring & Drift

Monitor:

### Data drift

```text
Ticket distribution changes
Intent distribution changes
```

### Model drift

```text
Classification performance
Priority prediction
```

### RAG drift

```text
Retrieval quality
Knowledge changes
```

### Agent drift

```text
Tool usage
Escalation
Failure
```

### Business drift

```text
CSAT
FCR
AHT
Automation
```

---

# PHASE 30 — Feedback & Continuous Improvement

Create:

```text
Interaction
 ↓
Outcome
 ↓
Feedback
 ↓
Error analysis
 ↓
Dataset update
 ↓
Experiment
 ↓
Evaluation
 ↓
Deployment
```

This turns the project into a **continuous ML/AI lifecycle** rather than a one-time demo.

---

# PHASE 31 — Business Impact Analysis

Finally connect technical improvements to business outcomes.

Example:

```text
Hybrid retrieval
      ↓
Better context
      ↓
Better answers
      ↓
Higher resolution
      ↓
Higher FCR
      ↓
Lower AHT
      ↓
Lower cost
```

We'll quantify this where our synthetic data permits.

---

# PHASE 32 — Client/Stakeholder Delivery

Even though this isn't an FDE project, we should practice **technical delivery**.

Create:

```text
Customer Discovery
Requirements
Architecture
ADRs
Demo
Deployment Guide
Runbook
Rollout Plan
```

Create a 10–15 minute demo.

We should be able to explain:

> Problem → Architecture → AI → Evaluation → Reliability → Business impact.

---

# PHASE 33 — Portfolio & Principal DS Story

At the end, we should be able to honestly describe:

> **Architected and deployed an enterprise customer-support AI/ML platform combining classical ML, hybrid retrieval, reranking, agentic workflows, tool orchestration, automated evaluation, observability, guardrails, human-in-the-loop controls and production reliability mechanisms. Established experimental baselines and quality gates linking AI system performance to customer-support business KPIs.**

And importantly, **every word should be demonstrable in the repository**.

---

# The final repository

Something approximately like:

```text
enterprise-customer-support-ai/
│
├── app/
│   ├── api/
│   ├── agents/
│   ├── skills/
│   ├── tools/
│   ├── workflows/
│   ├── rag/
│   ├── ml/
│   ├── evaluation/
│   ├── integrations/
│   ├── workers/
│   ├── security/
│   ├── observability/
│   └── core/
│
├── data/
│
├── models/
│
├── tests/
│
├── experiments/
│
├── docs/
│   ├── requirements/
│   ├── architecture/
│   ├── adr/
│   ├── data/
│   ├── evaluation/
│   ├── deployment/
│   └── runbooks/
│
├── scripts/
│
├── docker/
│
├── .github/
│   └── workflows/
│
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── README.md
└── LICENSE
```

---

# How we'll work through it

We **will not execute these 33 phases blindly one after another**.

Some phases will overlap.

The practical progression will be:

```text
PHASE 0–5
Problem + Business + Data + Requirements + Architecture
             ↓
        "What are we building?"
             ↓
PHASE 6–8
Backend + Database + Classical ML
             ↓
        "Can the system understand?"
             ↓
PHASE 9–14
RAG + Evaluation + Agent + Skills + Workflows
             ↓
        "Can AI solve the problem?"
             ↓
PHASE 15–19
Tools + OAuth + Webhooks + Jobs + Guardrails
             ↓
        "Can it operate safely?"
             ↓
PHASE 20–24
Observability + Evaluation + Experiments + Docker + Testing
             ↓
        "Can we prove it works?"
             ↓
PHASE 25–30
CI/CD + Cloud + Reliability + Optimization + Monitoring
             ↓
        "Can we operate it?"
             ↓
PHASE 31–33
Business Impact + Delivery + Portfolio
             ↓
        "Can we demonstrate Principal-level impact?"
```

## One rule we'll follow throughout

Whenever we introduce a technology, we'll first ask:

> **What problem does this solve?**

Then:

> **What are the alternatives?**

Then:

> **How do we know our choice is better?**

Only then:

> **Implement it.**

That prevents this from becoming a "learn FastAPI + LangGraph + Docker + Redis" project.

It becomes an **end-to-end AI/ML systems project with measurable engineering and business decisions**.

### Our immediate next step

We've already completed the initial **problem/data framing**. So now we should begin **Phase 3: Requirements Engineering**, starting with the **Functional Requirements** and building the requirements document systematically.


---

# LLM Selection & Serving — Project Decision

The project will use **Ollama as the initial local LLM serving/runtime layer**.

Important distinction:

> **Ollama is the model serving/runtime layer, not the LLM itself.**

The actual open-weight model remains **TBD until benchmarking**.

Initial architecture:

```text
Our Application
      ↓
LLM abstraction
      ↓
Ollama
      ↓
Open-weight model
```

During experimentation, we will benchmark 2–3 suitable open-weight models rather than permanently locking the project to one model.

Candidate models will be selected based on compatibility with the available development hardware and the requirements of the application.

We will evaluate candidate models using:

- answer correctness
- tool-calling accuracy
- structured-output reliability
- RAG groundedness
- agent task success
- latency
- memory/VRAM requirements
- model license
- inference cost

For development:

> **Ollama + open-weight model**

For experiments:

> **Compare multiple open-weight models**

For production:

> **Choose based on measured quality, cost, latency, resource requirements, and operational constraints — not model popularity.**

This decision should eventually be documented as an ADR:

> **ADR — LLM Selection & Serving Architecture**

The final model should be selected only after benchmarking against our domain-specific evaluation suite.

This gives us a Principal-level engineering/DS decision:

> Benchmark candidate open-weight models against domain-specific evaluation criteria and select the model based on quality, tool reliability, latency, resource requirements, and cost.
