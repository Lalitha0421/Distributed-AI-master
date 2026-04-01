"""
llm_service.py — Streaming answer generation via Groq.

Generates answers that are grounded ONLY in the supplied document context.
Uses async generator + SSE-compatible yielding for real-time frontend updates.
"""

from __future__ import annotations

from typing import AsyncGenerator, List

from groq import AsyncGroq

from app.core.config import settings
from app.core.logger import logger

_client = AsyncGroq(api_key=settings.groq_api_key)

_SYSTEM_PROMPT = """
You are a Senior Technical Analyst. Your goal is to extract and summarize information from documents with 100% accuracy.

GUIDELINES:
1. EXHAUSTIVE LISTS: If a user asks for 'projects', 'skills', or 'experience', list EVERY item found in the text. Do not summarize into a single line.
2. STRUCTURE: Use clear bullet points for lists. Use bold text for key terms.
3. GROUNDING: Use ONLY the provided document content. If details are missing, state it clearly.
4. TONE: Professional, technical, and precise.
"""

_USER_TEMPLATE = """\
Document Content:
{context}

Previous Conversation:
{history}

Question: {question}

Provide a clear, well-formatted answer based only on the document.\
"""


async def generate_answer_stream(
    question: str,
    context: str,
    history: List[dict],
) -> AsyncGenerator[str, None]:
    """
    Stream answer tokens for *question* grounded in *context*.
    """
    history_str = (
        "\n".join(f"{m['role']}: {m['content']}" for m in history)
        if history
        else "No previous conversation."
    )

    try:
        print(f"[DEBUG] Calling Groq API with model: {settings.model_name}...")
        stream = await _client.chat.completions.create(
            model=settings.model_name,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": _USER_TEMPLATE.format(
                        context=context,
                        history=history_str,
                        question=question,
                    ),
                },
            ],
            temperature=0.1,
            max_tokens=1200,
            stream=True,
        )

        total_tokens = 0
        async for chunk in stream:
            token = chunk.choices[0].delta.content
            if token is not None:
                total_tokens += 1
                yield token

        print(f"[DEBUG] AI Generation complete ({total_tokens} tokens).")

    except Exception as exc:
        print(f"[ERROR] Groq API Failed: {exc}")
        logger.error(f"Streaming generation failed: {exc}")
        yield "\nSorry, I encountered an error while generating the answer. Please try again."