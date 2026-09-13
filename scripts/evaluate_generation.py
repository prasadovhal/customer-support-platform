#!/usr/bin/env python
"""Evaluate RAG generation quality (groundedness) against the golden QA set.

Uses lexical groundedness scoring (context coverage + token F1) — no LLM required.
For LLM-graded correctness, set OLLAMA_BASE_URL and pass --llm-grade.

Usage:
    python scripts/evaluate_generation.py
    python scripts/evaluate_generation.py --top-k 5
    python scripts/evaluate_generation.py --save-baseline
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from loguru import logger

GOLDEN_QA_PATH = Path("data/evaluation/golden_qa.jsonl")
RESULTS_DIR = Path("data/evaluation/results")
BASELINE_PATH = Path("data/evaluation/baselines/groundedness_baseline.json")
KB_DIR = Path("data/raw/knowledge_base")


def load_jsonl(path: Path) -> list[dict]:
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate RAG generation groundedness")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--save-baseline", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records = load_jsonl(GOLDEN_QA_PATH)
    logger.info(f"Loaded {len(records)} golden QA records")

    from app.evaluation.groundedness import (
        aggregate_groundedness,
        score_groundedness,
    )
    from app.evaluation.retrieval_eval import (
        _build_offline_bm25,
        _doc_id_from_path,
        _retrieve_bm25,
    )
    from app.rag.pipeline import _build_context
    from app.rag.retriever import RetrievalResult

    bm25, all_chunks = _build_offline_bm25(KB_DIR)

    # Build chunk lookup: doc_id → list of Chunk
    chunk_map: dict[str, list] = {}
    for c in all_chunks:
        did = _doc_id_from_path(c.doc_path)
        chunk_map.setdefault(did, []).append(c)

    results = []
    for rec in records:
        if not rec.get("requires_retrieval", True):
            continue

        qa_id = rec["qa_id"]
        question = rec["question"]
        expected_answer = rec.get("expected_answer", "")
        expected_docs = rec.get("expected_document_ids", [])

        retrieved_doc_ids = _retrieve_bm25(bm25, question, top_k=args.top_k)

        # Build context from retrieved chunk text
        context_chunks = []
        for doc_id in retrieved_doc_ids:
            for c in chunk_map.get(doc_id, [])[:1]:  # first chunk per doc
                context_chunks.append(
                    RetrievalResult(
                        chunk_id=f"{doc_id}_0",
                        chunk_index=c.chunk_index,
                        text=c.text,
                        doc_id=doc_id,
                        doc_title=c.doc_metadata.get("title", ""),
                        doc_category=c.doc_metadata.get("category", ""),
                        doc_path=c.doc_path,
                        doc_version=str(c.doc_metadata.get("version", "1.0")),
                        rrf_score=1.0,
                    )
                )

        context = _build_context(context_chunks, max_chars=4000)
        result = score_groundedness(
            qa_id=qa_id,
            question=question,
            expected_answer=expected_answer,
            context=context,
            expected_doc_ids=expected_docs,
            retrieved_doc_ids=retrieved_doc_ids,
        )
        results.append(result)

    agg = aggregate_groundedness(results)

    print(f"\n{'='*65}")
    print(f"Generation Evaluation: golden_qa  [bm25_offline, top_k={args.top_k}]")
    print(f"Queries evaluated: {agg['n_queries']}")
    print(f"{'-'*65}")
    print(f"  Context coverage   : {agg['mean_context_coverage']:.4f}  (answer tokens in context)")
    print(f"  Answer-context F1  : {agg['mean_answer_context_f1']:.4f}  (token F1)")
    print(f"  Doc ID hit rate    : {agg['doc_id_hit_rate']:.4f}  (retrieved ∩ expected docs)")
    print(f"  Grounded rate      : {agg['grounded_rate']:.4f}  (coverage ≥ 0.70)")
    print(f"  Target (FR-005)    : groundedness ≥ 0.90")
    print("=" * 65)

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = {
        "eval_set": "golden_qa",
        "retrieval_strategy": f"bm25_offline_top{args.top_k}",
        "aggregate": agg,
        "per_query": [
            {
                "qa_id": r.qa_id,
                "context_coverage": r.context_coverage,
                "answer_context_f1": r.answer_context_f1,
                "doc_id_hit": r.doc_id_hit,
                "grounded": r.grounded,
            }
            for r in results
        ],
    }
    out_path = RESULTS_DIR / "generation_groundedness.json"
    with open(out_path, "w") as f:
        json.dump(out, f, indent=2)
    logger.info(f"Results saved → {out_path}")

    if args.save_baseline:
        BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(BASELINE_PATH, "w") as f:
            json.dump(agg, f, indent=2)
        logger.info(f"Groundedness baseline saved → {BASELINE_PATH}")


if __name__ == "__main__":
    main()
