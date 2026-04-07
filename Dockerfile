# ── Phase 1: Frontend Builder ──
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ── Phase 2: Final Production Environment ──
FROM python:3.11-slim

# Set system dependencies (OCR + Nginx)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    nginx \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. Install Backend dependencies
COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# 2. Pre-download AI Models to avoid slow runtime download
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; \
    SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2'); \
    CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

# 3. Copy Backend source
COPY backend/ ./backend/

# 4. Copy Frontend build output to Nginx's global directory
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

# 5. Connect Frontend and Backend with Nginx
COPY frontend/nginx.conf /etc/nginx/sites-available/default
# Link for standard nginx load
RUN ln -sf /etc/nginx/sites-available/default /etc/nginx/conf.d/default.conf

# 6. Copy and prepare the startup script
COPY start_app.sh ./
RUN chmod +x ./start_app.sh

# Expose port (Hugging Face standard)
EXPOSE 7860

# Start everything!
CMD ["./start_app.sh"]
