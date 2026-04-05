"""
feedback_store.py — Persistence for user feedback and agent metrics in SQLite.
"""

from __future__ import annotations

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.core.config import settings
from app.core.logger import logger

class FeedbackStore:
    def __init__(self, db_path: str = "feedback.db"):
        self.db_path = Path(db_path)
        self._init_db()

    def _init_db(self):
        """Create the metrics and feedback table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                question TEXT,
                answer TEXT,
                faithfulness REAL,
                relevance REAL,
                context_precision REAL,
                answer_accuracy REAL,
                user_rating INTEGER DEFAULT 0,  -- 1-5 (stars)
                user_comment TEXT,
                retry_count INTEGER DEFAULT 0,
                confidence TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """)
            conn.commit()
            logger.info(f"SQLite database initialized at {self.db_path}")

    def save_feedback(
        self,
        session_id: str,
        question: str,
        answer: str,
        rating: int,
        comment: Optional[str] = None,
        faithfulness: Optional[float] = None,
        relevance: Optional[float] = None,
        context_precision: Optional[float] = None,
        answer_accuracy: Optional[float] = None,
        retry_count: int = 0,
        confidence: str = "medium"
    ) -> int:
        """Store a new feedback/evaluation record. Returns the feedback ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                INSERT INTO feedback (
                    session_id, question, answer, user_rating, user_comment, 
                    faithfulness, relevance, context_precision, answer_accuracy, 
                    retry_count, confidence
                ) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_id, question, answer, rating, comment,
                    faithfulness, relevance, context_precision, answer_accuracy, 
                    retry_count, confidence
                ))
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            logger.error(f"Failed to save feedback: {e}")
            return -1

    def get_aggregate_metrics(self) -> Dict[str, Any]:
        """Aggregate all metrics for the dashboard."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Overall Stats
                stats = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    AVG(faithfulness) as avg_faith,
                    AVG(relevance) as avg_relev,
                    AVG(answer_accuracy) as avg_acc,
                    AVG(NULLIF(user_rating, 0)) as avg_rating,
                    AVG(retry_count) as avg_retry
                FROM feedback
                """).fetchone()

                # Daily History (Last 7 Days)
                history = conn.execute("""
                SELECT 
                    DATE(timestamp) as date,
                    AVG(faithfulness) as avg_faithfulness,
                    AVG(relevance) as avg_relevance,
                    AVG(answer_accuracy) as avg_accuracy,
                    COUNT(*) as total_questions,
                    AVG(NULLIF(user_rating, 0)) as avg_rating
                FROM feedback
                GROUP BY DATE(timestamp)
                ORDER BY DATE(timestamp) DESC
                LIMIT 7
                """).fetchall()

                # Reverse history so it flows from oldest to newest in the chart
                history_list = [dict(h) for h in history]
                history_list.reverse()

                return {
                    "total_questions": stats["total"] or 0,
                    "avg_faithfulness": round(stats["avg_faith"] or 0.0, 2),
                    "avg_relevance": round(stats["avg_relev"] or 0.0, 2),
                    "avg_accuracy": round(stats["avg_acc"] or 0.0, 2),
                    "avg_user_rating": round(stats["avg_rating"] or 0.0, 1),
                    "avg_retry_count": round(stats["avg_retry"] or 0.0, 2),
                    "daily_history": history_list
                }
        except Exception as e:
            logger.error(f"Failed to fetch metrics: {e}")
            return {}

# Singleton for the app
feedback_store = FeedbackStore()
