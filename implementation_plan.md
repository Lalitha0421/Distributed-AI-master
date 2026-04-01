# Distributed Multi-Agent AI Knowledge System — Upgrade Plan

## What We're Upgrading

You have a solid single-pipeline RAG system (FastAPI + ChromaDB + Groq + Hybrid Search + React frontend). 

The goal is to evolve it into a **Production-Grade Multi-Agent AI System** that looks like real AI Engineering work — the kind that lands you a mid-level AI Engineer role in 2026.

We'll go in **4 focused phases**, each building directly on the previous one. No throwaway work.

---

## Current State Audit

### ✅ What's Already Great
| Component | Status | Quality |
|---|---|---|
| FastAPI backend | ✅ Working | Good |
| ChromaDB vector store | ✅ Working | Good |
| Hybrid Search (Vector + BM25) | ✅ Working | **Excellent** – rare in student projects |
| Cross-encoder reranking | ✅ Working | **Excellent** – production-level |
| Query rewriting via Groq | ✅ Working | Good |
| Streaming SSE responses | ✅ Working | Good |
| Session memory | ✅ Working | Basic |
| React + Vite + TypeScript frontend | ✅ Working | Functional |
| CORS, modular routers | ✅ Working | Clean |

### ❌ What's Missing (The AI Engineer Gap)
| Feature | Why It Matters |
|---|---|
| Multi-Agent orchestration (LangGraph) | Core differentiator vs basic RAG |
| Agent visibility in UI | Shows system thinking, not just answers |
| Evaluation & metrics (Ragas) | Proves the system works scientifically |
| Feedback loop / self-improvement | Makes the project "live" and intelligent |
| Proper Pydantic v2 models everywhere | Production code quality signal |
| Structured logging + tracing | Real engineering, not scripting |
| Docker containerization | Shows deployment awareness |

---

## Architecture After Upgrade

```
┌─────────────────────────────────────────────────────────┐
│                   React Frontend                        │
│  Upload → Select Doc → Chat → See Agent Trace → Rate   │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP + SSE
┌────────────────────────▼────────────────────────────────┐
│                   FastAPI Gateway                       │
│   /api/upload  /api/ask  /api/agents  /api/feedback     │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│            LangGraph Multi-Agent Orchestrator           │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐  │
│  │ Planner  │→ │Retriever │→ │Generator │→ │Grader  │  │
│  │  Agent   │  │  Agent   │  │  Agent   │  │ Agent  │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘  │
│       ↑               ↑           ↑              ↓      │
│  [Query Rewrite]  [Hybrid    [Streaming      [Score +   │
│  [Intent Detect]   Search +   Generation]    Feedback]  │
│                    Rerank]                              │
└─────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              Services Layer (unchanged)                 │
│  ChromaDB  │  BM25  │  Groq  │  SentenceTransformers   │
└─────────────────────────────────────────────────────────┘
```

---

## Phased Implementation Plan

### Phase 1 — Code Quality & Strict Models (Days 1–3)
**Goal**: Clean the codebase to production standards before adding complexity.

#### [MODIFY] `backend/app/services/` — All service files
- Add strict **Pydantic v2** input/output models for all service functions
- Add proper **structured logging** (timestamps, log levels, context IDs)
- Remove all commented-out dead code (the old versions clog files)
- Add `try/except` with typed error responses everywhere

#### [NEW] `backend/app/models/schemas.py`
- `UploadResponse`, `AskRequest`, `AskResponse`, `ChunkResult`, `AgentState` Pydantic models
- Used by all routes and services for type safety

#### [NEW] `backend/app/core/tracing.py`
- Simple request ID generator (UUID per request)
- Log every API call with request_id, duration, service name
- This is "observability" — a key word in AI engineering interviews

#### [MODIFY] `backend/app/api/routes/chat.py` & `upload.py`
- Use Pydantic models for all request/response validation
- Add request_id to every log line

---

### Phase 2 — LangGraph Multi-Agent Orchestration (Days 4–10)
**Goal**: Replace the linear pipeline with a stateful, inspectable agent graph.

> [!IMPORTANT]
> This is the core upgrade. LangGraph is the 2026 standard for production multi-agent systems. It gives you: checkpointing, conditional routing, human-in-the-loop, and agent state visibility — all things that plain function chains cannot do.

#### [NEW] `backend/app/agents/` — New agents module

**`agent_state.py`** — Shared state object that flows through the graph
```python
class AgentState(TypedDict):
    session_id: str
    question: str
    rewritten_query: str
    intent: str               # "factual", "summary", "compare"
    retrieved_chunks: list
    reranked_chunks: list
    context: str
    answer: str
    sources: list
    agent_trace: list         # List of {"agent": name, "action": str, "duration_ms": int}
    feedback_score: Optional[int]
```

**`planner_agent.py`** — First node in the graph
- Receives raw question
- Rewrites query for better retrieval
- Detects intent (factual Q&A / summarize / compare)
- Routes to appropriate retrieval strategy
- Logs: `{"agent": "Planner", "action": "Query rewritten + intent=factual", "ms": 120}`

**`retriever_agent.py`** — Second node
- Runs hybrid search (vector + BM25)
- Applies cross-encoder reranking
- Returns top-K chunks with scores
- Logs each retrieval step

**`generator_agent.py`** — Third node
- Assembles context from chunks
- Generates streaming answer via Groq
- Builds source citations
- Handles "no relevant info" gracefully

**`grader_agent.py`** — Fourth node (runs after generation)
- Scores answer quality (0-1) using a simple Groq prompt
- Detects potential hallucination (answer not grounded in context)
- Adds confidence score to response

**`graph.py`** — LangGraph StateGraph definition
```
Planner → Retriever → Generator → Grader → END
              ↑
        (conditional: if intent=summary → SummaryRetriever)
```

#### [MODIFY] `backend/app/api/routes/chat.py`
- Replace direct service calls with `graph.invoke()`
- Stream both answer tokens AND agent trace events via SSE
- New SSE event types: `[AGENT_TRACE]`, `[SOURCES]`, `[TOKEN]`, `[DONE]`

#### [NEW] `backend/app/api/routes/agents.py`
- `GET /api/agents/status` — Current agent graph status
- `GET /api/agents/trace/{session_id}` — Full trace for a session

---

### Phase 3 — Evaluation Dashboard (Days 11–16)
**Goal**: Add measurable quality metrics. This is what separates projects from toys.

#### [NEW] `backend/app/services/evaluator.py`
- **Faithfulness score**: Does the answer use the context? (Groq-based judge)
- **Relevance score**: Is the retrieved context relevant to the question?
- **Answer completeness**: Does it fully answer the question?
- Store all metrics in a SQLite evaluation log (no extra DB needed)

#### [NEW] `backend/app/api/routes/evaluation.py`
- `POST /api/feedback` — User submits 👍/👎 + optional text
- `GET /api/metrics` — Returns aggregated quality metrics
- `GET /api/metrics/history` — Returns chart data (scores over time)

#### [NEW] `backend/app/services/feedback_store.py`
- SQLite-backed storage for user feedback + auto-eval scores
- Simple schema: `session_id, question, answer, faithfulness, relevance, user_rating, timestamp`

---

### Phase 4 — Frontend Multi-Agent UI (Days 17–25)
**Goal**: Make the agent orchestration **visible** to the user. This is the "wow" factor in demos.

> [!IMPORTANT]
> The UI visual upgrade is as important as the backend. Recruiters and interviewers will see a live demo. The current frontend is functional but plain. We rebuild it to be stunning.

#### [MODIFY] `frontend/src/` — Complete UI Rebuild

**New layout: 3-panel design**
```
┌──────────┬──────────────────────┬───────────────┐
│          │                      │  Agent Trace  │
│ Sidebar  │    Chat Area         │  Panel (live) │
│ (docs +  │  (messages +         │               │
│ metrics) │   streaming)         │  📊 Metrics   │
│          │                      │  Panel        │
└──────────┴──────────────────────┴───────────────┘
```

**New components to build:**

| Component | Description |
|---|---|
| `AgentTracePanel.tsx` | Live updates as each agent runs. Shows spinner → ✅ per agent |
| `MetricsDashboard.tsx` | Charts: Faithfulness over time, user ratings bar chart |
| `FeedbackButtons.tsx` | 👍 / 👎 + optional text reason below each answer |
| `DocumentLibrary.tsx` | Richer doc list with upload progress bar, doc stats |
| `SourceBubbles.tsx` | Clickable source chunks that expand to show raw text |
| `StreamingMessage.tsx` | Improved streaming with cursor animation |

**Design system upgrade:**
- Switch from basic zinc/blue to a rich dark theme with purple/cyan accents
- Glassmorphism cards for panels
- Smooth Framer Motion animations for agent trace appearance
- Google Font: **Inter** (already industry standard for AI tools)

---

### Phase 5 — Docker + Final Polish (Days 26–30)
**Goal**: Make the entire system deployable with a single command.

#### [NEW] `docker-compose.yml` (project root)
```yaml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    volumes: ["./backend/chroma_db:/app/chroma_db"]
    env_file: ./backend/.env
    
  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    depends_on: [backend]
```

#### [NEW] `backend/Dockerfile`
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### [NEW] `frontend/Dockerfile`
- Multi-stage: build with node → serve with nginx

#### [NEW] `README.md` (project root — major upgrade)
- Architecture diagram (Mermaid)
- Screenshot gallery
- Quick start with Docker
- Feature list with badges
- Live demo link (Render/Railway for backend, Vercel for frontend)

---

## What the Full System Looks Like to a Recruiter

```
Resume bullet: "Built a production multi-agent RAG system using LangGraph, 
FastAPI, and ChromaDB with measurable evaluation metrics (faithfulness, 
relevance), real-time agent trace visibility, and streaming responses via SSE."
```

Skills demonstrated:
- **LangGraph** (most in-demand agent framework, 2026)
- **FastAPI** with streaming + SSE
- **RAG Engineering** (hybrid search, reranking, query rewriting)
- **Evaluation** (Ragas-style metrics, auto-grading)
- **Full-stack** (React + TypeScript + real-time UI updates)
- **Docker** (containerized deployment)
- **Observability** (request tracing, structured logs)
- **Self-improving loop** (feedback → metrics → system improvement)

---

## Verification Plan

### After Each Phase
- Phase 1: All routes return typed Pydantic responses, logs are structured JSON
- Phase 2: `POST /api/ask` response includes `agent_trace` array + streaming works
- Phase 3: `GET /api/metrics` returns faithfulness/relevance scores
- Phase 4: Agent trace panel animates live in the UI during a question
- Phase 5: `docker compose up` starts the full system from scratch

### Demo Flow (for interviews)
1. Open the app → Upload a PDF
2. Ask a question → Watch agent trace panel light up (Planner → Retriever → Generator → Grader)
3. See streaming answer with source citations
4. Click 👍/👎 feedback
5. Open metrics dashboard → Show faithfulness score trend

---

## Open Questions

> [!IMPORTANT]
> Please answer these before we begin — they affect implementation decisions:

1. **Frontend preference**: Do you want to keep Tailwind CSS (current) or switch to Vanilla CSS? Tailwind is fine since you already have it.
2. **Evaluation depth**: Should the auto-evaluator run on EVERY question (slower, ~2s extra) or only when you click an "Evaluate" button?
3. **Agent trace visibility**: Should the agent trace panel be always visible (3-panel layout) or collapsible (toggle button)?
4. **Animations**: Should we add Framer Motion for smooth agent-step animations, or keep it CSS-only?
5. **Deployment target**: Are you planning to deploy to Render/Railway/Vercel, or just local for now?
6. **Day 1 start**: Should we begin immediately with Phase 1 (clean code + Pydantic models), or go straight to Phase 2 (LangGraph agents)?
