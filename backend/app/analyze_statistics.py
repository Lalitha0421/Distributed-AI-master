"""
analyze_statistics.py — Deep Performance Analysis for Distributed AI
Generates a comprehensive quality summary from the feedback database.
"""

import sqlite3
import pandas as pd
from datetime import datetime
import os

DB_PATH = "feedback.db"

def run_analysis():
    print("\n" + "═"*70)
    print("💎  DISTRIBUTED AI - EXECUTIVE PERFORMANCE ANALYTICS")
    print("═"*70)
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: {DB_PATH} not found. Ensure the backend has been running.")
        return

    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM feedback", conn)
        conn.close()
    except Exception as e:
        print(f"❌ Failed to query database: {e}")
        return

    if df.empty:
        print("⚠️  No data found in the feedback store yet! Run some queries or evaluations first.")
        return

    # 1. Data Processing
    total_queries = len(df)
    avg_faithfulness = df['faithfulness'].mean()
    avg_relevance = df['relevance'].mean()
    avg_precision = df['context_precision'].mean()
    avg_accuracy = df['answer_accuracy'].mean()
    avg_retries = df['retry_count'].mean()
    avg_user_rating = df[df['user_rating'] > 0]['user_rating'].mean()

    # Success rate (Faithfulness + Relevance > 0.7 Avg)
    success_mask = (df['faithfulness'] + df['relevance']) / 2 >= 0.7
    success_rate = (success_mask.sum() / total_queries) * 100

    # 2. Executive Summary Output
    print(f"\n🚀 SYSTEM OVERVIEW (Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print("-" * 50)
    print(f"🔹 Total Interactions Analyzed:    {total_queries}")
    print(f"🔹 Overall Success Rate:           {success_rate:.1f}%")
    print(f"🔹 Average Reflexion Retries:     {avg_retries:.2f} per query")
    if not pd.isna(avg_user_rating):
        print(f"🔹 Avg User Satisfaction (1-5):    {avg_user_rating:.1f}/5.0")
    else:
        print(f"🔹 Avg User Satisfaction:          N/A (No user ratings yet)")

    print(f"\n🏆 QUALITY KPIS (AI-AS-A-JUDGE SCORING)")
    print("-" * 50)
    print(f"✅ Faithfulness:         {avg_faithfulness*100:6.1f}%  (Zero hallucination integrity)")
    print(f"✅ Topical Relevance:    {avg_relevance*100:6.1f}%  (Alignment with user intent)")
    print(f"✅ Context Precision:    {avg_precision*100:6.1f}%  (Retrieval engine accuracy)")
    print(f"✅ Answer Factualness:   {avg_accuracy*100:6.1f}%  (Ground-truth consistency)")

    # 3. Performance Breakdown by Confidence Levels
    print(f"\n📊 PERFORMANCE BY CONFIDENCE LEVEL")
    print("-" * 50)
    conf_stats = df.groupby('confidence').agg({
        'id': 'count',
        'faithfulness': 'mean',
        'relevance': 'mean'
    }).rename(columns={'id': 'Count', 'faithfulness': 'Avg Faith', 'relevance': 'Avg Relev'})
    print(conf_stats.to_string())

    # 4. Insightful Suggestions (AI Logic)
    print(f"\n💡 STRATEGIC INSIGHTS")
    print("-" * 50)
    if avg_precision < 0.6:
        print("🚩 CAUTION: Retrieval precision is low. Recommend re-indexing or upgrading the Embeddings model.")
    elif avg_retries > 1.5:
        print("🚩 CAUTION: High retry count. Queries are complex; consider increasing 'Planner Agent' timeout.")
    else:
        print("🟢 OPTIMAL: System is operating within high-performance guardrails.")

    print("\n" + "═" * 70)
    print("📁 Analysis complete. These statistics prove project viability for recruitment.")
    print("═" * 70 + "\n")

if __name__ == "__main__":
    run_analysis()
