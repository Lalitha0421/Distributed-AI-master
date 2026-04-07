#!/bin/bash
# start_app.sh — Hugging Face Entry Point

# 1. Start the backend in the background
echo "🚀 Starting Backend (FastAPI)..."
cd /app/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# 2. Start Nginx to serve the Frontend
echo "🌐 Starting Frontend (Nginx)..."
nginx -g 'daemon off;'
