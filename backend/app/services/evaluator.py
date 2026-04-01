"""
evaluator.py — Automated RAG evaluation using an LLM judge (Groq).
Evaluates faithfulness, relevance, and context precision.
"""

from __future__ import annotations

import json
import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from groq import AsyncGroq
from app.core.config import settings
from app.core.logger import logger

_client = AsyncGroq(api_key=settings.groq_api_key)

_EVAL_PROMPT = """
You are an expert evaluator. Given a question, a context of document chunks, and an answer, score the following metrics from 0.0 to 1.0 (with 1.0 being perfect).

METRICS:
1. FAITHFULNESS: Is every claim in the answer backed by the context provided? If the answer hallucinates info not in context, score low.
2. RELEVANCE: Does the answer directly and accurately address the user's question?
3. CONTEXT_PRECISION: Are the retrieved document chunks actually relevant and useful for answering the question?

OUTPUT FORMAT: Return ONLY a valid JSON object.

Example Output:
{{
    "faithfulness": 0.95,
    "relevance": 1.0,
    "context_precision": 0.85,
    "explanation": "Brief reasoning for these scores."
}}

---
QUESTION: {question}
CONTEXT: {context}
ANSWER: {answer}
"""

class EvaluationResult(BaseModel):
    faithfulness: float = Field(ge=0.0, le=1.0)
    relevance: float = Field(ge=0.0, le=1.0)
    context_precision: float = Field(ge=0.0, le=1.0)
    explanation: str

async def evaluate_rag_response(
    question: str,
    answer: str,
    context: str,
) -> Optional[EvaluationResult]:
    """
    Asks the LLM to judge the quality of the generated answer and retrieved context.
    """
    logger.info("Starting automated evaluation via LLM Judge...")
    
    # Trim context to avoid token limits during evaluation
    trimmed_context = context[:3000]

    try:
        start_time = time.time()
        
        response = await _client.chat.completions.create(
            model=settings.model_name,
            messages=[
                {"role": "system", "content": "You are a precise evaluation bot."},
                {"role": "user", "content": _EVAL_PROMPT.format(
                    question=question,
                    context=trimmed_context,
                    answer=answer
                )}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content
        data = json.loads(content)
        
        # Add basic validation / defaults if missing
        result = EvaluationResult(
            faithfulness=data.get("faithfulness", 0.0),
            relevance=data.get("relevance", 0.0),
            context_precision=data.get("context_precision", 0.0),
            explanation=data.get("explanation", "No explanation provided.")
        )
        
        duration = int((time.time() - start_time) * 1000)
        logger.info(f"Evaluation complete in {duration}ms | Avg Score: {(result.faithfulness + result.relevance) / 2:.2f}")
        
        return result

    except Exception as exc:
        logger.error(f"Evaluation failed: {exc}")
        return None
