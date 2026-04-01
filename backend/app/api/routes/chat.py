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

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.core.logger import logger
from app.models.schemas import QuestionRequest
from app.services.hybrid_search import hybrid_search
from app.services.llm_service import generate_answer_stream
from app.services.memory import add_message, get_history
from app.services.query_rewriter import rewrite_query
from app.services.reranker import rerank

from app.agents.graph import knowledge_graph

router = APIRouter(prefix="/ask", tags=["chat"])

@router.post("/")
async def ask_question(
    request: QuestionRequest,
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
            "source": source,
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
            # If the generator finished, we stream the tokens for the live feel
            if node_name == "generator" and "answer" in delta:
                answer = delta["answer"]
                # CRITICAL FIX: Split by newlines so SSE doesn't break
                lines = answer.split("\n")
                for i, line_text in enumerate(lines):
                    # Re-add the newline character so the UI renders it
                    suffix = "\n" if i < len(lines) - 1 else ""
                    yield f"data: [TOKEN]{line_text}{suffix}\n\n"
            
            # Keep track of the final state to get the full result
            final_state = delta

        # ── Final Persistence ──────────────────────────────────────────────────
        if final_state and "answer" in final_state:
            add_message(session_id, "user", question)
            add_message(session_id, "assistant", final_state["answer"])
            
            sources = [
                {"source": s} for s in final_state.get("sources", [])
            ]
            yield f"data: [SOURCES]{json.dumps(sources)}\n\n"

        yield "data: [DONE]\n\n"
        logger.info(f"Graph execution complete for session={session_id}")

    return StreamingResponse(_graph_stream(), media_type="text/event-stream")