"""
upload.py — Document upload and processing route.
POST /api/upload/
"""

from __future__ import annotations

import os
import shutil

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.config import settings
from app.core.logger import logger
from app.models.schemas import UploadResponse
from app.services.document_processor import extract_text_from_file
from app.services.text_chunker import split_text_into_chunks
from app.services.vector_store import store_chunks

router = APIRouter(prefix="/upload", tags=["upload"])

_ALLOWED_EXTENSIONS = {".pdf", ".txt", ".docx"}

# Ensure upload directory exists at startup
os.makedirs(settings.upload_dir, exist_ok=True)


@router.post("/", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    """
    Upload a document (PDF / TXT / DOCX), extract text, chunk it, and
    store embeddings in ChromaDB. Returns processing statistics.
    """
    # ── Validate file type ────────────────────────────────────────────────────
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {_ALLOWED_EXTENSIONS}",
        )

    file_path = os.path.join(settings.upload_dir, file.filename)

    try:
        # ── Save file ─────────────────────────────────────────────────────────
        print(f"[DEBUG] Saving file: {file.filename}...")
        with open(file_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)
        logger.info(f"Saved upload: '{file.filename}' ({os.path.getsize(file_path)} bytes)")

        # ── Extract text ──────────────────────────────────────────────────────
        print(f"[DEBUG] Starting text extraction for {file.filename}...")
        text = extract_text_from_file(file_path)
        print(f"[DEBUG] Extraction complete: {len(text)} characters found.")
        
        if not text.strip():
            print("[DEBUG] No text found, raising 422.")
            raise HTTPException(
                status_code=422,
                detail="Could not extract any text from the file. Is it an image-only PDF?",
            )

        # ── Chunk ─────────────────────────────────────────────────────────────
        print("[DEBUG] Splitting into chunks...")
        chunks = split_text_into_chunks(text)
        print(f"[DEBUG] Created {len(chunks)} chunks.")
        
        # ── Embed + store (Run in a thread to prevent blocking) ────────────────
        from starlette.concurrency import run_in_threadpool
        print("[DEBUG] Sending to Vector Store (Embedding)...")
        stored = await run_in_threadpool(store_chunks, chunks, document_name=file.filename)
        print(f"[DEBUG] Successfully stored {stored} chunks.")

        print("[DEBUG] Sending Response...")
        return UploadResponse(
            filename=file.filename,
            characters_extracted=len(text),
            chunks_created=len(chunks),
            chunks_stored=stored,
            extracted_text=text[:5000],  # Return up to 5k characters to keep JSON light
            message="Document uploaded and processed successfully ✅",
        )

    except HTTPException:
        raise  # pass through already-formatted errors

    except Exception as exc:
        logger.error(f"Upload failed for '{file.filename}': {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {exc}",
        )