# Master Plan: Distributed Multi-Agent AI Knowledge System
### From: Working RAG Pipeline → To: Production AI Engineer Portfolio Project

---

## Where You Are Right Now

You have built more than you think. Here is an honest audit:

| Component | Status | Resume Value |
|---|---|---|
| FastAPI backend with CORS | ✅ Working | Medium |
| PDF + OCR text extraction | ✅ Working | Medium |
| Sentence-based chunking | ✅ Working | Low (basic) |
| ChromaDB vector store | ✅ Working | Medium |
| Hybrid Search (Vector + BM25) | ✅ Working | **High** — rare in student projects |
| Cross-encoder reranking | ✅ Working | **High** — production-level technique |
| Query rewriting via Groq | ✅ Working | **High** — agentic pattern |
| Streaming SSE responses | ✅ Working | High |
| Session memory (conversation history) | ✅ Working | Medium |
| React + TypeScript frontend | ✅ Working | High |
| CORS, modular routers, Pydantic models | ✅ Working | Medium |

**What you already have is NOT a basic project. It is a solid RAG system.**

The gap between where you are and an AI Engineer role is:

1. Real multi-agent orchestration (not just function calls in sequence)
2. Measurable evaluation (can you prove your system is accurate?)
3. Self-improvement loop (can the system get better over time?)
4. Distributed architecture (can it scale?)
5. A UI that makes the intelligence *visible* (demos win interviews)

---

## What the Final System Will Be

**Name**: AI Knowledge Assistant with Self-Improving Multi-Agent RAG

**One-liner for your resume**:
> "Production multi-agent RAG system with LangGraph orchestration, Reflexion self-correction, Ragas evaluation, real-time agent trace UI, and Docker microservices."

**Full Architecture (post all phases):**

```
┌─────────────────────────────────────────────────────────────────────┐
│                        React Frontend                               │
│                                                                     │
│  ┌──────────┐  ┌─────────────────────┐  ┌───────────────────────┐  │
│  │ Sidebar  │  │    Streaming Chat   │  │  Live Agent Trace     │  │
│  │          │  │                    │  │                       │  │
│  │ Documents│  │  User → AI msgs    │  │  ⚡ Planner (120ms)   │  │
│  │ Upload   │  │  Source bubbles    │  │  ✅ Retriever (340ms) │  │
│  │ Metrics  │  │  👍 👎 Feedback    │  │  🔄 Retry (low score) │  │
│  │ Dashboard│  │  Confidence score  │  │  ✅ Generator (1.2s)  │  │
│  └──────────┘  └─────────────────────┘  └───────────────────────┘  │
└────────────────────────────┬────────────────────────────────────────┘
                             │ HTTP + SSE
┌────────────────────────────▼────────────────────────────────────────┐
│                        FastAPI Gateway                              │
│   /api/upload   /api/ask   /api/feedback   /api/metrics             │
└────────────────────────────┬────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                  LangGraph StateGraph                               │
│                                                                     │
│   ┌─────────┐    ┌──────────────────────────────────────────────┐  │
│   │ Planner │───►│         ROUTE (conditional edge)             │  │
│   │  Agent  │    └──────┬─────────────────┬──────────────┬──────┘  │
│   └─────────┘           │                 │              │          │
│   • Rewrite query        ▼                 ▼              ▼          │
│   • Detect intent   [Factual]         [Summary]      [Compare]      │
│   • Choose branch   retriever         retriever      retriever      │
│                          └─────────────────┘──────────────┘         │
│                                       │                             │
│                             ┌─────────▼──────────┐                 │
│                             │   Retriever Agent  │                 │
│                             │                    │                 │
│                             │  Tools available:  │                 │
│                             │  • vector_search() │                 │
│                             │  • bm25_search()   │                 │
│                             │  • get_metadata()  │                 │
│                             └─────────┬──────────┘                 │
│                                       │                             │
│                             ┌─────────▼──────────┐                 │
│                             │  Generator Agent   │                 │
│                             │                    │                 │
│                             │  Tools available:  │                 │
│                             │  • groq_stream()   │                 │
│                             │  • build_context() │                 │
│                             │  • cite_sources()  │                 │
│                             └─────────┬──────────┘                 │
│                                       │                             │
│                             ┌─────────▼──────────┐                 │
│                             │    Grader Agent    │                 │
│                             │                    │                 │
│                             │  Scores answer:    │                 │
│                             │  • faithfulness    │                 │
│                             │  • relevance       │                 │
│                             │  • completeness    │                 │
│                             └─────────┬──────────┘                 │
│                                       │                             │
│                              score >= 0.7? ─── NO ──► Retry        │
│                                       │              (max 2x)      │
│                              score < 0.4? ─── YES ─► "Low         │
│                              YES ▼                   Confidence"   │
│                              [END]                   warning       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                      Services Layer                                 │
│   ChromaDB │ BM25 │ CrossEncoder │ Groq │ SentenceTransformers     │
│                      (all preserved from current code)              │
└─────────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────────┐
│                   Storage Layer                                     │
│   chroma_db/ (vectors)  │  feedback.db (SQLite)  │  logs/           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Final Folder Structure (After All Phases)

```
Distributed-AI-master/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI app (Phase 1 clean)
│   │   ├── api/
│   │   │   └── routes/
│   │   │       ├── upload.py          # MODIFY: Pydantic v2 models
│   │   │       ├── chat.py            # MODIFY: calls agent graph
│   │   │       ├── feedback.py        # NEW: POST /feedback, GET /metrics
│   │   │       └── agents.py          # NEW: GET /agents/status
│   │   ├── agents/                    # NEW Phase 2
│   │   │   ├── __init__.py
│   │   │   ├── state.py               # AgentState TypedDict
│   │   │   ├── planner.py             # Query rewrite + intent detection
│   │   │   ├── retriever.py           # Hybrid search + rerank (tool-calling)
│   │   │   ├── generator.py           # Groq streaming + source citation
│   │   │   ├── grader.py              # Quality scoring + retry logic
│   │   │   └── graph.py               # LangGraph StateGraph definition
│   │   ├── services/                  # EXISTING (mostly preserved)
│   │   │   ├── document_processor.py  # MODIFY: add DOCX, better chunking
│   │   │   ├── text_chunker.py        # MODIFY: fixed-size + overlap chunks
│   │   │   ├── vector_store.py        # KEEP (working well)
│   │   │   ├── hybrid_search.py       # KEEP (excellent)
│   │   │   ├── reranker.py            # KEEP (excellent)
│   │   │   ├── llm_service.py         # KEEP (streaming works)
│   │   │   ├── memory.py              # MODIFY: add long-term memory
│   │   │   ├── query_rewriter.py      # KEEP (used by Planner agent)
│   │   │   ├── evaluator.py           # NEW Phase 3: Ragas-style scoring
│   │   │   └── feedback_store.py      # NEW Phase 3: SQLite storage
│   │   ├── models/                    # EXISTING + EXPAND
│   │   │   ├── request_models.py      # KEEP + expand
│   │   │   └── schemas.py             # NEW: all Pydantic v2 schemas
│   │   └── core/
│   │       ├── config.py              # MODIFY: use pydantic-settings
│   │       ├── logger.py              # MODIFY: structured JSON logging
│   │       └── tracing.py             # NEW: request ID tracing
│   ├── requirements.txt               # ADD: langgraph, ragas, aiofiles
│   ├── Dockerfile                     # NEW Phase 6
│   └── .env
│
├── frontend/
│   └── src/
│       ├── App.tsx                    # REPLACE: 3-panel layout
│       ├── components/
│       │   ├── AgentTracePanel.tsx    # NEW: live agent step visualization
│       │   ├── ChatArea.tsx           # NEW: extracted from App.tsx
│       │   ├── DocumentSidebar.tsx    # NEW: richer document UI
│       │   ├── FeedbackButtons.tsx    # NEW: 👍 👎 + text reason
│       │   ├── MetricsDashboard.tsx   # NEW: Phase 3 charts
│       │   ├── SourceBubbles.tsx      # NEW: expandable source chunks
│       │   └── StreamingMessage.tsx   # NEW: cursor animation
│       ├── hooks/
│       │   ├── useAgentStream.ts      # NEW: SSE parsing for agent events
│       │   └── useDocuments.ts        # NEW: document list management
│       ├── types/
│       │   └── index.ts               # NEW: TypeScript interfaces
│       ├── api/
│       │   └── client.ts             # NEW: Axios instance + all API calls
│       ├── index.css                  # REPLACE: new design system
│       └── main.tsx                   # KEEP
│
├── docker-compose.yml                 # NEW Phase 6
└── README.md                          # NEW: architecture diagrams + demo
```

---

# Phase 1 — Production Code Quality
**Duration**: 2 days | **Risk**: Low | **Impact**: Medium

### What Changes and Why

The entire codebase has commented-out old code, inconsistent error handling, and no structured logging. Before adding agents on top, clean this foundation — otherwise debugging Phase 2 becomes a nightmare.

### Day 1: Schema Cleanup + Pydantic v2

**`backend/app/models/schemas.py`** — NEW file

```python
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class UploadResponse(BaseModel):
    filename: str
    chunks_stored: int
    characters_extracted: int
    message: str

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)

class ChunkResult(BaseModel):
    text: str
    source: str
    chunk_id: Optional[int]
    score: Optional[float]

class FeedbackRequest(BaseModel):
    session_id: str
    question: str
    answer: str
    rating: int  # 1=thumbs up, -1=thumbs down
    comment: Optional[str] = None

class MetricsResponse(BaseModel):
    total_questions: int
    avg_faithfulness: float
    avg_relevance: float
    positive_feedback_rate: float
    last_updated: datetime
```

**`backend/app/core/tracing.py`** — NEW file
- UUID-per-request middleware
- Logs every request: endpoint, duration, request_id, status
- This is "observability" — key term in AI engineering interviews

**`backend/app/services/text_chunker.py`** — MODIFY
- Switch from sentence-based (7 sentences) to **fixed-size with overlap**
- Chunk size: 512 tokens, overlap: 64 tokens
- Add metadata to each chunk: `{source, chunk_index, total_chunks, char_start}`

**`backend/app/services/document_processor.py`** — MODIFY
- Add TXT and DOCX support (python-docx already in requirements)
- Add proper file type routing based on extension

### Day 2: Logging + Route Cleanup

**`backend/app/core/logger.py`** — MODIFY
- Structured JSON logging with timestamps
- Different log levels: DEBUG (chunking), INFO (requests), WARNING (fallbacks), ERROR (failures)

**Remove ALL commented-out dead code** from:
- `main.py` (keep only the active code — 141 lines → ~40 lines)
- `llm_service.py` (keep only the active streaming function — 197 lines → ~50 lines)
- `vector_store.py` (remove old versions — 249 lines → ~120 lines)
- `hybrid_search.py`, `chat.py` (same pattern)

This cleanup makes the project look professional. Dead code is the #1 sign of a learning project vs a production project.

---

# Phase 2 — LangGraph Multi-Agent System
**Duration**: 7 days | **Risk**: Medium | **Impact**: Very High

> This is the core upgrade. Everything hinges on getting this right.

### Key Design Decisions (And Why)

**Why LangGraph over plain function calls:**
- LangGraph gives you a **StateGraph** where each node is an agent that reads/writes shared state
- You get **conditional edges** (route to different agents based on results)
- You get **checkpointing** (replay/debug exact agent steps)
- You get **human-in-the-loop** capability (pause and ask user before proceeding)
- The entire trace is automatically captured in `AgentState.agent_trace`

**Why Reflexion (retry loop):**
- If the Grader scores the answer below 0.6, the graph loops back to the Retriever with a refined query
- Max 2 retries to prevent infinite loops
- This is genuine autonomous behavior — the system improves its own answer without human intervention

**Why tool-calling agents:**
- Each agent declares the tools it can use (functions)
- The agent decides WHICH tool to call based on context
- This is what separates "LLM that calls functions" from "agent that uses tools"

---

### Day 3–4: Agent State + Planner Agent

**`backend/app/agents/state.py`**

```python
from typing import TypedDict, Optional, List, Annotated
import operator

class AgentState(TypedDict):
    # Input
    session_id: str
    question: str
    source: Optional[str]        # document filter

    # Planner output
    rewritten_query: str
    intent: str                  # "factual" | "summary" | "compare"

    # Retriever output
    retrieved_chunks: List[dict]
    reranked_chunks: List[dict]
    context: str

    # Generator output
    answer: str
    sources: List[dict]

    # Grader output
    faithfulness_score: float    # 0.0 to 1.0
    relevance_score: float       # 0.0 to 1.0
    confidence: str              # "high" | "medium" | "low"

    # Control flow
    retry_count: int             # max 2 retries
    should_retry: bool

    # Trace (append-only)
    agent_trace: Annotated[List[dict], operator.add]
    # Each entry: {"agent": "Planner", "action": "...", "duration_ms": 120, "status": "done"}
```

**`backend/app/agents/planner.py`**

```python
async def planner_node(state: AgentState) -> AgentState:
    """
    Responsibilities:
    1. Rewrite query for better retrieval (using existing query_rewriter)
    2. Detect intent: factual / summary / compare
    3. Log trace entry
    """
    start = time.time()
    
    # Rewrite query (reuse existing service)
    rewritten = rewrite_query(state["question"])
    
    # Detect intent via Groq
    intent = await detect_intent(state["question"])
    # Returns: "factual" | "summary" | "compare"
    
    duration = int((time.time() - start) * 1000)
    
    return {
        "rewritten_query": rewritten,
        "intent": intent,
        "agent_trace": [{
            "agent": "Planner",
            "action": f"Rewrote query. Intent detected: {intent}",
            "duration_ms": duration,
            "status": "done"
        }]
    }
```

---

### Day 5: Retriever Agent + Generator Agent

**`backend/app/agents/retriever.py`**

The Retriever agent wraps existing services as **tools**:

```python
# Tool 1: Vector + BM25 hybrid search
def search_tool(query: str, source: str, n_results: int = 10) -> List[dict]:
    return hybrid_search(query, source)

# Tool 2: Cross-encoder reranking
def rerank_tool(query: str, chunks: List[dict]) -> List[dict]:
    return rerank(query, chunks)

# Tool 3: Get document metadata
def metadata_tool(source: str) -> dict:
    return {"filename": source, "chunk_count": len(get_all_chunks(source))}

async def retriever_node(state: AgentState) -> AgentState:
    start = time.time()

    # If retry, refine the query further
    query = state["rewritten_query"]
    if state["retry_count"] > 0:
        query = f"{query} - more specific details"

    chunks = search_tool(query, state.get("source"))
    ranked = rerank_tool(query, chunks)
    context = build_context(ranked[:5])  # top 5 chunks

    duration = int((time.time() - start) * 1000)

    return {
        "retrieved_chunks": chunks,
        "reranked_chunks": ranked,
        "context": context,
        "agent_trace": [{
            "agent": "Retriever",
            "action": f"Retrieved {len(chunks)} chunks, reranked to top 5",
            "duration_ms": duration,
            "status": "done"
        }]
    }
```

**`backend/app/agents/generator.py`**

```python
async def generator_node(state: AgentState) -> AgentState:
    start = time.time()

    # Generate streaming answer (SSE tokens sent in real-time)
    # The full answer is assembled in state for Grader to evaluate
    full_answer = ""
    sources = [{"source": c["source"], "chunk_id": c["chunk_id"]} 
               for c in state["reranked_chunks"][:3]]

    async for token in generate_answer_stream(
        state["question"], 
        state["context"], 
        get_history(state["session_id"])
    ):
        full_answer += token
        # Token streamed to client via SSE (handled in graph.py)

    duration = int((time.time() - start) * 1000)

    return {
        "answer": full_answer,
        "sources": sources,
        "agent_trace": [{
            "agent": "Generator",
            "action": f"Generated {len(full_answer)} character answer",
            "duration_ms": duration,
            "status": "done"
        }]
    }
```

---

### Day 6: Grader Agent + Reflexion Loop

**`backend/app/agents/grader.py`**

This is the most important agent. It uses Groq to evaluate the answer against the context:

```python
GRADER_PROMPT = """
You are an evaluation judge. Given a question, context, and answer, score:

1. Faithfulness (0.0–1.0): Is every claim in the answer supported by the context?
2. Relevance (0.0–1.0): Does the answer actually address the question?

Return ONLY valid JSON: {"faithfulness": 0.85, "relevance": 0.90}

Question: {question}
Context: {context}
Answer: {answer}
"""

async def grader_node(state: AgentState) -> AgentState:
    start = time.time()

    scores = await get_quality_scores(
        state["question"], 
        state["context"], 
        state["answer"]
    )

    faithfulness = scores["faithfulness"]
    relevance = scores["relevance"]
    avg_score = (faithfulness + relevance) / 2

    # Determine if retry is needed
    should_retry = avg_score < 0.6 and state["retry_count"] < 2

    # Determine confidence label
    if avg_score >= 0.75: confidence = "high"
    elif avg_score >= 0.5: confidence = "medium"  
    else: confidence = "low"

    duration = int((time.time() - start) * 1000)

    return {
        "faithfulness_score": faithfulness,
        "relevance_score": relevance,
        "confidence": confidence,
        "should_retry": should_retry,
        "retry_count": state["retry_count"] + (1 if should_retry else 0),
        "agent_trace": [{
            "agent": "Grader",
            "action": f"Scored: faithfulness={faithfulness:.2f}, relevance={relevance:.2f}, confidence={confidence}",
            "duration_ms": duration,
            "status": "retrying" if should_retry else "done"
        }]
    }
```

---

### Day 7: LangGraph Graph Assembly

**`backend/app/agents/graph.py`**

```python
from langgraph.graph import StateGraph, END

def create_agent_graph():
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("planner", planner_node)
    graph.add_node("retriever", retriever_node)
    graph.add_node("generator", generator_node)
    graph.add_node("grader", grader_node)

    # Linear flow
    graph.set_entry_point("planner")
    graph.add_edge("planner", "retriever")
    graph.add_edge("retriever", "generator")
    graph.add_edge("generator", "grader")

    # REFLEXION: conditional edge after grader
    def route_after_grader(state: AgentState) -> str:
        if state["should_retry"]:
            return "retriever"  # Loop back with refined query
        return END

    graph.add_conditional_edges(
        "grader",
        route_after_grader,
        {
            "retriever": "retriever",
            END: END
        }
    )

    # INTENT ROUTING: conditional edge after planner
    # (for future: "summary" → different retriever config)
    
    return graph.compile()

agent_graph = create_agent_graph()
```

**Modify `chat.py`** to use the graph:

```python
@router.post("/")
async def ask_question(request: QuestionRequest, session_id: str = "default", source: str = None):
    
    initial_state = AgentState(
        session_id=session_id,
        question=request.question,
        source=source,
        rewritten_query="",
        intent="factual",
        retry_count=0,
        should_retry=False,
        agent_trace=[],
        # ... other fields with defaults
    )

    async def stream_graph_events():
        async for event in agent_graph.astream_events(initial_state, version="v2"):
            # When agent_trace updates → send [AGENT_TRACE] SSE event
            if event["event"] == "on_chain_stream":
                if "agent_trace" in event["data"]:
                    new_trace = event["data"]["agent_trace"][-1]
                    yield f"data: [AGENT_TRACE]{json.dumps(new_trace)}\n\n"
            
            # When answer tokens arrive → send [TOKEN] SSE event
            if "token" in event["data"]:
                yield f"data: [TOKEN]{event['data']['token']}\n\n"
        
        # After graph completes → send final state
        final_state = ...  # get from graph result
        yield f"data: [SOURCES]{json.dumps(final_state['sources'])}\n\n"
        yield f"data: [SCORE]{json.dumps({'confidence': final_state['confidence']})}\n\n"
        yield f"data: [DONE]\n\n"

    return StreamingResponse(stream_graph_events(), media_type="text/event-stream")
```

---

# Phase 3 — Evaluation + Feedback System
**Duration**: 4 days | **Risk**: Low | **Impact**: High

### Why This Matters for AI Engineering

Every AI engineer interview will ask: "How do you know your RAG system is accurate?" Without evaluation, you can't answer. With this phase, you say: "We track faithfulness and relevance scores per query, store user feedback, and trend them over time."

### Day 8–9: Evaluator Service

**`backend/app/services/evaluator.py`** — NEW

Ragas-inspired evaluation but using Groq as the judge (no Ragas library needed initially):

```python
class EvaluationResult(BaseModel):
    faithfulness: float        # 0-1: answer grounded in context?
    answer_relevance: float    # 0-1: answer addresses question?
    context_precision: float   # 0-1: retrieved chunks were relevant?
    overall_score: float       # weighted average
    explanation: str           # why these scores

async def evaluate_response(
    question: str,
    answer: str,
    context: str,
    retrieved_chunks: List[dict]
) -> EvaluationResult:
    # Uses Groq as LLM judge (same API you already have)
    # Evaluates each metric with a specific prompt
    # Returns structured scores
```

**`backend/app/services/feedback_store.py`** — NEW (SQLite)

```python
# Schema stored in feedback.db:
CREATE TABLE feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    question TEXT,
    answer TEXT,
    faithfulness REAL,
    relevance REAL,
    context_precision REAL,
    user_rating INTEGER,     -- 1=thumbs up, -1=thumbs down, 0=no rating
    user_comment TEXT,
    retry_count INTEGER,     -- how many times agent retried
    confidence TEXT,         -- high/medium/low from Grader
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
```

### Day 10–11: Feedback API Routes

**`backend/app/api/routes/feedback.py`** — NEW

```
POST /api/feedback
  Body: { session_id, question, answer, rating, comment }
  Stores user rating + links to auto-eval scores

GET /api/metrics
  Returns: { total_questions, avg_faithfulness, avg_relevance, 
             positive_rate, trend_data }

GET /api/metrics/history?days=30
  Returns: Array of daily averages for charting
```

---

# Phase 4 — Frontend Complete Rebuild
**Duration**: 7 days | **Risk**: Low | **Impact**: Very High (Demo Value)

> The agent trace panel is the single most impressive thing you can show in an interview.
> When a recruiter sees each agent step light up in real-time, they immediately understand the system.

### New Design System

**Font**: Inter (Google Fonts) — industry standard for AI products  
**Color palette**: Deep midnight background + electric indigo + cyan accents  
**Style**: Glassmorphism cards + gradient borders + smooth animations  

```css
:root {
  --bg-base:       #080c14;   /* deep midnight navy */
  --bg-card:       #0f1628;   /* card surface */
  --bg-glass:      rgba(255,255,255,0.04);
  --accent-purple: #7c3aed;   /* primary actions */
  --accent-cyan:   #06b6d4;   /* highlights */
  --accent-green:  #10b981;   /* success/done states */
  --accent-amber:  #f59e0b;   /* warning/retrying */
  --text-primary:  #f0f4ff;
  --text-muted:    #64748b;
  --border:        rgba(255,255,255,0.08);
}
```

### 3-Panel Layout

```
┌─────────────┬────────────────────────┬──────────────────────┐
│  Sidebar    │      Chat Panel        │   Agent Trace Panel  │
│  (300px)    │      (flex-1)          │   (360px)            │
│             │                        │                      │
│ 📁 Documents│ User message bubbles   │ ⚡ Planner          │
│ ─────────── │                        │    "Rewrote query"   │
│ AI-word.docx│ AI streaming response  │    120ms ✅          │
│ report.pdf  │ with cursor blink      │                      │
│             │                        │ 🔍 Retriever        │
│ 📊 Metrics  │ Source bubbles:        │    "10 chunks found" │
│ ─────────── │ [AI-word.docx #3] ▼   │    340ms ✅          │
│ Faith: 0.84 │   expanded chunk text  │                      │
│ Relev: 0.91 │                        │ ✍️ Generator        │
│ 👍 Rate: 87%│ 👍 👎 [Rate this]     │    "Streaming..."    │
│             │                        │    ⚡ in progress    │
│ [Upload +]  │ [Type your question]   │                      │
└─────────────┴────────────────────────┴──────────────────────┘
```

### Day 12–13: New Components

**`frontend/src/components/AgentTracePanel.tsx`**

This is the centrepiece component. It:
- Receives SSE events of type `[AGENT_TRACE]`
- Each event adds a step card with: agent name, action description, duration badge
- Status styles: `pending` (grey pulse) → `running` (blue spin) → `done` (green check) → `retrying` (amber warning)
- Smooth slide-in animation (CSS transition, no library needed)
- Shows total time taken at the bottom

```tsx
interface TraceStep {
  agent: "Planner" | "Retriever" | "Generator" | "Grader";
  action: string;
  duration_ms: number;
  status: "running" | "done" | "retrying";
}

// Renders as:
// ┌─────────────────────────────┐
// │ ⚡ Planner          120ms  │ ✅
// │ "Rewrote query to: [...]"  │
// └─────────────────────────────┘
```

**`frontend/src/hooks/useAgentStream.ts`**

Custom hook that:
1. Opens an SSE fetch stream to `/api/ask`
2. Parses each SSE line's event type: `[TOKEN]`, `[AGENT_TRACE]`, `[SOURCES]`, `[SCORE]`, `[DONE]`
3. Updates separate state slices for each type
4. Handles retry/error cases

**`frontend/src/components/FeedbackButtons.tsx`**

Appears below each AI message after streaming completes:
- 👍 / 👎 buttons (styled, not plain HTML)
- Optional text field: "Tell us why (optional)"
- On submit: POST to `/api/feedback`, show "Thanks for your feedback!" toast

**`frontend/src/components/SourceBubbles.tsx`**

Each source is a clickable chip. On click, it expands to show:
- Raw chunk text
- Document name + chunk ID
- Relevance score badge

**`frontend/src/components/MetricsDashboard.tsx`**

Small panel in the sidebar showing:
- Faithfulness trend (sparkline)
- User satisfaction rate
- Total questions answered
- Last 7 days avg score

### Day 14–15: Wire Everything Together

- Replace single `App.tsx` monolith with component tree
- `useAgentStream` hook drives all three panels simultaneously
- Add document drag-and-drop with upload progress bar
- Add keyboard shortcuts: `Enter` to send, `Escape` to cancel

---

# Phase 5 — Self-Improving Feedback Loop
**Duration**: 4 days | **Risk**: Medium | **Impact**: High (Unique Feature)

> This is what makes the project standout. Most RAG projects are static. Yours learns.

### What "Self-Improving" Means Here

After collecting enough feedback, the system automatically:

1. **Detects weak areas**: Which question types consistently score low?
2. **Adjusts chunk size**: If faithfulness is low, chunks might be too large (splitting context)
3. **Refines prompts**: If relevance is low, the generator prompt needs adjustment
4. **Reports insights**: What has improved over time?

**`backend/app/services/self_improver.py`** — NEW

```python
class ImprovementInsight(BaseModel):
    metric: str
    trend: str           # "improving" | "declining" | "stable"
    suggestion: str      # human-readable improvement action
    auto_applied: bool   # was this automatically adjusted?

async def analyze_feedback_trends(days: int = 7) -> List[ImprovementInsight]:
    """Runs weekly to detect patterns and suggest/apply improvements."""
    
    # Queries feedback.db for recent scores
    # Identifies: which question intents fail most often
    # Identifies: time-of-day patterns, document-specific failures
    # Returns actionable insights
```

**`GET /api/improvements`** — New endpoint

Returns:
```json
{
  "insights": [
    {
      "metric": "faithfulness",
      "trend": "improving",
      "suggestion": "Cross-encoder reranking is working well",
      "auto_applied": false
    },
    {
      "metric": "relevance", 
      "trend": "declining",
      "suggestion": "Questions about dates/numbers score lowest. Consider metadata filtering.",
      "auto_applied": false
    }
  ],
  "last_analyzed": "2026-03-30T10:00:00"
}
```

---

# Phase 6 — Docker + Distributed + Polish
**Duration**: 4 days | **Risk**: Low | **Impact**: High (Deployment Signal)

### Day 22–23: Docker

**`backend/Dockerfile`**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y tesseract-ocr poppler-utils && apt-get clean
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

**`frontend/Dockerfile`**
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

**`docker-compose.yml`**
```yaml
version: "3.9"
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    volumes:
      - ./backend/chroma_db:/app/chroma_db
      - ./backend/feedback.db:/app/feedback.db
    env_file: ./backend/.env
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s

  frontend:
    build: ./frontend
    ports: ["80:80"]
    depends_on:
      backend:
        condition: service_healthy
```

### Day 24–25: README + Final Polish

**`README.md`** — The project's public face

Must include:
- Architecture diagram (Mermaid code + rendered)
- Feature list with checkmarks
- Quick start: `git clone → docker compose up → open localhost`
- Screenshot gallery: chat UI, agent trace panel, metrics dashboard
- Tech stack badges
- Live demo link

---

# Day-by-Day Implementation Schedule

| Day | Phase | Task | Deliverable |
|-----|-------|------|-------------|
| 1 | P1 | Schemas + Pydantic v2 | All types defined, dead code removed |
| 2 | P1 | Logging + chunking upgrade | Structured logs, overlap chunking |
| 3 | P2 | AgentState + Planner | `state.py`, `planner.py` working |
| 4 | P2 | Retriever agent (tool-calling) | `retriever.py` with 3 tools |
| 5 | P2 | Generator agent | `generator.py` streaming through graph |
| 6 | P2 | Grader + Reflexion loop | `grader.py`, retry logic working |
| 7 | P2 | Graph assembly + chat.py | Full graph runs, SSE sends agent trace |
| 8 | P3 | Evaluator service | Groq-based scoring working |
| 9 | P3 | SQLite feedback store | Schema created, CRUD working |
| 10 | P3 | Feedback API routes | `/feedback`, `/metrics` endpoints |
| 11 | P3 | Test full backend E2E | Upload → ask → evaluate → feedback works |
| 12 | P4 | Design system + CSS | New color palette, typography |
| 13 | P4 | AgentTracePanel component | Live step visualization working |
| 14 | P4 | Chat + sidebar components | 3-panel layout assembled |
| 15 | P4 | Source bubbles + feedback UI | Expandable sources, 👍👎 buttons |
| 16 | P4 | MetricsDashboard | Charts connected to `/metrics` |
| 17 | P4 | `useAgentStream` hook | SSE parsing all event types |
| 18 | P4 | Wire frontend to backend | Full E2E working with new UI |
| 19 | P5 | Feedback trend analysis | `self_improver.py` + insights endpoint |
| 20 | P5 | Dashboard shows insights | Frontend shows improvement suggestions |
| 21 | P5 | Test self-improving loop | 20+ test queries, see metrics change |
| 22 | P6 | Backend Dockerfile | `docker build` succeeds |
| 23 | P6 | Frontend Dockerfile + compose | `docker compose up` starts everything |
| 24 | P6 | README with architecture | Diagrams, screenshots, quick start |
| 25 | P6 | Final polish + demo prep | Fix any remaining bugs, record demo |

---

# What You Can Say in an Interview

**"Tell me about a project you built."**

> "I built a multi-agent RAG system using LangGraph for orchestration. The system has four specialized agents — Planner, Retriever, Generator, and Grader — connected in a StateGraph with conditional routing and a Reflexion self-correction loop. If the Grader scores an answer below 0.6 on faithfulness, the graph automatically routes back to the Retriever with a refined query. I implemented hybrid search combining vector similarity and BM25 keyword ranking with cross-encoder reranking. The frontend shows a live agent trace panel so users can see exactly which agent is running and how long each step took. I added Ragas-inspired evaluation metrics and stored them in SQLite to track system quality over time. The whole thing runs in Docker with docker-compose."

That answer covers: LangGraph, RAG pipeline, hybrid retrieval, evaluation, system design, full-stack, Docker. That is an AI Engineer answer.

---

# Requirements Additions (New packages to add)

```
# Add to requirements.txt
langgraph>=0.2.0          # Already there ✅
aiofiles==23.2.1          # Async file handling
aiosqlite==0.19.0         # Async SQLite for feedback store  
httpx==0.27.0             # Async HTTP (for evaluator Groq calls)
python-jose==3.3.0        # JWT tokens (if adding auth later)
tenacity==8.2.3           # Retry decorator for service calls

# Frontend (run: npm install)
framer-motion             # Smooth agent trace animations
recharts                  # Metrics dashboard charts
react-hot-toast           # Feedback submission notifications
```

---

## Start Here — Day 1 First Task

Open `backend/app/models/schemas.py` and create it with the Pydantic v2 models shown in Phase 1.

Then remove all commented-out code from `main.py`, `llm_service.py`, and `vector_store.py`.

These two tasks take 2-3 hours and immediately make the project look professional.

**Reply with "Day 1 done" after completing, and I will give you the exact Day 2 code.**
