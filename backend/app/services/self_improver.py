"""
self_improver.py — Analyzes feedback trends and suggests system improvements.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
from app.core.logger import logger
from app.models.schemas import ImprovementInsight

class SelfImprover:
    def __init__(self, db_path: str = "feedback.db"):
        self.db_path = Path(db_path)

    async def analyze_feedback_trends(self, days: int = 7) -> List[ImprovementInsight]:
        """
        Runs an analysis on recent feedback data to detect patterns 
        and suggest system-wide improvements.
        """
        try:
            # 1. Load data into a DataFrame for easier analysis
            with sqlite3.connect(self.db_path) as conn:
                query = f"SELECT * FROM feedback WHERE timestamp >= datetime('now', '-{days} days')"
                df = pd.read_sql_query(query, conn)

            if df.empty:
                return [ImprovementInsight(
                    metric="overall",
                    trend="stable",
                    suggestion="Not enough data yet for trend analysis. Continue collecting feedback.",
                    auto_applied=False,
                    confidence_score=0.5
                )]

            insights = []

            # 2. Analyze Faithfulness
            faith_insight = self._analyze_metric(df, "faithfulness", "Faithfulness (Groundedness)")
            if faith_insight:
                insights.append(faith_insight)

            # 3. Analyze Relevance
            relev_insight = self._analyze_metric(df, "relevance", "Answer Relevance")
            if relev_insight:
                insights.append(relev_insight)

            # 4. Pattern Recognition: Questions with low scores
            pattern_insight = self._identify_problem_patterns(df)
            if pattern_insight:
                insights.append(pattern_insight)

            # 5. Retry Efficiency
            retry_insight = self._analyze_retry_impact(df)
            if retry_insight:
                insights.append(retry_insight)

            return insights

        except Exception as e:
            logger.error(f"Error in self-improver analysis: {e}")
            return []

    def _analyze_metric(self, df: pd.DataFrame, column: str, label: str) -> Optional[ImprovementInsight]:
        """Analyzes a specific metric column for trends."""
        scores = df[column].dropna()
        if len(scores) < 2:
            return None

        avg_score = scores.mean()
        
        # Split into two halves to check trend
        mid = len(scores) // 2
        recent_avg = scores.iloc[mid:].mean()
        older_avg = scores.iloc[:mid].mean()

        diff = recent_avg - older_avg
        trend = "stable"
        if diff > 0.05: trend = "improving"
        elif diff < -0.05: trend = "declining"

        suggestion = f"Maintain current strategy. Average {label} is {avg_score:.2f}."
        if trend == "declining":
            suggestion = f"{label} is dropping. Consider reviewing recent document uploads or increasing chunk overlap."
        elif trend == "improving":
            suggestion = f"{label} is rising. Recent changes to retrieval or ranking are likely working."

        return ImprovementInsight(
            metric=column,
            trend=trend,
            suggestion=suggestion,
            auto_applied=False,
            confidence_score=0.7
        )

    def _identify_problem_patterns(self, df: pd.DataFrame) -> Optional[ImprovementInsight]:
        """Identifies types of questions that consistently score low."""
        low_score_df = df[df['faithfulness'] < 0.6]
        if low_score_df.empty:
            return None

        # Simple keyword frequency analysis on questions
        all_words = " ".join(low_score_df['question'].tolist()).lower().split()
        stopwords = {'what', 'is', 'the', 'how', 'to', 'of', 'in', 'and', 'a', 'an'}
        keywords = [w for w in all_words if len(w) > 3 and w not in stopwords]
        
        if not keywords:
            return None

        top_keyword = pd.Series(keywords).value_counts().idxmax()
        
        return ImprovementInsight(
            metric="pattern_recognition",
            trend="active_learning",
            suggestion=f"System struggles with questions containing '{top_keyword}'. Consider adding specialized documentation or metadata filtering for this topic.",
            auto_applied=False,
            confidence_score=0.8
        )

    def _analyze_retry_impact(self, df: pd.DataFrame) -> Optional[ImprovementInsight]:
        """Checks if the Reflexion loop (retries) actually improves scores."""
        retried = df[df['retry_count'] > 0]
        not_retried = df[df['retry_count'] == 0]

        if retried.empty:
            return None

        retried_avg = retried['faithfulness'].mean()
        normal_avg = not_retried['faithfulness'].mean()

        if retried_avg > normal_avg:
            return ImprovementInsight(
                metric="reflexion_loop",
                trend="improving",
                suggestion="The Reflexion loop is successfully self-correcting low-quality answers. Consider lowering the Grader threshold to trigger it more often.",
                auto_applied=False,
                confidence_score=0.9
            )
        else:
            return ImprovementInsight(
                metric="reflexion_loop",
                trend="declining",
                suggestion="Retries are not significantly improving faithfulness. The refinement prompt may need adjustment.",
                auto_applied=False,
                confidence_score=0.7
            )

# Singleton instance
self_improver = SelfImprover()
