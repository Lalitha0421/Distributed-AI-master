"""
run_evaluation.py — Formal RAG Quality Evaluation Script.
Runs a batch of questions through the LangGraph and scores them for a final quality report.
"""

import asyncio
import json
import os
import pandas as pd
from datetime import datetime
import sys

# Ensure backend directory is in the path for app imports
sys.path.append(os.getcwd())

from app.agents.graph import knowledge_graph
from app.services.evaluator import evaluate_rag_response
from app.services.feedback_store import feedback_store
from app.core.logger import logger

async def run_batch_eval(test_file: str = None):
    # Auto-locate test_set.json relative to this script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if test_file is None:
        test_file = os.path.join(script_dir, "test_set.json")
    
    print("\n" + "="*60)
    print("🚀  Distributed AI - Formal RAG Quality Evaluation")
    print("="*60)
    
    if not os.path.exists(test_file):
        print(f"❌ Error: {test_file} not found. Ensure it exists in the same folder as this script.")
        return

    with open(test_file, 'r') as f:
        test_set = json.load(f)

    if not test_set:
        print(f"⚠️ Warning: {test_file} is empty. Generate some test cases first!")
        return

    print(f"📋 Loaded {len(test_set)} test cases.")
    results = []
    
    for i, item in enumerate(test_set):
        question = item['question']
        print(f"\n[{i+1}/{len(test_set)}] Question: {question}")

        # 1. Execute the Agentic Graph
        print(f"  ⚡ Running LangGraph orchestration...")
        initial_state = {
            "session_id": f"eval-run-{datetime.now().strftime('%m%d_%H%M')}",
            "question": question,
            "source": None,
            "agent_trace": [],
            "rewritten_query": "",
            "intent": "factual",
            "retry_count": 0,
            "should_retry": False,
            "retrieved_chunks": [],
            "context": "",
            "answer": "",
            "sources": [],
            "confidence_score": None
        }
        
        # We use ainvoke for the graph (includes planner, retriever, generator, grader)
        try:
            final_state = await knowledge_graph.ainvoke(initial_state)
            answer = final_state.get("answer", "NO ANSWER GENERATED")
            context = final_state.get("context", "")
            
            # Print agent reasoning summary
            for entry in final_state.get("agent_trace", []):
                print(f"    - {entry.get('agent', 'Unknown')}: {entry.get('action', '...')}")

            # 2. Automated Quality Scoring
            print(f"  🔍 Performing automated evaluation...")
            ground_truth = item.get('ground_truth', "No ground truth provided.")
            
            # Pass ground truth to the evaluator for high-precision comparison
            eval_result = await evaluate_rag_response(
                question=question, 
                answer=answer, 
                context=context,
                ground_truth=ground_truth
            )

            if eval_result:
                print(f"    ✅ Faithfulness: {eval_result.faithfulness:.2f}")
                print(f"    ✅ Relevance: {eval_result.relevance:.2f}")
                print(f"    ✅ Precision: {eval_result.context_precision:.2f}")
            else:
                print(f"    ⚠️  Evaluation failed/skipped for this question.")

            results.append({
                "Question": question,
                "Answer Snippet": answer[:80] + "...",
                "Faithfulness": eval_result.faithfulness if eval_result else 0.0,
                "Relevance": eval_result.relevance if eval_result else 0.0,
                "Precision": eval_result.context_precision if eval_result else 0.0,
                "Reflexion Retries": final_state.get("retry_count", 0),
                "Explanation": eval_result.explanation if eval_result else "Evaluation Failed"
            })
            
            # 3. Log to Dashboard database for live visualization
            feedback_store.save_feedback(
                session_id=final_state.get("session_id", "eval-batch"),
                question=question,
                answer=answer,
                rating=0, # Neutral rating for automated evals
                comment="Automated Batch Evaluation",
                faithfulness=eval_result.faithfulness if eval_result else 0.0,
                relevance=eval_result.relevance if eval_result else 0.0,
                context_precision=eval_result.context_precision if eval_result else 0.0,
                answer_accuracy=eval_result.answer_accuracy if eval_result else 0.0,
                retry_count=final_state.get("retry_count", 0),
                confidence=final_state.get("confidence_score", "not_rated")
            )
            
        except Exception as e:
            print(f"  ❌ Error processing question: {e}")
            continue

    # 3. Generate Final Report (Markdown)
    df = pd.DataFrame(results)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    # Save report in the same directory as the script
    report_file = os.path.join(script_dir, f"rag_eval_report_{timestamp}.md")
    
    with open(report_file, 'w') as f:
        f.write("# 📊 Formal RAG Quality Report\n\n")
        f.write(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 🏆 System Metrics (Averages)\n\n")
        f.write(f"- **Total Questions:** {len(df)}\n")
        f.write(f"- **Avg Faithfulness:** {df['Faithfulness'].mean():.2f}\n")
        f.write(f"- **Avg Relevance:** {df['Relevance'].mean():.2f}\n")
        f.write(f"- **Avg Context Precision:** {df['Precision'].mean():.2f}\n")
        f.write(f"- **Success Rate (Score > 0.7):** {((df['Faithfulness'] + df['Relevance'])/2 > 0.7).mean() * 100:.1f}%\n\n")
        
        f.write("## 📝 Detailed Evaluation Logs\n\n")
        # Markdown table from DataFrame
        f.write(df.to_markdown(index=False))
        
        f.write("\n\n---\n*Report generated by Distributed-AI Evaluation Engine.*")

    print(f"\n" + "="*60)
    print(f"🎉 FINAL QUALITY REPORT GENERATED: {report_file}")
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(run_batch_eval())
