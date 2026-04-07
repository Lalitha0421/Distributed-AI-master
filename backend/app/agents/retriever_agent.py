from __future__ import annotations

import time
from typing import Dict, Any

from app.agents.agent_state import AgentState
from app.services.hybrid_search import hybrid_search
from app.services.reranker import rerank
from app.core.logger import logger
from app.core.config import settings

async def retriever_agent(state: AgentState) -> Dict[str, Any]:
    """
    Second node: Searches and reranks document chunks.
    
    Args:
        state: Shared AgentState.
        
    Returns:
        Updated state dictionary.
    """
    start_time = time.time()
    logger.info(f"Retriever Agent starting search for: '{state['rewritten_query']}'")
    
    query = state["rewritten_query"]
    # ── Broaden search on retry ──────────────────────────────────────────
    if state.get("retry_count", 0) > 0:
        query = state["question"]
        logger.info(f"Retrying with original query to broaden search: '{query}'")

    session_id = state.get("session_id", "default")
    
    try:
        # ── 1. Hybrid Search (Vector + BM25) ──────────────────────────────────
        raw_chunks = hybrid_search(query, state.get("source"))
        logger.info(f"Found {len(raw_chunks)} candidate chunks via hybrid search")
        
        # ── 2. Cross-Encoder Rerank ───────────────────────────────────────────
        reranked = rerank(query, raw_chunks)
        
        # Limit to top K from settings
        top_k = settings.rerank_top_k or 5
        final_chunks = reranked[:top_k]
        
        # ── 3. Build context string ───────────────────────────────────────────
        context = "\n\n".join([c["text"] for c in final_chunks])
        sources = list(set([c.get("source", "Unknown") for c in final_chunks]))
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # ── 4. Log trace ──────────────────────────────────────────────────────
        trace = {
            "agent": "Retriever",
            "action": f"Search complete (top_k={len(final_chunks)})",
            "duration_ms": duration_ms,
            "details": f"Found info in documents: {', '.join(sources)}"
        }
        
        return {
            "retrieved_chunks": final_chunks,
            "context": context,
            "sources": sources,
            "agent_trace": [trace]
        }
        
    except Exception as exc:
        logger.error(f"Retriever Agent failed: {exc}")
        return {
            "retrieved_chunks": [],
            "context": "ERROR: Could not retrieve document context.",
            "sources": [],
            "agent_trace": [{
                "agent": "Retriever",
                "action": "Failed retrieval",
                "details": str(exc),
                "duration_ms": int((time.time() - start_time) * 1000)
            }]
        }
