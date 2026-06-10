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

## Running with Docker

```bash
docker compose up --build
```

This builds and starts both containers:
- `backend` — FastAPI/uvicorn on `:8000`
- `frontend` — Vite build served by nginx on `:5173`. The build is given `VITE_API_URL=http://localhost:8000` (see `docker-compose.yml`), so the browser calls the backend directly via its host-mapped port — nginx only serves static files, no `/api` proxy.

Requires an `.env` file in the project root with `OPENAI_API_KEY=sk-...` (Compose reads it automatically). `./vector_db` and `./chat_history.db` are bind-mounted into the backend container so data persists across restarts — `chat_history.db` must already exist as a file (an empty SQLite file, e.g. via `New-Item chat_history.db`) before the first run on a fresh checkout, otherwise Docker creates it as a directory.

## Deploying to Railway

Backend and frontend are deployed as **two separate services** in the same Railway project, each built from its own Dockerfile:

| Service | Root directory | Dockerfile | Env vars |
|---|---|---|---|
| backend | `/` (repo root) | `Dockerfile` | `OPENAI_API_KEY`, `ALLOWED_ORIGINS=<frontend-url>` |
| frontend | `/frontend` | `frontend/Dockerfile` | `VITE_API_URL=<backend-url>` (build-time) |

- `VITE_API_URL` is read in `frontend/src/api.js` and baked into the static build at build time (passed as a Docker `ARG` in `frontend/Dockerfile`) — set it to the backend's public Railway URL, e.g. `https://aidocanalyzer-production.up.railway.app`. The frontend's nginx (`frontend/nginx.conf`) only ever serves static files and has no `/api` proxy or upstream — every API call goes straight from the browser to that URL, so there's no `backend` hostname for nginx to resolve.
- `ALLOWED_ORIGINS` (comma-separated) is read in `api.py` and appended to the CORS allow-list alongside `http://localhost:5173` — set it to the frontend's public Railway URL.
- Railway sets `PORT` automatically; the backend Dockerfile's `CMD` binds to `0.0.0.0:8000` — override the start command to `uvicorn api:app --host 0.0.0.0 --port $PORT` if Railway's assigned port differs from 8000. The frontend's nginx listens on `:80`, which Railway maps automatically.
- `vector_db/` and `chat_history.db` are not persisted on Railway unless a volume is attached to the backend service.

## Architecture

**DocuMind AI** is a document Q&A RAG app. Three Python files + a React frontend:

| File | Role |
|---|---|
| `services.py` | All backend logic: ChromaDB, document ingestion, OpenAI calls, SQLite chat history, export generation. No UI calls — pure Python. |
| `api.py` | FastAPI layer. Thin — just routes, request parsing, and delegating to `services.py`. |
| `frontend/src/` | React UI (Vite). See below. |
| `app.py` | Legacy Streamlit app — still works but no longer the primary UI. |

### Frontend structure (`frontend/src/`)

| File | Role |
|---|---|
| `api.js` | All `fetch` wrappers + the `streamChat` async generator for SSE streaming |
| `App.jsx` | State management shell: sessions, documents, streaming, upload |
| `Sidebar.jsx` | Left panel: sessions, upload, doc list/filter, export/clear actions |
| `Chat.jsx` | Primary surface: message list, input pill, streaming cursor |
| `index.css` | Design tokens (OKLCH), global resets, Inter font |
| `*.module.css` | Component-scoped styles |

### Data flow

1. User uploads a file → `POST /api/documents/upload` → `process_and_save_document()` extracts text (PDF/DOCX/TXT) or calls GPT-4o Vision (images) → chunks via `RecursiveCharacterTextSplitter` → stored in ChromaDB at `./vector_db/`.
2. User sends a message → `POST /api/chat/stream` → `query_openai_api()` runs a LangChain tool-calling agent (`gpt-4o-mini`, or `gpt-4o` if an image is attached) → streams SSE chunks → `streamChat()` async generator in the frontend yields chunks → Chat.jsx updates state each tick.
3. Every message is persisted to SQLite at `./chat_history.db` via `PUT /api/sessions/{name}`.
4. On app load, `GET /api/sessions` restores all sessions.

### Key design decisions

- **ChromaDB** uses `text-embedding-3-small`. Collection: `corporate_docs`. Path resolved from `__file__`.
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
