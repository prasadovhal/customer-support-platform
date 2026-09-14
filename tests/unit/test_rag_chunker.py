from __future__ import annotations

from pathlib import Path
from textwrap import dedent


from app.rag.chunker import (
    CHUNK_SIZE,
    Chunk,
    ParsedDocument,
    chunk_document,
    parse_article,
)


SAMPLE_ARTICLE = dedent(
    """\
    ---
    document_id: KB-TEST-001
    title: Test Return Policy
    category: returns
    version: "1.0"
    effective_from: "2026-01-01"
    ---

    # Test Return Policy

    You can return most items within 30 days of purchase.

    ## Conditions

    Items must be:
    - Unused
    - In original packaging
    - With receipt

    ## Exclusions

    The following cannot be returned:
    - Digital downloads
    - Perishable goods
"""
)


def test_parse_article_extracts_metadata(tmp_path: Path) -> None:
    f = tmp_path / "KB-TEST-001.md"
    f.write_text(SAMPLE_ARTICLE, encoding="utf-8")
    doc = parse_article(f)
    assert doc.metadata["title"] == "Test Return Policy"
    assert doc.metadata["category"] == "returns"
    assert "# Test Return Policy" in doc.body


def test_parse_article_no_frontmatter(tmp_path: Path) -> None:
    f = tmp_path / "plain.md"
    f.write_text("# Just a title\n\nSome content.", encoding="utf-8")
    doc = parse_article(f)
    assert doc.metadata == {}
    assert "Just a title" in doc.body


def test_chunk_document_returns_list() -> None:
    doc = ParsedDocument(
        path="test.md",
        metadata={"category": "returns", "title": "Test"},
        body="This is a test document. " * 20,
    )
    chunks = chunk_document(doc)
    assert isinstance(chunks, list)
    assert len(chunks) >= 1
    assert all(isinstance(c, Chunk) for c in chunks)


def test_chunk_document_preserves_index_order() -> None:
    doc = ParsedDocument(
        path="test.md",
        metadata={},
        body="\n\n".join([f"Section {i}. " + "Content. " * 50 for i in range(10)]),
    )
    chunks = chunk_document(doc)
    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(chunks)))


def test_chunk_document_respects_chunk_size() -> None:
    long_body = "word " * 2000
    doc = ParsedDocument(path="test.md", metadata={}, body=long_body)
    chunks = chunk_document(doc)
    for chunk in chunks:
        assert (
            len(chunk.text) <= CHUNK_SIZE * 1.2
        )  # allow small overage at word boundaries


def test_chunk_document_token_count_estimated() -> None:
    doc = ParsedDocument(
        path="test.md",
        metadata={},
        body="Hello world this is a test.",
    )
    chunks = chunk_document(doc)
    assert chunks[0].token_count >= 1


def test_chunk_document_empty_body() -> None:
    doc = ParsedDocument(path="test.md", metadata={}, body="")
    chunks = chunk_document(doc)
    assert chunks == []
