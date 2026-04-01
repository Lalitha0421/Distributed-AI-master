"""
config.py — Centralised application settings using pydantic-settings.
All env vars are validated at startup. Never use os.getenv() elsewhere.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration loaded from .env file.
    pydantic-settings validates types and raises clear errors at startup.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",             # ignore unknown env vars silently
    )

    # ── LLM ──────────────────────────────────────────────────────────────────
    groq_api_key: str
    model_name: str = "llama-3.1-8b-instant"

    # ── App ───────────────────────────────────────────────────────────────────
    app_name: str = "AI Knowledge Assistant"
    app_version: str = "2.0.0"
    debug: bool = False

    # ── ChromaDB ─────────────────────────────────────────────────────────────
    chroma_persist_dir: str = "../data/chroma_db_store"

    # ── Chunking ─────────────────────────────────────────────────────────────
    chunk_size: int = 512
    chunk_overlap: int = 64

    # ── Retrieval ────────────────────────────────────────────────────────────
    retrieval_top_k: int = 10           # how many chunks to retrieve
    rerank_top_k: int = 5              # how many to keep after reranking

    # ── Storage paths ────────────────────────────────────────────────────────
    upload_dir: str = "../data/uploads"
    feedback_db_path: str = "feedback.db"

    # ── OCR (Windows-specific paths) ─────────────────────────────────────────
    tesseract_cmd: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    poppler_path: str = r"C:\Users\DELL\Downloads\Release-25.12.0-0\poppler-25.12.0\Library\bin"

    # ── CORS ─────────────────────────────────────────────────────────────────
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()


# ── Convenience aliases (backward-compatible with existing service imports) ──
settings = get_settings()
GROQ_API_KEY: str = settings.groq_api_key
MODEL_NAME: str = settings.model_name