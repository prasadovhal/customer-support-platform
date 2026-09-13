"""Add embedding vector column and HNSW index for RAG pipeline.

Revision ID: 002
Revises: 001
Create Date: 2026-09-13 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # pgvector extension already created in 001; ensure it's present
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Add embedding vector column to embedding_metadata
    op.execute(
        "ALTER TABLE embedding_metadata ADD COLUMN IF NOT EXISTS embedding vector(768)"
    )

    # HNSW index for fast approximate nearest-neighbour cosine search
    # m=16, ef_construction=64 are standard defaults balancing build time vs recall
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_embedding_metadata_hnsw
        ON embedding_metadata
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_embedding_metadata_hnsw")
    op.execute(
        "ALTER TABLE embedding_metadata DROP COLUMN IF EXISTS embedding"
    )
