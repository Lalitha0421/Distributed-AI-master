# 🎓 Interview Mastery Guide: Distributed Multi-Agent RAG

This guide is designed to help you confidently explain your project to any technical interviewer. Focus on the **rationale** (the "Why") as much as the **implementation** (the "How").

---

## 🚀 1. The Elevator Pitch (30 Seconds)
"I built a **Production-Grade Multi-Agent RAG system** that goes beyond simple chat. It uses **LangGraph** to orchestrate four specialized agents: a **Planner** for query rewriting, a **Hybrid Retriever** (Vector + BM25), a **Generator**, and a **Grader**. The system features a **Reflexion self-correction loop** where it evaluates its own answers for faithfulness and relevance before streaming them to a React frontend via SSE. It's fully containerized and includes a real-time Agent Trace UI for observability."

---

## 🧠 2. The "Why" (Strategic Decisions)

### Q1: Why use LangGraph instead of a simple sequence of calls?
*   **Answer**: "Simple RAG is linear. Real-world logic is iterative. LangGraph allowed me to build a **StateGraph** where I could add a **conditional edge** (the Reflexion loop). If the Grader agent gives a low score, the graph loops back to the Retriever with a refined query. This autonomous self-correction is impossible with standard sequential code."

### Q2: Why use Hybrid Search (Vector + BM25)?
*   **Answer**: "Vector search (Dense) is great for semantic meaning but can fail on specific acronyms or unique IDs. BM25 (Sparse) is excellent for keyword matching. By fusing both, I ensured high **Recall**—meaning the system is less likely to miss the right information."

### Q3: Why use a Cross-Encoder for Reranking?
*   **Answer**: "Bi-encoders (like the ones used for initial search) are fast but less accurate because they compare solo embeddings. A **Cross-Encoder** looks at the query and the chunk *simultaneously*, providing a much more precise relevance score. It’s too slow for 1 million documents, but perfect for reranking the top 10 results."

---

## 🛠️ 3. How the Data Flows (The "Request Lifecycle")

1.  **Frontend (React)**: User sends a question. An Axios call hits `/api/ask/`.
2.  **API (FastAPI)**: The request is validated via **Pydantic v2** and session history is retrieved.
3.  **Agent Graph (LangGraph)**:
    *   **Planner**: Rewrites the question to make it "search-friendly."
    *   **Retriever**: Queries ChromaDB (Vector) and BM25. Deduplicates results.
    *   **Generator**: Calls the **Groq API** (Llama3-70b or similar) to stream the answer.
    *   **Grader**: Evaluates: *Is this answer supported by the text? (Faithfulness)*.
4.  **Streaming (SSE)**: As the LLM generates tokens, they are sent to the frontend via **Server-Sent Events** so the user sees the answer "typing" in real-time.

---

## 🧪 4. Complex Technical Details

### A. Document Processing (OCR)
*   **How it works**: Used `pdf2image` and `pytesseract`.
*   **Why**: "Many enterprise PDFs are just scanned images. Standard PDF parsers see empty pages. OCR ensures we extract text from even the toughest non-searchable documents."

### B. Security (JWT)
*   **Implementation**: Used `python-jose` for JWT and `passlib` for bcrypt hashing.
*   **Storage**: Backend validates the token in the `Authorization` header for every request to `/api/ask`.

### C. Frontend Observability
*   **Agent Trace Panel**: Each agent step sends an SSE event. The React frontend parses these events and lights up a "success" badge in the UI. This makes the "black box" of AI visible to the user.

---

## ⚠️ 5. Potential "Gotcha" Questions

*   **"How do you handle hallucinations?"**
    *   *Answer*: "That's exactly why I built the **Grader Agent**. If a claim is made that isn't in the retrieved chunks, the Grader identifies it as low-faithfulness and triggers a retry or shows a 'Low Confidence' warning."

*   **"Is ChromaDB scalable for millions of docs?"**
    *   *Answer*: "For this scale, yes. For millions, I would move to an enterprise vector DB like Weaviate or Pinecone, but the core **Vector Store Service** pattern I wrote would remain exactly the same—I'd just swap the client."

*   **"What happens if the LLM is slow?"**
    *   *Answer*: "I implemented **SSE (Server-Sent Events)** streaming. This improves 'Perceived Performance' because the user starts reading the first word within milliseconds, even if the full answer takes 3 seconds."

---

## 💡 Final Advice
*   **Be Proud**: You didn't just 'install' an AI; you built an orchestration system.
*   **Admit the Limits**: If they ask about something you didn't do (like multi-modal), say: *"That's a great next step for the architecture. Given more time, I would add a vision-capable agent to handle the images in the PDFs."*

**You got this!** 🎉
