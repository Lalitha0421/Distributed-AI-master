"""
text_chunker.py — Upgraded fixed-size chunking with overlap and rich metadata.

Strategy:
  - Split on character boundaries respecting natural break points (. \\n space).
  - Each chunk carries metadata so agents can reason about source position.
  - chunk_size / chunk_overlap come from centralised Settings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from app.core.config import settings
from app.core.logger import logger


@dataclass
class Chunk:
    """A single text chunk with positional metadata."""
    text: str
    chunk_index: int
    char_start: int
    char_end: int
    total_chunks: int = field(default=0)   # filled in after all chunks known


def split_text_into_chunks(
    text: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> List[str]:
    """
    Split *text* into overlapping fixed-size chunks.

    Returns a plain list of strings (compatible with existing vector_store API).
    Internally uses :func:`split_text_into_chunks_with_metadata` which carries
    full positional metadata required by the agent layer.

    Args:
        text:          Input document text.
        chunk_size:    Char limit per chunk (defaults to settings.chunk_size = 512).
        chunk_overlap: Overlap between consecutive chunks (defaults to settings.chunk_overlap = 64).

    Returns:
        List of chunk text strings.
    """
    chunks = split_text_into_chunks_with_metadata(text, chunk_size, chunk_overlap)
    return [c.text for c in chunks]


def split_text_into_chunks_with_metadata(
    text: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> List[Chunk]:
    """
    Full metadata-aware chunker. Used internally and by future agent tools.

    Splitting rules (in priority order):
      1. Hard limit: chunk_size characters.
      2. Prefer to break at the last '.' (sentence boundary).
      3. Fall back to last '\\n' (paragraph boundary).
      4. Fall back to last ' ' (word boundary).
      5. Hard cut at chunk_size if none of the above found past the midpoint.
    """
    if not text or not text.strip():
        logger.warning("split_text_into_chunks received empty text — returning empty list")
        return []

    _chunk_size = chunk_size or settings.chunk_size
    _overlap = chunk_overlap or settings.chunk_overlap
    text = text.strip()

    # Very short documents — return as a single chunk
    if len(text) <= _chunk_size:
        logger.debug(f"Document fits in one chunk ({len(text)} chars)")
        chunk = Chunk(
            text=text,
            chunk_index=0,
            char_start=0,
            char_end=len(text),
            total_chunks=1,
        )
        return [chunk]

    raw_chunks: List[Chunk] = []
    start = 0
    idx = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + _chunk_size, text_length)
        segment = text[start:end]

        # Try to find a natural break point in the second half of the segment
        if end < text_length:
            midpoint = len(segment) // 2
            for sep in (".", "\n", " "):
                pos = segment.rfind(sep, midpoint)
                if pos != -1:
                    end = start + pos + 1   # include the separator
                    segment = text[start:end]
                    break

        clean = segment.strip()
        if clean:
            raw_chunks.append(
                Chunk(
                    text=clean,
                    chunk_index=idx,
                    char_start=start,
                    char_end=end,
                )
            )
            idx += 1

        # Advance with overlap
        if end >= text_length:
            break  # We reached the end of the document
        
        new_start = end - _overlap
        # Ensure we always make at least some progress
        start = max(new_start, start + 1)

    # Back-fill total_chunks now that we know the count
    total = len(raw_chunks)
    for c in raw_chunks:
        c.total_chunks = total

    logger.info(
        f"Chunked {text_length} chars → {total} chunks "
        f"(size={_chunk_size}, overlap={_overlap})"
    )
    return raw_chunks