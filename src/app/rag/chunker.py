from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# PyYAML is available as a transitive dependency (via langchain)
import yaml  # type: ignore[import-untyped]

CHUNK_SIZE = 1500  # characters (~400 tokens at 3.75 chars/token)
CHUNK_OVERLAP = 200  # characters
CHUNK_VERSION = "1.0.0"

# Separators in priority order — split on paragraph breaks first, then lines, then words
_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]


@dataclass
class ParsedDocument:
    path: str
    metadata: dict[str, Any]
    body: str


@dataclass
class Chunk:
    doc_path: str
    chunk_index: int
    text: str
    token_count: int
    chunk_version: str
    doc_metadata: dict[str, Any]


def parse_article(path: Path) -> ParsedDocument:
    """Parse a knowledge base markdown file into metadata + body."""
    raw = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", raw, re.DOTALL)
    if match:
        try:
            metadata = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError:
            metadata = {}
        body = raw[match.end() :]
    else:
        metadata = {}
        body = raw
    return ParsedDocument(path=str(path), metadata=metadata, body=body.strip())


def _estimate_tokens(text: str) -> int:
    """Fast token estimate: 1 token ≈ 3.75 characters."""
    return max(1, len(text) // 4)


def _split_recursive(
    text: str, separators: list[str], chunk_size: int, chunk_overlap: int
) -> list[str]:
    """Recursively split text using the separator list, smallest unit last."""
    if not text:
        return []

    for sep in separators:
        if sep == "" or sep in text:
            parts = text.split(sep) if sep else list(text)
            chunks: list[str] = []
            current = ""

            for part in parts:
                candidate = (current + sep + part).lstrip(sep) if current else part
                if len(candidate) <= chunk_size:
                    current = candidate
                else:
                    if current:
                        chunks.append(current)
                        # Overlap: start new chunk with tail of previous
                        overlap_start = max(0, len(current) - chunk_overlap)
                        current = current[overlap_start:] + sep + part if sep else part
                    else:
                        # Part alone exceeds chunk_size — recurse with smaller separator
                        remaining_seps = separators[separators.index(sep) + 1 :]
                        if remaining_seps:
                            chunks.extend(
                                _split_recursive(
                                    part, remaining_seps, chunk_size, chunk_overlap
                                )
                            )
                        else:
                            chunks.append(part[:chunk_size])
                        current = ""
            if current:
                chunks.append(current)
            return [c.strip() for c in chunks if c.strip()]

    return [text[:chunk_size]] if text else []


def chunk_document(doc: ParsedDocument) -> list[Chunk]:
    """Split a parsed document into overlapping text chunks."""
    raw_chunks = _split_recursive(doc.body, _SEPARATORS, CHUNK_SIZE, CHUNK_OVERLAP)
    return [
        Chunk(
            doc_path=doc.path,
            chunk_index=i,
            text=text,
            token_count=_estimate_tokens(text),
            chunk_version=CHUNK_VERSION,
            doc_metadata=doc.metadata,
        )
        for i, text in enumerate(raw_chunks)
        if text.strip()
    ]


def load_all_articles(kb_dir: Path) -> list[ParsedDocument]:
    """Load and parse all .md files under kb_dir."""
    docs = []
    for path in sorted(kb_dir.rglob("*.md")):
        try:
            docs.append(parse_article(path))
        except Exception as exc:
            import warnings

            warnings.warn(f"Failed to parse {path}: {exc}")
    return docs
