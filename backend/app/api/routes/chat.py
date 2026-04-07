"""
chat.py — Streaming Q&A route.
POST /api/ask/

Current (Phase 1): direct service pipeline with SSE streaming.
Phase 2 will replace this with the LangGraph agent graph.
The SSE event protocol is already defined here so the frontend
doesn't need changes when we upgrade to agents.

SSE event types emitted:
  data: [TOKEN]<token>      — one answer token
  data: [SOURCES]<json>     — source list (after generation)
  data: [DONE]              — stream complete
"""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse

from app.core.logger import logger
from app.core.security import get_current_user
from app.models.schemas import QuestionRequest
from app.services.hybrid_search import hybrid_search
from app.services.llm_service import generate_answer_stream
from app.services.memory import add_message, get_history
from app.services.query_rewriter import rewrite_query
from app.services.reranker import rerank
from app.services.evaluator import evaluate_rag_response
from app.services.feedback_store import feedback_store

from app.agents.graph import knowledge_graph

router = APIRouter(
    prefix="/ask", 
    tags=["ask"],
    dependencies=[Depends(get_current_user)]
)

async def _bg_evaluate(session_id: str, question: str, answer: str, context: str, retry_count: int):
    """Run evaluation in the background and save to metrics store."""
    try:
        eval_result = await evaluate_rag_response(
            question=question,
            answer=answer,
            context=context
        )
        feedback_store.save_feedback(
            session_id=session_id,
            question=question,
            answer=answer,
            rating=0, # Auto-evaluated (no user rating yet)
            faithfulness=eval_result.faithfulness if eval_result else 0.0,
            relevance=eval_result.relevance if eval_result else 0.0,
            context_precision=eval_result.context_precision if eval_result else 0.0,
            retry_count=retry_count
        )
    except Exception as e:
        logger.error(f"Background evaluation failed: {e}")

@router.post("/")
async def ask_question(
    request: QuestionRequest,
    background_tasks: BackgroundTasks,
    session_id: str = "default",
    source: str | None = None,
) -> StreamingResponse:
    """
    Accept a question and stream the agent graph execution + final answer.
    """
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    logger.info(f"LangGraph Ask: '{question[:80]}' | session={session_id}")

    async def _graph_stream():
        # ── Initialize the shared state ──────────────────────────────────────
        # Note: 'source' filter would be passed here to the Retriever via state
        initial_state = {
            "session_id": session_id,
            "question": question,
            "source": request.source,
            "agent_trace": [],
            "history": get_history(session_id),
            "retry_count": 0,
            "should_retry": False,
        }

        final_state = None
        
        # ── Execute the graph node by node ────────────────────────────────────
        # astream allows us to catch each agent as it finishes
        async for output in knowledge_graph.astream(initial_state):
            # output is a dict like {'node_name': {state_delta}}
            node_name = list(output.keys())[0]
            delta = list(output.values())[0]
            
            # Send trace events to the UI
            if "agent_trace" in delta:
                trace = delta["agent_trace"][-1]
                yield f"data: [AGENT_TRACE]{json.dumps(trace)}\n\n"
            
            # If the generator finished, we can stream the tokens 
            # (In this phase we send the whole answer once generated)
            # If the generator finished, we stream the answer safely as a JSON-encoded string
            if node_name == "generator" and "answer" in delta:
                answer = delta["answer"]
                # We send the whole answer as one safely encoded token sweep
                # This prevents raw \n from breaking the SSE protocol
                safe_answer = json.dumps(answer)
                yield f"data: [TOKEN]{safe_answer}\n\n"
            
            # Keep track of the final cumulative state
            if not final_state:
                final_state = delta.copy()
            else:
                final_state.update(delta)

        # ── Final Persistence ──────────────────────────────────────────────────
        if final_state and "answer" in final_state:
            add_message(session_id, "user", question)
            add_message(session_id, "assistant", final_state["answer"])
            
            sources = [
                {"source": s} for s in final_state.get("sources", [])
            ]
            yield f"data: [SOURCES]{json.dumps(sources)}\n\n"

            # ── Background Evaluation ──────────────────────────────────────────
            context_str = final_state.get("context", "No context retrieved.")
            background_tasks.add_task(
                _bg_evaluate, 
                session_id, 
                question, 
                final_state["answer"], 
                context_str, 
                final_state.get("retry_count", 0)
            )

        yield "data: [DONE]\n\n"
        logger.info(f"Graph execution complete for session={session_id}")

    return StreamingResponse(_graph_stream(), media_type="text/event-stream")