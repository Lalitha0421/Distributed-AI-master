"""
vector_store.py — ChromaDB-backed vector store with sentence-transformer embeddings.

One ChromaDB collection per document (sanitised name).
All public functions are typed and logged.
"""

from __future__ import annotations

import os

# Disable ChromaDB telemetry noise
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import os
import re
from typing import List, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.logger import logger

# ── Initialise once at module import ──────────────────────────────────────────
os.makedirs(settings.chroma_persist_dir, exist_ok=True)

# Use PersistentClient (new API) with anonymized_telemetry off.
# We supply embeddings ourselves so embedding_function=None on every collection.
_chroma_client = chromadb.PersistentClient(
    path=settings.chroma_persist_dir,
    settings=ChromaSettings(anonymized_telemetry=False),
)

_embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
logger.info("SentenceTransformer embedding model loaded (all-MiniLM-L6-v2)")


# ── Collection name sanitisation ──────────────────────────────────────────────

def _sanitize_collection_name(name: str) -> str:
    """
    ChromaDB collection names must:
      - Be 3–63 characters
      - Start and end with an alphanumeric character
      - Contain only [a-zA-Z0-9._-]
    """
    if not name:
        return "default_document"

    # Strip file extension so "report.pdf" → "report"
    name = os.path.splitext(name)[0]

    # Replace invalid chars with underscore
    name = re.sub(r"[^a-zA-Z0-9._-]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_.-")

    if len(name) < 3:
        name = "doc_" + name
    if not name[0].isalnum():
        name = "doc_" + name
    if not name[-1].isalnum():
        name = name + "_doc"
    if len(name) > 63:
        name = name[:60] + "_doc"

    return name.lower()


def _get_collection(document_name: str):
    """Return (or create) a ChromaDB collection for *document_name*.
    
    embedding_function=None is critical — we supply our own embeddings.
    Without it ChromaDB tries to load its ONNX model and hangs on Windows.
    """
    col_name = _sanitize_collection_name(document_name)
    logger.debug(f"Collection: '{col_name}' (source: '{document_name}')")
    return _chroma_client.get_or_create_collection(
        name=col_name,
        embedding_function=None,   # We provide embeddings manually
    )


# ── Public API ────────────────────────────────────────────────────────────────

def store_chunks(chunks: List[str], document_name: str = "uploaded_document") -> int:
    """
    Embed and store *chunks* in the collection for *document_name*.

    Returns the number of chunks actually stored.
    """
    if not chunks:
        logger.warning(f"store_chunks called with 0 chunks for '{document_name}'")
        return 0

    collection = _get_collection(document_name)
    logger.info(f"Generating embeddings for {len(chunks)} chunks... (this may take a minute on first run)")
    embeddings = _embedding_model.encode(chunks).tolist()
    logger.info("Embeddings generated successfully.")

    ids = [f"chunk_{i}_{document_name}" for i in range(len(chunks))]
    metadatas = [
        {"source": document_name, "chunk_id": i, "chunk_index": i}
        for i in range(len(chunks))
    ]

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas,
    )

    logger.info(f"Stored {len(chunks)} chunks for '{document_name}'")
    return len(chunks)


def search_chunks(query: str, source: Optional[str] = None) -> List[dict]:
    """
    Retrieve the top-K most similar chunks for *query*.

    Args:
        query:  User question or rewritten query.
        source: If provided, restrict search to this document's collection.

    Returns:
        List of dicts: {text, source, chunk_id, score}
    """
    try:
        query_embedding = _embedding_model.encode(query).tolist()
        collection = _get_collection(source if source else "default")

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=settings.retrieval_top_k,
            where={"source": source} if source else None,
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        if not documents:
            logger.warning(f"No chunks found for query: '{query[:60]}'")
            return []

        chunks = [
            {
                "text": doc,
                "source": meta.get("source", "unknown"),
                "chunk_id": meta.get("chunk_id"),
                "score": float(dist) if dist is not None else None,
            }
            for doc, meta, dist in zip(documents, metadatas, distances)
        ]

        logger.debug(f"Vector search returned {len(chunks)} results")
        return chunks

    except Exception as exc:
        logger.error(f"Vector search failed: {exc}")
        return []


def get_all_chunks(source: Optional[str] = None) -> List[dict]:
    """
    Retrieve all stored chunks (optionally filtered by *source*).
    Used by BM25 in hybrid_search.
    """
    try:
        collection = _get_collection(source if source else "default")
        results = collection.get()

        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])

        chunks = []
        for doc, meta in zip(documents, metadatas):
            if source and meta.get("source") != source:
                continue
            chunks.append(
                {
                    "text": doc,
                    "source": meta.get("source", "unknown"),
                    "chunk_id": meta.get("chunk_id"),
                }
            )

        logger.debug(f"get_all_chunks: {len(chunks)} chunks for source='{source}'")
        return chunks

    except Exception as exc:
        logger.error(f"get_all_chunks failed: {exc}")
        return []