# 🛠️ Tools & Backend — Complete Interview Mastery Guide

> **Purpose:** After reading this guide, you should be able to answer ANY interview question about Docker, Nginx, Git, REST APIs, Asyncio, and SSE — confidently and with examples from YOUR own project.

---

## Table of Contents

1. [Docker](#1-docker)
2. [Nginx](#2-nginx)
3. [Git](#3-git)
4. [REST APIs](#4-rest-apis)
5. [Asynchronous Processing (Asyncio)](#5-asynchronous-processing-asyncio)
6. [SSE (Server-Sent Events)](#6-sse-server-sent-events)

---

---

# 1. Docker

## 1.1 What is Docker? (The Analogy)

Imagine you cook a perfect dish at home. You want to send it to your friend so they taste the EXACT same thing. But if you just send the recipe, their oven might be different, their ingredients might be different brands. **Docker is like sending the entire kitchen** — the oven, the ingredients, the recipe, everything — sealed in a box. Your friend opens it, and it works perfectly.

**Technical Translation:**
Docker packages your application + its entire environment (OS, libraries, Python version, dependencies) into a **Container**. This container runs identically on your laptop, your friend's laptop, a cloud server, or anywhere.

## 1.2 Key Concepts You MUST Know

| Concept | What It Is | Analogy |
|---|---|---|
| **Image** | A read-only blueprint/template | A recipe card |
| **Container** | A running instance of an image | The actual dish being cooked from the recipe |
| **Dockerfile** | Instructions to build an image | The step-by-step recipe |
| **Volume** | Persistent storage outside the container | A fridge that survives even if the kitchen is destroyed |
| **Port Mapping** | Connecting container's internal port to the host | Putting a doorbell on the kitchen so outsiders can ring it |
| **Layer** | Each Dockerfile instruction creates a cached layer | Each step in the recipe is saved so you don't repeat it |
| **Registry** | A cloud storage for images (Docker Hub) | A cookbook library where you publish/pull recipes |

## 1.3 Your Dockerfile — Line by Line

> [!TIP]
> Your project uses a **Multi-Stage Build**, which is an advanced Docker technique. This alone is impressive to mention in an interview.

```dockerfile
# ── Phase 1: Frontend Builder ──
FROM node:20-alpine AS frontend-builder    # Start with a small Node.js image
WORKDIR /app/frontend                       # Set the working directory
COPY frontend/package*.json ./              # Copy ONLY dependency files first (for caching!)
RUN npm ci                                  # Install dependencies (clean install)
COPY frontend/ .                            # Now copy the rest of the frontend source
RUN npm run build                           # Build the React app into static files (dist/)

# ── Phase 2: Final Production Environment ──
FROM python:3.11-slim                       # Start FRESH with a small Python image

RUN apt-get update && apt-get install -y \
    tesseract-ocr \                         # OCR engine for scanned PDFs
    poppler-utils \                         # PDF rendering utilities
    nginx \                                 # Web server for frontend
    curl \                                  # For health checks
    && apt-get clean                        # Clean up to reduce image size

WORKDIR /app

COPY backend/requirements.txt ./backend/
RUN pip install --no-cache-dir -r ./backend/requirements.txt  # Install Python deps

# Pre-download AI models so they're baked into the image
RUN python -c "from sentence_transformers import SentenceTransformer, CrossEncoder; \
    SentenceTransformer('sentence-transformers/all-MiniLM-L-6-v2'); \
    CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

COPY backend/ ./backend/

# Magic: Copy the BUILT frontend from Phase 1 into Nginx's serving directory
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html

COPY frontend/nginx.conf /etc/nginx/sites-available/default
COPY start_app.sh ./
RUN chmod +x ./start_app.sh

EXPOSE 7860
CMD ["./start_app.sh"]
```

### Why Multi-Stage?

**Phase 1** has `node_modules` (500MB+), but the **final image** (Phase 2) only has the tiny `dist/` folder (~2MB). Result: your production image is **~70% smaller**.

## 1.4 Docker Compose — What & Why

Your `docker-compose.yml` defines **multiple services** (frontend + backend) and how they talk to each other.

```yaml
services:
  backend:
    build:
      context: ./backend
    ports:
      - "8000:8000"          # Host port 8000 → Container port 8000
    volumes:
      - chroma_data:/app/chroma_db   # Named volume: data survives container restarts
      - ./backend/uploads:/app/uploads  # Bind mount: share files with host
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/upload/list"]
      interval: 30s          # Check every 30 seconds
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

  frontend:
    depends_on:
      backend:
        condition: service_healthy  # Frontend won't start until backend is healthy
```

## 1.5 Interview Questions & Answers

### Q1: "What is the difference between an Image and a Container?"
> **Answer:** "An **Image** is a read-only blueprint — like a class in OOP. A **Container** is a running instance of that image — like an object. You can create multiple containers from the same image. Images are built from Dockerfiles and stored in registries like Docker Hub."

### Q2: "What is a Multi-Stage Build and why did you use it?"
> **Answer:** "A Multi-Stage Build uses multiple `FROM` statements. In my project, the first stage builds the React frontend with Node.js, producing a `dist/` folder. The second stage starts fresh with Python and copies ONLY that `dist/` folder. This means the final image doesn't contain `node_modules` or the Node.js runtime at all, reducing the image size by about 70%."

### Q3: "Why did you copy `package.json` BEFORE copying the source code?"
> **Answer:** "Docker builds use **layer caching**. Each instruction creates a layer. If a layer hasn't changed, Docker reuses the cached version. Since `package.json` changes rarely but source code changes often, copying it first means `npm ci` is cached and doesn't re-run on every build. This speeds up builds from minutes to seconds."

### Q4: "What is the difference between `COPY` and `ADD`?"
> **Answer:** "`COPY` simply copies files. `ADD` can also extract tar files and download URLs. Best practice is to always use `COPY` unless you specifically need `ADD`'s extra features, because `COPY` is more predictable."

### Q5: "What is a Docker Volume?"
> **Answer:** "Volumes are Docker's mechanism for **persistent storage**. Containers are ephemeral — when you delete one, its filesystem is gone. In my project, I use a named volume `chroma_data` to persist the ChromaDB vector database, so uploaded documents survive container restarts."

### Q6: "What is `CMD` vs `ENTRYPOINT`?"
> **Answer:** "`CMD` provides default arguments that can be overridden at runtime. `ENTRYPOINT` defines the fixed command. In my Dockerfile, `CMD [\"./start_app.sh\"]` runs my startup script, but I could override it with `docker run myimage /bin/bash` for debugging."

### Q7: "What does `--no-cache-dir` do in `pip install`?"
> **Answer:** "It tells pip not to save downloaded packages in a cache directory. In Docker, we don't need the cache because the layer itself IS the cache. Removing it reduces the final image size."

### Q8: "How does `depends_on` with `service_healthy` work?"
> **Answer:** "In my docker-compose, the frontend service has `depends_on: backend: condition: service_healthy`. This means Docker Compose won't start the frontend container until the backend's healthcheck (`curl` to `/api/upload/list`) returns a 200 status. This prevents the frontend from trying to proxy to a backend that isn't ready yet."

## 1.6 Cheat Sheet — Essential Docker Commands

```bash
docker build -t myapp .          # Build an image from Dockerfile
docker run -p 8000:8000 myapp    # Run a container, map port
docker ps                        # List running containers
docker ps -a                     # List ALL containers (including stopped)
docker logs <container_id>       # See container logs
docker exec -it <id> /bin/bash   # SSH into a running container
docker stop <id>                 # Gracefully stop a container
docker system prune -a           # Clean up ALL unused images/containers

docker-compose up --build        # Build and start all services
docker-compose down              # Stop and remove all services
docker-compose logs -f backend   # Follow logs of backend service
```

---

---

# 2. Nginx

## 2.1 What is Nginx? (The Analogy)

Think of Nginx as a **hotel receptionist**. When a guest (user) arrives, the receptionist doesn't cook the food or clean the room. Instead, they **route** the guest to the right department:
- "Want a webpage?" → *Here's the static file from the storage room*
- "Want data from the API?" → *Let me call the backend kitchen for you*

**Technical Translation:**
Nginx is a **reverse proxy** and **static file server**. It sits in front of your application, serving static files directly (very fast) and forwarding API requests to your backend.

## 2.2 Key Concepts You MUST Know

| Concept | What It Is |
|---|---|
| **Reverse Proxy** | Nginx receives the request and forwards it to Python/Node.js (the real server). The user never talks to Python directly. |
| **Static File Server** | Serves HTML, CSS, JS, images directly from disk — much faster than Python |
| **Load Balancer** | Distributes traffic across multiple backend instances |
| **Gzip Compression** | Compresses responses before sending to reduce bandwidth |
| **`try_files`** | Tries to serve a file; if not found, falls back to `index.html` (critical for SPAs) |
| **`proxy_pass`** | Forwards the request to another server (your FastAPI) |

## 2.3 Your nginx.conf — Line by Line

```nginx
server {
    listen 7860;                    # Nginx listens on port 7860 (Hugging Face standard)
    server_name localhost;

    # ── Performance: Compress responses ──
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;
    # This reduces the size of transferred files by 60-80%, making your app faster.

    # ── Route 1: Frontend (Static Files) ──
    location / {
        root /usr/share/nginx/html;         # Where the built React app lives
        index index.html;
        try_files $uri $uri/ /index.html;   # ← THIS IS THE KEY LINE
    }

    # ── Route 2: Backend API (Reverse Proxy) ──
    location /api {
        proxy_pass http://localhost:8000/api;  # Forward to FastAPI on port 8000
        proxy_http_version 1.1;

        # Headers so backend knows the real client's IP
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        # Timeouts for long LLM responses (5 minutes!)
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }

    # ── Route 3: Health Check ──
    location /health {
        proxy_pass http://localhost:8000/;
        access_log off;   # Don't spam logs with health checks
    }
}
```

## 2.4 The `try_files` Explanation (Very Important!)

This is the **#1 most asked Nginx question** for frontend developers:

```nginx
try_files $uri $uri/ /index.html;
```

**What it does:** When a user visits `yoursite.com/dashboard`:
1. Nginx first tries to find a file literally named `dashboard` → Not found
2. Then tries a directory named `dashboard/` → Not found
3. **Falls back** to serving `index.html` → React Router takes over and renders the `/dashboard` component

**Why it's needed:** React is a **Single Page Application (SPA)**. There's only ONE HTML file. All "pages" like `/dashboard`, `/login`, `/settings` are handled by JavaScript (React Router) inside that single file. Without `try_files`, refreshing on `/dashboard` would give a **404 error** because no file named `dashboard` exists on disk.

## 2.5 Interview Questions & Answers

### Q1: "What is a Reverse Proxy and why did you use Nginx?"
> **Answer:** "A reverse proxy sits between the user and the backend. The user talks to Nginx, and Nginx forwards requests to FastAPI. I used it for three reasons: (1) Nginx serves static React files 10x faster than Python, (2) It acts as a single entry point — the user only sees port 7860, not separate ports for frontend and backend, (3) It adds security headers like `X-Real-IP` and `X-Forwarded-For`."

### Q2: "What would happen without `try_files $uri $uri/ /index.html`?"
> **Answer:** "If a user refreshes the page on `/dashboard`, Nginx would look for a physical file at `/usr/share/nginx/html/dashboard`. Since React is an SPA and that file doesn't exist, they'd get a 404. `try_files` ensures that all unknown paths fall back to `index.html`, where React Router handles the routing on the client side."

### Q3: "Why did you set `proxy_read_timeout 300`?"
> **Answer:** "My application uses LLMs (Large Language Models) that can take several seconds to generate a full response. The default Nginx timeout is 60 seconds, which would close the connection mid-generation, breaking the SSE stream. I set it to 300 seconds (5 minutes) to accommodate long-running AI responses."

### Q4: "Why Gzip?"
> **Answer:** "Gzip compresses the response body before sending. A 200KB JavaScript file can be compressed to ~40KB. This reduces bandwidth usage by 60-80% and speeds up page load times, especially on mobile networks."

### Q5: "Forward Proxy vs Reverse Proxy?"
> **Answer:** "A **Forward Proxy** sits in front of the **client** (like a VPN — the server doesn't know who you really are). A **Reverse Proxy** sits in front of the **server** (like Nginx in my project — the client doesn't know about my FastAPI server). The key difference is WHO is being hidden."

## 2.6 Cheat Sheet

```bash
nginx -t                    # Test config syntax without restarting
nginx -s reload             # Reload config without downtime
nginx -g 'daemon off;'      # Run in foreground (used in Docker)
cat /var/log/nginx/error.log  # Debug errors
```

---

---

# 3. Git

## 3.1 What is Git? (The Analogy)

Git is like a **time machine for your code**. Every time you make a save point (`commit`), Git remembers the exact state of every file. You can go back to any point in time, create parallel timelines (`branches`), and merge different timelines together.

## 3.2 Key Concepts You MUST Know

| Concept | What It Is | Analogy |
|---|---|---|
| **Repository (Repo)** | A project tracked by Git | A time-machine-enabled folder |
| **Commit** | A snapshot of your project at a point in time | A save point in a video game |
| **Branch** | A parallel line of development | An alternate timeline |
| **Merge** | Combining two branches together | Merging two timelines into one |
| **Staging Area (Index)** | A preparation zone before committing | A "pack your bag" step before traveling |
| **Remote** | A copy of your repo on a server (GitHub) | A backup in the cloud |
| **HEAD** | A pointer to your current commit/branch | "You are HERE" on a map |
| **Clone** | Copy a remote repo to your local machine | Download the whole project |
| **Fork** | Copy someone else's repo to your GitHub account | Making your own copy of someone's cookbook |

## 3.3 The Three Areas of Git

```
┌──────────────┐     git add     ┌──────────────┐    git commit    ┌──────────────┐
│  Working     │ ──────────────→ │   Staging    │ ───────────────→ │  Repository  │
│  Directory   │                 │   Area       │                  │  (.git)      │
│  (your files)│                 │  (index)     │                  │  (history)   │
└──────────────┘                 └──────────────┘                  └──────────────┘
       ↑                                                                    │
       └──────────────────── git checkout ──────────────────────────────────┘
```

**Working Directory** → Your actual files on disk.
**Staging Area** → Files you've selected to include in the next commit (`git add`).
**Repository** → The committed history (the `.git` folder).

## 3.4 Interview Questions & Answers

### Q1: "What is the difference between `git merge` and `git rebase`?"
> **Answer:**
> - **`git merge`** creates a new "merge commit" that combines two branches. It preserves the complete history but can look messy.
> - **`git rebase`** replays your commits on top of the target branch, creating a **linear** history. It's cleaner but rewrites commit hashes.
> - **Rule of thumb:** Use `merge` for public/shared branches (like `main`). Use `rebase` for cleaning up your own feature branch before merging.

### Q2: "What is a merge conflict and how do you resolve it?"
> **Answer:** "A merge conflict happens when two branches modify the **same line** of the **same file**. Git can't decide which version to keep, so it marks the file with conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`). I resolve it by opening the file, deciding which code to keep (or combining both), removing the markers, and then committing the result."

### Q3: "What is `git stash`?"
> **Answer:** "`git stash` temporarily saves your uncommitted changes and reverts your working directory to a clean state. It's useful when you need to switch branches to fix a bug but don't want to commit your half-finished work. You get them back with `git stash pop`."

### Q4: "What is the difference between `git pull` and `git fetch`?"
> **Answer:** "`git fetch` downloads changes from the remote but does NOT modify your working files. `git pull` does `fetch` + `merge` — it downloads AND applies the changes. I prefer `git fetch` first so I can review changes before merging."

### Q5: "What is `.gitignore` and what did you ignore in your project?"
> **Answer:** "`.gitignore` tells Git which files/folders to NOT track. In my project, I ignore `node_modules/` (huge dependency folder), `.env` (contains secret API keys like GROQ_API_KEY), `__pycache__/` (Python cache), and `chroma_db/` (the vector database data — it's generated, not source code)."

### Q6: "What is `git cherry-pick`?"
> **Answer:** "It lets you take a **specific commit** from one branch and apply it to another, without merging the entire branch. Useful when a bug fix is on a feature branch but you need it on `main` immediately."

### Q7: "Explain `HEAD`, `HEAD~1`, and `HEAD^`."
> **Answer:**
> - `HEAD` = the current commit you're on
> - `HEAD~1` = one commit before HEAD (the parent)
> - `HEAD~3` = three commits before HEAD
> - `HEAD^` = also the parent (same as `HEAD~1` for single-parent commits)

### Q8: "What is `git reset` vs `git revert`?"
> **Answer:**
> - **`git reset`** moves HEAD backwards and can DELETE commits from history. Use with caution. Types: `--soft` (keeps changes staged), `--mixed` (keeps changes in working dir), `--hard` (deletes everything).
> - **`git revert`** creates a NEW commit that undoes a previous commit. It's safe for shared branches because it doesn't rewrite history.

## 3.5 Cheat Sheet

```bash
# Basics
git init                         # Initialize a new repo
git clone <url>                  # Clone a remote repo
git status                       # Check current state
git log --oneline -10            # View last 10 commits (clean format)

# Stage & Commit
git add .                        # Stage all changes
git add <file>                   # Stage a specific file
git commit -m "feat: add SSE streaming"  # Commit with a message
git commit --amend               # Modify the last commit

# Branches
git branch                       # List branches
git branch feature-x             # Create a new branch
git checkout feature-x           # Switch to a branch
git checkout -b feature-x        # Create AND switch (shortcut)
git merge feature-x              # Merge feature-x into current branch
git branch -d feature-x          # Delete a branch

# Remote
git remote -v                    # Show remote URLs
git push origin main             # Push to remote
git pull origin main             # Pull from remote
git fetch origin                 # Download without merging

# Undo
git stash                        # Save uncommitted work temporarily
git stash pop                    # Restore stashed work
git reset --hard HEAD~1          # DELETE last commit (DANGER!)
git revert <commit-hash>         # Safely undo a commit
```

---

---

# 4. REST APIs

## 4.1 What is a REST API? (The Analogy)

Imagine a **restaurant**:
- You (Client/Frontend) sit at the table.
- The **Waiter (API)** takes your order to the kitchen.
- The **Kitchen (Server/Backend)** prepares your food.
- The waiter brings the food back.

You never go into the kitchen. You communicate through a **menu** (API documentation) and the **waiter** (HTTP requests).

**REST** (Representational State Transfer) is a set of rules for how this communication should work.

## 4.2 The 6 Principles of REST

| Principle | Meaning | Your Project Example |
|---|---|---|
| **Stateless** | Each request contains ALL the info needed. The server doesn't "remember" you between requests. | Every request includes the JWT token in the `Authorization` header |
| **Client-Server** | Frontend and Backend are separate systems | React (port 7860) ↔ FastAPI (port 8000) |
| **Uniform Interface** | Standard URL patterns and HTTP methods | `POST /api/ask/`, `GET /api/upload/list`, `DELETE /api/upload/{filename}` |
| **Resource-Based** | URLs represent "things" (nouns), not "actions" (verbs) | `/api/upload/` (the resource is "upload"), not `/api/doUpload` |
| **Layered System** | Client doesn't know if it's talking to the real server or a proxy | Nginx sits between your React frontend and FastAPI |
| **Cacheable** | Responses can indicate if they're cacheable | Static files served by Nginx with caching headers |

## 4.3 HTTP Methods — The 5 Verbs

| Method | Purpose | Your Project Example | Analogy |
|---|---|---|---|
| **GET** | Read/retrieve data | `GET /api/upload/list` — get all uploaded documents | Looking at the menu |
| **POST** | Create new data or trigger an action | `POST /api/ask/` — ask a question | Placing an order |
| **PUT** | Replace an entire resource | (Not used in your project) | Sending food back and getting a completely new plate |
| **PATCH** | Partially update a resource | (Not used in your project) | Asking for extra salt on your plate |
| **DELETE** | Remove a resource | `DELETE /api/upload/{filename}` — delete a document | Canceling an order |

## 4.4 HTTP Status Codes — What You MUST Know

| Range | Meaning | Common Codes |
|---|---|---|
| **2xx** | ✅ Success | `200 OK`, `201 Created`, `204 No Content` |
| **3xx** | ↪️ Redirect | `301 Moved Permanently`, `304 Not Modified` |
| **4xx** | ❌ Client Error (your fault) | `400 Bad Request`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `422 Unprocessable Entity` |
| **5xx** | 💥 Server Error (server's fault) | `500 Internal Server Error`, `502 Bad Gateway`, `503 Service Unavailable` |

**In your project:**
- `401` → Invalid or missing JWT token (from `auth.py`)
- `400` → Empty question sent to `/api/ask/`
- `422` → No valid documents processed in upload

## 4.5 Your REST API Routes — Complete Map

```
┌───────────────────────────────────────────────────────────────────┐
│                     YOUR API ROUTES                               │
├───────────────────────────────────────────────────────────────────┤
│                                                                   │
│  AUTH (No token needed)                                           │
│  ├── POST  /api/auth/login        → Get JWT token                │
│                                                                   │
│  UPLOAD (Token required)                                          │
│  ├── POST  /api/upload/           → Upload documents              │
│  ├── GET   /api/upload/list       → List all documents            │
│  ├── DELETE /api/upload/{file}    → Delete a document             │
│  └── POST  /api/upload/sync      → Cleanup orphan entries        │
│                                                                   │
│  CHAT (Token required)                                            │
│  └── POST  /api/ask/              → Ask a question (SSE stream)  │
│                                                                   │
│  FEEDBACK (Token required)                                        │
│  ├── POST  /api/feedback/         → Submit feedback               │
│  ├── GET   /api/feedback/metrics  → Get system performance        │
│  └── GET   /api/feedback/improvements → Self-improvement logs    │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

## 4.6 Request/Response Anatomy

### Example: Upload a Document

**Request:**
```http
POST /api/upload/ HTTP/1.1
Host: localhost:7860
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI...
Content-Type: multipart/form-data; boundary=----FormBoundary

------FormBoundary
Content-Disposition: form-data; name="files"; filename="notes.pdf"
Content-Type: application/pdf

<binary PDF data>
------FormBoundary--
```

**Response:**
```json
[
  {
    "filename": "notes.pdf",
    "characters_extracted": 12450,
    "chunks_created": 23,
    "chunks_stored": 23,
    "message": "Processed successfully ✅"
  }
]
```

## 4.7 Interview Questions & Answers

### Q1: "What is REST?"
> **Answer:** "REST stands for Representational State Transfer. It's a design style for APIs that uses standard HTTP methods (GET, POST, PUT, DELETE) on resource-based URLs. Key principles include statelessness (each request is self-contained), a uniform interface (predictable URL patterns), and separation of client and server."

### Q2: "What is the difference between PUT and PATCH?"
> **Answer:** "**PUT** replaces the entire resource. If you PUT a user object without an email field, the email is deleted. **PATCH** partially updates — it only modifies the fields you send, leaving the rest unchanged."

### Q3: "How do you handle authentication in your REST API?"
> **Answer:** "I use **JWT (JSON Web Tokens)**. The user sends credentials to `POST /api/auth/login`. If valid, the server returns a signed JWT. For every subsequent request, the client includes this token in the `Authorization: Bearer <token>` header. On the backend, FastAPI's dependency injection system (`Depends(get_current_user)`) validates the token on every protected route before executing the handler."

### Q4: "What is the difference between 401 and 403?"
> **Answer:** "**401 Unauthorized** means 'I don't know who you are' — you haven't logged in or your token expired. **403 Forbidden** means 'I know who you are, but you don't have permission to access this' — like a regular user trying to access an admin route."

### Q5: "What is `multipart/form-data`?"
> **Answer:** "It's a Content-Type used for sending **files** via HTTP. Unlike `application/json` which is pure text, `multipart/form-data` can include binary data (like PDFs, images). In my project, the upload route accepts multiple files using this encoding — FastAPI handles it with the `UploadFile` type."

### Q6: "What is idempotency?"
> **Answer:** "An operation is **idempotent** if doing it multiple times has the same effect as doing it once. `GET` and `DELETE` are idempotent — getting a resource twice gives the same result, deleting a resource twice doesn't delete it 'more.' `POST` is NOT idempotent — posting the same upload twice creates two entries. This is why APIs sometimes use `PUT` for updates."

---

---

# 5. Asynchronous Processing (Asyncio)

## 5.1 What is Async? (The Analogy)

Imagine you're a **chef cooking alone**:

**Synchronous (Blocking):** You put water to boil, then STAND AND WATCH the pot for 10 minutes doing NOTHING. Then you start chopping vegetables. Total time: 10 + 5 = **15 minutes.**

**Asynchronous (Non-Blocking):** You put water to boil, and WHILE it boils, you start chopping vegetables. When the water is ready, you come back to it. Total time: **10 minutes** (both happened in parallel).

**Technical Translation:**
In a web server, the "boiling water" is **waiting for external I/O** — waiting for the database, waiting for an API response, waiting for a file to upload. `async` lets your server handle OTHER requests while it waits, instead of sitting idle.

## 5.2 Key Concepts

| Concept | What It Is |
|---|---|
| **Coroutine** | A function defined with `async def`. It CAN be paused and resumed. |
| **`await`** | The pause point. "I'm waiting for this slow thing; go handle someone else." |
| **Event Loop** | The manager that decides which coroutine to run next (like a chef deciding what to work on) |
| **`async def`** | Declares a coroutine function |
| **Blocking vs Non-Blocking** | Blocking = waiting and doing nothing. Non-blocking = waiting but doing other work. |
| **Concurrency** | Doing multiple things by switching between them (one CPU) |
| **Parallelism** | Doing multiple things at the literal same time (multiple CPUs) |

> [!IMPORTANT]
> **Asyncio is CONCURRENCY, not PARALLELISM.** It uses ONE thread, ONE CPU. It's fast because web servers spend 90% of their time WAITING (for database, API calls, file I/O), and asyncio uses that waiting time productively.

## 5.3 Your Project's Async Usage

### Example 1: The Chat Route (async generator + await)

```python
# chat.py
@router.post("/")
async def ask_question(request: QuestionRequest, ...):
    # FastAPI knows this is a coroutine — it won't block other users

    async def _graph_stream():
        # This is an async generator — it yields data piece by piece
        async for output in knowledge_graph.astream(initial_state):
            # Each 'await' is a pause point. While waiting for the LLM,
            # the server can handle OTHER users' requests!
            yield f"data: [TOKEN]{json.dumps(answer)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(_graph_stream(), media_type="text/event-stream")
```

### Example 2: Background Tasks (fire-and-forget)

```python
# After sending the answer to the user, evaluate quality in the background
background_tasks.add_task(
    _bg_evaluate, session_id, question, final_state["answer"], context_str, retry_count
)
# The user gets their answer immediately — evaluation happens later
```

### Example 3: Blocking code in an async world (`run_in_threadpool`)

```python
# upload.py
stored = await run_in_threadpool(store_chunks, chunks, document_name=file.filename)
```

> **Why?** `store_chunks` uses ChromaDB, which is a **synchronous** library. If you call it directly in an `async` function, it BLOCKS the event loop and freezes ALL other users. `run_in_threadpool` runs it in a separate thread so it doesn't block.

## 5.4 Sync vs Async — Visual Comparison

```
SYNCHRONOUS SERVER (handles 1 user at a time):
────────────────────────────────────────────────────

User A: [──── wait for DB ────][process][respond]
User B:                                          [──── wait for DB ────][process][respond]
User C:                                                                                     [──── wait ...]

Total time: Very long (sequential)

ASYNCHRONOUS SERVER (handles many users concurrently):
────────────────────────────────────────────────────

User A: [start].....................[DB ready → process → respond]
User B:    [start].................[DB ready → process → respond]
User C:       [start].............[DB ready → process → respond]

    (during "..." the server is handling other users)

Total time: Much shorter (concurrent)
```

## 5.5 Interview Questions & Answers

### Q1: "What is the difference between Concurrency and Parallelism?"
> **Answer:** "**Concurrency** is about dealing with multiple things at once — like one chef switching between tasks. **Parallelism** is about doing multiple things at the literal same time — like having multiple chefs. Python's `asyncio` provides concurrency using a single-threaded event loop. For CPU-heavy tasks (like training a model), you'd need `multiprocessing` for true parallelism."

### Q2: "Why use async in FastAPI?"
> **Answer:** "Web servers spend most of their time waiting — waiting for database responses, waiting for external API calls (like Groq), waiting for file I/O. With async, while one request is waiting for the Groq API to generate tokens, the server handles another user's request. In my project, this means multiple users can ask questions simultaneously without blocking each other."

### Q3: "What happens if you call a blocking function inside an async function?"
> **Answer:** "It blocks the entire event loop! Since asyncio is single-threaded, a blocking call (like `time.sleep(10)` or a synchronous database query) freezes ALL concurrent requests. In my project, I solved this by using `run_in_threadpool()` from Starlette to offload synchronous ChromaDB operations to a separate thread, keeping the event loop free."

### Q4: "What is `async for`?"
> **Answer:** "It's used to iterate over an **async iterator** — a stream of data that arrives piece by piece. In my chat route, `async for output in knowledge_graph.astream(...)` processes each agent's output as it becomes available, instead of waiting for the entire graph to finish. This enables real-time streaming."

### Q5: "What is a BackgroundTask in FastAPI?"
> **Answer:** "It's a way to run code AFTER the response has been sent to the user. In my project, I send the answer to the user immediately, then run the LLM-Judge evaluation as a background task. The user doesn't wait for evaluation — they get their answer right away."

### Q6: "Async/Await vs Threading vs Multiprocessing?"
> **Answer:**
> - **Async/Await:** Best for **I/O-bound** tasks (API calls, database, file reads). Single thread, cooperative multitasking. Used in my FastAPI backend.
> - **Threading:** Good for I/O-bound tasks too, but uses OS threads. More memory overhead. Risk of race conditions.
> - **Multiprocessing:** Best for **CPU-bound** tasks (number crunching, model training). Uses multiple processes with separate memory spaces.

## 5.6 Cheat Sheet

```python
import asyncio

# Define an async function (coroutine)
async def fetch_data():
    await asyncio.sleep(2)  # Simulate waiting (non-blocking)
    return "data"

# Run multiple tasks concurrently
async def main():
    results = await asyncio.gather(
        fetch_data(),
        fetch_data(),
        fetch_data(),
    )
    # All 3 finish in ~2 seconds, not 6!

asyncio.run(main())
```

---

---

# 6. SSE (Server-Sent Events)

## 6.1 What is SSE? (The Analogy)

Think of **three communication styles**:

| Style | Analogy | Tech Equivalent |
|---|---|---|
| **Request-Response** | You call someone, they answer, you hang up | Normal REST API (`GET /data`) |
| **WebSocket** | You call someone and stay on the line — both can talk anytime | Real-time chat (both sides send messages) |
| **SSE** | You turn on a **radio station** — the station broadcasts, you only listen | Live news feed, stock tickers, **AI token streaming** |

**SSE = Server sends data to the client continuously over a single HTTP connection. The client only listens.**

## 6.2 Why SSE Instead of WebSockets?

| Feature | SSE | WebSocket |
|---|---|---|
| **Direction** | Server → Client only | Bidirectional |
| **Protocol** | Standard HTTP | Separate WS protocol |
| **Reconnection** | Automatic (built-in) | Manual (you code it) |
| **Firewall/Proxy** | No issues (it's just HTTP) | Can be blocked by proxies |
| **Complexity** | Simple | Complex |
| **Best For** | AI streaming, notifications, live feeds | Chat apps, gaming, collaboration tools |

> **Why in your project?** You only need server-to-client streaming (the AI "types" tokens to the user). The user sends ONE request, and the server streams back tokens. SSE is simpler, more reliable, and works perfectly through Nginx.

## 6.3 The SSE Protocol (How It Actually Works)

SSE uses a specific text format over HTTP:

```
HTTP/1.1 200 OK
Content-Type: text/event-stream    ← THIS tells the browser: "keep the connection open"
Cache-Control: no-cache            ← Don't cache streaming data

data: [AGENT_TRACE]{"agent":"planner","status":"done","duration_ms":150}

data: [AGENT_TRACE]{"agent":"retriever","status":"done","duration_ms":320}

data: [TOKEN]"The answer to your question is..."

data: [SOURCES][{"source":"notes.pdf"}]

data: [DONE]

```

**Rules:**
- Each message starts with `data: `
- Messages are separated by `\n\n` (double newline)
- The connection stays open until the server sends `[DONE]` or closes it

## 6.4 Your SSE Implementation — Both Sides

### Backend (FastAPI — the broadcaster)

```python
# chat.py — The server-side SSE generator
async def _graph_stream():
    # 1. Stream agent trace events (so UI shows which agent is working)
    yield f"data: [AGENT_TRACE]{json.dumps(trace)}\n\n"

    # 2. Stream the actual answer token
    yield f"data: [TOKEN]{json.dumps(answer)}\n\n"

    # 3. Stream source documents
    yield f"data: [SOURCES]{json.dumps(sources)}\n\n"

    # 4. Signal completion
    yield "data: [DONE]\n\n"

# Return as StreamingResponse with the correct media type
return StreamingResponse(_graph_stream(), media_type="text/event-stream")
```

### Frontend (React — the listener)

```typescript
// useAgentStream.ts — The client-side SSE reader
const response = await fetch(`${API_BASE_URL}/ask/`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({ question, source }),
});

// Read the response body as a stream
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
    const { value, done } = await reader.read();  // Read chunk by chunk
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // Split by double-newline (SSE message boundary)
    const lines = buffer.split('\n\n');

    for (const line of lines) {
        const rawData = line.replace(/^data: /, '').trim();

        if (rawData.startsWith('[TOKEN]')) {
            // Update the message in React state → user sees text appearing
            const tokenValue = JSON.parse(rawData.substring(7));
            setMessages(prev => prev.map(m =>
                m.id === assistantId ? { ...m, content: tokenValue } : m
            ));
        }
        else if (rawData.startsWith('[AGENT_TRACE]')) {
            // Light up the agent trace badges in the UI
            const traceItem = JSON.parse(rawData.substring(13));
            setCurrentTrace(prev => [...prev, traceItem]);
        }
        else if (rawData.startsWith('[DONE]')) {
            // Mark the message as complete
            setMessages(prev => prev.map(m =>
                m.id === assistantId ? { ...m, isStreaming: false } : m
            ));
        }
    }
}
```

## 6.5 The Data Flow (Visual)

```
┌──────────┐         POST /api/ask/          ┌──────────────┐
│  React   │ ─────────────────────────────→  │   FastAPI     │
│ Frontend │                                  │   Backend     │
│          │  ← data: [AGENT_TRACE]{...}     │               │
│          │  ← data: [AGENT_TRACE]{...}     │  LangGraph    │
│          │  ← data: [TOKEN]"The answer..." │  Agent Graph  │
│          │  ← data: [SOURCES][{...}]       │               │
│          │  ← data: [DONE]                 │               │
└──────────┘                                  └──────────────┘
     ↑                                              ↑
     │  User sees text appearing live                │  Groq LLM generates
     │  Agent badges light up in UI                  │  tokens one by one
```

## 6.6 Interview Questions & Answers

### Q1: "What is SSE and when would you use it over WebSockets?"
> **Answer:** "SSE (Server-Sent Events) is a standard HTTP-based protocol for streaming data from server to client. Unlike WebSockets which are bidirectional, SSE is unidirectional — server to client only. I chose SSE for my AI project because: (1) I only need server-to-client streaming (the AI sends tokens to the user), (2) SSE works through standard HTTP proxies like Nginx without special configuration, (3) SSE has built-in auto-reconnection if the connection drops, and (4) it's simpler to implement and debug."

### Q2: "How did you implement SSE in your project?"
> **Answer:** "On the **backend**, I used FastAPI's `StreamingResponse` with an async generator that yields SSE-formatted strings (`data: [TOKEN]...\n\n`). On the **frontend**, I used the Fetch API's `ReadableStream` to read the response body chunk by chunk. I parse each chunk by splitting on double-newlines, identify the event type by the prefix (`[TOKEN]`, `[AGENT_TRACE]`, `[DONE]`), and update React state accordingly. The user sees the text appearing in real-time as tokens arrive."

### Q3: "What is `text/event-stream`?"
> **Answer:** "It's the MIME type that tells the browser to treat the response as a Server-Sent Events stream. Instead of waiting for the entire response before processing, the browser processes data as it arrives. In FastAPI, I set this as `media_type='text/event-stream'` in the `StreamingResponse`."

### Q4: "How do you handle errors in SSE?"
> **Answer:** "On the frontend, I wrap the stream reader in a try-catch. If the connection fails, I update the message to show an error state. I also use an `AbortController` so the user can cancel a generation mid-stream. On the backend, if the LLM throws an error, the generator catches it and can yield a `[ERROR]` event before closing."

### Q5: "What Nginx configuration is needed for SSE?"
> **Answer:** "Three things: (1) `proxy_http_version 1.1` — SSE requires HTTP/1.1 for persistent connections, (2) `proxy_set_header Connection 'upgrade'` — prevents Nginx from closing the connection prematurely, (3) `proxy_read_timeout 300` — sets a long timeout because SSE connections stay open for the duration of the response, which can be several minutes for long AI-generated answers."

### Q6: "SSE vs Long Polling?"
> **Answer:** "**Long Polling** is a hack where the client makes a request, the server holds it until data is available, responds, and the client immediately makes another request. It creates a new HTTP connection for each message — wasteful. **SSE** opens ONE connection and the server pushes data whenever it's ready. SSE is more efficient, uses less bandwidth, and has lower latency."

## 6.7 Cheat Sheet

```python
# Minimal SSE in FastAPI
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio

app = FastAPI()

async def event_generator():
    for i in range(10):
        yield f"data: Message {i}\n\n"
        await asyncio.sleep(1)  # One message per second
    yield "data: [DONE]\n\n"

@app.get("/stream")
async def stream():
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

```javascript
// Minimal SSE in JavaScript (using EventSource — simpler but GET only)
const source = new EventSource('/stream');
source.onmessage = (event) => {
    console.log(event.data);
};

// For POST requests (like your project), use fetch + ReadableStream
```

---

---

# 🎯 Quick Revision Table — All 6 Technologies

| Technology | What It Is (1 Line) | Why You Used It | Your File |
|---|---|---|---|
| **Docker** | Packages your app + environment into a portable container | Consistent deployment across dev, staging, production | `Dockerfile`, `docker-compose.yml` |
| **Nginx** | Reverse proxy + static file server | Serves React (fast), proxies API requests, single entry point | `frontend/nginx.conf` |
| **Git** | Version control for tracking code changes | Collaboration, history, branching, deployment | `.git/`, `.gitignore` |
| **REST APIs** | Standard HTTP-based interface for client-server communication | Frontend-backend communication with clear route structure | `backend/app/api/routes/` |
| **Asyncio** | Non-blocking I/O for handling concurrent requests | Multiple users can query the AI simultaneously without blocking | All `async def` functions in backend |
| **SSE** | Server-to-client streaming over HTTP | Real-time token streaming for AI responses + agent traces | `chat.py` (backend), `useAgentStream.ts` (frontend) |

---

> [!TIP]
> **The Golden Rule for Interviews:** When asked about ANY of these technologies, follow this structure:
> 1. **Define it** in one simple sentence
> 2. **Explain WHY** you used it (not just how)
> 3. **Give a specific example** from your project (mention a file name!)
> 4. **Mention a trade-off** ("I chose X over Y because...")
