# ADR-002 — Vector Store: pgvector (V1 Baseline)

**Status:** Accepted (V1 baseline; review at RAG evaluation milestone)  
**Date:** 2026-09-07  
**Deciders:** Engineering Lead, Data Scientist  
**Supersedes:** —  
**Superseded by:** To be determined after retrieval benchmarking

---

## Context

The RAG pipeline requires a store capable of:
- Storing dense vector embeddings of knowledge base chunks.
- Approximate nearest-neighbour (ANN) similarity search at query time.
- Metadata filtering: by document category, effective date range, product scope, document version.
- Returning chunk IDs traceable back to source documents in PostgreSQL.

V1 knowledge base scale: approximately 100 Markdown articles, estimated 800–1,200 chunks at 512-token chunk size with 64-token overlap. This is a small corpus — the vector store choice at this scale is primarily an operational and architectural decision, not a performance one.

The retrieval pipeline uses hybrid retrieval (BM25 + dense + optional reranker). The vector store handles only the dense retrieval leg.

---

## Decision Drivers

| Driver | Weight | Notes |
|---|---|---|
| Operational simplicity (V1) | High | Minimize services; one database preferred |
| V1 corpus size fitness | High | ~1,000 chunks — no dedicated store needed |
| Metadata filtering | High | category, effective_date, product_scope |
| Retrieval quality at V1 scale | High | Must meet Recall@5 ≥ 0.80 baseline |
| Migration path (if needed) | Medium | Must be able to swap without redesign |
| Self-hostable / open-source | High | Project principle |
| Cost | Medium | No extra service → lower infra cost |
| ANN index types | Medium | IVFFlat sufficient for V1 scale |

---

## Considered Options

### Option A — pgvector (PostgreSQL extension)

Adds vector column type and ANN search operators to PostgreSQL. Same instance as transactional data.

**Pros:**
- Zero additional service to operate.
- Metadata filtering via standard SQL WHERE clause — highly expressive.
- Chunk metadata and embeddings in same transaction scope.
- HNSW index (pgvector ≥ 0.5) provides good recall at V1 scale.
- Embedding metadata (model, version, index_version) stored in same DB — no sync needed.

**Cons:**
- ANN search not as fast as dedicated stores at millions of vectors.
- Limited to PostgreSQL instance resources — vector search competes with transactional queries.
- Less operational tooling for vector-specific monitoring.

### Option B — Qdrant (dedicated vector database)

Purpose-built vector database with REST/gRPC API, HNSW indexing, rich payload filtering.

**Pros:**
- Excellent ANN performance at large scale.
- Rich filtering on arbitrary payload fields.
- Built-in collection management and snapshot/backup.
- Active open-source community.

**Cons:**
- Additional service to deploy, configure, monitor, and back up.
- Chunk metadata must be kept in sync between Qdrant (payload) and PostgreSQL (embedding_metadata table) — dual-write complexity.
- Overkill for V1 scale (~1,000 chunks).

### Option C — Weaviate

GraphQL-native vector database with multi-tenancy and hybrid search built-in.

**Pros:**
- Hybrid BM25 + vector search natively (no need for separate BM25 index).
- Multi-tenancy support.

**Cons:**
- Additional service.
- GraphQL API adds complexity vs. SQL-native filtering.
- Hybrid search being in-database reduces experimental control (can't independently tune BM25 vs. dense).
- Larger operational footprint than Qdrant.

### Option D — Chroma (in-process)

Embedded vector store, useful for prototyping.

**Pros:**
- Zero operational overhead for local dev.

**Cons:**
- Not production-suitable (no replication, no horizontal scale, no access control).
- Would require full swap for production.

---

## Decision

**Use pgvector (PostgreSQL extension) for V1.**

Install the `pgvector` extension on the existing PostgreSQL instance. Store chunk embeddings in a `chunk_embeddings` table with an HNSW index. Metadata filtering uses standard SQL WHERE clauses joining to `knowledge_chunks` and `knowledge_documents`.

**This decision is explicitly time-bounded.** It must be re-evaluated after retrieval benchmarking at the RAG phase (Phase 9). If pgvector fails to meet the Recall@5 ≥ 0.80 target or retrieval latency exceeds budget, this ADR is superseded.

---

## Rationale

At ~1,000 chunks, any vector store will return correct results. The decision is purely operational:
- pgvector adds zero new services to the Docker Compose stack and production deployment.
- SQL-native metadata filtering is more expressive than payload filtering in Qdrant for date-range and multi-field queries.
- The retrieval pipeline abstraction layer (see LLM-001 analogue for retrieval) means the vector store can be swapped without changing Agent Service logic.

The migration path to Qdrant or Weaviate is:
1. Stand up new vector store service.
2. Re-run embedding pipeline targeting new store.
3. Run retrieval evaluation on both — compare Recall@5, latency.
4. If new store wins → cut over; update ADR.

---

## Implementation Notes

```sql
-- pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Chunk embeddings table
CREATE TABLE chunk_embeddings (
    chunk_id        UUID PRIMARY KEY REFERENCES knowledge_chunks(id),
    embedding       VECTOR(1024),           -- dimension matches selected model
    embedding_model VARCHAR(100) NOT NULL,
    model_version   VARCHAR(50)  NOT NULL,
    indexed_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- HNSW index (pgvector >= 0.5)
CREATE INDEX chunk_embeddings_hnsw_idx
    ON chunk_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
```

**Retrieval query pattern:**

```sql
SELECT
    ce.chunk_id,
    kc.text,
    kd.category,
    kd.version,
    kd.effective_from,
    kd.effective_to,
    1 - (ce.embedding <=> $1::vector) AS similarity_score
FROM chunk_embeddings ce
JOIN knowledge_chunks kc ON ce.chunk_id = kc.id
JOIN knowledge_documents kd ON kc.doc_id = kd.id
WHERE
    kd.category = ANY($2)                            -- category filter
    AND kd.effective_from <= $3                       -- effective date filter
    AND (kd.effective_to IS NULL OR kd.effective_to >= $3)
ORDER BY ce.embedding <=> $1::vector
LIMIT 20;
```

---

## Consequences

**Positive:**
- Docker Compose stack: API + Worker + PostgreSQL + Redis + Ollama (no vector DB service).
- Single backup target covers both transactional and vector data.
- Metadata filtering expressed in SQL — no dual-write to keep payload in sync.

**Negative / Trade-offs:**
- Vector search runs inside PostgreSQL, competing for I/O and memory with transactional queries. At V1 scale this is not a concern; at 100k+ chunks it may require a read replica or partitioning.
- HNSW index build time increases with corpus size (rebuild required on embedding model change).

---

## Review Triggers

Revisit this ADR if:
- Retrieval benchmarking shows Recall@5 < 0.80 attributable to ANN quality (not chunking/model choice).
- P95 retrieval latency exceeds budget with pgvector on target hardware.
- Corpus grows beyond ~50,000 chunks.
- Filtering requirements become too complex for SQL (multi-vector, hybrid-native, multi-tenant).
