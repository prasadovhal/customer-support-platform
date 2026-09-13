# ADR-004 — Reranker Model Selection

**Status:** Accepted  
**Date:** 2026-09-13  
**Deciders:** Engineering Lead  
**Supersedes:** —  
**Superseded by:** —

---

## Context

The hybrid retrieval pipeline (ADR-003) returns a fused candidate set of up to 20 chunks. These chunks are ranked by RRF score, which is based on retrieval-list rank rather than query-document relevance. A reranking step can significantly improve precision by directly scoring each candidate against the query using a cross-attention model.

The trade-off is latency: a cross-encoder must score each candidate independently (no batch embedding trick), so a reranker over 20 candidates adds meaningful inference time. For V1, the reranker is designed as an **optional quality gate** that can be enabled or disabled per request type.

The reranker sits between the retrieval layer and the LLM context window:

```
Hybrid retrieval → top-20 candidates → reranker → top-5 → LLM context
```

The LLM context window budget is directly affected by reranking quality: 5 highly relevant chunks improve generation groundedness (FR-005, EVAL-003) while consuming less context than 20 mixed-quality chunks.

---

## Decision Drivers

| Driver | Weight | Notes |
|---|---|---|
| Reranking precision improvement | High | Direct impact on groundedness (FR-005, target ≥ 0.90) |
| Self-hostable / open-weight | High | Project principle |
| Inference latency | High | Must fit within 8s P95 SLO with margin for LLM call |
| VRAM / CPU requirements | Medium | Dev hardware may not have large GPU |
| License | High | Must be permissive for commercial use |
| sentence-transformers compatibility | Medium | Already in pyproject.toml |

---

## Considered Options

| Option | Precision gain | Latency (20 docs) | Self-hosted | VRAM | License |
|---|---|---|---|---|---|
| No reranking (RRF order) | Baseline | 0ms | N/A | 0 | N/A |
| BM25 score re-sort | Marginal | <1ms | Yes | 0 | N/A |
| **cross-encoder/ms-marco-MiniLM-L-6-v2** | High | ~50ms | Yes | ~100MB | Apache 2.0 |
| cross-encoder/ms-marco-MiniLM-L-12-v2 | Higher | ~100ms | Yes | ~200MB | Apache 2.0 |
| cross-encoder/ms-marco-electra-base | Very high | ~200ms | Yes | ~450MB | Apache 2.0 |
| LLM-based reranking (GPT-4 / LLaMA) | Very high | 1–5s | Depends | High | Varies |

---

## Decision

Use **`cross-encoder/ms-marco-MiniLM-L-6-v2`** via `sentence-transformers` as the V1 reranker.

- Model: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Library: `sentence-transformers` (already in pyproject.toml)
- Input: query + chunk text pairs
- Output: relevance score per pair
- Pipeline position: after hybrid retrieval (top-20 candidates), before LLM context construction
- Reranker is **enabled by default** but can be bypassed via a feature flag in config when latency is the priority

### Serving

The cross-encoder runs in-process on CPU within the API/worker service. It does not require a separate service or GPU at V1 scale (~100 chunks, ~1,000 queries/day).

### Top-K Selection

After reranking, pass top-5 chunks to the LLM context. This is configurable in the policy store and can be increased to top-8 for complex multi-document queries.

---

## Rationale

**Why cross-encoder over no reranking:**  
Cross-encoders jointly encode query and document (unlike bi-encoder dense retrievers) and produce a relevance score that directly models query-document relevance. Precision@5 improvements of 10–20% over retrieval-only approaches are typical in customer support QA benchmarks. Given the groundedness target of ≥ 0.90 (FR-005), improving precision of context chunks directly improves generation quality.

**Why MiniLM-L-6-v2 over larger cross-encoders:**  
The L-6 model (6 transformer layers, ~22M parameters) delivers a strong precision improvement at ~50ms latency on CPU for 20 candidates — well within the headroom of the 8s P95 SLO after accounting for BM25 + dense retrieval (~30ms combined) and LLM inference (~2–5s). The L-12 and ELECTRA models offer marginal quality improvement at 2–4× the latency cost, which is not justified for V1.

**Why not LLM-based reranking:**  
LLM-based reranking (using the same LLM as a relevance judge) adds 1–5s of additional latency per reranking pass, pushing the total pipeline well above the P95 SLO. It is a Phase 22 experimentation candidate for async or offline evaluation workflows.

**Why not BM25 re-sort:**  
BM25 score re-sorting is redundant after the hybrid retrieval step already incorporates BM25 signal via RRF. It would not materially improve precision.

---

## Consequences

**Positive:**
- Direct improvement in context precision, expected to raise groundedness scores toward the ≥ 0.90 target.
- CPU-only inference — no GPU required for development or low-volume production.
- Apache 2.0 license — no restrictions on commercial use or self-hosting.
- Already compatible with the `sentence-transformers` library in pyproject.toml.
- The reranker is a localized component: switching to a different model requires only changing the model name string.

**Negative / Trade-offs:**
- Adds ~50ms to the synchronous request path. For the 8s P95 SLO this is acceptable, but latency-sensitive deployments may want to disable it for low-complexity queries.
- Cross-encoder inference does not scale as cheaply as retrieval at high query volume; at scale, a dedicated GPU instance or batching strategy becomes necessary.
- Model loading time (~1s) must be managed via warm startup; cold-start penalty hits the first request after deployment.

**Risks and Mitigations:**
- Latency regression at high concurrency: mitigated by load testing during Phase 24; the bypass flag allows disabling reranking for degraded-mode operation (REL-004).
- Model quality on support-specific language: mitigated by EVAL-002 measurement; if the reranker does not improve Precision@5 on the retrieval evaluation dataset, it can be removed.

---

## Review Triggers

Revisit this ADR if:
- EVAL-002 benchmarking shows the reranker does not improve Precision@5 or MRR on the domain evaluation set.
- Query volume exceeds ~500 queries/minute, at which point in-process CPU inference becomes a bottleneck.
- A newer MiniLM variant or domain-specific cross-encoder shows significantly better performance without latency regression.
