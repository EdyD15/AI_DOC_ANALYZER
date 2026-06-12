# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the app

Two processes must run simultaneously:

**Backend (FastAPI):**
```bash
uvicorn api:app --reload --port 8000
```

**Frontend (React + Vite dev server):**
```bash
cd frontend && npm run dev
```

The app is at `http://localhost:5173`. Vite proxies `/api/*` to `http://localhost:8000`.

## Installing dependencies

**Python:**
```bash
pip install -r requirements.txt
```

**Node:**
```bash
cd frontend && npm install
```

## API key

Set `OPENAI_API_KEY` as an environment variable, or store it in `.streamlit/secrets.toml` (gitignored):
```toml
OPENAI_API_KEY = "sk-..."
```

`services.py` reads the env var first, falls back to `st.secrets`.

## Authentication

JWT-based auth. `auth.py` holds the JWT helpers and the `get_current_user` FastAPI dependency; every route in `api.py` (except `/api/auth/register` and `/api/auth/login`) requires a valid `Authorization: Bearer <token>` header.

- `JWT_SECRET_KEY` env var signs tokens (HS256, 7-day expiry). If unset, `auth.py` falls back to an insecure default and logs a warning — set a real random value locally (`.env`) and on the Railway backend service.
- `POST /api/auth/register` and `POST /api/auth/login` create/verify users (bcrypt-hashed passwords) in a `users` table and return `{ "access_token": ..., "username": ... }`. `GET /api/auth/me` returns the current user.
- **Database backend**: `services.py` checks `DATABASE_URL` at import time. If set, `users` and `chat_sessions` live in that Postgres database (via `psycopg2`); otherwise they live in a local SQLite file at `chat_history.db`. On Railway, set `DATABASE_URL` to the attached Postgres plugin's connection string — without it, `chat_history.db` is wiped on every redeploy and all accounts/sessions are lost. `init_chat_db()` creates both tables on startup for whichever backend is active.
- Each user's documents live in their own ChromaDB collection, `corporate_docs_{user_id}` — full isolation by construction, no metadata filtering needed.
- `chat_sessions` is keyed by `(user_id, session_name)`.
- Frontend stores the token + username in `localStorage` (`api.js`); `App.jsx` renders `AuthPage` (`Login.jsx`/`Register.jsx`) when no token is present, and logs the user out (clearing localStorage and resetting state) on any `AuthError` (401) from the API.
- **Migration note**: introducing auth was a breaking change to the pre-existing `chat_sessions` table (it had no `user_id`) — old anonymous sessions were dropped on first run after upgrading. The old `corporate_docs` ChromaDB collection (pre-auth) is now orphaned; users need to register an account and re-upload their documents.

## Running with Docker

```bash
docker compose up --build
```

This builds and starts both containers:
- `backend` — FastAPI/uvicorn on `:8000`
- `frontend` — Vite build served by nginx on `:5173`. The build is given `VITE_API_URL=http://localhost:8000` (see `docker-compose.yml`), so the browser calls the backend directly via its host-mapped port — nginx only serves static files, no `/api` proxy.

Requires an `.env` file in the project root with `OPENAI_API_KEY=sk-...` and `JWT_SECRET_KEY=<random-string>` (Compose reads it automatically). `./vector_db` and `./chat_history.db` are bind-mounted into the backend container so data persists across restarts — `chat_history.db` must already exist as a file (an empty SQLite file, e.g. via `New-Item chat_history.db`) before the first run on a fresh checkout, otherwise Docker creates it as a directory.

## Deploying to Railway

Backend and frontend are deployed as **two separate services** in the same Railway project, each built from its own Dockerfile:

| Service | Root directory | Dockerfile | Env vars |
|---|---|---|---|
| backend | `/` (repo root) | `Dockerfile` | `OPENAI_API_KEY`, `JWT_SECRET_KEY`, `ALLOWED_ORIGINS=<frontend-url>`, `DATABASE_URL=<postgres-plugin-url>` |
| frontend | `/frontend` | `frontend/Dockerfile` | `VITE_API_URL=<backend-url>` (build-time) |

- `VITE_API_URL` is read in `frontend/src/api.js` and baked into the static build at build time (passed as a Docker `ARG` in `frontend/Dockerfile`) — set it to the backend's public Railway URL, e.g. `https://aidocanalyzer-production.up.railway.app`. The frontend's nginx only ever serves static files and has no `/api` proxy or upstream — every API call goes straight from the browser to that URL, so there's no `backend` hostname for nginx to resolve.
- `ALLOWED_ORIGINS` (comma-separated) is read in `api.py` and appended to the CORS allow-list alongside `http://localhost:5173` — set it to the frontend's public Railway URL.
- Railway sets `PORT` automatically and routes the public domain to whatever port the container listens on at runtime; it does **not** default to 80. The backend Dockerfile's `CMD` binds to `0.0.0.0:8000` — override the start command to `uvicorn api:app --host 0.0.0.0 --port $PORT` if Railway's assigned port differs from 8000. The frontend's nginx is configured via `frontend/nginx.conf.template` (`listen ${PORT};`), rendered at container startup by the base image's envsubst entrypoint script — `frontend/Dockerfile` sets `ENV PORT=80` as a default for local/Docker Compose use, and Railway's injected `PORT` overrides it automatically.
- `vector_db/` is not persisted on Railway unless a volume is attached to the backend service. `chat_history.db` (users/sessions) is only relevant if `DATABASE_URL` is unset — with it set, users/sessions persist in Postgres across redeploys instead.

## Architecture

**DocuMind AI** is a document Q&A RAG app. Python backend + a React frontend:

| File | Role |
|---|---|
| `services.py` | All backend logic: ChromaDB, document ingestion, OpenAI calls, SQLite chat history, user accounts, export generation. No UI calls — pure Python. |
| `api.py` | FastAPI layer. Thin — just routes, request parsing, and delegating to `services.py`. |
| `auth.py` | JWT helpers (`create_access_token`) and the `get_current_user` dependency used to protect routes in `api.py`. |
| `frontend/src/` | React UI (Vite). See below. |
| `app.py` | Legacy Streamlit app — still works but no longer the primary UI. |

### Frontend structure (`frontend/src/`)

| File | Role |
|---|---|
| `api.js` | All `fetch` wrappers + the `streamChat` async generator for SSE streaming + auth (`login`/`register`/`logout`/token storage) |
| `App.jsx` | State management shell: auth gating, sessions, documents, streaming, upload |
| `AuthPage.jsx` | Toggles between `Login.jsx` and `Register.jsx` |
| `Login.jsx` / `Register.jsx` | Auth forms, styled via `Auth.module.css` |
| `Sidebar.jsx` | Left panel: sessions, upload, doc list/filter, export/clear actions, user info + logout |
| `Chat.jsx` | Primary surface: message list, input pill, streaming cursor |
| `index.css` | Design tokens (OKLCH), global resets, Inter font |
| `*.module.css` | Component-scoped styles |

### Data flow

1. User uploads a file → `POST /api/documents/upload` → `process_and_save_document()` extracts text (PDF/DOCX/TXT) or calls GPT-4o Vision (images) → chunks via `RecursiveCharacterTextSplitter` → stored in ChromaDB at `./vector_db/`.
2. User sends a message → `POST /api/chat/stream` → `query_openai_api()` runs a LangChain tool-calling agent (`gpt-4o-mini`, or `gpt-4o` if an image is attached) → streams SSE chunks → `streamChat()` async generator in the frontend yields chunks → Chat.jsx updates state each tick.
3. Every message is persisted to SQLite at `./chat_history.db` via `PUT /api/sessions/{name}`.
4. On app load, `GET /api/sessions` restores all sessions.

### Key design decisions

- **ChromaDB** uses `text-embedding-3-small`. Per-user collections: `corporate_docs_{user_id}`. Path resolved from `__file__`.
- **Chunking** uses `RecursiveCharacterTextSplitter` (1000 chars, 200 overlap) with separators `["\n\n", "\n", ". ", ...]` — splits on paragraph/sentence boundaries before falling back to characters.
- **Image OCR** uses `gpt-4o` vision (20 MB limit). Chat uses `gpt-4o-mini`.
- **PDF export** uses fpdf2 with latin-1 — non-ASCII chars (emoji, curly quotes) become `?`. DOCX export has no such limit.
- **Streaming**: `api.py` returns `StreamingResponse` with SSE (`text/event-stream`). Each event is `data: {"chunk": "..."}`. Done signal is `data: [DONE]`.
- **Chat input** hard-limited to 5000 chars (enforced in `App.jsx` before the API call).
- **AI error rollback**: if the stream errors, `App.jsx` removes both the user message and the AI placeholder from state and re-saves the session.
- **`_get_api_key()`** in `services.py`: reads `OPENAI_API_KEY` env var first, lazy-imports `st.secrets` as fallback — so the file works with or without Streamlit installed.

### LangChain agent (`query_openai_api` in `services.py`)

- Built with `langchain_openai.ChatOpenAI` + `bind_tools()`. Three tools (`_build_tools`):
  - `search_knowledge_base(query)` — ChromaDB similarity search (top-4), respecting the active document filter (`selected_documents`).
  - `list_documents()` — returns all file names currently in the knowledge base.
  - `summarize_document(document_name)` — fetches all chunks for a file (sorted by page, truncated at 12k chars) for the model to summarize.
- The agent loop streams each turn via `.stream()`, accumulating `AIMessageChunk`s to detect `tool_calls`; tool results are appended as `ToolMessage`s and the loop repeats (max `MAX_TOOL_ITERATIONS = 5`).
- **First-turn tool forcing**: if an image is attached or a document filter (`selected_documents`) is active, the first turn forces `search_knowledge_base` specifically — the user is almost certainly asking about that scoped content, and OCR'd image descriptions only surface via search. Otherwise the first turn forces "any tool" (`tool_choice="required"`), letting the agent pick `list_documents`/`summarize_document` for meta-questions. Subsequent turns use `tool_choice="auto"`.
- When `selected_documents` is set, the system prompt is extended to tell the agent which document(s) the conversation is scoped to.
- `chat_history` (list of `{role, content}` dicts from `ChatBody`) is converted to `HumanMessage`/`AIMessage` and prepended before the current question, enabling multi-turn follow-ups.

## Design system

Product register (UI serves the task). Light theme. Restrained OKLCH color strategy.

Tokens are in `frontend/src/index.css`. Key values:
- Accent: `oklch(54% 0.19 264)` (blue) — used only on primary actions and active states
- Font: Inter (Google Fonts), 13px base, tight scale
- Transitions: 150ms ease on bg/border/color only

Absolute bans (impeccable skill): gradient text, glassmorphism, side-stripe colored borders, hero-metric template, decorative motion.
