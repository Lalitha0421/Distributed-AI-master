"""
document_processor.py — Extract plain text from PDF, TXT, and DOCX files.

For scanned PDFs (very little machine-readable text) it falls back to
Tesseract OCR via pdf2image. Paths are loaded from settings so they
never need to be hardcoded again.
"""

from __future__ import annotations

import os
import re
import pytesseract
from docx import Document
from PIL import Image  # noqa: F401 — ensures Pillow is importable
from pypdf import PdfReader

from app.core.config import settings
from app.core.logger import logger

# Windows paths from centralised settings
pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
POPPLER_PATH: str = settings.poppler_path

_SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx"}
def _clean_text(text: str) -> str:
    """Remove excessive whitespace and fix common PDF extraction artifacts."""
    if not text:
        return ""
    # Replace multiple spaces with one
    text = re.sub(r" +", " ", text)
    # Fix words that got split by spaces (e.g. 2 0 2 4 -> 2024 if surrounded by spaces)
    # We use a safer approach to just squash multiple newlines/spaces
    text = re.sub(r"\n+", "\n", text)
    return text.strip()


def extract_text_from_file(file_path: str) -> str:
    """
    Extract plain text from a PDF, TXT, or DOCX file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in _SUPPORTED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext}'. Supported: {_SUPPORTED_EXTENSIONS}"
        )

    logger.info(f"Extracting text from: {os.path.basename(file_path)} ({ext})")

    if ext == ".txt":
        text = _extract_txt(file_path)
    elif ext == ".docx":
        text = _extract_docx(file_path)
    elif ext == ".pdf":
        text = _extract_pdf(file_path)
    else:
        raise ValueError(f"Unhandled extension: {ext}")

    return _clean_text(text)


# ── Internal helpers ──────────────────────────────────────────────────────────

def _extract_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    logger.debug(f"TXT extraction: {len(text)} chars")
    return text.strip()


def _extract_docx(file_path: str) -> str:
    doc = Document(file_path)
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    text = "\n".join(paragraphs)
    logger.debug(f"DOCX extraction: {len(paragraphs)} paragraphs, {len(text)} chars")
    return text.strip()


def _extract_pdf(file_path: str) -> str:
    """Extract PDF text; fall back to OCR if fewer than 100 chars extracted."""
    reader = PdfReader(file_path)
    pages_text: list[str] = []

    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages_text.append(page_text)

    text = "\n".join(pages_text).strip()
    logger.debug(f"PDF native extraction: {len(text)} chars from {len(reader.pages)} pages")

    if len(text) < 100:
        logger.warning("PDF has very little text — attempting OCR fallback")
        text = _ocr_pdf(file_path)

    return text.strip()


def _ocr_pdf(file_path: str) -> str:
    """Convert PDF pages to images and run Tesseract OCR on each."""
    try:
        from pdf2image import convert_from_path  # lazy import

        images = convert_from_path(file_path, poppler_path=POPPLER_PATH)
        ocr_parts: list[str] = []

        for i, img in enumerate(images):
            page_text = pytesseract.image_to_string(img)
            if page_text.strip():
                ocr_parts.append(page_text)
            logger.debug(f"OCR page {i + 1}/{len(images)}: {len(page_text)} chars")

        result = "\n".join(ocr_parts)
        logger.info(f"OCR fallback complete: {len(result)} chars from {len(images)} pages")
        return result

    except Exception as exc:
        logger.error(f"OCR failed: {exc}")
        return ""