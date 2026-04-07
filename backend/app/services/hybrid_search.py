"""
hybrid_search.py — Combines vector similarity search and BM25 keyword search.

Merge strategy: union of vector results and BM25 results, deduplicated by
(source, chunk_id). This gives recall from both dense and sparse retrieval.
"""

from __future__ import annotations

from typing import List, Optional

from rank_bm25 import BM25Okapi

from app.core.logger import logger
from app.services.vector_store import get_all_chunks, search_chunks


def hybrid_search(query: str, source: Optional[str] = None) -> List[dict]:
    """
    Retrieve relevant chunks using both vector search and BM25.

    Args:
        query:  The (possibly rewritten) user query.
        source: Optional document name to restrict retrieval scope.

    Returns:
        Merged, deduplicated list of chunk dicts: {text, source, chunk_id, score}
    """
    # ── Vector search ─────────────────────────────────────────────────────────
    vector_results: List[dict] = search_chunks(query, source) or []

    # ── BM25 keyword search ───────────────────────────────────────────────────
    all_chunks = get_all_chunks(source)
    bm25_results: List[dict] = []

    if all_chunks:
        texts = [c["text"] for c in all_chunks]
        tokenized = [t.lower().split() for t in texts]

        bm25 = BM25Okapi(tokenized)
        scores = bm25.get_scores(query.lower().split())

        bm25_ranked = sorted(
            zip(all_chunks, scores),
            key=lambda x: x[1],
            reverse=True,
        )
        bm25_results = [item[0] for item in bm25_ranked[:5]]
    else:
        logger.warning("BM25: no chunks available — returning vector-only results")

    # ── Merge and deduplicate ─────────────────────────────────────────────────
    # Vector results take precedence (they have distance scores).
    seen: dict[tuple, dict] = {
        (r["source"], r.get("chunk_id")): r for r in vector_results
    }
    for r in bm25_results:
        key = (r["source"], r.get("chunk_id"))
        if key not in seen:
            seen[key] = r

    merged = list(seen.values())
    logger.info(
        f"Hybrid search: {len(vector_results)} vector + {len(bm25_results)} BM25 "
        f"→ {len(merged)} merged (source='{source}')"
    )
    return merged