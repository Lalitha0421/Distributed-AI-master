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

    # ── Security ─────────────────────────────────────────────────────────────
    secret_key: str = "super-secret-key-change-this-in-env"
    admin_password: str = "admin123"
    access_token_expire_minutes: int = 60 * 24 * 7 # 1 week
    
    # ── App ───────────────────────────────────────────────────────────────────
    app_name: str = "AI Knowledge Assistant"
    app_version: str = "2.0.0"
    debug: bool = False

    # ── ChromaDB ─────────────────────────────────────────────────────────────
    chroma_persist_dir: str = "chroma_db"

    # ── Chunking ─────────────────────────────────────────────────────────────
    chunk_size: int = 1500
    chunk_overlap: int = 300

    # ── Retrieval ────────────────────────────────────────────────────────────
    retrieval_top_k: int = 10           # how many chunks to retrieve
    rerank_top_k: int = 5              # how many to keep after reranking

    # ── Storage paths ────────────────────────────────────────────────────────
    upload_dir: str = "uploads"
    feedback_db_path: str = "feedback.db"

    # ── OCR (Auto-detects Windows vs Docker) ─────────────────────────────────
    # For Windows manual run: Update these paths if they differ on your PC
    tesseract_cmd: str = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    poppler_path: str = r"C:\Users\DELL\Downloads\Release-25.12.0-0\poppler-25.12.0\Library\bin"

    @property
    def get_tesseract_cmd(self) -> str:
        """Returns system path for Docker/Linux, or full path for Windows."""
        import os
        if os.name != 'nt': # Linux/Docker
            return "tesseract"
        return self.tesseract_cmd

    @property
    def get_poppler_path(self) -> Optional[str]:
        """Returns None for Docker/Linux (uses system PATH), or full path for Windows."""
        import os
        if os.name != 'nt': # Linux/Docker
            return None
        return self.poppler_path

    # ── CORS ─────────────────────────────────────────────────────────────────
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://localhost:3000",
        "http://localhost",
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Allow adding extra origins via ENV like CORS_EXTRA="https://myapp.com,https://test.net"
        import os
        extra = os.getenv("CORS_EXTRA")
        if extra:
            origins = [o.strip() for o in extra.split(",") if o.strip()]
            self.cors_origins.extend(origins)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()


# ── Convenience aliases (backward-compatible with existing service imports) ──
settings = get_settings()
GROQ_API_KEY: str = settings.groq_api_key
MODEL_NAME: str = settings.model_name