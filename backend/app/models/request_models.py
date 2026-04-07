"""
request_models.py — Re-exports from the central schemas module.

Keeps backward-compatible import paths for existing code that imports
from app.models.request_models.
"""

from app.models.schemas import QuestionRequest  # noqa: F401 — re-export
