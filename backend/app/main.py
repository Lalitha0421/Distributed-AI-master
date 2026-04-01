"""
main.py — FastAPI application entry point.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.chat import router as chat_router
from app.api.routes.upload import router as upload_router
from app.api.routes.feedback import router as feedback_router
from app.core.config import settings
from app.core.logger import logger
from app.core.tracing import RequestTracingMiddleware
from app.models.schemas import HealthResponse

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    description="Multi-agent RAG system with LangGraph orchestration, hybrid retrieval, and self-evaluation.",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware (order matters — tracing first, then CORS) ─────────────────────
app.add_middleware(RequestTracingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(upload_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(feedback_router, prefix="/api")

# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/", response_model=HealthResponse, tags=["health"])
async def health_check() -> HealthResponse:
    logger.info("Health check called")
    return HealthResponse(
        message=f"{settings.app_name} is running 🚀",
        llm_model=settings.model_name,
        version=settings.app_version,
        status="healthy",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)