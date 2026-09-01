# Project: Enterprise Customer Support AI/ML Platform — Data Generation

You are responsible for creating the complete, reproducible data foundation for an **Enterprise Customer Support AI/ML Platform**.

This is NOT a simple chatbot dataset.

The eventual system will demonstrate Principal-level Data Science / Applied AI capabilities across:

- Classical ML
- RAG / information retrieval
- Agentic AI
- Tool calling
- Workflow orchestration
- Evaluation
- Observability
- Guardrails
- Human-in-the-loop
- Enterprise integrations
- Reliability
- Deployment
- Business KPI optimization

The fictional enterprise is:

> **Acme Store**

Acme Store is a fictional e-commerce company.

The goal of this task is ONLY to create the data foundation. Do not build the complete AI application yet.

---



# 1. Core principle

All generated data must be:

1. Internally consistent
2. Reproducible
3. Realistic
4. Relationally consistent
5. Suitable for ML experimentation
6. Suitable for RAG experimentation
7. Suitable for agent/tool-calling workflows
8. Suitable for evaluation
9. Versioned
10. Traceable to its source
11. Free from real personally identifiable information
12. Clearly marked as synthetic where applicable

Do NOT use real people's personal information.

Do NOT randomly scrape websites.

Do NOT introduce external proprietary/copyrighted content.

The dataset should be self-contained and reproducible.

Use a fixed random seed for synthetic data generation.

---



# 2. Required repository structure

Create the following structure:

```text
data/
│
├── README.md
│
├── raw/
│   ├── knowledge_base/
│   └── external_sources/
│
├── processed/
│   ├── knowledge_base/
│   ├── support_tickets/
│   ├── conversations/
│   └── evaluation/
│
├── structured/
│   ├── customers/
│   ├── products/
│   ├── orders/
│   ├── tickets/
│   └── conversations/
│
├── database/
│   ├── schema.sql
│   ├── seed.sql
│   └── README.md
│
├── evaluation/
│   ├── golden_qa.jsonl
│   ├── retrieval_eval.jsonl
│   ├── agent_eval.jsonl
│   ├── classification_eval.csv
│   └── evaluation_data_card.md
│
├── data_cards/
│   ├── knowledge_base_data_card.md
│   ├── support_ticket_data_card.md
│   ├── customer_data_card.md
│   ├── order_data_card.md
│   └── evaluation_dataset_card.md
│
└── schemas/
    ├── customer_schema.md
    ├── product_schema.md
    ├── order_schema.md
    ├── ticket_schema.md
    ├── conversation_schema.md
    └── knowledge_article_schema.md
```

Adjust the exact structure if necessary, but preserve the conceptual separation.

---



# 3. Dataset sizes

Create these initial datasets.

IMPORTANT: These are the REQUIRED INITIAL sizes.


| Dataset              | Size   | Primary purpose               |
| -------------------- | ------ | ----------------------------- |
| Knowledge articles   | ~100   | RAG                           |
| FAQ / user questions | ~300   | RAG testing                   |
| Golden QA pairs      | ~200   | RAG evaluation                |
| Customers            | ~1,000 | Customer lookup / tools       |
| Products             | ~100   | Product lookup / tools        |
| Orders               | ~5,000 | Order lookup / tools          |
| Support tickets      | ~1,000 | Classical ML                  |
| Conversations        | ~300   | Agent/conversation evaluation |


The quantities may differ slightly only if required to preserve referential integrity, but target these numbers closely.

Do NOT generate massive datasets such as 100K+ records at this stage.

The dataset will be expanded later if experiments require it.

---



# 4. Acme Store business domain

Create a realistic fictional e-commerce company.

Acme Store should have:

### Product categories

At minimum:

- Electronics
- Laptops
- Smartphones
- Tablets
- Accessories
- Home Appliances
- Wearables
- Audio
- Networking
- Gaming

Products should have realistic but fictional names, prices, specifications and policies.

Do not use real product SKUs that could be confused with actual products.

---



# 5. Customer dataset

Target:

> 1,000 synthetic customers

Primary storage:

> PostgreSQL

Also create a reproducible source file:

> `structured/customers/customers.csv`

Schema:

```text
customer_id
first_name
last_name
email
phone
customer_segment
account_status
country
state
city
registration_date
preferred_language
created_at
updated_at
```

Use synthetic names and synthetic contact information.

Customer segments may include:

```text
standard
premium
business
enterprise
```

Account status:

```text
active
inactive
suspended
```

Maintain realistic distributions.

Customer IDs must be unique.

---



# 6. Product dataset

Target:

> 100 products

Primary storage:

> PostgreSQL

Source:

> `structured/products/products.csv`

Schema:

```text
product_id
sku
product_name
category
subcategory
description
price
currency
stock_status
warranty_months
return_window_days
is_active
created_at
updated_at
```

Important:

Products must have meaningful relationships with the knowledge base.

For example:

- product warranty information
- return restrictions
- troubleshooting documentation
- product-specific support information

---



# 7. Order dataset

Target:

> 5,000 orders

Primary storage:

> PostgreSQL

Source:

> `structured/orders/orders.csv`

Schema:

```text
order_id
customer_id
order_date
product_id
quantity
unit_price
total_amount
currency
payment_method
payment_status
order_status
shipping_method
tracking_number
expected_delivery_date
actual_delivery_date
created_at
updated_at
```

Order status should include realistic states such as:

```text
placed
confirmed
processing
shipped
out_for_delivery
delivered
delayed
cancelled
returned
refunded
```

Payment status:

```text
pending
paid
failed
refunded
partially_refunded
```

Shipping methods:

```text
standard
express
next_day
international
```

Create realistic temporal relationships.

For example:

- cancelled orders should not normally have a successful delivery
- delivered orders should have actual delivery dates
- refunded orders should have appropriate payment status
- delayed orders may have expected delivery dates in the past
- returned orders should normally correspond to previously delivered orders

Maintain referential integrity:

```text
customer_id → customers.customer_id
product_id → products.product_id
```

---



# 8. Knowledge Base

This is one of the MOST IMPORTANT parts of the project.

Target:

> Approximately 100 knowledge articles.

Format:

> Markdown (`.md`)

Do NOT store the articles initially as CSV.

Directory:

```text
raw/knowledge_base/
```

Organize them into:

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

Create approximately 10–15 articles per major domain.

---



# 9. Knowledge article content

Articles should represent realistic enterprise support documentation.

Include topics such as:

### Shipping

- domestic shipping
- international shipping
- delayed delivery
- lost package
- tracking
- delivery attempts
- address changes
- shipping charges



### Returns

- standard return policy
- damaged products
- defective products
- return window
- return shipping
- opened products
- electronics returns
- enterprise returns



### Refunds

- refund policy
- refund processing
- partial refunds
- cancelled order refunds
- payment reversal
- refund timelines



### Payments

- supported payment methods
- failed payments
- duplicate charges
- payment authorization
- invoice payments
- business accounts



### Products

- warranty
- product registration
- replacement
- troubleshooting
- compatibility



### Account

- password reset
- account security
- account closure
- profile changes



### Orders

- order cancellation
- order modification
- order status
- split shipments

---



# 10. IMPORTANT: Make the knowledge base challenging

Do NOT make all articles independent and trivial.

We specifically need realistic retrieval challenges.

For example:

Article A:

> Standard products can be returned within 30 days.

Article B:

> Damaged products may be returned within 60 days.

Article C:

> Certain electronics have a 15-day standard return window.

Article D:

> Enterprise customers may have different return terms under their contract.

This allows us to test whether retrieval can identify the correct policy and exception.

Create:

- overlapping terminology
- similar articles
- policy exceptions
- product-specific policies
- customer-segment-specific policies
- temporal policies
- related but non-answering documents

---



# 11. Temporal knowledge

Some policies must have versions.

For example:

```text
Return Policy v1
effective: 2025-01-01
expires: 2025-12-31

Return Policy v2
effective: 2026-01-01
expires: null
```

Create realistic policy changes.

Each article must have metadata:

```yaml
document_id:
title:
category:
subcategory:
source:
source_type:
version:
effective_from:
effective_to:
product_scope:
customer_segment:
language:
created_at:
updated_at:
```

Example:

```yaml
document_id: KB-RET-001
title: Standard Return Policy
category: returns
subcategory: policy
source: Acme Store
source_type: synthetic
version: "2.0"
effective_from: "2026-01-01"
effective_to: null
product_scope: all
customer_segment: standard
language: en
```

---



# 12. Document provenance

Every document must be traceable.

For every article store:

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

For synthetic documents:

```text
source_type = synthetic
```

and:

```text
source = Acme Store Internal Knowledge Base
```

If there is no external URL, leave `source_url` null.

Do NOT invent external URLs.

---



# 13. RAG document processing metadata

Do NOT generate embeddings yet unless needed for reproducibility.

We will generate embeddings later as part of the actual ingestion pipeline.

However, create metadata that supports later chunking:

```text
document_id
section_id
title
section_title
category
version
effective_from
effective_to
```

The eventual RAG pipeline should be able to transform:

```text
Markdown article
      ↓
sections
      ↓
chunks
      ↓
embeddings
      ↓
vector database
```

Do not prematurely hard-code a chunk size into the source documents.

---



# 14. FAQ / user-question dataset

Target:

> ~300 questions

Format:

> JSONL

File:

```text
processed/evaluation/faq_questions.jsonl
```

Each record should contain:

```json
{
  "question_id": "FAQ-0001",
  "question": "...",
  "intent": "...",
  "category": "...",
  "difficulty": "...",
  "expected_document_ids": [],
  "expected_answer": "...",
  "requires_tool": false,
  "requires_human": false
}
```

Question difficulty:

```text
easy
medium
hard
adversarial
```

Create questions covering:

- straightforward factual questions
- paraphrases
- multi-hop questions
- ambiguous questions
- questions requiring policy exceptions
- temporal questions
- product-specific questions
- customer-segment-specific questions
- questions whose answer is NOT in the knowledge base

---



# 15. Golden QA dataset

Target:

> ~200 high-quality golden examples

File:

```text
evaluation/golden_qa.jsonl
```

This is NOT simply another FAQ dataset.

It is the authoritative evaluation dataset.

Each record:

```json
{
  "qa_id": "QA-0001",
  "question": "...",
  "expected_answer": "...",
  "acceptable_answers": [],
  "expected_document_ids": [],
  "expected_sections": [],
  "intent": "...",
  "category": "...",
  "difficulty": "...",
  "requires_retrieval": true,
  "requires_tool": false,
  "requires_human": false,
  "ground_truth_action": null
}
```

Where appropriate include:

```text
expected_customer_id
expected_order_id
expected_tool
expected_tool_arguments
expected_policy
```

This dataset will later support:

- answer correctness
- retrieval recall
- context precision
- context recall
- faithfulness
- groundedness
- tool correctness
- agent correctness

---



# 16. Difficult evaluation examples

The golden dataset MUST contain:

### Simple

"What is the return period?"

### Paraphrased

"I received my item a few days ago. How long do I have if I change my mind?"

### Multi-hop

"My laptop arrived damaged 35 days ago and I am an enterprise customer. Can I get a replacement?"

### Ambiguous

"Can I return it?"

### Out-of-domain

"Can you recommend a good laptop for gaming?"

### Unanswerable

"What will Acme Store's return policy be in 2030?"

If the information does not exist, the expected behavior should be:

> acknowledge lack of information / avoid hallucination / escalate where appropriate.



### Conflicting retrieval

Create cases where several documents look relevant but only one contains the correct exception.

### Temporal

"What was the return policy in June 2025?"

The system must use the correct historical version.

### Adversarial

Questions designed to tempt the model into ignoring policy or inventing exceptions.

---



# 17. Support ticket dataset

Target:

> 1,000 synthetic support tickets

Primary storage:

> PostgreSQL

Source:

> `structured/tickets/support_tickets.csv`

Schema:

```text
ticket_id
customer_id
order_id
product_id
created_at
channel
subject
message
category
subcategory
intent
priority
sentiment
assigned_team
status
resolution
resolution_code
resolution_time_minutes
escalated
escalation_reason
customer_satisfaction
first_response_time_minutes
```

---



# 18. Ticket categories

Use:

```text
shipping
returns
refunds
payments
orders
products
warranty
account
technical
security
```

Priorities:

```text
P0
P1
P2
P3
```

Status:

```text
open
in_progress
waiting_for_customer
resolved
closed
```

Channels:

```text
web
email
chat
phone
```

---



# 19. Make the support-ticket dataset ML-ready

The ticket data should support experiments for:

### Intent classification

```text
message → intent
```



### Category classification

```text
message → category
```



### Priority prediction

```text
ticket → priority
```



### Routing

```text
ticket → assigned_team
```



### Escalation prediction

```text
ticket → probability of escalation
```



### Resolution prediction

```text
ticket → probability of automatic resolution
```

Do NOT make labels perfectly correlated with obvious keywords.

Introduce realistic ambiguity and class imbalance.

For example:

- most tickets should be P2/P3
- relatively few should be P0
- some tickets should have ambiguous wording
- some high-priority tickets should have neutral sentiment
- some angry customers should not necessarily be high priority

This is important for realistic ML experiments.

---



# 20. Support teams

Use teams such as:

```text
general_support
shipping_support
billing_support
technical_support
returns_support
enterprise_support
security_support
```

Create logical relationships between category/intent and assigned team, but allow realistic exceptions.

---



# 21. Conversations

Target:

> ~300 synthetic customer-support conversations

Format:

> JSONL

File:

```text
processed/conversations/conversations.jsonl
```

Each conversation should contain:

```json
{
  "conversation_id": "CONV-0001",
  "customer_id": "CUS-0001",
  "channel": "chat",
  "started_at": "...",
  "messages": [
    {
      "turn_id": 1,
      "speaker": "customer",
      "message": "...",
      "timestamp": "..."
    },
    {
      "turn_id": 2,
      "speaker": "agent",
      "message": "...",
      "timestamp": "..."
    }
  ],
  "primary_intent": "...",
  "resolution": "...",
  "escalated": false,
  "customer_satisfaction": 4
}
```

---



# 22. Conversation scenarios

Include:

- simple FAQ
- order status
- delayed delivery
- return request
- refund request
- damaged product
- technical troubleshooting
- account issue
- payment issue
- multi-turn clarification
- ambiguous request
- frustrated customer
- policy exception
- human escalation
- tool-dependent conversation
- unsafe/high-risk action request

The conversations should not all end successfully.

Some should:

- escalate
- fail to resolve
- require clarification
- require human intervention

This is important for agent evaluation.

---



# 23. High-risk actions

Define actions that should require human approval.

Examples:

```text
issue_refund
cancel_high_value_order
change_customer_account_email
change_shipping_address_after_shipping
override_policy
account_security_changes
```

Define lower-risk actions:

```text
get_order_status
get_tracking_information
get_customer_information
search_knowledge_base
check_return_policy
create_support_ticket
```

The data should contain examples covering both categories.

---



# 24. Tool-call ground truth

For relevant evaluation examples, specify expected tool calls.

Example:

```json
{
  "question": "Where is my order 12345?",
  "requires_tool": true,
  "expected_tool": "get_order_status",
  "expected_tool_arguments": {
    "order_id": "12345"
  }
}
```

For transactional actions:

```json
{
  "requires_tool": true,
  "requires_human": true,
  "expected_tool": "issue_refund"
}
```

This will later allow us to evaluate whether the agent:

1. selected the correct tool
2. supplied correct arguments
3. respected authorization
4. correctly requested human approval

---



# 25. Synthetic data consistency

All datasets must be interconnected.

For example:

```text
Customer
   ↓
Order
   ↓
Product
   ↓
Ticket
   ↓
Conversation
```

If a ticket references:

```text
customer_id = CUS-0100
order_id = ORD-0234
```

both must exist.

If the order references:

```text
product_id = PROD-0020
```

that product must exist.

Conversations should reference real customers/orders where appropriate.

Do NOT create orphaned foreign keys.

---



# 26. Business scenarios to represent

Ensure the data includes realistic examples of:

### Shipping

- on-time delivery
- delayed delivery
- lost shipment
- wrong address
- tracking unavailable
- failed delivery



### Returns

- eligible return
- expired return
- damaged item
- defective item
- non-returnable product
- enterprise exception



### Refunds

- full refund
- partial refund
- refund pending
- refund rejected
- duplicate payment
- cancelled order refund



### Payments

- payment failure
- duplicate charge
- authorization failure
- invoice payment



### Technical

- product malfunction
- setup problem
- compatibility issue
- troubleshooting



### Account

- password reset
- account lock
- email change
- security issue

---



# 27. Data quality validation

Create validation scripts.

At minimum:

```text
scripts/
├── validate_customers.py
├── validate_products.py
├── validate_orders.py
├── validate_tickets.py
├── validate_conversations.py
├── validate_knowledge_base.py
└── validate_all.py
```

Validation must check:

### Referential integrity

```text
orders.customer_id exists
orders.product_id exists
tickets.customer_id exists
tickets.order_id exists
tickets.product_id exists
```



### Uniqueness

IDs must be unique.

### Nullability

Required fields cannot be null.

### Temporal consistency

Examples:

```text
actual_delivery_date >= order_date
resolution timestamp >= creation timestamp
```



### Business rules

Examples:

```text
refunded order → appropriate payment status
delivered order → actual delivery date
cancelled order → should not normally be delivered
```



### Knowledge metadata

Every document must have:

```text
document_id
version
effective_from
source
source_type
```

---



# 28. Data Cards

Create a Data Card for each major dataset.

Each Data Card must document:

```text
Dataset name
Purpose
Source
Generation method
Synthetic/real status
Size
Schema
Features
Labels
Class distributions
Known assumptions
Known limitations
Potential biases
Intended use
Non-intended use
Privacy considerations
Version
Generation seed
Quality checks
```

Especially document that customer/order/ticket data is synthetic.

---



# 29. Reproducibility

Create a single data-generation entry point:

```text
scripts/generate_all_data.py
```

Running:

```bash
python scripts/generate_all_data.py
```

should regenerate the synthetic datasets.

Use a fixed random seed.

Make the seed configurable:

```bash
python scripts/generate_all_data.py --seed 42
```

The default seed should be:

```text
42
```

The generation should be deterministic wherever practical.

---



# 30. Database

Create PostgreSQL-compatible schema:

```text
database/schema.sql
database/seed.sql
```

Tables should include at minimum:

```text
customers
products
orders
support_tickets
conversations
conversation_messages
```

Use:

- primary keys
- foreign keys
- indexes
- appropriate data types
- constraints

Do NOT create the vector database yet.

The future RAG pipeline will create the vector representation from the Markdown knowledge base.

---



# 31. Vector database decision

Do NOT prematurely generate vectors.

For now:

```text
Markdown
   ↓
future ingestion pipeline
   ↓
chunking
   ↓
embedding
   ↓
vector database
```

We will decide the exact vector database as an architectural decision later.

The current data must remain vector-database-agnostic.

---



# 32. CSV vs JSONL vs Markdown vs PostgreSQL

Use the following policy:

### Markdown

Use for:

```text
knowledge articles
policies
documentation
```



### CSV

Use for:

```text
customers
products
orders
support tickets
```

because these are tabular datasets useful for ML analysis.

### JSONL

Use for:

```text
FAQ questions
golden evaluation examples
conversations
```

because these contain nested/variable structures.

### PostgreSQL

Use as the relational runtime representation of:

```text
customers
products
orders
support tickets
conversations
```



### Vector DB

DO NOT populate yet.

It will be populated by the actual RAG ingestion pipeline later.

---



# 33. README

Create:

```text
data/README.md
```

It must explain:

1. What Acme Store is
2. What datasets exist
3. Dataset sizes
4. File formats
5. Relationships
6. How to regenerate data
7. How to validate data
8. How to load PostgreSQL
9. Dataset limitations
10. Synthetic-data disclaimer

Include an architecture diagram similar to:

```text
Knowledge Articles ──────┐
                          │
                          ▼
                    RAG Pipeline
                          │
                          ▼
                     Vector DB

Customers ────────┐
Products ─────────┤
Orders ───────────┤──→ PostgreSQL
Tickets ──────────┤
Conversations ────┘

FAQ ───────────────→ Evaluation
Golden QA ─────────→ Evaluation
```

---



# 34. Important: Do not build the application

For this task, DO NOT implement:

- FastAPI
- LangGraph
- agents
- RAG pipeline
- embeddings
- vector database
- OAuth
- Redis
- Celery
- Docker
- cloud deployment

Those will be built later.

Your responsibility right now is:

> **Create a high-quality, reproducible enterprise AI dataset foundation.**

---



# 35. Final validation report

After generating everything, create:

```text
data/VALIDATION_REPORT.md
```

Include:

```text
Dataset                    Expected    Actual
------------------------------------------------
Knowledge articles          ~100
FAQ questions               ~300
Golden QA                   ~200
Customers                  1,000
Products                    100
Orders                    5,000
Support tickets           1,000
Conversations               300
```

Also report:

- number of orphaned records
- duplicate IDs
- null violations
- temporal violations
- invalid business rules
- category distributions
- ticket priority distribution
- ticket intent distribution
- escalation rate
- customer satisfaction distribution
- knowledge article category distribution

The report should clearly state PASS/FAIL for each validation category.

---



# 36. Quality over quantity

Do not blindly generate text to reach a number.

For the knowledge base and evaluation datasets especially:

> 100 high-quality coherent documents are more valuable than 1,000 repetitive documents.

The knowledge base must be internally coherent enough that we can later establish reliable ground truth.

The golden evaluation dataset must be manually/algorithmically validated against the knowledge base.

Every `expected_document_id` in evaluation data MUST point to a real document.

Every expected answer must be supported by the specified document(s).

---



# 37. Final deliverable

When finished, provide:

```text
1. Complete data/ directory
2. PostgreSQL schema
3. PostgreSQL seed data
4. Synthetic data generation scripts
5. Validation scripts
6. Data Cards
7. Dataset schemas
8. Evaluation datasets
9. Validation report
10. README
```

Before declaring completion, run the complete validation pipeline.

The final system should be reproducible from scratch using the documented commands.

---



# 38. Success criterion

The generated data should allow us, in later phases, to build and experimentally compare:

```text
RAG:
Dense
vs
BM25
vs
Hybrid
vs
Hybrid + reranking

Agent:
RAG-only
vs
RAG + tools
vs
Agentic workflow

ML:
Rule-based priority
vs
ML priority prediction

Evaluation:
Offline evaluation
+
Golden datasets
+
Regression testing
+
Online/business KPIs
```

The data foundation should therefore be designed specifically to support these future experiments.

Do not optimize for making a flashy demo.

Optimize for:

> **realistic enterprise problem representation + reproducibility + evaluation + ML experimentation + production AI architecture.**

Start by inspecting the repository and environment, then implement this data-generation system systematically. Do not ask for clarification unless a blocking technical ambiguity exists; make reasonable documented assumptions and record them in the relevant Data Card.

---



# LLM / Model Data Generation Alignment

The data foundation must remain **LLM-provider/model agnostic**.

The eventual development environment will initially use:

> **Ollama as the local LLM serving/runtime layer**

The actual open-weight model is intentionally **not fixed yet**.

The generated data must therefore support benchmarking multiple candidate models.

The evaluation datasets must be suitable for comparing models on:

- answer correctness
- RAG groundedness
- structured-output reliability
- tool-calling accuracy
- agent task success
- hallucination/unsupported claims
- policy compliance

Do NOT generate data that is tailored to one specific LLM.

The golden QA, agent evaluation, tool-call ground truth, and expected answers should remain model-independent wherever possible.

The future flow will be:

```text
Evaluation Dataset
       ↓
Candidate Model
       ↓
Ollama
       ↓
Run Evaluation
       ↓
Metrics
       ↓
Compare Models
```

The selected model will be determined later through benchmarking.