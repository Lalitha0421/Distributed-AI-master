from __future__ import annotations

import time
from typing import Dict, Any, List

from app.agents.agent_state import AgentState
from app.services.llm_service import generate_answer_stream
from app.core.logger import logger

async def generator_agent(state: AgentState) -> Dict[str, Any]:
    """
    Third node: Generates the grounded answer using the retrieved context.
    
    In a full LangGraph setup, streaming is often handled by the runner. 
    Here, the node gathers the answer for the state so the Grader can check it.
    """
    start_time = time.time()
    logger.info(f"Generator Agent starting answer for: '{state['question'][:50]}...'")
    
    question = state["question"]
    context = state["context"]
    # history will be added in a later step when we integrate history into the state
    history: List[dict] = []
    
    if not context or "ERROR" in context:
        return {
            "answer": "I'm sorry, but I couldn't find any information in the documents to answer that.",
            "agent_trace": [{
                "agent": "Generator",
                "action": "Aborted (no context)",
                "duration_ms": 0
            }]
        }
    
    try:
        # ── 1. Call existing streaming service ────────────────────────────────
        answer_parts: List[str] = []
        async for token in generate_answer_stream(question, context, history):
            # We filter out the error token if it appears
            if "encountered an error" in token:
                continue
            answer_parts.append(token)
            
        final_answer = "".join(answer_parts).strip()
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # ── 2. Log trace ──────────────────────────────────────────────────────
        trace = {
            "agent": "Generator",
            "action": f"Answer generated ({len(final_answer)} characters)",
            "duration_ms": duration_ms,
            "details": f"Context length used: {len(context)} chars"
        }
        
        return {
            "answer": final_answer,
            "agent_trace": [trace]
        }
        
    except Exception as exc:
        logger.error(f"Generator Agent failed: {exc}")
        return {
            "answer": "I encountered an error trying to generate that answer.",
            "agent_trace": [{
                "agent": "Generator",
                "action": "Failed generation",
                "details": str(exc),
                "duration_ms": int((time.time() - start_time) * 1000)
            }]
        }
