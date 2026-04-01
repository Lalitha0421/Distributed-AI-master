"""
tracing.py — Request ID middleware for the AI Knowledge System.

Attaches a UUID to every incoming request so that all log lines
from that single request share the same request_id — making debugging trivial.

Usage: app.add_middleware(RequestTracingMiddleware)
"""

from __future__ import annotations

import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.logger import logger, set_request_id


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """
    For every HTTP request:
      1. Generate a UUID request ID (or read X-Request-ID header if provided).
      2. Store it in the ContextVar so all loggers in this request see it.
      3. Add it to the response header so the frontend can correlate logs.
      4. Log request start and finish with duration.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # Allow the caller to supply their own request ID (e.g. from API gateway)
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
        set_request_id(request_id)

        start = time.perf_counter()
        logger.info(f"→ {request.method} {request.url.path}")

        try:
            response: Response = await call_next(request)
        except Exception as exc:
            duration_ms = int((time.perf_counter() - start) * 1000)
            logger.error(f"✗ {request.method} {request.url.path} | {duration_ms}ms | UNHANDLED: {exc}")
            raise

        duration_ms = int((time.perf_counter() - start) * 1000)
        logger.info(f"← {request.method} {request.url.path} | {response.status_code} | {duration_ms}ms")

        # Forward request_id in response header so the frontend can log it
        response.headers["X-Request-ID"] = request_id
        return response
