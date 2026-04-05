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
4. ANSWER_ACCURACY (if GROUND TRUTH provided): How similar is the answer to the GROUND TRUTH?

OUTPUT FORMAT: Return ONLY a valid JSON object.

Example Output:
{{
    "faithfulness": 0.95,
    "relevance": 1.0,
    "context_precision": 0.85,
    "answer_accuracy": 0.9,
    "explanation": "Brief reasoning for these scores."
}}

---
QUESTION: {question}
CONTEXT: {context}
GROUND TRUTH: {ground_truth}
ANSWER: {answer}
"""

class EvaluationResult(BaseModel):
    faithfulness: float = Field(ge=0.0, le=1.0)
    relevance: float = Field(ge=0.0, le=1.0)
    context_precision: float = Field(ge=0.0, le=1.0)
    answer_accuracy: float = Field(default=0.0, ge=0.0, le=1.0)
    explanation: str

async def evaluate_rag_response(
    question: str,
    answer: str,
    context: str,
    ground_truth: str = "Not provided"
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
                    ground_truth=ground_truth,
                    answer=answer
                )}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )

        # Robust extraction with type enforcement (handles null values from LLM)
        def _get_float(key: str) -> float:
            val = data.get(key, 0.0)
            return float(val) if val is not None else 0.0

        result = EvaluationResult(
            faithfulness=_get_float("faithfulness"),
            relevance=_get_float("relevance"),
            context_precision=_get_float("context_precision"),
            answer_accuracy=_get_float("answer_accuracy"),
            explanation=data.get("explanation", "No explanation provided.")
        )
        
        duration = int((time.time() - start_time) * 1000)
        logger.info(f"Evaluation complete in {duration}ms | Avg Score: {(result.faithfulness + result.relevance) / 2:.2f}")
        
        return result

    except Exception as exc:
        logger.error(f"Evaluation failed: {exc}")
        return None
