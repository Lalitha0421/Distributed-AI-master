"""
query_rewriter.py — Rewrites user queries to improve retrieval quality.

Uses a small, fast Groq model (llama-3.1-8b-instant) to produce a
concise, keyword-rich search query from the user's natural-language question.
On failure, the original query is returned so retrieval still proceeds.
"""

from __future__ import annotations

from groq import Groq

from app.core.config import settings
from app.core.logger import logger

_client = Groq(api_key=settings.groq_api_key)

_SYSTEM_PROMPT = (
    "You are an expert query optimizer for document retrieval systems. "
    "Rewrite queries to maximise keyword overlap with technical documents."
)

_USER_TEMPLATE = """\
Rewrite the following user query for better document retrieval in a RAG system.

Rules:
- Return ONLY the improved search query — no explanation, no quotes.
- Maximum 15 words.
- Focus on key technical terms and make the query more specific.

User query: {query}

Improved search query:"""


def rewrite_query(query: str) -> str:
    """
    Return a retrieval-optimised version of *query*.

    Falls back to the original query if the LLM call fails.
    """
    try:
        response = _client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _USER_TEMPLATE.format(query=query)},
            ],
            temperature=0.1,
            max_tokens=50,
        )

        rewritten = (
            response.choices[0].message.content
            .strip()
            .split("\n")[0]
            .replace('"', "")
            .strip()
        )

        logger.info(f"Query rewrite: '{query[:60]}' → '{rewritten}'")
        return rewritten

    except Exception as exc:
        logger.warning(f"Query rewrite failed ({exc}) — using original query")
        return query