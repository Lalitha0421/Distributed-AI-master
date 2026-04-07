import json
import time
import logging
from typing import Dict, Any
from groq import AsyncGroq
from app.core.config import settings
from app.agents.agent_state import AgentState

logger = logging.getLogger("ai_knowledge")

_client = AsyncGroq(api_key=settings.groq_api_key)

_GRADER_PROMPT = """
You are a Quality Control Agent for a high-performance RAG system.
Evaluate the AI's answer based on the context provided.

CRITICAL CHECKS:
1. FAITHFULNESS: Is the answer 100% grounded in the context?
2. RELEVANCE: Does it answer the user's specific question?
3. COMPLETENESS: Is the answer comprehensive? If it's a list, are ALL items included? Is it cut-off?

If the answer is incomplete, hallucinated, or irrelevant, set confidence < 0.6.
If it's perfect and comprehensive, set confidence 0.9+.

Return ONLY JSON:
{
  "confidence": 0.0 to 1.0,
  "reasoning": "Brief explanation of the score"
}
"""

async def grader_agent(state: AgentState) -> Dict[str, Any]:
    """Evaluates the answer quality and decides if a retry is needed."""
    logger.info("Grader Agent evaluating response...")
    start_time = time.time()
    
    answer = state["answer"]
    context = state["context"]
    question = state["question"]
    
    # ── Handle empty or error states ────────────────────────────────────
    if not answer or "error" in answer.lower() or not context or len(state.get("retrieved_chunks", [])) == 0:
        logger.warning(f"Low quality detection. Retries left: {2 - state.get('retry_count', 0)}")
        should_retry = state.get("retry_count", 0) < 2
        
        return {
            "confidence_score": 0.0,
            "should_retry": should_retry,
            "retry_count": state.get("retry_count", 0) + (1 if should_retry else 0),
            "agent_trace": [{
                "agent": "Grader",
                "action": "Low confidence (Retry needed)" if should_retry else "Low confidence (Giving up)",
                "duration_ms": 0,
                "details": "No answer or 0 search results found."
            }]
        }
    
    try:
        # ── 1. Call Groq for grading ──────────────────────────────────────────
        response = await _client.chat.completions.create(
            model=settings.model_name,
            messages=[
                {"role": "system", "content": _GRADER_PROMPT},
                {
                    "role": "user", 
                    "content": f"Context: {context}\n\nQuestion: {question}\n\nAnswer: {answer}"
                }
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        # ── 2. Parse response ───────────────────────────────────────────────────
        grade = json.loads(response.choices[0].message.content)
        confidence = float(grade.get("confidence", 0.5))
        reasoning = grade.get("reasoning", "Standard evaluation")
        
        # We trigger retry if confidence is low AND we haven't exceeded 2 retries
        should_retry = confidence < 0.7 and state.get("retry_count", 0) < 2
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # ── 3. Log trace ───────────────────────────────────────────────────────
        trace = {
            "agent": "Grader",
            "action": f"Response graded (score={confidence})",
            "duration_ms": duration_ms,
            "details": f"{reasoning} (Retrying={should_retry})"
        }
        
        return {
            "confidence_score": confidence,
            "should_retry": should_retry,
            "retry_count": state.get("retry_count", 0) + (1 if should_retry else 0),
            "agent_trace": [trace]
        }
        
    except Exception as e:
        logger.error(f"Grader error: {e}")
        return {
            "confidence_score": 0.5,
            "should_retry": False,
            "agent_trace": [{
                "agent": "Grader",
                "action": "Grader failed (Exception)",
                "duration_ms": 0,
                "details": str(e)
            }]
        }
