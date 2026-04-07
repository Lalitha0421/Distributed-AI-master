"""
schemas.py — Centralised Pydantic v2 models for the entire AI Knowledge System.
All request/response types live here. Import from this file everywhere.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────
# Authentication
# ──────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    username: str
    password: str

# ──────────────────────────────────────────────
# Upload
# ──────────────────────────────────────────────

class UploadResponse(BaseModel):
    """Returned after a successful document upload and processing."""
    filename: str
    characters_extracted: int
    chunks_created: int
    chunks_stored: int
    extracted_text: Optional[str] = None  # Add this
    message: str


# ──────────────────────────────────────────────
# Chat / Ask
# ──────────────────────────────────────────────

class QuestionRequest(BaseModel):
    """Payload for POST /api/ask/"""
    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's question about the uploaded documents.",
    )
    source: Optional[str] = Field(
        default=None,
        description="Specific document filename to restrict the search to."
    )


class ChunkResult(BaseModel):
    """A single retrieved document chunk with metadata."""
    text: str
    source: str
    chunk_id: Optional[int] = None
    score: Optional[float] = None


class AskResponse(BaseModel):
    """
    Non-streaming response shape (used for testing / fallback).
    The live endpoint streams SSE events instead.
    """
    question: str
    rewritten_query: str
    answer: str
    sources: List[ChunkResult]
    agent_trace: List[dict] = []
    confidence: str = "medium"          # "high" | "medium" | "low"
    faithfulness_score: Optional[float] = None
    relevance_score: Optional[float] = None


# ──────────────────────────────────────────────
# Agent Trace
# ──────────────────────────────────────────────

class AgentTraceStep(BaseModel):
    """One step in the multi-agent execution trace."""
    agent: str                          # "Planner" | "Retriever" | "Generator" | "Grader"
    action: str                         # Human-readable description of what happened
    duration_ms: int                    # Wall-clock time for this step
    status: str = "done"               # "running" | "done" | "retrying" | "failed"


# ──────────────────────────────────────────────
# Feedback
# ──────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    """Payload for POST /api/feedback/"""
    session_id: str
    question: str
    answer: str
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="User rating from 1 (poor) to 5 (excellent)",
    )
    comment: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional free-text reason from the user.",
    )


class FeedbackResponse(BaseModel):
    """Returned after storing user feedback."""
    message: str
    feedback_id: int


# ──────────────────────────────────────────────
# Metrics / Evaluation
# ──────────────────────────────────────────────

class DailyMetric(BaseModel):
    """A single day's aggregated metrics for charting."""
    date: str                           # ISO date string e.g. "2026-03-31"
    avg_faithfulness: float
    avg_relevance: float
    avg_accuracy: float                 # 0.0 to 1.0
    total_questions: int
    avg_rating: float                   # 1.0 to 5.0


class MetricsResponse(BaseModel):
    """Returned by GET /api/metrics/"""
    total_questions: int
    avg_faithfulness: float
    avg_relevance: float
    avg_accuracy: float
    avg_user_rating: float              # 1.0 to 5.0 overall
    avg_retry_count: float
    last_updated: Optional[datetime] = None
    daily_history: List[DailyMetric] = []


class ImprovementInsight(BaseModel):
    """A single automated system improvement suggestion."""
    metric: str
    trend: str                           # "improving" | "declining" | "stable"
    suggestion: str                      # Human-readable improvement action
    auto_applied: bool                   # Was this automatically adjusted?
    confidence_score: float              # 0.0 to 1.0


class ImprovementsResponse(BaseModel):
    """Returned by GET /api/feedback/improvements/"""
    insights: List[ImprovementInsight]
    last_analyzed: datetime


# ──────────────────────────────────────────────
# Health
# ──────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Returned by GET /"""
    message: str
    llm_model: str
    version: str
    status: str


# ──────────────────────────────────────────────
# Generic error wrapper
# ──────────────────────────────────────────────

class ErrorDetail(BaseModel):
    """Standard error response body."""
    detail: str
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
