"""
logger.py — Structured logging for the AI Knowledge System.

Every log line includes: timestamp, level, request_id (if set), module, message.
The request_id is injected via context var by the tracing middleware so you can
trace a single request across all service calls.
"""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar

# ── Context var: request ID injected by tracing middleware ────────────────────
_request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def get_request_id() -> str:
    return _request_id_var.get()


def set_request_id(request_id: str) -> None:
    _request_id_var.set(request_id)


# ── Custom formatter: adds request_id to every line ──────────────────────────
class RequestIdFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        record.request_id = get_request_id()
        return super().format(record)


# ── Build logger ──────────────────────────────────────────────────────────────
def _build_logger() -> logging.Logger:
    logger = logging.getLogger("ai_knowledge")
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)

        fmt = RequestIdFormatter(
            fmt="%(asctime)s | %(levelname)-8s | req=%(request_id)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(fmt)
        logger.addHandler(handler)

    logger.propagate = False
    return logger


logger = _build_logger()