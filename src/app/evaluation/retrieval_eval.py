from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.evaluation.metrics import (
    RetrievalMetrics,
    compute_retrieval_metrics,
    ndcg_at_k,
    mrr as mrr_fn,
    precision_at_k,
    recall_at_k,
)
from app.rag.bm25_index import BM25Index, BM25Result
from app.rag.chunker import Chunk, chunk_document, load_all_articles


def _doc_id_from_path(path: str) -> str:
    """Extract the KB document ID from a file path.

    'data/raw/knowledge_base/returns/KB-RET-001.md' → 'KB-RET-001'
    """
    return Path(path).stem


@dataclass
class QueryResult:
    eval_id: str
    query: str
    relevant_ids: list[str]
    retrieved_ids: list[str]
    recall_at_1: float
    recall_at_3: float
    recall_at_5: float
    precision_at_5: float
    mrr: float
    ndcg_at_5: float
    difficulty: str = "unknown"
    query_type: str = "unknown"


@dataclass
class RetrievalEvalReport:
    eval_set: str
    retrieval_strategy: str
    metrics: RetrievalMetrics
    by_difficulty: dict[str, RetrievalMetrics] = field(default_factory=dict)
    by_query_type: dict[str, RetrievalMetrics] = field(default_factory=dict)
    per_query: list[QueryResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "eval_set": self.eval_set,
            "retrieval_strategy": self.retrieval_strategy,
            "metrics": self.metrics.to_dict(),
            "by_difficulty": {k: v.to_dict() for k, v in self.by_difficulty.items()},
            "by_query_type": {k: v.to_dict() for k, v in self.by_query_type.items()},
            "per_query": [asdict(q) for q in self.per_query],
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    def print_summary(self) -> None:
        m = self.metrics
        print(f"\n{'='*65}")
        print(f"Retrieval Evaluation: {self.eval_set}  [{self.retrieval_strategy}]")
        print(f"Queries: {m.n_queries}")
        print(f"{'-'*65}")
        print(f"  Recall@1 : {m.recall_at_1:.4f}")
        print(f"  Recall@3 : {m.recall_at_3:.4f}")
        print(f"  Recall@5 : {m.recall_at_5:.4f}   ← primary gate metric")
        print(f"  Recall@10: {m.recall_at_10:.4f}")
        print(f"  Prec@5   : {m.precision_at_5:.4f}")
        print(f"  MRR      : {m.mrr:.4f}")
        print(f"  nDCG@5   : {m.ndcg_at_5:.4f}")
        print(f"  nDCG@10  : {m.ndcg_at_10:.4f}")
        if self.by_difficulty:
            print("\n  By difficulty:")
            for diff, dm in sorted(self.by_difficulty.items()):
                print(
                    f"    {diff:<10} R@5={dm.recall_at_5:.3f}  MRR={dm.mrr:.3f}  nDCG@5={dm.ndcg_at_5:.3f}  (n={dm.n_queries})"
                )
        if self.by_query_type:
            print("\n  By query type:")
            for qtype, qm in sorted(self.by_query_type.items()):
                print(
                    f"    {qtype:<15} R@5={qm.recall_at_5:.3f}  MRR={qm.mrr:.3f}  (n={qm.n_queries})"
                )
        print("=" * 65)


def _build_offline_bm25(kb_dir: Path) -> tuple[BM25Index, list[Chunk]]:
    """Build a BM25 index directly from KB files (no DB required)."""
    docs = load_all_articles(kb_dir)
    all_chunks: list[Chunk] = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc))

    records = [
        BM25Result(
            chunk_id=f"{_doc_id_from_path(c.doc_path)}_{c.chunk_index}",
            score=0.0,
            text=c.text,
            doc_title=c.doc_metadata.get("title", ""),
            doc_category=c.doc_metadata.get("category", ""),
            doc_path=c.doc_path,
            chunk_index=c.chunk_index,
        )
        for c in all_chunks
    ]
    bm25 = BM25Index()
    bm25.build(records)
    return bm25, all_chunks


def _retrieve_bm25(bm25: BM25Index, query: str, top_k: int = 10) -> list[str]:
    """Return document IDs (KB-XXX-YYY) for the top-k BM25 results."""
    results = bm25.search(query, top_k=top_k)
    seen: list[str] = []
    for record, _ in results:
        doc_id = _doc_id_from_path(record.doc_path)
        if doc_id not in seen:
            seen.append(doc_id)
    return seen


def _slice_per_group(
    per_query: list[QueryResult], group_key: str
) -> dict[str, RetrievalMetrics]:
    """Compute metrics grouped by a field (difficulty or query_type)."""
    groups: dict[str, list[tuple[list[str], list[str]]]] = {}
    for qr in per_query:
        key = getattr(qr, group_key, "unknown")
        groups.setdefault(key, []).append((qr.retrieved_ids, qr.relevant_ids))
    return {k: compute_retrieval_metrics(v) for k, v in groups.items()}


def evaluate_bm25_offline(
    eval_records: list[dict],
    kb_dir: Path,
    top_k: int = 10,
    eval_set_name: str = "golden_qa",
) -> RetrievalEvalReport:
    """Offline BM25 retrieval evaluation — no DB required.

    Uses the knowledge base files directly to build the index and evaluate.
    """
    bm25, _ = _build_offline_bm25(kb_dir)

    per_query: list[QueryResult] = []
    pairs: list[tuple[list[str], list[str]]] = []

    for rec in eval_records:
        query = rec.get("question") or rec.get("query", "")
        relevant = rec.get("expected_document_ids") or rec.get(
            "relevant_document_ids", []
        )
        eval_id = rec.get("qa_id") or rec.get("eval_id", "")
        difficulty = rec.get("difficulty", "unknown")
        query_type = rec.get("query_type") or rec.get("intent", "unknown")

        if not query or not relevant:
            continue

        retrieved = _retrieve_bm25(bm25, query, top_k=top_k)
        pairs.append((retrieved, relevant))

        per_query.append(
            QueryResult(
                eval_id=eval_id,
                query=query,
                relevant_ids=relevant,
                retrieved_ids=retrieved,
                recall_at_1=recall_at_k(retrieved, relevant, 1),
                recall_at_3=recall_at_k(retrieved, relevant, 3),
                recall_at_5=recall_at_k(retrieved, relevant, 5),
                precision_at_5=precision_at_k(retrieved, relevant, 5),
                mrr=mrr_fn(retrieved, relevant),
                ndcg_at_5=ndcg_at_k(retrieved, relevant, 5),
                difficulty=difficulty,
                query_type=query_type,
            )
        )

    metrics = compute_retrieval_metrics(pairs)
    by_difficulty = _slice_per_group(per_query, "difficulty")
    by_query_type = _slice_per_group(per_query, "query_type")

    return RetrievalEvalReport(
        eval_set=eval_set_name,
        retrieval_strategy="bm25_offline",
        metrics=metrics,
        by_difficulty=by_difficulty,
        by_query_type=by_query_type,
        per_query=per_query,
    )
