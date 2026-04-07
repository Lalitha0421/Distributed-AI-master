"""
reranker.py — Cross-encoder reranking of candidate chunks.

The cross-encoder (ms-marco-MiniLM-L-6-v2) scores (query, chunk) pairs jointly,
giving much better relevance ordering than vector cosine similarity alone.
Loaded once at module import to avoid repeated disk reads.
"""

from __future__ import annotations

from typing import List

from sentence_transformers import CrossEncoder

from app.core.logger import logger

_reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
logger.info("CrossEncoder reranker loaded (ms-marco-MiniLM-L-6-v2)")


def rerank(query: str, chunks: List[dict]) -> List[dict]:
    """
    Rerank *chunks* by cross-encoder relevance score for *query*.

    Args:
        query:  The (possibly rewritten) user query.
        chunks: List of chunk dicts from hybrid_search.

    Returns:
        Same chunks sorted by descending cross-encoder score.
        On failure, returns chunks in original order.
    """
    if not chunks:
        return []

    try:
        pairs = [(query, c["text"]) for c in chunks]
        scores = _reranker.predict(pairs)

        ranked = sorted(
            zip(chunks, scores),
            key=lambda x: x[1],
            reverse=True,
        )
        reranked = [item[0] for item in ranked]
        logger.info(f"Reranked {len(chunks)} chunks (top score: {scores.max():.3f})")
        return reranked

    except Exception as exc:
        logger.warning(f"Reranking failed ({exc}) — returning original order")
        return chunks