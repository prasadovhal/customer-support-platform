# ADR-006 — Embedding Model Selection

**Status:** Accepted  
**Date:** 2026-09-13  
**Deciders:** Engineering Lead  
**Supersedes:** —  
**Superseded by:** —

---

## Context

Dense retrieval (ADR-003) requires an embedding model to encode both knowledge base chunks and incoming customer queries into vector representations. The embedding model directly determines the quality of semantic retrieval: chunks and queries that should be considered relevant must map to nearby vectors in the embedding space.

The embedding model is a **long-lived infrastructure decision**: once chunks are indexed with a given model, a model change requires full re-indexing of the knowledge base and re-evaluation of retrieval quality (EMB-002). Early selection of a high-quality, stable model reduces operational churn.

Requirements specific to this project:

- **Self-hostable**: must run locally via the `sentence-transformers` library or equivalent (LLM-002 principle: open-weight, self-hosted development stack).
- **Embedding versioning**: every indexed chunk must carry `embedding_model_id`, `embedding_version`, and `embedding_config` (EMB-002). This is a data-layer requirement independent of model choice.
- **Domain relevance**: the model must handle customer support language well: informal queries, product names, policy phrasing, and mixed technical/conversational text.
- **Latency**: embedding must complete within the retrieval latency budget (~30ms for the full retrieval step).

---

## Decision Drivers

| Driver | Weight | Notes |
|---|---|---|
| Retrieval quality (MTEB English Retrieval) | High | Primary proxy for in-domain performance before evaluation |
| Open-weight / permissive license | High | Project principle; must be self-hostable |
| Sentence-transformers compatibility | High | Already in pyproject.toml |
| Embedding dimension / pgvector storage | Medium | Lower dimension = faster ANN search and less storage |
| Memory footprint | Medium | Must run on development hardware (CPU + optional GPU) |
| Stability of model weights | Medium | Avoid frequent re-indexing due to model updates |

---

## Considered Options

| Model | MTEB Retrieval Avg | Dim | Size | License | Notes |
|---|---|---|---|---|---|
| OpenAI text-embedding-3-small | ~62 | 1536 | API-only | Proprietary | API dependency, cost per token |
| OpenAI text-embedding-ada-002 | ~61 | 1536 | API-only | Proprietary | Older, API-only |
| all-MiniLM-L6-v2 | ~41 | 384 | ~80MB | Apache 2.0 | Fast, weaker retrieval |
| all-mpnet-base-v2 | ~57 | 768 | ~420MB | Apache 2.0 | Good baseline |
| **BAAI/bge-base-en-v1.5** | ~63 | 768 | ~440MB | MIT | Strong MTEB, supports query prefix |
| BAAI/bge-large-en-v1.5 | ~64 | 1024 | ~1.3GB | MIT | Marginal gain, 3× larger |
| intfloat/e5-base-v2 | ~61 | 768 | ~440MB | MIT | Competitive; requires "query: " prefix |
| hkunlp/instructor-base | ~60 | 768 | ~440MB | Apache 2.0 | Task-specific prefix, harder to operationalize |

*MTEB scores are approximate averages from the MTEB English Retrieval benchmark.*

---

## Decision

Use **`BAAI/bge-base-en-v1.5`** via `sentence-transformers` as the V1 baseline embedding model.

### Configuration

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-base-en-v1.5")

# Query encoding requires the BGE instruction prefix
query_prefix = "Represent this sentence for searching relevant passages: "
query_embedding = model.encode(query_prefix + query_text)

# Document/chunk encoding does not require a prefix
chunk_embedding = model.encode(chunk_text)
```

### Embedding Metadata (EMB-002 compliance)

Every indexed chunk stores:
```json
{
  "embedding_model_id": "BAAI/bge-base-en-v1.5",
  "embedding_version": "1.5",
  "embedding_dim": 768,
  "feature_version": "1.0.0",
  "indexed_at": "<ISO timestamp>"
}
```

### Vector Storage

768-dimensional float32 vectors stored in pgvector (ADR-002). ANN search via HNSW index (`vector_cosine_ops`).

---

## Rationale

**Why BGE-base-en-v1.5 over OpenAI embeddings:**  
OpenAI embeddings require an API call for every query and every indexed chunk. This introduces network latency, per-token cost, an external dependency for both indexing and retrieval, and a data residency concern (customer query text sent to a third party). BGE-base achieves comparable or better MTEB retrieval scores while running locally.

**Why BGE-base-en-v1.5 over all-MiniLM-L6-v2:**  
MiniLM-L6 is significantly weaker on retrieval benchmarks (~41 vs ~63 MTEB average). The smaller 384-dim vectors offer speed benefits, but the quality gap is too large for a production retrieval system targeting ≥ 0.90 groundedness.

**Why BGE-base over BGE-large:**  
BGE-large offers ~1 point improvement in MTEB retrieval scores at 3× the model size and ~2× the inference latency. The marginal quality gain does not justify the resource cost for V1. BGE-large is a Phase 22 experimentation candidate.

**Why BGE-base over e5-base:**  
Both are competitive. BGE-base was chosen due to better-documented behavior with the query instruction prefix, MIT license (vs Apache 2.0 — both permissive, but MIT is less ambiguous), and wider adoption in sentence-transformers tutorials that match this project's tech stack.

**Why not instructor-base:**  
The instructor model requires task-specific instruction strings that vary by use case, complicating the embedding pipeline. For a unified support retrieval use case, BGE's single query prefix is simpler and more operationally predictable.

---

## Consequences

**Positive:**
- MIT license: no restrictions on self-hosted commercial use.
- Runs on CPU; ~440MB model load into memory at service startup.
- `sentence-transformers` library already in pyproject.toml — no additional dependencies.
- MTEB scores provide a pre-evaluation quality proxy before domain-specific evaluation is complete.
- 768-dimensional vectors are well-supported by pgvector HNSW indexes.

**Negative / Trade-offs:**
- BGE requires a specific query instruction prefix for optimal performance; chunk encoding does not. This asymmetry must be consistently applied at both indexing and query time.
- Model cold-load takes ~1s; must be loaded at service startup, not lazily.
- Embedding model changes require full knowledge-base re-indexing and EVAL-002 re-evaluation.

**Risks and Mitigations:**
- Query/chunk prefix inconsistency: mitigated by encapsulating embedding logic in a single `EmbeddingService` class that enforces the prefix rule.
- Model performance on support-specific language not yet validated: mitigated by EVAL-002 retrieval evaluation against the domain evaluation dataset before promotion to production.
- MTEB benchmark contamination (model was likely trained on MTEB test sets): mitigated by evaluating on the project's own domain-specific retrieval evaluation set (EVAL-002).

---

## Review Triggers

Revisit this ADR if:
- EVAL-002 domain evaluation shows BGE-base significantly underperforming an alternative on domain-specific retrieval quality.
- The knowledge base grows beyond ~50,000 chunks, at which point ANN search performance at 768 dimensions may require a smaller dimension or dedicated vector store (ADR-002 review trigger).
- A superior open-weight model emerges in the 400–500MB size class with materially better retrieval quality.
