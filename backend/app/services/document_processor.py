"""
document_processor.py — Extract plain text from PDF, TXT, and DOCX files.
Safely manages file handles to prevent file locks on Windows.
"""

from __future__ import annotations

import os
import re
import pytesseract
from docx import Document
from PIL import Image  # noqa: F401
from pypdf import PdfReader

from app.core.config import settings
from app.core.logger import logger

pytesseract.pytesseract.tesseract_cmd = settings.get_tesseract_cmd
POPPLER_PATH: str = settings.get_poppler_path

_SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx", ".md"}

def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r" +", " ", text)
    text = re.sub(r"\n+", "\n", text)
    return text.strip()

def extract_text_from_file(file_path: str) -> str:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in _SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported ext: {ext}")

    logger.info(f"Extracting text from: {os.path.basename(file_path)}")

    if ext in {".txt", ".md"}:
        with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    elif ext == ".docx":
        # python-docx opens the path, we can't easily use a 'with' but we don't hold it long
        doc = Document(file_path)
        text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    elif ext == ".pdf":
        text = _extract_pdf(file_path)
    else:
        text = ""

    return _clean_text(text)

def _extract_pdf(file_path: str) -> str:
    text = ""
    # Use context manager to ensure file is closed immediately after reading
    with open(file_path, "rb") as f:
        reader = PdfReader(f)
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n".join(pages).strip()
    
    if len(text) < 100:
        text = _ocr_pdf(file_path)
    return text

def _ocr_pdf(file_path: str) -> str:
    from pdf2image import convert_from_path
    images = convert_from_path(file_path, poppler_path=POPPLER_PATH)
    text = "\n".join([pytesseract.image_to_string(img) for img in images])
    return text