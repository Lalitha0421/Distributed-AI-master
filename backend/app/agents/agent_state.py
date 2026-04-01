from __future__ import annotations

from typing import Annotated, List, Optional, TypedDict

import operator

def merge_trace(existing: List[dict], new: List[dict]) -> List[dict]:
    """Helper to append new trace logs to the existing list."""
    return existing + new

class AgentState(TypedDict):
    """
    Shared state object for the multi-agent graph.
    
    Using LangGraph's state management:
    - Lists with 'Annotated' + 'operator.add' merge updates rather than overwriting.
    """
    session_id: str
    question: str
    source: Optional[str]        # Filename filter
    rewritten_query: str
    intent: str               # "factual", "summary", "compare"
    
    # Control flow
    retry_count: int = 0
    should_retry: bool = False

    # Retrieved & Reranked info
    retrieved_chunks: List[dict]
    context: str
    
    # Final outputs
    answer: str
    sources: List[str]
    
    # Observability & Trace (accumulates per agent)
    # Using Annotated[..., operator.add] means agents can just 'return {"agent_trace": [...]}'
    # and it will automatically append it to the existing list.
    agent_trace: Annotated[List[dict], operator.add]
    
    # Final quality scores (from Grader)
    confidence_score: Optional[float]
