# Enterprise Customer Support AI Platform — Project Overview

---

## 1. Problem Statement

Enterprise customer support operations face three compounding challenges:

1. **Volume & latency** — Support teams receive thousands of tickets per day across email, web, chat, and phone. Manual triage, routing, and first-response introduce multi-hour delays, degrading customer satisfaction.
2. **Inconsistency** — Human agents apply policies (refund thresholds, return windows, cancellation rules) inconsistently, creating compliance risk and customer disputes.
3. **Knowledge fragmentation** — Policy and product information is scattered across internal wikis, PDFs, and tribal knowledge. Agents waste time searching rather than resolving.

**Goal:** Build a production-grade AI platform that (a) automatically classifies, routes, and responds to incoming tickets using a hybrid RAG + agent workflow, (b) enforces business policy deterministically, and (c) escalates to a human agent only when genuinely warranted — with a full audit trail.

---

## 2. Data

### 2.1 Structured Ticket Data

| Property | Value |
|---|---|
| File | `data/structured/tickets/support_tickets.csv` |
| Total records | 1,000 |
| Total columns | 22 |
| Date range | 2024-07 to 2025-12 |
| Channels | email (342), web (315), chat (239), phone (104) |

**Columns:** `ticket_id`, `customer_id`, `order_id`, `product_id`, `created_at`, `channel`, `subject`, `message`, `category`, `subcategory`, `intent`, `priority`, `sentiment`, `assigned_team`, `status`, `resolution`, `resolution_code`, `resolution_time_minutes`, `escalated`, `escalation_reason`, `customer_satisfaction`, `first_response_time_minutes`

**Class distributions (ML label columns):**

| Label | Class | Count | % |
|---|---|---|---|
| **category** | account | 107 | 10.7 |
| | orders | 106 | 10.6 |
| | payments | 109 | 10.9 |
| | products | 108 | 10.8 |
| | refunds | 91 | 9.1 |
| | returns | 97 | 9.7 |
| | security | 94 | 9.4 |
| | shipping | 105 | 10.5 |
| | technical | 89 | 8.9 |
| | warranty | 94 | 9.4 |
| **priority** | P0 (critical) | 29 | 2.9 |
| | P1 (high) | 115 | 11.5 |
| | P2 (medium) | 511 | 51.1 |
| | P3 (low) | 345 | 34.5 |
| **sentiment** | angry | 138 | 13.8 |
| | negative | 466 | 46.6 |
| | neutral | 293 | 29.3 |
| | positive | 103 | 10.3 |
| **escalated** | false | 852 | 85.2 |
| | true | 148 | 14.8 |
| **assigned_team** | general\_support | 208 | 20.8 |
| | technical\_support | 194 | 19.4 |
| | billing\_support | 191 | 19.1 |
| | returns\_support | 187 | 18.7 |
| | shipping\_support | 101 | 10.1 |
| | security\_support | 91 | 9.1 |
| | enterprise\_support | 28 | 2.8 |

### 2.2 Knowledge Base

| Property | Value |
|---|---|
| Location | `data/raw/knowledge_base/` |
| Format | Markdown files with YAML front matter |
| Total documents | 90 |
| Total chunks (after chunking) | 185 |
| Categories (10) | account, orders, payments, products, refunds, returns, security, shipping, troubleshooting, warranty |
| Files per category | 7–12 |

Each document contains structured YAML front matter (`category`, `title`, `version`, `effective_from`, `effective_to`) followed by policy/product body text.

---

## 3. System Components

| Component | Purpose | What Was Built |
|---|---|---|
| **FastAPI REST API** | HTTP interface for all client interactions | Full async API with JWT auth, versioned routes under `/api/v1/`, rate limiting, idempotency keys, request-ID middleware |
| **PostgreSQL + pgvector** | Relational storage + vector similarity search | Async SQLAlchemy ORM, 14 models, pgvector HNSW index for 768-dim embeddings, Alembic migrations |
| **Redis** | Caching and async task queue | Three logical databases: cache (db0), Celery broker (db1), Celery results (db2) |
| **Celery Worker** | Background task processing | 7 queues (critical, approvals, notifications, ingestion, evaluation, analytics, celery), concurrency=2 |
| **Celery Beat** | Periodic task scheduler | Approval SLA expiry job every 900 s (15 min) |
| **ML Pipeline** | Ticket auto-classification | 5 tasks × 3 model types = 15 trained sklearn pipelines; TF-IDF + classifier; saved with joblib |
| **RAG Pipeline** | Knowledge retrieval and context building | Hybrid BM25 + dense retrieval, RRF fusion, cross-encoder reranking, 6 000-char context budget |
| **Embedding Service** | Text → vector encoding | BAAI/bge-base-en-v1.5, 768-dim, L2-normalised, lazy-loaded |
| **LangGraph Agent** | Orchestrated multi-step conversation workflow | 4-node graph: classify → retrieve → handle_action → generate; conditional routing |
| **Policy Engine** | Deterministic business-rule enforcement | Refund threshold by segment, cancellation by order status, account-change always requires approval |
| **Approval Workflow** | Human-in-the-loop for high-risk actions | ApprovalRequest + AuditLog models; outcomes: auto_approve / approval_required / denied |
| **Evaluation Framework** | Offline quality gates | Retrieval metrics (Recall@k, nDCG@k, MRR, Precision@k), groundedness scoring, 5% regression gate |
| **Observability** | Runtime telemetry | Prometheus metrics for HTTP, LLM, RAG, ML, agent, and approval layers; OpenTelemetry + Jaeger traces |
| **CI/CD** | Automated quality pipeline | GitHub Actions: lint (ruff), format check, mypy type check, unit tests (179 tests), integration tests, eval gate, Docker build |
| **Docker Compose** | Local full-stack deployment | 5 services: db, redis, api, worker, beat; optional profiles for Ollama LLM and Jaeger tracing |

---

## 4. Machine Learning

### 4.1 Problem Formulation

All five ML tasks are **multi-class text classification** problems. The raw input is unstructured customer support text; labels are structured operational metadata used for routing, prioritisation, and SLA management.

### 4.2 Input Variables

The ML models receive **text only** — no structured features.

| Field | Source | Description |
|---|---|---|
| `subject` | Ticket field | Short subject line entered by customer or inferred from channel |
| `message` | Ticket field | Full free-text message body written by the customer |

**Text combination:** `subject` and `message` are concatenated with a single space, lowercased, and whitespace-stripped into one string:

```
combined_text = (subject + " " + message).strip().lower()
```

No stopword removal, stemming, or lemmatisation is applied at this stage — that is handled implicitly by TF-IDF's `min_df=2` and `sublinear_tf` parameters.

### 4.3 Preprocessing Pipeline

Text goes through a two-stage preprocessing pipeline:

**Stage 1 — Feature extraction (`src/app/ml/features.py`)**

```
Raw ticket row
      │
      ▼
extract_text(row):
  subject = str(row["subject"] or "")
  message = str(row["message"] or "")
  return f"{subject} {message}".strip().lower()
      │
      ▼
Plain lowercased string  (e.g., "warranty claim my laptop screen cracked after 3 months")
```

**Stage 2 — TF-IDF vectorisation (inside sklearn Pipeline)**

| Parameter | Value | Rationale |
|---|---|---|
| `max_features` | 10 000 | Caps vocabulary to the 10k most frequent terms |
| `ngram_range` | (1, 2) | Captures unigrams and bigrams (e.g., "return request", "order status") |
| `sublinear_tf` | True | Applies `1 + log(tf)` to dampen high-frequency term dominance |
| `min_df` | 2 | Ignores terms appearing in fewer than 2 documents (removes typos/noise) |
| `strip_accents` | "unicode" | Normalises accented characters |
| `analyzer` | "word" | Tokenises on word boundaries |

The output is a sparse TF-IDF matrix of shape `(n_samples, ≤10 000)` which is fed directly into the classifier.

### 4.4 Output Variables & Classes

| Task | Label Column | Output Classes | Class Imbalance | `use_class_weight` |
|---|---|---|---|---|
| **Category** | `category` | account, orders, payments, products, refunds, returns, security, shipping, technical, warranty | Near-balanced (89–109 per class) | No |
| **Priority** | `priority` | P0, P1, P2, P3 | Severe (P0=2.9%, P1=11.5%, P2=51.1%, P3=34.5%) | Yes (`balanced`) |
| **Sentiment** | `sentiment` | angry, negative, neutral, positive | Moderate (angry=13.8%, positive=10.3%) | Yes (`balanced`) |
| **Escalation** | `escalated` | false, true | Severe (85.2% vs 14.8%) | Yes (`balanced`) |
| **Routing** | `assigned_team` | account\_support, billing\_support, orders\_support, returns\_support, security\_support, shipping\_support, technical\_support | Moderate (enterprise\_support=2.8%) | No |

### 4.5 Train / Validation / Test Split

| Split | Fraction | Size (from 1 000 records) |
|---|---|---|
| Train | 60% | 600 |
| Validation | 20% | 200 |
| Test | 20% | 200 |

Method: stratified `train_test_split` with `random_state=42`. First split: 60/40; second split of the 40% holdout: 50/50.

### 4.6 Models

Three classifier types are wrapped in an identical `sklearn.Pipeline([("tfidf", TfidfVectorizer(...)), ("clf", <classifier>)])`:

**Logistic Regression**

| Parameter | Value |
|---|---|
| `C` | 1.0 |
| `solver` | lbfgs |
| `max_iter` | 1000 |
| `class_weight` | balanced (imbalanced tasks) / None |
| `random_state` | 42 |

**Random Forest**

| Parameter | Value |
|---|---|
| `n_estimators` | 200 |
| `max_depth` | None (fully grown) |
| `min_samples_leaf` | 2 |
| `class_weight` | balanced (imbalanced tasks) / None |
| `random_state` | 42 |
| `n_jobs` | -1 |

**Gradient Boosting**

| Parameter | Value |
|---|---|
| `n_estimators` | 150 |
| `max_depth` | 5 |
| `learning_rate` | 0.1 |
| `subsample` | 0.8 |
| `random_state` | 42 |
| Note | No class_weight support; imbalance accepted |

### 4.7 Performance Metrics

All metrics computed on the held-out **test set (n=200)**. Accuracy, Macro F1, and Weighted F1 are reported for every task/model. Priority and escalation tasks also report class-specific recall for the minority classes of operational importance (P0, P1, escalated=true).

**Performance measures explained:**
- **Accuracy** — fraction of correct predictions
- **Macro F1** — unweighted average F1 across all classes (penalises minority-class failures equally)
- **Weighted F1** — F1 weighted by class support (dominated by majority classes)
- **P0 Recall** — recall on the critical-priority class (P0); missing a P0 ticket is the costliest error
- **P1 Recall** — recall on the high-priority class
- **Escalation Recall** — recall on `escalated=true`; missing an escalation means a frustrated customer gets no senior agent

#### Task: Category (10 classes, balanced)

| Model | Test Accuracy | Test Macro F1 | Test Weighted F1 |
|---|---|---|---|
| Logistic Regression | **1.0000** | **1.0000** | **1.0000** |
| Random Forest | **1.0000** | **1.0000** | **1.0000** |
| Gradient Boosting | **1.0000** | **1.0000** | **1.0000** |

> All models achieve perfect test accuracy. The category label is perfectly separable from the synthetic ticket text (subjects like "Warranty claim", "Return request" directly encode the category). This reflects synthetic data characteristics.

#### Task: Priority (4 classes, severe imbalance)

| Model | Test Accuracy | Test Macro F1 | Test Weighted F1 | P0 Recall | P1 Recall |
|---|---|---|---|---|---|
| Logistic Regression | 0.3000 | 0.2450 | 0.3255 | 0.3333 | 0.3478 |
| Random Forest | 0.2800 | 0.2338 | 0.3079 | 0.3333 | 0.3478 |
| Gradient Boosting | 0.4350 | 0.2372 | 0.4079 | **0.0000** | 0.0435 |

> Priority is a hard task: the message text does not directly encode urgency in the synthetic data. Gradient Boosting has higher accuracy (driven by P2 majority) but zero P0 recall — it never predicts the critical class, making it operationally unsuitable. Logistic Regression is preferred for balanced minority-class recall.

#### Task: Sentiment (4 classes, moderate imbalance)

| Model | Test Accuracy | Test Macro F1 | Test Weighted F1 |
|---|---|---|---|
| Logistic Regression | 0.2550 | 0.2400 | 0.2659 |
| Random Forest | 0.2350 | 0.2360 | 0.2327 |
| Gradient Boosting | 0.4000 | 0.2475 | 0.3614 |

> Sentiment in the synthetic dataset appears to be assigned with low correlation to message word choice, making this the hardest task for all models. All models perform near random-chance at the macro level.

#### Task: Escalation (binary, severe imbalance: 85.2% / 14.8%)

| Model | Test Accuracy | Test Macro F1 | Test Weighted F1 | Escalation Recall (true class) |
|---|---|---|---|---|
| Logistic Regression | 0.5750 | 0.4295 | 0.6341 | 0.2414 |
| Random Forest | 0.5450 | 0.4327 | 0.6119 | **0.3448** |
| Gradient Boosting | 0.8000 | 0.4679 | 0.7664 | 0.0345 |

> Gradient Boosting achieves highest accuracy (predicts majority class) but misses 96.6% of escalations. Random Forest is preferred — highest escalation recall (34.5%) with reasonable macro F1.

#### Task: Routing (7 teams)

| Model | Test Accuracy | Test Macro F1 | Test Weighted F1 |
|---|---|---|---|
| Logistic Regression | 0.9700 | 0.8448 | 0.9555 |
| Random Forest | 0.9700 | 0.8448 | 0.9555 |
| Gradient Boosting | 0.9700 | 0.8448 | 0.9555 |

> All three models perform identically on routing. The team assignment is strongly predictable from the category-level text signals. Macro F1 of 0.845 reflects lower performance on `enterprise_support` (only 28 samples = 2.8% of data).

---

## 5. RAG Pipeline

### 5.1 Pipeline Flow

```
Customer query (natural language)
         │
         ▼
  ┌─────────────────────────────────────────────────────┐
  │  1. EMBED QUERY                                     │
  │     EmbeddingService.embed_query(query)             │
  │     Prepend BGE instruction prefix                  │
  │     → 768-dim L2-normalised vector                  │
  └─────────────────┬───────────────────────────────────┘
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
  ┌─────────────┐     ┌────────────────┐
  │  2a. DENSE  │     │   2b. BM25     │
  │  pgvector   │     │   In-memory    │
  │  ANN search │     │   BM25 index   │
  │  cosine (<=>)│    │   (rank-bm25)  │
  │  top-20     │     │   top-20       │
  └──────┬──────┘     └───────┬────────┘
         │                    │
         └──────────┬─────────┘
                    ▼
  ┌─────────────────────────────────────────────────────┐
  │  3. RRF FUSION                                      │
  │     score(chunk) = Σ  1 / (60 + rank_i)            │
  │     Merges dense and BM25 ranked lists              │
  │     into single ranked set (up to 40 candidates)   │
  └─────────────────┬───────────────────────────────────┘
                    │
                    ▼
  ┌─────────────────────────────────────────────────────┐
  │  4. CROSS-ENCODER RERANKING                         │
  │     ms-marco-MiniLM-L-6-v2                          │
  │     Scores each (query, chunk) pair                 │
  │     Selects top-5 by rerank score                   │
  └─────────────────┬───────────────────────────────────┘
                    │
                    ▼
  ┌─────────────────────────────────────────────────────┐
  │  5. CONTEXT BUILDING                                │
  │     Concatenate chunk texts with source headers     │
  │     Budget: 6 000 chars (~1 500 tokens)             │
  │     Format: [Source N: <title> — <category>]\n<text>│
  └─────────────────┬───────────────────────────────────┘
                    │
                    ▼
             LLM prompt context
```

### 5.2 Embedding Model

| Property | Value |
|---|---|
| Model | `BAAI/bge-base-en-v1.5` |
| Embedding dimension | 768 |
| Model version tag | 1.5 |
| Normalisation | L2-normalised (cosine similarity = dot product) |
| Query prefix | `"Represent this sentence for searching relevant passages: "` |
| Document prefix | None (raw chunk text) |
| Batch size (indexing) | 64 chunks |
| Batch size (ingestion script) | 32 documents |
| Loading | Lazy (loaded on first call, reused for all subsequent calls) |
| Library | `sentence-transformers` |

The BGE query prefix is mandatory for asymmetric retrieval: queries and documents live in different semantic spaces without it, degrading recall.

### 5.3 Vector Database

| Property | Value |
|---|---|
| Database | PostgreSQL 15 |
| Extension | `pgvector` (via `pgvector/pgvector:pg15` Docker image) |
| Table | `embedding_metadata` |
| Vector column type | `vector(768)` |
| Index type | HNSW (Hierarchical Navigable Small World) |
| Distance metric | Cosine (`<=>` operator) |
| Retrieval query | `ORDER BY em.embedding <=> :vec::vector LIMIT :k` |
| candidate_k | 20 |

### 5.4 BM25 Index

| Property | Value |
|---|---|
| Library | `rank-bm25` |
| Index scope | All active `knowledge_chunks` rows (185 chunks) |
| Build trigger | On first request or explicit rebuild |
| Tokenisation | Whitespace split on lowercased chunk text |
| candidate_k | 20 |

### 5.5 Retrieval Strategy

| Parameter | Value |
|---|---|
| Dense candidates | 20 |
| BM25 candidates | 20 |
| RRF constant K | 60 |
| RRF formula | `score = Σ 1/(60 + rank_i)` for each ranked list |
| Candidates after fusion | Up to 40 (union of both lists) |
| Cross-encoder input | Top-20 by RRF score → re-scored with cross-encoder |
| Final top_k | 5 |
| Context char budget | 6 000 characters (~1 500 tokens) |

Named strategy labels returned in API response:

| Strategy | Description |
|---|---|
| `dense` | Vector-only retrieval |
| `bm25` | BM25-only retrieval |
| `dense+bm25` | RRF fusion without reranking |
| `dense+bm25+reranked` | Full pipeline (default) |

### 5.6 Cross-Encoder Reranker

| Property | Value |
|---|---|
| Model | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| Input format | `[query, chunk_text]` pairs |
| Output | Relevance score (float) per pair |
| Inference latency | ~50 ms for 20 candidates (CPU) |
| Loading | Lazy |
| Library | `sentence-transformers.CrossEncoder` |

### 5.7 Document Chunking

| Property | Value |
|---|---|
| Chunk size | 1 500 characters (~400 tokens at 3.75 chars/token) |
| Chunk overlap | 200 characters |
| Chunk version | 1.0.0 |
| Separator priority | `["\n\n", "\n", ". ", " ", ""]` (paragraph → line → sentence → word → char) |
| Token estimate | `max(1, len(text) // 4)` |
| Algorithm | Recursive splitting — tries coarser separators first, falls back to finer ones |

### 5.8 LLM

| Property | Value |
|---|---|
| Model | `llama3.2` (configurable via `OLLAMA_MODEL` env var) |
| Serving | Ollama (`http://ollama:11434` in Docker; `http://localhost:11434` local) |
| Protocol | Ollama REST API (`/api/chat`) |
| Context window usage | System prompt + up to 6 history turns + user prompt + 6 000-char KB context |
| Timeout | 60 s |
| HTTP client | `httpx.AsyncClient` |

### 5.9 Prompts

**System Prompt** (injected as the `system` role in every LLM call):

```
You are a helpful customer support AI assistant for Acme Store.
You assist customers with orders, returns, refunds, shipping, products, and account questions.

Guidelines:
- Answer concisely and accurately using the knowledge base context provided.
- If the context doesn't cover the question, say so and offer to escalate.
- Never fabricate order details, policies, or guarantees not in the context.
- Keep a friendly, professional tone.
```

**User Prompt — with context:**

```
== Knowledge Base Context ==
[Source 1: <doc_title> — <doc_category>]
<chunk_text>

[Source 2: ...]
...
== End Context ==

Customer question: <customer_message>

Provide a helpful response based on the context above.
```

**User Prompt — no context found:**

```
Customer question: <customer_message>

No relevant knowledge base articles were found.
Provide a helpful response; if you cannot answer, politely offer escalation to a human agent.
```

**Approval note injected into context when handle_action fires:**

| Outcome | Appended note |
|---|---|
| `auto_approve` | `[System: Request automatically approved. <reason>]` |
| `approval_required` | `[System: Request is pending human approval (approval ID: <uuid>). <reason>]` |
| `denied` | `[System: Request denied by policy. <reason>]` |

### 5.10 RAG Evaluation Metrics (Offline)

The evaluation framework (`src/app/evaluation/`) computes the following metrics offline against a labelled QA set.

**Retrieval Metrics** (computed per query, averaged across the eval set):

| Metric | Formula | What it measures |
|---|---|---|
| Recall@1 | `|retrieved[:1] ∩ relevant| / |relevant|` | Does the top result contain the answer? |
| Recall@3 | `|retrieved[:3] ∩ relevant| / |relevant|` | Does any of top-3 contain the answer? |
| Recall@5 | `|retrieved[:5] ∩ relevant| / |relevant|` | Does any of top-5 contain the answer? |
| Recall@10 | `|retrieved[:10] ∩ relevant| / |relevant|` | Does any of top-10 contain the answer? |
| Precision@1 | `|retrieved[:1] ∩ relevant| / 1` | Is the top result relevant? |
| Precision@3 | `|retrieved[:3] ∩ relevant| / 3` | Fraction of top-3 that are relevant |
| Precision@5 | `|retrieved[:5] ∩ relevant| / 5` | Fraction of top-5 that are relevant |
| MRR | `1 / rank_of_first_relevant` | How early is the first relevant result? |
| nDCG@5 | `DCG@5 / IDCG@5` with log₂ discount | Ranked quality of top-5 results |
| nDCG@10 | `DCG@10 / IDCG@10` | Ranked quality of top-10 results |

**Groundedness Metrics** (LLM answer vs. retrieved context):

| Metric | Formula | Threshold |
|---|---|---|
| Context Coverage | `|answer_tokens ∩ context_tokens| / |answer_tokens|` | ≥ 0.70 = grounded |
| Answer-Context F1 | `2 × P × R / (P + R)` on content tokens | — |
| Doc-ID Hit Rate | `|expected_doc_ids ∩ retrieved_doc_ids| > 0` | — |
| Grounded Rate | Fraction of queries where context_coverage ≥ 0.70 | Target: 1.0 |

Tokenisation: lowercase, strip punctuation, remove 40 English stop words.

**Regression Gate (EVAL-006):** CI blocks promotion if any metric regresses by more than 5% relative to the baseline:

| Gated Metric | Max Allowed Regression |
|---|---|
| Recall@5 | 5% relative |
| nDCG@5 | 5% relative |
| MRR | 5% relative |

---

## 6. Agent

### 6.1 Architecture

The agent is implemented as a **LangGraph `StateGraph`** with four nodes:

```
                  ┌─────────────┐
  initial state → │   classify  │
                  └──────┬──────┘
                         │
              ┌──────────┴──────────┐
              │                     │
        needs_retrieval=True    needs_retrieval=False
              │                     │
              ▼                     │
       ┌──────────────┐             │
       │   retrieve   │             │
       └──────┬───────┘             │
              ▼                     │
       ┌──────────────┐             │
       │ handle_action│             │
       └──────┬───────┘             │
              └──────────┬──────────┘
                         ▼
                  ┌─────────────┐
                  │   generate  │
                  └──────┬──────┘
                         ▼
                        END
```

**Greeting/thanks/goodbye intents** skip both retrieve and handle_action — response is generated directly from history and system prompt.

### 6.2 Agent State (`AgentState` TypedDict)

| Field | Type | Set by |
|---|---|---|
| `conversation_id` | str | Input |
| `customer_id` | Optional[str] | Input |
| `message` | str | Input |
| `history` | list[dict] | Input |
| `order_id` | Optional[str] | Input |
| `intent` | Optional[str] | classify node |
| `intent_confidence` | Optional[float] | classify node |
| `category` | Optional[str] | classify node |
| `needs_retrieval` | bool | classify node |
| `retrieved_doc_ids` | list[str] | retrieve node |
| `context_text` | str | retrieve node |
| `sources` | list[dict] | retrieve node |
| `approval_result` | Optional[dict] | handle_action node |
| `response` | Optional[str] | generate node |
| `groundedness_score` | Optional[float] | generate node |
| `tool_calls` | list[dict] | retrieve + handle_action nodes |
| `error` | Optional[str] | error passthrough |

### 6.3 Intent Classification

The classify node first attempts ML-based intent classification using `TicketPredictor` (the trained category model). If no model is available, it falls back to keyword heuristics:

| Intent | Trigger keywords |
|---|---|
| `order_status` | order, tracking, shipped, delivery, track |
| `return_refund` | return, refund, exchange, send back |
| `cancel_order` | cancel, cancellation, cancel my order |
| `billing` | charge, invoice, payment, bill, receipt |
| `product_info` | product, item, spec, warranty, how does |
| `shipping` | ship, shipping, address, carrier, estimated |
| `account` | account, password, login, email, profile |
| `escalation` | escalate, supervisor, manager, not happy, complaint |
| `greeting` | hello, hi, hey, thanks, thank you, bye |
| `general_inquiry` | fallback (default) |

Intents in `{greeting, thanks, goodbye}` set `needs_retrieval=False`.
Intents in `{return_refund, cancel_order}` trigger the `handle_action` node.

### 6.4 Tools

| Tool | Signature | Returns | DB calls |
|---|---|---|---|
| `get_customer` | `(customer_id, db)` | `{id, name, email, customer_segment, account_status}` | `SELECT customers WHERE id=?` |
| `get_order` | `(order_id, db)` | `{id, order_number, status, total_amount, currency, tracking_number, carrier, shipped_at, delivered_at}` | `SELECT orders WHERE id=?` |
| `request_approval` | `(action, conversation_id, customer_id, db, order_id, amount, currency, summary)` | `{outcome, approval_id, status, reason}` | SELECT order, SELECT customer_segment, INSERT approval + audit_log, INSERT/UPDATE workflow_state |
| `create_ticket` | `(customer_id, conversation_id, category, priority, summary, db)` | `{ticket_number, status}` | `INSERT support_tickets` |

`request_approval` outcomes:

| Outcome | Trigger |
|---|---|
| `auto_approve` | Refund ≤ segment threshold AND within return window; OR order status in {pending, processing} for cancellation |
| `approval_required` | Refund > threshold; OR order shipped; OR account change |
| `denied` | Order older than 30 days (refund); OR order delivered/cancelled/refunded (cancel) |

### 6.5 Policy Engine

| Action | Rule | Outcome |
|---|---|---|
| `issue_refund` | order_age_days > 30 | denied |
| `issue_refund` | amount ≤ standard=$50 / premium=$100 / enterprise=$200 | auto_approve |
| `issue_refund` | amount > threshold | approval_required |
| `cancel_order` | status in {pending, processing} | auto_approve |
| `cancel_order` | status = shipped | approval_required |
| `cancel_order` | status in {delivered, cancelled, refunded} | denied |
| `email_change` | always | approval_required |
| `address_change` | always | approval_required |
| unknown action | always | approval_required |

### 6.6 Agent Evaluation

The evaluation platform (`src/app/evaluation/`) assesses agent quality across three dimensions:

**Intent Accuracy**

| Metric | Definition |
|---|---|
| Intent Accuracy | `correct_intents / total_queries` — predicted intent matches expected intent |
| Outcome Accuracy | `correct_outcomes / total_queries` — agent chose the right action (retrieved vs. escalated vs. approved) |

**Groundedness** (see §5.10 — same metrics apply to agent responses)

- Context coverage ≥ 0.70 → response is grounded
- Mean context coverage and grounded rate tracked per evaluation run

**Retrieval Performance** (same metrics as §5.10)

- Recall@1, Recall@3, Recall@5, Recall@10
- Precision@1, Precision@3, Precision@5
- MRR
- nDCG@5, nDCG@10

**Regression Gate:** Any evaluation run that regresses Recall@5, nDCG@5, or MRR by more than 5% relative to the registered baseline fails the CI pipeline and blocks deployment.

---

## 7. Observability

All runtime events emit Prometheus metrics scraped at `/metrics`.

| Metric | Type | Labels | Buckets (s) |
|---|---|---|---|
| `http_requests_total` | Counter | method, path, status_code | — |
| `http_request_duration_seconds` | Histogram | method, path | 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10 |
| `agent_calls_total` | Counter | intent, outcome | — |
| `agent_latency_seconds` | Histogram | — | 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60 |
| `llm_calls_total` | Counter | model, outcome | — |
| `llm_latency_seconds` | Histogram | model | 0.5, 1, 2.5, 5, 10, 20, 30, 60 |
| `rag_retrievals_total` | Counter | strategy, outcome | — |
| `rag_latency_seconds` | Histogram | strategy | 0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5 |
| `ml_inferences_total` | Counter | task, outcome | — |
| `ml_latency_seconds` | Histogram | task | 0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25 |
| `approval_outcomes_total` | Counter | action, outcome | — |

Distributed tracing via OpenTelemetry (FastAPI, SQLAlchemy, Redis, Celery, httpx instrumentation) exported to Jaeger (`--profile observability`).

---

## 8. Key Dependencies

| Package | Version | Role |
|---|---|---|
| fastapi | ^0.104.0 | REST API framework |
| uvicorn | ^0.24.0 | ASGI server |
| sqlalchemy | ^2.0.0 | Async ORM |
| asyncpg | ^0.29.0 | Async PostgreSQL driver |
| alembic | ^1.12.0 | Database migrations |
| pgvector | ^0.2.4 | pgvector Python client |
| redis | ^5.0.0 | Redis client |
| celery | ^5.3.0 | Task queue |
| langgraph | ^0.0.30 | Agent workflow graph |
| langchain | ^0.1.0 | LLM utilities |
| sentence-transformers | ^2.2.0 | BGE embeddings + cross-encoder |
| rank-bm25 | ^0.2.2 | BM25 index |
| scikit-learn | ^1.3.0 | TF-IDF + classifiers |
| numpy | ^1.26.0 | Numerical arrays |
| pandas | ^2.1.0 | Data loading |
| ollama | ^0.1.0 | LLM client |
| PyJWT | ^2.8.0 | JWT authentication |
| passlib | ^1.7.0 | Password hashing (bcrypt) |
| prometheus-client | ^0.19.0 | Metrics export |
| opentelemetry-sdk | ^1.21.0 | Distributed tracing |
| loguru | ^0.7.0 | Structured logging |
| tenacity | ^8.2.0 | Retry logic |
| pydantic | ^2.5.0 | Data validation |
| pydantic-settings | ^2.1.0 | Config management |
