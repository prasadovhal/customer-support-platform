# Enterprise Customer Support AI/ML Platform — Technology Stack

## Technology selection philosophy

We will prioritize **open-source and self-hostable tools wherever practical**.

We will NOT select technologies simply because they are popular.

For every major technology, we will ask:

> What problem does this solve?

Then:

> What are the alternatives?

Then:

> How do we know our choice is better?

Only then:

> Implement it.

The project is designed to demonstrate **Principal Data Scientist / Principal Applied AI** capabilities, so technology choices should support:

- production AI systems
- rigorous evaluation
- ML experimentation
- reliability
- security
- observability
- deployment
- maintainability
- measurable business impact

---

# 1. Core stack

| Layer | Primary technology | Purpose |
|---|---|---|
| Language | Python | Main development language |
| Dependency management | Poetry | Reproducible Python environment |
| API | FastAPI | Backend/API layer |
| Validation | Pydantic | Request, response and structured-output validation |
| Database | PostgreSQL | Transactional/system-of-record data |
| Vector search | pgvector initially / final choice via ADR | RAG vector retrieval |
| Cache / queue broker | Redis | Caching and asynchronous messaging |
| Background jobs | Celery | Reliable asynchronous processing |
| Agent/workflow | LangGraph | Stateful agent/workflow orchestration; evaluated against alternatives |
| RAG | Custom pipeline + selected open-source libraries | Retrieval architecture and experimentation |
| Embeddings | Sentence Transformers / open-source embedding model | Semantic representations |
| Sparse retrieval | BM25 | Lexical retrieval baseline |
| Reranking | Open-source cross-encoder | Improve top-K retrieval quality |
| ML | scikit-learn initially | Classical ML baselines |
| ML advanced models | Appropriate open-source model libraries as needed | Improved classification/prioritization |
| HTTP client | httpx | External API integrations |
| Authentication | OAuth 2.0 + JWT | Enterprise authentication/authorization |
| API schema | OpenAPI via FastAPI | API contract |
| Observability | OpenTelemetry | Vendor-neutral tracing/metrics |
| Testing | pytest | Automated tests |
| HTTP/integration tests | pytest + httpx | API and integration testing |
| Containers | Docker | Reproducible packaging |
| Local orchestration | Docker Compose | Multi-service local environment |
| CI/CD | GitHub Actions | Automated testing/build/deployment |
| Infrastructure as code | OpenTofu/Terraform, decision via ADR | Reproducible infrastructure |
| Documentation | Markdown | Requirements, ADRs, architecture, runbooks |
| Diagrams | Mermaid initially | Architecture and sequence diagrams |
| Version control | Git + GitHub | Source control and collaboration |

---

# 2. Python

Use:

> Python

Reason:

- existing user expertise
- strong ML ecosystem
- strong AI/LLM ecosystem
- strong backend ecosystem
- good testing support

Python will be used for:

- API
- ML
- RAG
- agents
- workflows
- evaluation
- data generation
- background workers
- integration services

---

# 3. Dependency management

Use:

> Poetry

Reasons:

- reproducible dependency management
- lock file
- clear project metadata
- suitable for Python application development

Primary files:

```text
pyproject.toml
poetry.lock
```

We should avoid uncontrolled `pip install` workflows.

---

# 4. Backend — FastAPI

Use:

> FastAPI

Responsibilities:

```text
Client
  ↓
FastAPI
  ├── authentication
  ├── validation
  ├── conversations
  ├── tickets
  ├── customers
  ├── orders
  ├── webhooks
  └── health/readiness
```

Example APIs:

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

---

# 5. Data validation — Pydantic

Use:

> Pydantic

For:

- API request validation
- API response models
- configuration validation
- tool schemas
- agent structured outputs
- evaluation schemas

Example conceptual model:

```text
AgentDecision
├── intent
├── confidence
├── action
├── requires_human
└── tool_request
```

Critical principle:

> The LLM should not directly control critical business operations.

Structured outputs must be validated before actions are executed.

---

# 6. PostgreSQL

Use:

> PostgreSQL

as the primary relational database.

It will store:

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

PostgreSQL will provide:

- relational integrity
- transactions
- constraints
- indexes
- reliable persistence

---

# 7. Vector database

Initial direction:

> pgvector with PostgreSQL

But this is **not permanently fixed**.

We will create an ADR comparing alternatives if appropriate.

Potential alternatives include:

- pgvector
- Qdrant
- Weaviate
- Milvus

Decision criteria:

- retrieval performance
- filtering
- operational complexity
- scalability
- developer experience
- open-source/self-hosting
- integration
- cost

The vector database will NOT be populated during initial data generation.

Future pipeline:

```text
Markdown
 ↓
Parse
 ↓
Chunk
 ↓
Embedding
 ↓
Vector DB
```

---

# 8. Redis

Use:

> Redis

for:

- caching
- queue/broker functionality
- short-lived state where appropriate
- asynchronous job infrastructure

Do not use Redis as the primary source of truth for transactional customer/order data.

---

# 9. Background jobs — Celery

Use:

> Celery

for production-style asynchronous work.

Potential jobs:

```text
document ingestion
embedding
evaluation
CRM synchronization
notifications
long-running workflows
```

Architecture:

```text
FastAPI
   ↓
Redis
   ↓
Celery Worker
   ↓
Task
```

We'll learn:

- retries
- exponential backoff
- task state
- idempotency
- failure handling
- dead-letter concepts

---

# 10. RAG stack

RAG will be treated as an **architecture and experimentation problem**, not merely a library feature.

Pipeline:

```text
Knowledge Articles
       ↓
Parsing
       ↓
Chunking
       ↓
Embedding
       ↓
Index
       ↓
Query
       ↓
Retrieval
       ↓
Reranking
       ↓
Context
       ↓
LLM
       ↓
Grounded Answer
```

We will compare:

```text
BM25
Dense
Hybrid
Hybrid + reranker
```

---

# 11. Embeddings

Use open-source embedding models through:

> Sentence Transformers / compatible open-source embedding tooling

The exact model will be chosen experimentally.

Selection criteria:

- retrieval quality
- embedding dimension
- latency
- memory
- license
- domain suitability
- multilingual needs if later required

We will not assume `all-MiniLM-L6-v2` is automatically optimal.

---

# 12. Sparse retrieval — BM25

Use:

> BM25

as the lexical retrieval baseline.

Why?

Support queries can contain:

- product names
- SKUs
- order IDs
- policy terms
- technical terminology

Exact lexical matching can outperform semantic search for some queries.

This gives us a strong baseline for hybrid retrieval.

---

# 13. Hybrid retrieval

Combine:

```text
BM25
 +
Dense retrieval
```

We'll compare different fusion strategies where useful.

Measure:

- Recall@K
- Precision@K
- MRR
- NDCG

---

# 14. Reranking

Use an open-source cross-encoder/reranker.

Architecture:

```text
Hybrid retrieval
      ↓
Top 20
      ↓
Cross-encoder
      ↓
Top 5
      ↓
LLM
```

We will test whether reranking produces a statistically/usefully significant improvement.

---

# 15. Classical ML

Use:

> scikit-learn initially

Tasks:

```text
Intent classification
Category classification
Priority prediction
Ticket routing
Escalation prediction
```

Baselines:

```text
Rules
 ↓
Logistic Regression
 ↓
Tree-based model
```

Evaluate:

- precision
- recall
- F1
- macro F1
- confusion matrix
- calibration
- class-specific metrics

For priority prediction, pay special attention to P0/P1 recall.

---

# 16. Agent framework

Initial candidate:

> LangGraph

But the decision is explicitly **not assumed to be final**.

We'll evaluate the need for stateful workflow orchestration and document the decision in an ADR.

Agent architecture:

```text
Agent
 ├── Skills
 ├── Tools
 ├── Memory
 ├── Policies
 ├── Workflow
 └── Guardrails
```

---

# 17. Agent Skills

Skills will be a first-class project concept.

Potential structure:

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

Each skill contains:

- purpose
- inputs
- outputs
- tools
- preconditions
- guardrails
- failure handling
- evaluation criteria

Distinction:

```text
Tool
= capability

Skill
= reusable capability + instructions + rules

Agent
= decides when/how to use capabilities
```

---

# 18. Tool layer

Tools will represent enterprise capabilities.

Examples:

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

Initially, these will call mock internal services backed by our synthetic data.

Later they can behave like external enterprise APIs.

---

# 19. Workflow orchestration

Use a stateful workflow approach.

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

The workflow must explicitly model:

- branching
- state
- retries
- timeouts
- checkpoints
- failures
- human approval

---

# 20. OAuth and authentication

Use open standards:

> OAuth 2.0 + JWT

Concepts:

- access tokens
- refresh tokens
- scopes
- roles
- service-to-service authentication

We will distinguish:

```text
Customer authorization
Agent authorization
Service-to-service authorization
```

Authorization must be enforced by application/policy logic, not delegated solely to the LLM.

---

# 21. Webhooks

Implement event-driven integration.

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

- signatures
- event IDs
- retries
- duplicate delivery
- replay protection
- idempotency
- event ordering

Critical rule:

> The same event received twice must not cause the business action twice.

---

# 22. Idempotency

Idempotency is a first-class reliability requirement.

Example:

```text
Webhook event
      ↓
event_id = ABC123
      ↓
Already processed?
   ├── Yes → ignore safely
   └── No  → process
              ↓
           record event
```

Apply this to:

- webhooks
- background jobs
- transactional actions
- retries

---

# 23. Observability — OpenTelemetry

Use:

> OpenTelemetry

as the vendor-neutral observability/instrumentation layer.

Trace:

```text
HTTP Request
 ↓
Agent
 ├── Retrieval
 │    └── Database
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

---

# 24. Evaluation stack

Evaluation is a core system, not a final add-on.

We'll use:

- custom evaluation code
- golden datasets
- pytest for regression tests
- appropriate open-source evaluation libraries where useful

Potential libraries:

- RAGAS
- DeepEval
- TruLens

But we will choose based on actual requirements rather than using every framework.

Evaluation areas:

```text
ML
RAG
Agent
Safety
Reliability
Business
```

---

# 25. RAG evaluation

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

Run the golden dataset after important changes.

Eventually:

```text
Git commit
 ↓
Evaluation
 ↓
Threshold
 ├── PASS → continue
 └── FAIL → block
```

---

# 26. Agent evaluation

Measure:

- task success
- tool selection accuracy
- tool argument accuracy
- policy compliance
- human-escalation accuracy
- response correctness
- failure recovery

We will maintain explicit ground truth for tool-dependent evaluation cases.

---

# 27. Testing

Use:

> pytest

Testing levels:

```text
Unit
Integration
Workflow
RAG
Evaluation
Reliability
Security
Load
```

We will deliberately test failure scenarios.

Examples:

- database unavailable
- external API timeout
- duplicate webhook
- invalid LLM output
- malformed tool arguments
- worker crash
- Redis unavailable
- LLM unavailable

---

# 28. Docker

Use:

> Docker

Containerize:

```text
FastAPI
Worker
PostgreSQL
Redis
Vector DB
Observability
```

Local orchestration:

> Docker Compose

Expected developer experience:

```bash
docker compose up
```

The goal is reproducible local production-like infrastructure.

---

# 29. CI/CD

Use:

> GitHub Actions

Pipeline:

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

> AI evaluation becomes part of CI/CD.

A retrieval/model change that breaks quality should be capable of failing the pipeline.

---

# 30. Infrastructure as Code

Use:

> OpenTofu or Terraform

Final choice will be made through an ADR.

Purpose:

- reproducible infrastructure
- version-controlled deployment configuration
- cloud resources
- networking
- databases
- secrets/configuration boundaries

---

# 31. Cloud deployment

We will deploy a real production-like system.

Target:

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

We will choose the actual provider later based on:

- cost
- free/low-cost availability
- container support
- managed services
- open-source compatibility
- ease of deployment
- learning value

GitHub Actions will automate deployment.

---

# 32. Configuration and secrets

Never hard-code:

- API keys
- passwords
- tokens
- database credentials
- OAuth secrets

Use:

```text
.env
.env.example
```

locally.

Cloud deployments should use the provider's secret-management mechanism.

`.env.example` contains names only, never real secrets.

---

# 33. Documentation

Use Markdown for:

```text
docs/
├── requirements/
├── architecture/
├── adr/
├── data/
├── evaluation/
├── deployment/
└── runbooks/
```

Important documents:

```text
requirements.md
architecture.md
threat_model.md
deployment.md
runbook.md
```

---

# 34. Architecture diagrams

Use:

> Mermaid

initially.

Diagram types:

- system architecture
- data flow
- sequence diagrams
- agent workflows
- deployment architecture
- trust boundaries

This keeps diagrams version-controlled with the code.

---

# 35. Data generation

Synthetic data will be generated with Python.

Initial datasets:

| Dataset | Size | Format |
|---|---:|---|
| Knowledge articles | ~100 | Markdown |
| FAQ questions | ~300 | JSONL |
| Golden QA | ~200 | JSONL |
| Customers | 1,000 | CSV + PostgreSQL |
| Products | 100 | CSV + PostgreSQL |
| Orders | 5,000 | CSV + PostgreSQL |
| Support tickets | 1,000 | CSV + PostgreSQL |
| Conversations | 300 | JSONL + PostgreSQL |

Data must be reproducible with a fixed seed.

Default:

```text
seed = 42
```

---

# 36. Storage format policy

### Markdown

For:

- knowledge articles
- policies
- documentation

### CSV

For:

- customers
- products
- orders
- support tickets

### JSONL

For:

- FAQ questions
- golden evaluation examples
- conversations

### PostgreSQL

Runtime relational representation of:

- customers
- products
- orders
- support tickets
- conversations

### Vector database

Do not populate during initial data creation.

Populate later through the RAG ingestion pipeline.

---

# 37. What we intentionally won't use initially

We will avoid unnecessary technology sprawl.

Do NOT automatically add:

- Kubernetes
- Kafka
- Spark
- Airflow
- dozens of agent frameworks
- multiple vector databases
- multiple observability platforms
- multiple cloud providers

We can introduce a technology later if a real requirement justifies it.

Every such addition should have a clear reason and preferably an ADR.

---

# 38. Technology decision process

For important components:

```text
Business requirement
        ↓
Technical requirement
        ↓
Candidate technologies
        ↓
Evaluation criteria
        ↓
Prototype/benchmark
        ↓
Decision
        ↓
ADR
        ↓
Implementation
```

Example:

> Why pgvector instead of Qdrant?

We should answer using:

- workload
- filtering
- scale
- latency
- operational complexity
- cost
- team familiarity
- deployment model

—not popularity.

---

# 39. Final target stack

The initial target stack is:

```text
                    ┌─────────────────────┐
                    │      Customer       │
                    └──────────┬──────────┘
                               │
                               ▼
                         HTTPS / API
                               │
                               ▼
                         ┌──────────┐
                         │ FastAPI  │
                         └────┬─────┘
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
          PostgreSQL       Agent            Webhooks
              │               │
              │         ┌─────┼─────┐
              │         ▼     ▼     ▼
              │       Skills Tools RAG
              │                     │
              │               ┌─────┴─────┐
              │               ▼           ▼
              │             BM25       Dense
              │                           │
              │                        Reranker
              │                           │
              │                       Vector DB
              │
              └──────────────┐
                             ▼
                          Redis
                             │
                             ▼
                          Celery
                             │
                             ▼
                           Worker

        ┌──────────────────────────────────────┐
        │ OpenTelemetry / Observability         │
        └──────────────────────────────────────┘

        ┌──────────────────────────────────────┐
        │ Docker + Docker Compose               │
        └──────────────────────────────────────┘

        ┌──────────────────────────────────────┐
        │ GitHub + GitHub Actions               │
        └──────────────────────────────────────┘

        ┌──────────────────────────────────────┐
        │ Cloud + OpenTofu/Terraform             │
        └──────────────────────────────────────┘
```

---

# 40. Important principle

The final project is **not** intended to demonstrate that we know a particular list of tools.

It is intended to demonstrate:

> **We can take an ambiguous enterprise AI/ML problem, select appropriate technologies, justify architectural decisions, build the system, evaluate it experimentally, deploy it, operate it reliably, and connect technical performance to business outcomes.**

Therefore:

**Architecture first. Technology second.**

And:

**Measurement before claims.**


---

# LLM / Model Serving

## Initial LLM serving layer

Use:

> **Ollama**

Ollama is the **local LLM serving/runtime layer** for development and initial experimentation.

Important:

> Ollama is not the LLM itself.

The architecture is:

```text
Application
    ↓
LLM abstraction
    ↓
Ollama
    ↓
Open-weight model
```

---

## Actual LLM model

The actual model is:

> **TBD — selected through benchmarking**

Do NOT permanently lock the application to a single model at the beginning.

We will benchmark approximately 2–3 suitable open-weight models.

Candidate selection will depend on:

- local hardware compatibility
- context length
- tool-calling capability
- structured-output reliability
- reasoning capability
- RAG performance
- agent performance
- model license
- inference speed
- memory/VRAM requirements

---

## Model evaluation criteria

Candidate models will be compared using our domain-specific evaluation datasets.

Measure:

### General response quality

- answer correctness
- relevance
- completeness

### RAG

- groundedness
- faithfulness
- context utilization

### Structured output

- schema compliance
- invalid-output rate
- retry rate

### Agent

- task success
- tool selection accuracy
- tool argument accuracy
- policy compliance

### Engineering

- latency
- throughput
- CPU/RAM/VRAM usage
- model size
- context capacity

### Cost

For local inference:

- compute requirements
- infrastructure cost
- inference throughput

For any later alternative deployment:

- inference cost
- infrastructure cost
- operational cost

---

## Model-selection process

Use:

```text
Candidate models
       ↓
Ollama
       ↓
Common evaluation suite
       ↓
Quality + reliability + latency + resource measurements
       ↓
Comparison
       ↓
Model selection
       ↓
ADR
```

The final choice should be based on measured results, not popularity.

---

## Development vs production

### Development

Use:

> Ollama + open-weight model

This keeps the initial development environment local and low-cost.

### Experimentation

Compare multiple open-weight models using the same evaluation suite.

### Production

The production serving architecture will be decided later.

Possible considerations include:

- continue using Ollama where appropriate
- use another open-source inference server if scale/performance requires it
- deploy the selected open-weight model on suitable cloud compute

The production decision must be supported by measurements and an ADR.

---

## Required ADR

Create:

```text
ADR — LLM Selection & Serving Architecture
```

It should document:

- requirements
- candidate models
- serving options
- evaluation criteria
- benchmark results
- quality trade-offs
- latency trade-offs
- resource requirements
- licensing
- cost
- final decision
- consequences

This is intentionally a **model-selection and serving architecture decision**, not simply a decision to "use Ollama."

---

## Important architectural principle

The application should interact with an **LLM abstraction/interface**, rather than hard-coding application logic directly around one specific model.

Conceptually:

```text
Application
     ↓
LLM Interface
     ↓
Ollama Adapter
     ↓
Selected Model
```

This allows us to benchmark and replace models without redesigning the entire application.
