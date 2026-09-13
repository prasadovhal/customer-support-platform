#!/usr/bin/env python
"""Ingest the knowledge base: parse → chunk → embed → store in PostgreSQL.

Usage:
    python scripts/ingest_knowledge_base.py
    python scripts/ingest_knowledge_base.py --dry-run          # parse only, no DB writes
    python scripts/ingest_knowledge_base.py --kb-dir data/raw/knowledge_base
    python scripts/ingest_knowledge_base.py --force-reindex    # re-embed already-indexed docs
"""
from __future__ import annotations

import argparse
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from loguru import logger


KB_DIR = Path("data/raw/knowledge_base")
INDEX_VERSION = "1.0.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest knowledge base into PostgreSQL + pgvector")
    parser.add_argument("--kb-dir", default=str(KB_DIR), help="Knowledge base root directory")
    parser.add_argument("--dry-run", action="store_true", help="Parse and chunk only; skip DB writes")
    parser.add_argument("--force-reindex", action="store_true", help="Re-embed already-indexed documents")
    parser.add_argument("--batch-size", type=int, default=32, help="Embedding batch size")
    return parser.parse_args()


async def ingest(
    kb_dir: Path,
    dry_run: bool,
    force_reindex: bool,
    batch_size: int,
) -> None:
    from app.rag.chunker import Chunk, chunk_document, load_all_articles
    from app.rag.embedder import (
        EMBEDDING_DIM,
        EMBEDDING_MODEL,
        EMBEDDING_VERSION,
        EmbeddingService,
    )

    docs = load_all_articles(kb_dir)
    logger.info(f"Loaded {len(docs)} knowledge base articles from {kb_dir}")

    all_chunks: list[Chunk] = []
    for doc in docs:
        chunks = chunk_document(doc)
        all_chunks.extend(chunks)

    logger.info(f"Total chunks: {len(all_chunks)} from {len(docs)} documents")

    if dry_run:
        _print_dry_run_summary(docs, all_chunks)
        return

    # --- DB operations ---
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)

    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.orm import sessionmaker

    # Convert to async URL if needed
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)

    engine = create_async_engine(database_url, echo=False)
    AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    embedder = EmbeddingService()

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        from app.models.knowledge import EmbeddingMetadata, KnowledgeChunk, KnowledgeDocument

        docs_inserted = 0
        chunks_inserted = 0
        chunks_embedded = 0

        for doc in docs:
            meta = doc.metadata
            doc_path = doc.path

            # Check if document already exists
            existing = (
                await db.execute(
                    select(KnowledgeDocument).where(KnowledgeDocument.path == doc_path)
                )
            ).scalar_one_or_none()

            if existing and not force_reindex:
                logger.debug(f"Skipping already-indexed: {Path(doc_path).name}")
                continue

            # Parse effective dates
            eff_from_str = meta.get("effective_from", "2024-01-01")
            try:
                eff_from = datetime.fromisoformat(str(eff_from_str).replace("Z", "+00:00"))
            except ValueError:
                eff_from = datetime(2024, 1, 1, tzinfo=timezone.utc)

            eff_to = None
            if meta.get("effective_to"):
                try:
                    eff_to = datetime.fromisoformat(str(meta["effective_to"]).replace("Z", "+00:00"))
                except ValueError:
                    pass

            chunks = chunk_document(doc)
            if not chunks:
                continue

            # Upsert document record
            if existing:
                kb_doc = existing
                kb_doc.chunk_count = len(chunks)
                kb_doc.indexed_at = datetime.now(timezone.utc)
                kb_doc.index_version = INDEX_VERSION
                # Remove old chunks — cascade deletes embedding_metadata
                await db.execute(
                    select(KnowledgeChunk)
                    .where(KnowledgeChunk.doc_id == kb_doc.id)
                )
                from sqlalchemy import delete as sa_delete
                await db.execute(
                    sa_delete(KnowledgeChunk).where(KnowledgeChunk.doc_id == kb_doc.id)
                )
            else:
                kb_doc = KnowledgeDocument(
                    id=uuid.uuid4(),
                    path=doc_path,
                    category=meta.get("category", "unknown"),
                    title=meta.get("title", Path(doc_path).stem),
                    version=str(meta.get("version", "1.0")),
                    effective_from=eff_from,
                    effective_to=eff_to,
                    chunk_count=len(chunks),
                    indexed_at=datetime.now(timezone.utc),
                    index_version=INDEX_VERSION,
                    is_active=True,
                )
                db.add(kb_doc)
                await db.flush()
                docs_inserted += 1

            # Insert chunks
            chunk_objects = []
            for chunk in chunks:
                kc = KnowledgeChunk(
                    id=uuid.uuid4(),
                    doc_id=kb_doc.id,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    token_count=chunk.token_count,
                    chunk_version=chunk.chunk_version,
                )
                db.add(kc)
                chunk_objects.append(kc)
            await db.flush()
            chunks_inserted += len(chunk_objects)

            # Generate embeddings
            texts = [c.text for c in chunks]
            embeddings = embedder.embed_chunks(texts, batch_size=batch_size)

            for kc, emb in zip(chunk_objects, embeddings):
                em = EmbeddingMetadata(
                    id=uuid.uuid4(),
                    chunk_id=kc.id,
                    embedding_model=EMBEDDING_MODEL,
                    model_version=EMBEDDING_VERSION,
                    embedding_dim=EMBEDDING_DIM,
                    index_version=INDEX_VERSION,
                    embedded_at=datetime.now(timezone.utc),
                    embedding=emb.tolist(),
                )
                db.add(em)
            chunks_embedded += len(chunk_objects)

            await db.commit()
            logger.info(
                f"Ingested: {Path(doc_path).name} → {len(chunks)} chunks"
            )

    logger.info(
        f"Ingestion complete: {docs_inserted} documents, "
        f"{chunks_inserted} chunks, {chunks_embedded} embeddings"
    )


def _print_dry_run_summary(docs: list, chunks: list) -> None:
    from collections import Counter
    cat_counts = Counter(d.metadata.get("category", "unknown") for d in docs)
    chunk_per_doc = len(chunks) / max(len(docs), 1)
    print(f"\n{'='*60}")
    print(f"DRY RUN — No DB writes")
    print(f"Documents: {len(docs)}")
    print(f"Chunks:    {len(chunks)} (avg {chunk_per_doc:.1f}/doc)")
    print(f"\nBy category:")
    for cat, count in sorted(cat_counts.items()):
        print(f"  {cat:<20} {count} docs")
    print("=" * 60)


def main() -> None:
    args = parse_args()
    asyncio.run(
        ingest(
            kb_dir=Path(args.kb_dir),
            dry_run=args.dry_run,
            force_reindex=args.force_reindex,
            batch_size=args.batch_size,
        )
    )


if __name__ == "__main__":
    main()
