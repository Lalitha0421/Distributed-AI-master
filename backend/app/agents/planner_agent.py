from __future__ import annotations

import time
import json
from typing import Dict, Any

from app.agents.agent_state import AgentState
from app.core.config import settings
from app.core.logger import logger
from groq import AsyncGroq

_client = AsyncGroq(api_key=settings.groq_api_key)

_PLANNER_PROMPT = """
You are the Lead Strategist for a Multi-Agent RAG system.
Your job is to analyze the user's question and generate a HIGH-QUALITY search query.

RULES:
1. Identify the INTENT: (factual, summary, or comparative).
2. Rewrite the query to be SPECIFIC:
   - Preserve key NOUNS (e.g., 'projects', 'experience', 'skills').
   - Avoid generic phrases like 'of a specific person'.
   - Instead, use keywords that are likely to appear in a resume or document.
   - Example: 'what are his projects' -> 'Technical projects, development achievements, list of engineering works'

Return ONLY a JSON:
{
  "intent": "factual|summary|compare",
  "rewritten_query": "The optimized search query"
}
"""

async def planner_agent(state: AgentState) -> Dict[str, Any]:
    """
    Initial node: Analyzes the question and plans the retrieval strategy.
    
    Args:
        state: Shared AgentState.
        
    Returns:
        Updated state dictionary (automatically merged by LangGraph).
    """
    start_time = time.time()
    logger.info(f"Planner Agent starting for session: {state.get('session_id')}")
    
    question = state["question"]
    
    try:
        # ── Call Groq for planning ──────────────────────────────────────────
        response = await _client.chat.completions.create(
            model=settings.model_name,
            messages=[
                {"role": "system", "content": _PLANNER_PROMPT},
                {"role": "user", "content": f"Question: {question}"}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        # ── Parse response ───────────────────────────────────────────────────
        plan = json.loads(response.choices[0].message.content)
        rewritten = plan.get("rewritten_query", question)
        intent = plan.get("intent", "factual")
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # ── Log the trace ───────────────────────────────────────────────────
        trace = {
            "agent": "Planner",
            "action": f"Plan generated (intent={intent})",
            "duration_ms": duration_ms,
            "details": f"Rewritten query: '{rewritten}'"
        }
        
        logger.info(f"Planner complete: intent={intent} in {duration_ms}ms")
        
        return {
            "rewritten_query": rewritten,
            "intent": intent,
            "agent_trace": [trace]
        }
        
    except Exception as exc:
        logger.error(f"Planner Agent failed: {exc}")
        # Default fallback
        return {
            "rewritten_query": question,
            "intent": "factual",
            "agent_trace": [{
                "agent": "Planner",
                "action": "Failed, using defaults",
                "details": str(exc),
                "duration_ms": 0
            }]
        }
