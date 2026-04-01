"""
feedback.py — Routes for storing user feedback and viewing system metrics.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from app.core.logger import logger
from app.models.schemas import (
    FeedbackRequest, 
    FeedbackResponse, 
    MetricsResponse, 
    DailyMetric
)
from app.services.feedback_store import feedback_store
from app.services.evaluator import evaluate_rag_response

router = APIRouter(prefix="/feedback", tags=["feedback"])

@router.post("/", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest) -> FeedbackResponse:
    """
    Store user feedback (thumbs up/down) and trigger an automated quality evaluation
    if not already present.
    """
    logger.info(f"Received feedback for session {request.session_id} | rating: {request.rating}")

    # OPTIONAL: Automatically trigger an LLM-based evaluation of the response quality
    # For a high-performance production app, you might do this in a background task.
    # For now, we do it inline for simplicity.
    
    # Extract relevant fields for the evaluator
    eval_result = await evaluate_rag_response(
        question=request.question,
        answer=request.answer,
        context="", # We'd ideally pass the context used in generation if available in history
    )

    # Save to SQLite
    feedback_id = feedback_store.save_feedback(
        session_id=request.session_id,
        question=request.question,
        answer=request.answer,
        rating=request.rating,
        comment=request.comment,
        faithfulness=eval_result.faithfulness if eval_result else 0.0,
        relevance=eval_result.relevance if eval_result else 0.0,
        context_precision=eval_result.context_precision if eval_result else 0.0,
    )

    if feedback_id == -1:
        raise HTTPException(status_code=500, detail="Database error occurred.")

    return FeedbackResponse(
        message="Feedback saved successfully. Thank you!",
        feedback_id=feedback_id
    )

@router.get("/metrics", response_model=MetricsResponse)
async def get_system_metrics() -> MetricsResponse:
    """
    Fetch aggregated metrics for the dashboard.
    """
    data = feedback_store.get_aggregate_metrics()
    
    if not data:
        # Default empty response if no data exists yet
        return MetricsResponse(
            total_questions=0,
            avg_faithfulness=0.0,
            avg_relevance=0.0,
            avg_user_rating=0.0,
            avg_retry_count=0.0,
            daily_history=[]
        )

    # Convert raw dictionary data into structured Pydantic objects
    daily_history = [
        DailyMetric(
            date=day["date"],
            avg_faithfulness=round(day["avg_faithfulness"] or 0.0, 2),
            avg_relevance=round(day["avg_relevance"] or 0.0, 2),
            total_questions=day["total_questions"] or 0,
            avg_rating=round(day["avg_rating"] or 0.0, 1),
        )
        for day in data.get("daily_history", [])
    ]

    return MetricsResponse(
        total_questions=data["total_questions"],
        avg_faithfulness=data["avg_faithfulness"],
        avg_relevance=data["avg_relevance"],
        avg_user_rating=data["avg_user_rating"],
        avg_retry_count=data["avg_retry_count"],
        last_updated=datetime.now(),
        daily_history=daily_history
    )
