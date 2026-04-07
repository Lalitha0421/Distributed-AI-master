"""
vector_store.py — ChromaDB-backed vector store with sentence-transformer embeddings.
Refactored to use a SINGLE collection for all documents to allow cross-document search.
"""

from __future__ import annotations

import os
import re
from typing import List, Optional
from datetime import datetime

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.logger import logger

# ── Initialise once at module import ──────────────────────────────────────────
os.makedirs(settings.chroma_persist_dir, exist_ok=True)

# Use PersistentClient (new API) with anonymized_telemetry off.
_chroma_client = chromadb.PersistentClient(
    path=settings.chroma_persist_dir,
    settings=ChromaSettings(anonymized_telemetry=False),
)

_embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
logger.info("SentenceTransformer embedding model loaded (all-MiniLM-L6-v2)")

# ── Global Collection ─────────────────────────────────────────────────────────
# We use one collection for everything. Filtering is done via metadata.
_KNOWLEDGE_COLLECTION_NAME = "ai_knowledge_base"

def _get_main_collection():
    """Return the global ChromaDB collection."""
    return _chroma_client.get_or_create_collection(
        name=_KNOWLEDGE_COLLECTION_NAME,
        embedding_function=None,
    )

# ── Public API ────────────────────────────────────────────────────────────────

def store_chunks(chunks: List[str], document_name: str = "uploaded_document") -> int:
    """Embed and store *chunks* in the global collection."""
    if not chunks:
        logger.warning(f"store_chunks called with 0 chunks for '{document_name}'")
        return 0

    collection = _get_main_collection()
    logger.info(f"Generating embeddings for {len(chunks)} chunks... (source: {document_name})")
    embeddings = _embedding_model.encode(chunks).tolist()

    # Generate unique IDs using filename and index
    ids = [f"{document_name}_{i}" for i in range(len(chunks))]
    metadatas = [
        {"source": document_name, "chunk_id": i}
        for i in range(len(chunks))
    ]

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas,
    )

    logger.info(f"Stored {len(chunks)} chunks for '{document_name}' in global collection")
    return len(chunks)


def search_chunks(query: str, source: Optional[str] = None) -> List[dict]:
    """Retrieve the top-K chunks from the global collection."""
    try:
        query_embedding = _embedding_model.encode(query).tolist()
        collection = _get_main_collection()

        # Build metadata filter if source is specified
        where_filter = {"source": source} if source else None

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=settings.retrieval_top_k,
            where=where_filter,
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

        logger.info(f"Vector search: {len(chunks)} results found (source_filter='{source}')")
        return chunks

    except Exception as exc:
        logger.error(f"Vector search failed: {exc}")
        return []


def get_all_chunks(source: Optional[str] = None) -> List[dict]:
    """Retrieve all chunks for keyword search."""
    try:
        collection = _get_main_collection()
        where_filter = {"source": source} if source else None
        
        results = collection.get(where=where_filter)

        documents = results.get("documents", [])
        metadatas = results.get("metadatas", [])

        chunks = []
        for doc, meta in zip(documents, metadatas):
            chunks.append({
                "text": doc,
                "source": meta.get("source", "unknown"),
                "chunk_id": meta.get("chunk_id"),
            })

        logger.debug(f"get_all_chunks: {len(chunks)} chunks retrieved (source_filter='{source}')")
        return chunks

    except Exception as exc:
        logger.error(f"get_all_chunks failed: {exc}")
        return []

def get_document_stats() -> List[dict]:
    """Returns total chunk counts per document for the sidebar."""
    try:
        collection = _get_main_collection()
        results = collection.get(include=["metadatas"])
        
        metadatas = results.get("metadatas", [])
        counts = {}
        for meta in metadatas:
            src = meta.get("source", "unknown")
            counts[src] = counts.get(src, 0) + 1
            
        return [{"filename": k, "chunks": v} for k, v in counts.items()]
    except Exception as e:
        logger.error(f"Failed to get document stats: {e}")
        return []

def delete_document(document_name: str) -> bool:
    """Removes all chunks associated with a document from the global collection."""
    try:
        collection = _get_main_collection()
        collection.delete(where={"source": document_name})
        logger.info(f"Deleted all chunks for '{document_name}' from vector store")
        return True
    except Exception as e:
        logger.error(f"Failed to delete document from vector store: {e}")
        return False

def prune_orphans(valid_filenames: List[str]) -> int:
    """
    Removes any chunks from the vector store whose 'source' is not in valid_filenames.
    Returns the number of orphan sources removed.
    """
    try:
        collection = _get_main_collection()
        
        # Get unique sources from the vector store
        results = collection.get(include=["metadatas"])
        metadatas = results.get("metadatas", [])
        
        stored_sources = set()
        for m in metadatas:
            if m and "source" in m:
                stored_sources.add(m["source"])
        
        orphans = [src for src in stored_sources if src not in valid_filenames]
        
        for orphan in orphans:
            collection.delete(where={"source": orphan})
            logger.info(f"Pruned orphan document from vector store: {orphan}")
            
        return len(orphans)
    except Exception as e:
        logger.error(f"Failed to prune orphans: {e}")
        return 0