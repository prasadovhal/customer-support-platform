# ADR-003 — Hybrid Retrieval Strategy and Fusion Method

**Status:** Accepted  
**Date:** 2026-09-13  
**Deciders:** Engineering Lead  
**Supersedes:** —  
**Superseded by:** —

---

## Context

The platform must retrieve relevant knowledge articles when answering customer questions about policies, procedures, and troubleshooting guidance (FR-004). The knowledge base contains ~100 articles with deliberate complexity: overlapping documents, temporal versioning, product-specific rules, and ambiguous phrasing.

Two retrieval paradigms are commonly used:

- **Lexical / sparse retrieval (BM25)**: matches exact and near-exact terms. Strong when the query contains specific technical terms, product names, or policy identifiers. Fails when the customer uses different terminology than the document (vocabulary mismatch).
- **Dense / semantic retrieval**: matches meaning regardless of surface phrasing. Handles paraphrase and vocabulary mismatch. Can miss documents that contain exact relevant terms but are not semantically close to the query under the embedding model's representation.

Customer support queries exhibit both patterns: "my parcel hasn't arrived" (semantic match on delivery failure) and "30-day return window" (exact policy term). A hybrid approach that combines both signals is well-established in the retrieval literature and is the approach taken here.

The fusion method (how to combine two ranked lists) also requires a decision. The main options are:

1. **Score normalization + linear combination**: requires tuning a mixing coefficient α.
2. **Reciprocal Rank Fusion (RRF)**: parameter-free rank combination formula.

---

## Decision Drivers

| Driver | Weight | Notes |
|---|---|---|
| Retrieval quality (Recall@5, MRR) | High | Primary requirement from EVAL-002 |
| Vocabulary coverage | High | Customer phrasing ≠ document phrasing |
| Zero-parameter baseline | High | Avoid premature tuning before evaluation data exists |
| Alignment with EMB-002 (embedding versioning) | High | Must support controlled embedding changes |
| Latency budget | Medium | Retrieval + reranking must fit in 8s P95 SLO |
| Reproducibility | Medium | Results must be stable across runs for evaluation |
| Implementation complexity | Medium | Minimize components for V1 |

---

## Considered Options

| Option | Vocabulary coverage | Semantic coverage | Tuning required | Latency | Implementation |
|---|---|---|---|---|---|
| BM25 only | Excellent | Poor | None | Very low | Simple |
| Dense only (embedding) | Poor | Excellent | None | Low | Moderate |
| Hybrid: score normalization + linear | Good | Good | α coefficient | Low | Moderate |
| **Hybrid: BM25 + Dense with RRF** | Good | Good | None | Low | Moderate |
| Learned sparse (SPLADE) | Excellent | Good | Training required | Medium | High |
| Multi-stage cascaded | Excellent | Excellent | Multiple params | High | High |

---

## Decision

Use **hybrid retrieval (BM25 + dense vector search) fused with Reciprocal Rank Fusion (RRF)** as the V1 baseline retrieval strategy.

### RRF Formula

```
RRF_score(d) = Σ_r 1 / (k + rank_r(d))
```

Where `k = 60` (standard constant that dampens high-rank documents), `rank_r(d)` is the rank of document `d` in retrieval list `r`. Each retrieval list independently ranks up to N candidates; documents not appearing in a list receive rank = N+1.

### V1 Pipeline

```
Query
  ├── BM25 (rank-bm25)       → top-20 ranked chunks
  └── Dense (pgvector ANN)   → top-20 ranked chunks
        ↓
  RRF fusion                 → top-20 combined candidates
        ↓
  Optional cross-encoder     → top-5 (see ADR-004)
        ↓
  LLM context window
```

### Implementation

- BM25 index: `rank-bm25` library (already in pyproject.toml), built over chunk text at indexing time.
- Dense index: pgvector (ADR-002), ANN query using `<=>` cosine operator.
- RRF fusion: applied in Python after fetching both ranked lists; no external service required.
- Chunk metadata (document_id, section, effective_from/to, category, product_scope) preserved through fusion for source attribution (FR-005).

---

## Rationale

**Why hybrid over BM25 alone:**  
Customer queries frequently paraphrase policy language. "I want my money back" will not lexically match "refund processing timeline" — dense retrieval bridges this gap. Recall@5 improvements of 5–15% over single-retriever baselines are consistently reported in the information retrieval literature for domain-specific corpora.

**Why hybrid over dense alone:**  
Exact product names, order identifiers, and specific policy clauses (e.g., "30-day return window") benefit from exact match. Dense retrieval alone can retrieve semantically similar but factually different documents (e.g., a 30-day warranty clause when the customer asked about the 30-day return policy).

**Why RRF over score normalization:**  
Score normalization requires a known score distribution per retriever; BM25 and cosine similarity scores operate on incompatible scales and distributions that vary by corpus and query. Selecting an α coefficient without an evaluation dataset introduces an unvalidated tuning decision. RRF avoids this entirely: it operates on ranks, not scores, and the k=60 constant has been shown to be robust across a wide range of retrieval tasks. This gives a stable, reproducible baseline before the evaluation infrastructure (EVAL-002) has been built.

**Why not SPLADE:**  
SPLADE requires training a sparse encoder on in-domain data. The synthetic knowledge base does not yet have sufficient coverage to train a reliable sparse encoder. SPLADE is a Phase 22 experimentation candidate.

---

## Consequences

**Positive:**
- Zero-parameter baseline eliminates a tuning decision before evaluation data is available.
- Complementary retrieval signals improve coverage over either retriever alone.
- RRF scores are interpretable (relative rank combination, not opaque embeddings).
- BM25 index is CPU-only and adds negligible latency (<5ms for 1,000 chunks).
- Consistent with the EVAL-002 requirement: Recall@5, MRR, nDCG can be measured on the existing retrieval evaluation dataset.

**Negative / Trade-offs:**
- Two retrieval calls per query increases latency by ~10–30ms over a single-retriever approach (acceptable within the 8s P95 SLO).
- RRF does not weight individual retrievers; a higher-quality dense retriever cannot be given proportionally more influence without switching to score normalization.
- BM25 index must be rebuilt when the knowledge base changes; this is handled by the ingestion pipeline.

**Risks and Mitigations:**
- RRF sub-optimal for a highly skewed corpus: mitigated by EVAL-002 benchmarking; if RRF underperforms score normalization after evaluation, the fusion method can be changed without modifying the retrieval stack.
- Dense retrieval quality depends on embedding model selection (ADR-006); a weak embedding model reduces hybrid quality.

---

## Review Triggers

Revisit this ADR if:
- EVAL-002 benchmarking shows a single retriever outperforming hybrid by a statistically significant margin.
- Score normalization achieves meaningfully higher Recall@5 than RRF after evaluation data is available.
- Query distribution analysis shows strongly skewed lexical or semantic query types that benefit from a different fusion strategy.
