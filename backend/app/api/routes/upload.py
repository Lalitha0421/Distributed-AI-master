"""
upload.py — Document upload and processing route.
Supports multiple files via the 'files' parameter and deletion.
"""

from __future__ import annotations

import os
import shutil
from typing import List
from datetime import datetime

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings
from app.core.logger import logger
from app.models.schemas import UploadResponse
from app.services.document_processor import extract_text_from_file
from app.services.text_chunker import split_text_into_chunks
from app.services.vector_store import store_chunks
from starlette.concurrency import run_in_threadpool

router = APIRouter(prefix="/upload", tags=["upload"])

_ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx", ".md"}

# Ensure upload directory exists at startup
os.makedirs(settings.upload_dir, exist_ok=True)

@router.post("/", response_model=List[UploadResponse])
async def upload_documents(files: List[UploadFile] = File(...)) -> List[UploadResponse]:
    """
    Upload multiple documents, extract text, chunk them, and
    store embeddings in ChromaDB.
    """
    results = []
    
    for file in files:
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in _ALLOWED_EXTENSIONS:
            logger.warning(f"Unsupported file type skipping: {file.filename}")
            continue

        file_path = os.path.join(settings.upload_dir, file.filename)

        try:
            # 1. Save file
            with open(file_path, "wb") as buf:
                shutil.copyfileobj(file.file, buf)
            
            # 2. Extract text
            text = extract_text_from_file(file_path)
            
            if not text.strip():
                logger.warning(f"No text extracted from {file.filename}")
                continue

            # 3. Chunk
            chunks = split_text_into_chunks(text)
            
            # 4. Embed + store
            stored = await run_in_threadpool(store_chunks, chunks, document_name=file.filename)

            results.append(UploadResponse(
                filename=file.filename,
                characters_extracted=len(text),
                chunks_created=len(chunks),
                chunks_stored=stored,
                message="Processed successfully ✅"
            ))

        except Exception as exc:
            logger.error(f"Upload failed for '{file.filename}': {exc}")

    if not results:
        raise HTTPException(status_code=422, detail="No valid documents were processed.")

    return results

@router.get("/list")
async def list_documents():
    """Returns a list of all processed documents with metadata."""
    from app.services.vector_store import get_document_stats
    stats = get_document_stats()
    
    # ── Map stats with file system upload dates ──────────────────────────────
    files = []
    if os.path.exists(settings.upload_dir):
        for f in os.listdir(settings.upload_dir):
            if os.path.isfile(os.path.join(settings.upload_dir, f)):
                # Match filename from vector store stats
                doc_stats = next((s for s in stats if s["filename"] == f), {"chunks": 0})
                
                files.append({
                    "filename": f,
                    "uploaded_at": datetime.fromtimestamp(os.path.getmtime(os.path.join(settings.upload_dir, f))).isoformat(),
                    "chunks": doc_stats["chunks"]
                })
    return {"documents": files}

@router.delete("/{filename}")
async def delete_document_route(filename: str):
    """Deletes a document from the filesystem and vector store."""
    from app.services.vector_store import delete_document
    
    file_path = os.path.join(settings.upload_dir, filename)
    
    # 1. Delete from filesystem first
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.info(f"Deleted {filename} from disk ✅")
        except Exception as e:
            logger.error(f"Failed to delete file from disk: {e}")
            raise HTTPException(status_code=500, detail=f"File is locked: {e}")

    # 2. Delete from vector store
    v_success = delete_document(filename)
    
    return {"message": f"Successfully deleted {filename}", "vector_store": v_success}