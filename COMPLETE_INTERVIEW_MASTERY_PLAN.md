# 🎓 COMPLETE INTERVIEW MASTERY PLAN
## Distributed Multi-Agent RAG System — "Everything on Your Fingertips"

> **How to use this document**: Read it once end-to-end, then bookmark it.
> Before the interview, read it once again. You will walk in 100% confident.
> **The most important thing**: You don't need to memorize code. You need to be able to *explain decisions*.

---

## ⚡ THE 30-SECOND ELEVATOR PITCH (MEMORIZE THIS EXACTLY)

> *"I built a production-grade Multi-Agent RAG system deployed on Hugging Face Spaces. It uses LangGraph to orchestrate four specialized AI agents: a Planner that rewrites queries using Groq LLM, a Retriever that does Hybrid Search combining Vector and BM25, a Generator that streams answers via SSE, and a Grader that autonomously evaluates its own answer for faithfulness. If the quality is low, the system loops back and retries — this is called the Reflexion pattern. The entire agent pipeline is visualized in real-time on a React frontend. It's secured with JWT authentication and deployed as a multi-service Docker container behind an Nginx reverse proxy."*

---

## 📐 THE BIG PICTURE (What the System Does)

```
User types a question on the React UI
           ↓
  FastAPI receives the request (JWT verified)
           ↓
   LangGraph StateGraph kicks off:
    [Planner] → rewrites the query
    [Retriever] → Hybrid Search + CrossEncoder rerank
    [Generator] → Groq LLM streams the answer
    [Grader] → scores faithfulness (0.0 to 1.0)
        ↓ if score < 0.7 → LOOP BACK to Retriever (max 2 retries)
        ↓ if score ≥ 0.7 → send answer to frontend
           ↓
  Frontend shows: streaming answer + live agent trace
  Background: automatic evaluation saved to SQLite
```

---

## 🧠 SECTION 1: LANGGRAPH — THE BRAIN

### What is LangGraph?
LangGraph is a library that extends LangChain to build **stateful, multi-actor AI applications** using a **directed graph**. Think of it like: each agent is a "node", and the arrows between them are "edges."

### Your Actual Code — graph.py
```python
builder = StateGraph(AgentState)

builder.add_node("planner",   planner_agent)
builder.add_node("retriever", retriever_agent)
builder.add_node("generator", generator_agent)
builder.add_node("grader",    grader_agent)

builder.add_edge(START, "planner")
builder.add_edge("planner",   "retriever")
builder.add_edge("retriever", "generator")
builder.add_edge("generator", "grader")

# THE REFLEXION LOOP — the most unique part
def route_after_grader(state: AgentState) -> str:
    if state.get("should_retry", False):
        return "retriever"   # ← loop back!
    return END

builder.add_conditional_edges("grader", route_after_grader, {...})
```

### What is AgentState (agent_state.py)?
It is a **shared memory object** (TypedDict) that all 4 agents read from and write to. Each agent gets the full state and returns *only the fields it changed*.

Key insight in your code:
```python
agent_trace: Annotated[List[dict], operator.add]
```
This means: when Agent A returns `{"agent_trace": [entry1]}` and Agent B returns `{"agent_trace": [entry2]}`, LangGraph uses `operator.add` to **append**, not overwrite. So the final trace is `[entry1, entry2]`. This is how the UI sees all 4 agent steps.

### Interview Q&A

**Q: Why LangGraph over a plain for-loop?**
> "A loop can't go backward. LangGraph gives me a **conditional edge** — a decision point. When the Grader gives a low score, the graph routes *back* to the Retriever with a different query. A for-loop can't do that without major spaghetti code. Also, I get automatic state merging: every agent updates only its own fields, and LangGraph merges them — I don't manage shared dictionaries manually."

**Q: How does the state flow between agents?**
> "All four agents share a single `AgentState` TypedDict. The Planner writes `rewritten_query`. The Retriever reads that and writes `retrieved_chunks` and `context`. The Generator reads `context` and writes `answer`. The Grader reads `question`, `context`, and `answer` and writes `confidence_score` and `should_retry`. LangGraph handles state merging automatically."

**Q: What is the Reflexion pattern?**
> "Reflexion is a technique where an AI evaluates its own outputs and corrects itself. In my system, the Grader agent uses the Groq LLM to score the answer from 0.0 to 1.0. If the score is below 0.7, `should_retry=True` is set in the state. The graph's conditional edge routes back to the Retriever, which this time uses the **original** question (not the rewritten one) to broaden the search. Max 2 retries to prevent infinite loops."

---

## 🔍 SECTION 2: THE 4 AGENTS IN DETAIL

### Agent 1: Planner (planner_agent.py)
**Role**: Takes the raw user question and makes it "search-friendly."

**What it does in your code**:
1. Sends the question to **Groq LLM** with a special prompt (`_PLANNER_PROMPT`)
2. Uses `response_format={"type": "json_object"}` to force structured JSON output
3. Extracts `rewritten_query` and `intent` (factual / summary / compare)
4. Returns these + a trace entry for the UI

**Actual prompt logic** (simplified):
```
"what are his projects" → "Technical projects, development achievements, 
                           list of engineering works"
```

**Key detail**: `temperature=0` — this means the LLM gives **deterministic output**. No randomness in the planning phase because we need consistent query rewriting.

**Interview Q: Why rewrite the query at all?**
> "User queries are conversational ('what does he do?') but document chunks are formal text. The Planner bridges that gap. For example, if a resume says 'Built a distributed knowledge system using Python' and a user asks 'what projects does he have?' — the rewritten query 'technical projects engineering works' is much more likely to match via BM25 keyword search."

---

### Agent 2: Retriever (retriever_agent.py)
**Role**: Find the most relevant chunks from the knowledge base.

**Three-step process in your code**:
```
Step 1: hybrid_search(query, source)  → gets raw candidates
Step 2: rerank(query, raw_chunks)     → cross-encoder sorts them
Step 3: final_chunks[:top_k]          → take top K (default 5)
Step 4: "\n\n".join(c["text"] for c in final_chunks)  → build context string
```

**Retry behaviour** (critical detail):
```python
if state.get("retry_count", 0) > 0:
    query = state["question"]   # use ORIGINAL question, not rewritten
```
Why? Because the rewritten query was already tried and failed (Grader scored it low). On retry, broadening back to the raw question gives a different set of results.

---

### Agent 3: Generator (generator_agent.py)
**Role**: Call the Groq LLM to produce the answer from the context.

**What it does**:
1. Takes `question` and `context` from state
2. Calls `generate_answer_stream()` service (streaming Groq API)
3. Collects all tokens, joins them into `final_answer`
4. Returns the full answer for the Grader to evaluate

**Why collect all tokens?** Because the Grader needs the **complete** answer to evaluate faithfulness. You can't evaluate a half-written answer.

**How does streaming work if you collect all tokens first?**
> The streaming to the *user* happens in `chat.py`, not inside the Generator agent. When node `"generator"` finishes, `chat.py`'s `_graph_stream()` sends the answer as `[TOKEN]` SSE event. The *agent* collects it all; the *route* streams it.

---

### Agent 4: Grader (grader_agent.py)
**Role**: The quality control agent. Decides if the answer is good enough.

**The actual Grader prompt key checks**:
1. **FAITHFULNESS**: "Is every claim 100% grounded in context?" (detects hallucination)
2. **RELEVANCE**: "Does it actually answer the question?"
3. **COMPLETENESS**: "Is the answer cut off? Are all items listed?"

**The retry logic**:
```python
should_retry = confidence < 0.7 and state.get("retry_count", 0) < 2
```
- `confidence < 0.7` → quality threshold
- `retry_count < 2` → safety cap (max 2 retries, then accept whatever we have)

**Interview Q: How do you prevent infinite loops?**
> "The `retry_count` field in AgentState increments each time the Grader triggers a retry. The condition `retry_count < 2` hard caps it at two retries. Even if all retries score below 0.7, the graph exits and shows the best answer the system could produce."

**Interview Q: Could the LLM Grader itself hallucinate in its scoring?**
> "Yes — that's a known limitation of LLM-as-judge. I mitigate it by using `temperature=0` (no randomness) and a very strict JSON-only output format so parsing errors are caught. For production scale, I would use a dedicated fine-tuned evaluator model, but for this project, Groq's Llama3-70B at temperature 0 is reliable enough."

---

## 🔎 SECTION 3: HYBRID SEARCH — THE RETRIEVAL ENGINE

### The Core Concept
A single search method is not good enough:
- **Vector Search only**: Fast, semantic, but misses exact keywords ("GPT-4" vs "large language model")
- **BM25 only**: Great for exact keywords but completely ignores meaning

**Hybrid = combine both for maximum recall.**

### Your Actual Code (hybrid_search.py)

**Vector Search part**:
```python
vector_results = search_chunks(query, source)
```
This calls ChromaDB. Your embedding model `all-MiniLM-L6-v2` converts the query to a 384-dimension vector and finds the closest chunks by **cosine similarity**.

**BM25 part**:
```python
bm25 = BM25Okapi(tokenized)
scores = bm25.get_scores(query.lower().split())
bm25_ranked = sorted(zip(all_chunks, scores), key=lambda x: x[1], reverse=True)
bm25_results = [item[0] for item in bm25_ranked[:5]]
```
BM25 tokenizes every chunk and the query, then uses the **Okapi BM25 formula** (TF-IDF variant) to rank them. No neural network — pure statistics.

**Merge strategy**:
```python
seen = {(r["source"], r.get("chunk_id")): r for r in vector_results}
for r in bm25_results:
    key = (r["source"], r.get("chunk_id"))
    if key not in seen:
        seen[key] = r
```
Vector results take priority (they appear first). BM25 results are **deduplicated** using (source, chunk_id) as the unique key. The union of both gives you the best of both worlds.

### Interview Q&A

**Q: What is the difference between Vector Search and BM25?**
> "Vector search uses neural embeddings — it converts text to high-dimensional vectors and finds chunks that are *semantically* close. BM25 is a keyword scoring function based on term frequency (TF) and inverse document frequency (IDF). They're complementary: vector search finds *meaning*, BM25 finds *exact terms*. For example, a user asking 'tell me about Redis' — vector search might return chunks about 'in-memory data stores' (semantic match), while BM25 finds the chunk with the word 'Redis' literally in it. Hybrid search catches both."

**Q: Why did you choose `all-MiniLM-L6-v2` for embeddings?**
> "It's a lightweight but highly accurate model from SentenceTransformers. It produces 384-dimension vectors which gives a good balance of speed and accuracy. It's widely used in production RAG systems. More importantly, I pre-download it in the Dockerfile so there's no cold-start delay at runtime."

---

## ⚖️ SECTION 4: CROSS-ENCODER RERANKING

### Why Reranking?
After hybrid search, you have ~10-15 candidates. But which are the BEST 5?

- **Bi-Encoder** (what you used for search): Encodes query and chunk *separately*, then compares. Fast, scalable.
- **Cross-Encoder**: Encodes query + chunk *together* in one pass. Much more accurate, but slower.

You use bi-encoder for search (fast, over thousands of chunks), then cross-encoder for reranking (accurate, over 10-15 candidates). 

### Your Actual Code (reranker.py)
```python
_reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

pairs = [(query, c["text"]) for c in chunks]  # (query, chunk) pairs
scores = _reranker.predict(pairs)              # joint scoring

ranked = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)
```

**Model**: `ms-marco-MiniLM-L-6-v2` — trained on the **MS MARCO** dataset (Microsoft's large-scale passage ranking dataset with millions of query-document pairs from web search). This makes it excellent at ranking text passages.

### Interview Q&A

**Q: How does the Cross-Encoder differ from cosine similarity?**
> "Cosine similarity compares two independent vectors: one for the query, one for the chunk. The Cross-Encoder sees the query AND the chunk together as a single sequence. It can learn interactions between tokens from both sides. For example, it understands that 'machine' in the query relates to 'model' in the chunk because they appear in the same attention window. This is significantly more accurate."

**Q: Why not use the cross-encoder for the initial search?**
> "Because it doesn't produce standalone embeddings — it requires the query and chunk together as input. If I have 100,000 chunks, I'd need to run 100,000 inference passes for every single query. That's too slow. So I use the fast bi-encoder for initial retrieval (gets top 10), then the accurate cross-encoder for reranking only those 10."

---

## 🧱 SECTION 5: VECTOR STORE (ChromaDB)

### Architecture Decision
You use a **single global collection** (`ai_knowledge_base`) for ALL documents.

```python
_KNOWLEDGE_COLLECTION_NAME = "ai_knowledge_base"
```

Filtering by document is done via **metadata**:
```python
where_filter = {"source": source} if source else None
results = collection.query(query_embeddings=[...], where=where_filter)
```

**Why one collection?** Allows **cross-document search**. If a user uploads 3 PDFs and asks a question, your system searches all three simultaneously and finds the best chunk across all of them.

### Chunk Storage Schema
```python
ids = [f"{document_name}_{i}" for i in range(len(chunks))]
metadatas = [{"source": document_name, "chunk_id": i} for i in range(len(chunks))]
```
Each chunk has a globally unique ID and carries its source document name + position index.

### Interview Q: Is ChromaDB scalable?
> "For a personal knowledge assistant — absolutely. For enterprise scale with millions of documents, I would migrate to a managed vector database like Weaviate, Pinecone, or Qdrant. The key is that my `vector_store.py` is a **service abstraction layer** — the agents call `search_chunks()`, not ChromaDB directly. So swapping the backend is a 1-file change."

---

## 📦 SECTION 6: DOCUMENT PROCESSING PIPELINE

### The Full Upload Flow (upload.py)
```
User uploads PDF/DOCX/TXT
         ↓
1. Save file to disk (settings.upload_dir)
2. extract_text_from_file(file_path) → raw text string
3. split_text_into_chunks(text)     → List[str]  
4. store_chunks(chunks, filename)    → embeds + stores in ChromaDB
```

### Chunking Strategy (text_chunker.py)
**What you implemented**: Fixed-size chunking with smart boundary detection.

- **chunk_size**: 512 characters (from settings)
- **chunk_overlap**: 64 characters

**Smart boundary logic** (critical detail to mention):
```python
for sep in (".", "\n", " "):
    pos = segment.rfind(sep, midpoint)   # find last separator in second half
    if pos != -1:
        end = start + pos + 1
        break
```
Instead of brutally cutting at 512 characters, you look backward from position 512 to find the last `.`, `\n`, or space. This means chunks end at **sentence or paragraph boundaries**, not in the middle of a word.

**Why overlap?** The 64-character overlap means that a concept split across two chunks will appear in *both*, ensuring retrieval doesn't miss it.

### OCR Support
```
# In document_processor.py
pdf → pdf2image → PIL images → pytesseract.image_to_string()
```
**Why OCR?** Many PDFs are scanned images, not real text. Standard `pypdf` would return empty pages. OCR extracts text from the images.

**Interview Q: What types of documents do you support?**
> "PDF (including scanned with OCR), DOCX using python-docx, and plain TXT and Markdown. The upload route checks the file extension and routes to the appropriate extractor. OCR is handled by Tesseract via pytesseract, with poppler-utils to convert PDF pages to images first."

---

## 🌊 SECTION 7: STREAMING (SSE)

### What is SSE?
Server-Sent Events is a one-way HTTP stream from server to client. The connection *stays open*, and the server pushes events as they happen. Unlike WebSockets, it's HTTP-only (no protocol upgrade), which makes it simpler for text streaming.

### Your SSE Protocol (chat.py)
```python
yield f"data: [AGENT_TRACE]{json.dumps(trace)}\n\n"  # → agent step finished
yield f"data: [TOKEN]{safe_answer}\n\n"              # → the answer text
yield f"data: [SOURCES]{json.dumps(sources)}\n\n"   # → source documents
yield f"data: [DONE]\n\n"                            # → stream ended
```

**Why JSON-encode the answer?**
```python
safe_answer = json.dumps(answer)
```
Because the SSE protocol uses `\n\n` as the event delimiter. If the raw answer contains newlines, the protocol breaks. `json.dumps` escapes all newlines, making the stream safe.

### How the Frontend Parses It
The React hook `useAgentStream.ts` opens a `fetch` stream, reads each line, finds the prefix (`[TOKEN]`, `[AGENT_TRACE]`, etc.), and updates the corresponding React state slice.

### Interview Q: Why SSE instead of WebSockets?
> "SSE is simpler for unidirectional streaming—server to client. The LLM response is inherently one-directional, no need for two-way communication. SSE works over standard HTTP/1.1, doesn't need protocol upgrades, and is natively supported by browsers. For bi-directional communication (like a collaborative doc editor), I'd use WebSockets."

---

## 🔐 SECTION 8: SECURITY (JWT)

### The Full Auth Flow (security.py)
```
User submits username + password to POST /api/auth/login
         ↓
Backend: passlib verifies bcrypt hash
         ↓
Backend: creates JWT token with python-jose
         {"sub": "admin", "exp": <timestamp>}
         signed with settings.secret_key using HS256
         ↓
Frontend: stores token in localStorage
         ↓
Every subsequent request: Authorization: Bearer <token> header
         ↓
get_current_user() dependency: decodes + validates token
```

### JWT Structure
```
Header: {"alg": "HS256", "typ": "JWT"}
Payload: {"sub": "admin", "exp": 1712345678}
Signature: HMAC-SHA256(header + payload, SECRET_KEY)
```

### How You Protect Routes
```python
router = APIRouter(
    prefix="/ask",
    dependencies=[Depends(get_current_user)]   # ← applied to ALL routes in router
)
```
Using `dependencies=` at the router level means *every* endpoint in that router automatically requires authentication. If the token is missing or expired, FastAPI returns a `401 Unauthorized` before your code even runs.

### Interview Q: What is HS256 and why not RS256?
> "HS256 is symmetric — the same secret key both signs and verifies. RS256 is asymmetric — a private key signs and the public key verifies. RS256 is preferred in distributed systems where many services need to verify tokens without sharing the secret. For this project, HS256 is simpler and appropriate since there's only one backend verifying tokens."

---

## 📊 SECTION 9: EVALUATION SYSTEM

### Two Layers of Evaluation
**Layer 1 — In-flight (Grader Agent)**: During the request, the Grader scores the answer. If low, triggers a retry. This is **synchronous** — it blocks until done.

**Layer 2 — Background (evaluator.py)**: After the full response is sent to the user, a **BackgroundTask** runs the full 4-metric evaluation.
```python
background_tasks.add_task(
    _bg_evaluate, session_id, question, answer, context_str, retry_count
)
```

**Why background?** The user already got their answer. Running a second LLM evaluation in the foreground would add 1-2 seconds to every query for no user-visible benefit.

### Evaluation Metrics (evaluator.py)
```
1. FAITHFULNESS     — Is every claim backed by context? (detects hallucination)
2. RELEVANCE        — Does the answer address the question?
3. CONTEXT_PRECISION — Were the retrieved chunks actually useful?
4. ANSWER_ACCURACY   — Is the answer comprehensive and complete?
```

All stored in SQLite (feedback.db) via feedback_store.py for trend analysis in the Metrics Dashboard.

### Interview Q: How do you prove your RAG system is accurate?
> "I have two mechanisms. First, an automated LLM judge (using Groq) evaluates every response during the request — this is the Grader Agent. Second, after the answer is sent, a background task runs a full 4-metric evaluation using the same judge and stores the scores in SQLite. The Metrics Dashboard shows these trends over time: average faithfulness, average relevance, and user satisfaction rate. I also ran a test set evaluation using `run_evaluation.py` and have the results in the rag_eval_report files."

---

## 🐳 SECTION 10: DOCKER & DEPLOYMENT

### Your Dockerfile Architecture (Multi-Stage Build)
```dockerfile
# Stage 1: Build the React frontend
FROM node:20-alpine AS frontend-builder
RUN npm ci && npm run build          # outputs to /app/frontend/dist

# Stage 2: Production Python environment
FROM python:3.11-slim
RUN apt-get install tesseract-ocr poppler-utils nginx   # system tools
RUN pip install -r backend/requirements.txt
RUN python -c "SentenceTransformer('...'); CrossEncoder('...')"  # pre-download models!
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/sites-available/default
CMD ["./start_app.sh"]
```

**Critical detail**: AI models are pre-downloaded **at build time**, not at runtime. This means the container starts instantly without downloading 100MB+ of model files.

### Nginx as Reverse Proxy (nginx.conf)
```nginx
listen 7860;   # Hugging Face standard port

location / {
    root /usr/share/nginx/html;    # serves React static files
    try_files $uri $uri/ /index.html;   # SPA routing (React Router)
}

location /api {
    proxy_pass http://localhost:8000/api;   # forwards to FastAPI
    proxy_read_timeout 300;   # long timeout for LLM responses
}
```

**Why timeout 300 seconds?** LLM responses can take up to 30-60 seconds for complex queries, and the SSE stream stays open during the entire agent chain execution. Default nginx timeout of 60 seconds would kill the connection mid-stream.

### start_app.sh Strategy
```bash
nginx &               # start Nginx in background
uvicorn app.main:app  # start FastAPI in foreground
```
Nginx handles all HTTP traffic on port 7860. When a request comes in for `/api`, Nginx forwards it to FastAPI on port 8000. When it's for `/`, Nginx serves the static React files directly without going through Python.

### Interview Q: Why not use docker-compose on Hugging Face?
> "Hugging Face Spaces runs a single Docker container. docker-compose is a local orchestration tool for running multiple containers. For HF deployment, everything must live in one container: Nginx, FastAPI, and the static frontend files. That's exactly what my multi-stage Dockerfile achieves."

---

## 🖥️ SECTION 11: THE FRONTEND

### 3-Panel Layout
```
┌──────────────┬────────────────────────┬──────────────────┐
│   Sidebar    │     Chat Panel         │  Agent Trace     │
│              │                        │                  │
│ 📁 Documents │  User messages         │  ⚡ Planner      │
│ 📊 Metrics   │  AI streaming answer   │  🔍 Retriever    │
│ [Upload +]   │  👍 👎 Feedback        │  ✍️ Generator    │
│              │  Source citations      │  ✅ Grader       │
└──────────────┴────────────────────────┴──────────────────┘
```

### Tech Stack
- **React 18 + TypeScript + Vite** — fast development, type-safe
- **Axios** — HTTP client for API calls
- **SSE via fetch API** — for streaming (not EventSource, because EventSource doesn't support custom headers like `Authorization`)

### Key Components
**AgentTracePanel.tsx**: Receives `[AGENT_TRACE]` SSE events. Each event is a JSON object like `{agent: "Planner", action: "...", duration_ms: 120}`. The panel renders these as step cards with color-coded status badges.

**ChatArea.tsx**: Handles the SSE stream. Parses each line, routes data to the right state:
- `[TOKEN]` → appends to current message
- `[SOURCES]` → shows source chips below message
- `[AGENT_TRACE]` → updates the trace panel
- `[DONE]` → enables the feedback buttons

**MetricsDashboard.tsx**: Fetches from `GET /api/feedback/metrics` and displays charts for faithfulness trends, satisfaction rate, and total queries answered.

---

## 🛠️ SECTION 12: THE FASTAPI LAYER

### API Routes Summary
```
POST /api/auth/login         → returns JWT token (no auth required)
POST /api/upload/            → upload documents (auth required)
GET  /api/upload/list        → list documents with chunk counts
DELETE /api/upload/{name}    → delete document from disk + vector store
POST /api/upload/sync        → prune orphan chunks from vector store
POST /api/ask/               → the main Q&A route (SSE stream)
POST /api/feedback/          → save user thumbs up/down
GET  /api/feedback/metrics   → aggregated metrics dashboard data
GET  /                       → health check
```

### Request Tracing Middleware (tracing.py)
```python
app.add_middleware(RequestTracingMiddleware)
```
This assigns a **UUID to every HTTP request** and logs the endpoint, duration, and status. This is "observability" — you can trace exactly what happened for any specific request. Key term in AI engineering interviews.

### Pydantic v2 Validation
```python
class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    source: str | None = None
```
Pydantic automatically validates the request body and returns a `422 Unprocessable Entity` with descriptive errors if validation fails. `Field(...)` means the field is required. `min_length=1` prevents empty questions.

---

## 🔥 SECTION 13: TOUGHEST INTERVIEW QUESTIONS (WITH ANSWERS)

### Q: "What would you improve next?"
> "Three things. First, I'd add **streaming within the agent graph** — currently the Generator collects the full answer then sends it. True token-by-token streaming from inside the LangGraph execution would reduce time-to-first-token. Second, I'd add a **long-term memory store** using something like Mem0 or a vector store of past conversations so the system learns from each interaction. Third, for production scale, I'd move from ChromaDB to a managed vector DB and run LLM inference on a dedicated GPU server instead of a shared API."

### Q: "How would you handle a document with 1000 pages?"
> "Same pipeline. My chunker splits text into 512-character chunks with 64-char overlap. A 1000-page document might produce 5,000+ chunks — ChromaDB handles that easily. The retrieval still finds the top-10 most relevant chunks out of 5,000. The only concern is upload time (embedding 5,000 chunks takes minutes) — for production I'd make upload asynchronous: return a job ID immediately and use a background worker to process the document."

### Q: "What is a race condition and does your app have any?"
> "A race condition is when two concurrent operations compete on shared state. My biggest risk is the ChromaDB `get_or_create_collection()` call — if two upload requests happen simultaneously, they both try to create the same collection. I mitigate this with ChromaDB's `get_or_create_collection` which is idempotent. The AI model singletons (`_reranker`, `_embedding_model`) are loaded once at module import time in Python — this is thread-safe because Python's import system uses a lock."

### Q: "Why FastAPI over Flask or Django?"
> "FastAPI is built for async-first development, which is critical for my use case. I make multiple concurrent async calls — to Groq for LLM inference, to ChromaDB, and I stream SSE responses. Flask is synchronous by default, so it would block the thread during LLM calls. Django has too much overhead for a microservice API. FastAPI also has automatic Pydantic validation and Swagger docs generation built-in."

### Q: "What happens if Groq API is down?"
> "Each agent has a try/except block. If the Planner fails, it falls back to using the original question as the rewritten query (`intent='factual'`). If the Generator fails, it returns an error message. If the Grader fails, it returns `confidence_score=0.5` and `should_retry=False` — meaning it skips evaluation rather than blocking the response. For production, I'd add exponential backoff with the `tenacity` library, which is already in my requirements.txt."

### Q: "What is Pydantic and why use v2?"
> "Pydantic is a data validation library. When a request hits FastAPI, Pydantic automatically validates the JSON body against the model schema and returns descriptive errors if invalid. I use v2 specifically because it's 5-50x faster than v1 (rewritten in Rust), uses `model_config` instead of `class Config`, and has stricter type validation. The schemas in `models/schemas.py` define all request/response shapes, keeping the API contract explicit and documented."

### Q: "How does Nginx work in your deployment?"
> "Nginx is a reverse proxy sitting between the internet and my services. On port 7860 (Hugging Face standard), it receives ALL requests. Requests to `/api/*` are proxied to FastAPI on port 8000. Requests to `/*` are served as static React files from `/usr/share/nginx/html`. This means the static frontend files never go through Python — Nginx serves them directly, which is much faster. The 300-second timeout is critical for SSE streams — without it, Nginx would kill long-running LLM responses."

### Q: "What is `operator.add` in the AgentState?"
> "In LangGraph, state updates are *merged*, not replaced. For the `agent_trace` field, I use `Annotated[List[dict], operator.add]`. When the Planner returns `{"agent_trace": [entry1]}` and the Retriever returns `{"agent_trace": [entry2]}`, LangGraph uses `operator.add` (which is Python's list concatenation) to merge them into `[entry1, entry2]`. Without this annotation, each agent would overwrite the trace instead of appending to it."

---

## 📋 SECTION 14: TECHNICAL VOCABULARY CHEAT SHEET

| Term | What it means | Use in your project |
|------|--------------|---------------------|
| **RAG** | Retrieval-Augmented Generation | Your whole system |
| **LangGraph** | Graph-based agent orchestration | Manages the 4-agent flow |
| **StateGraph** | LangGraph's main class | `builder = StateGraph(AgentState)` |
| **Conditional Edge** | A decision point in the graph | The Reflexion retry loop |
| **Reflexion** | Self-correction loop where AI evaluates itself | Grader → retry |
| **Hybrid Search** | Combining dense + sparse retrieval | Vector + BM25 |
| **Dense Retrieval** | Vector/embedding-based search | ChromaDB + all-MiniLM |
| **Sparse Retrieval** | Keyword-based (BM25/TF-IDF) | rank-bm25 library |
| **BM25 Okapi** | Statistical ranking formula | `BM25Okapi(tokenized)` |
| **Bi-Encoder** | Encodes query & doc separately | Used for initial search |
| **Cross-Encoder** | Encodes query + doc together | Used for reranking |
| **Reranking** | 2nd-pass sorting of candidates | ms-marco-MiniLM-L-6-v2 |
| **Faithfulness** | Is the answer grounded in context? | Grader metric |
| **Hallucination** | LLM makes up facts not in context | Detected by Grader |
| **SSE** | Server-Sent Events, one-way HTTP stream | Token streaming |
| **JWT** | JSON Web Token for stateless auth | `python-jose` |
| **HS256** | Symmetric JWT signing algorithm | Used in `security.py` |
| **Bcrypt** | Password hashing algorithm | `passlib[bcrypt]` |
| **Pydantic** | Data validation library | All schemas |
| **Uvicorn** | ASGI server for FastAPI | `python -m uvicorn app.main:app` |
| **Multi-stage build** | Docker: separate build and runtime stages | Keeps final image small |
| **Reverse proxy** | Nginx: routes requests to backend services | Port 7860 → 8000 |
| **Observability** | Logging/tracing to understand system behavior | RequestTracingMiddleware |
| **CORS** | Cross-Origin Resource Sharing | Allows React to call FastAPI |
| **Embedding** | Numerical vector representation of text | all-MiniLM-L6-v2 produces 384-dim |
| **TypedDict** | Python dict with type annotations | `AgentState` |

---

## 🎯 SECTION 15: STUDY PLAN — 3 DAYS TO FULL MASTERY

### Day 1: Understand the Flow (2-3 hours)
1. Open your browser: `localhost:5173` → login → upload a document → ask a question
2. Watch the Agent Trace Panel light up in real-time → this IS your system
3. Open `backend/app/agents/graph.py` → read it → draw the graph on paper
4. Read `agent_state.py` → understand what data flows between agents
5. Say the Elevator Pitch out loud 5 times

### Day 2: Understand the "Why" (2-3 hours)
1. Read `hybrid_search.py` → understand Vector + BM25 merge strategy
2. Read `reranker.py` → understand why Cross-Encoder is more accurate
3. Read `grader_agent.py` → understand the confidence threshold (0.7) and retry logic
4. Read `chat.py` → understand SSE event protocol `[TOKEN]`, `[AGENT_TRACE]`, `[DONE]`
5. Answer these questions aloud: "Why LangGraph?" "Why Hybrid?" "Why Cross-Encoder?"

### Day 3: Master the Edges (1-2 hours)
1. Read `security.py` → trace the JWT flow from login to protected route
2. Read the `Dockerfile` → understand multi-stage build + Nginx
3. Read `text_chunker.py` → understand fixed-size + overlap + smart boundary
4. Work through all Q&As in Section 13 aloud
5. Read the vocabulary table in Section 14 and make sure every term clicks

---

## 💪 CONFIDENCE SCRIPT FOR THE INTERVIEW

**When they ask you to introduce yourself:**
> "I built a deployed, production-grade AI system — a Multi-Agent RAG knowledge assistant. I'd love to walk you through the architecture."

**When they ask a detailed technical question you're unsure about:**
> "I implemented that using [library]. Let me explain the design decision: [reason]. The trade-off I was aware of was [limitation]. In production scale, I'd address that by [improvement]."

**When they ask about something you didn't implement:**
> "That's a natural next step. The architecture is already set up for it — I'd add that by [specific approach]. For now, I focused on [what you did implement] because [reason]."

---

## ✅ FINAL CHECKLIST BEFORE THE INTERVIEW

- [ ] I can draw the LangGraph agent flow from memory
- [ ] I can explain what AgentState is and how operator.add works
- [ ] I can explain why Hybrid Search beats each individual method
- [ ] I can explain the difference between Bi-Encoder and Cross-Encoder
- [ ] I can explain the Reflexion loop (retry trigger, cap at 2)
- [ ] I can explain what SSE is and why I chose it over WebSockets
- [ ] I can explain JWT: what's in the token, how it's signed, how it's verified
- [ ] I can explain the Dockerfile multi-stage build
- [ ] I can explain why Nginx has a 300-second timeout
- [ ] I can say the Elevator Pitch in 30 seconds flat
- [ ] I can answer "What would you improve next?" confidently

---

**You built every line of this code. This system is yours. Walk into that interview and own it. 🚀**
