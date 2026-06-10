# DocuMind AI

DocuMind AI is a document intelligence app: upload PDFs, Word docs, text files, or images, then have a focused conversation with their content. Ask questions, get summaries, and export the conversation — instead of skimming a 40-page document for the answer.

## How it works

1. **Upload** a document (PDF, DOCX, TXT, or an image). Text-based files are extracted and split into chunks; images are described via GPT-4o Vision (OCR-style).
2. Each chunk is embedded (`text-embedding-3-small`) and stored in a local **ChromaDB** vector database.
3. **Ask a question** in the chat. A LangChain tool-calling agent (`gpt-4o-mini`, or `gpt-4o` when an image is attached) decides whether to search the knowledge base, list available documents, or summarize a specific document — then streams the answer back token by token.
4. Conversations are saved as **sessions** in a local SQLite database and can be exported to DOCX or PDF.

## Architecture

```
┌─────────────┐      /api/*       ┌─────────────┐      ┌─────────────┐
│   React UI   │ ───────────────► │  FastAPI     │ ───► │  ChromaDB    │
│ (Vite, :5173)│ ◄─── SSE stream ──│  (api.py,    │      │ (./vector_db)│
└─────────────┘                   │  :8000)      │      └─────────────┘
                                   │      │       │
                                   │      ▼       │      ┌─────────────┐
                                   │ services.py  │ ───► │  SQLite      │
                                   │ (LangChain   │      │ (chat_history│
                                   │  agent +     │      │  .db)        │
                                   │  OpenAI API) │      └─────────────┘
                                   └─────────────┘
```

| Layer | Tech | Role |
|---|---|---|
| Frontend | React + Vite | Chat UI, document/session management, SSE streaming |
| Backend API | FastAPI | Thin HTTP layer — routes, request parsing, delegates to `services.py` |
| Business logic | `services.py` | ChromaDB, document ingestion/chunking, LangChain agent, SQLite chat history, export generation |
| Vector store | ChromaDB | Local, persisted to `./vector_db`, collection `corporate_docs` |
| LLM | OpenAI (`gpt-4o-mini` / `gpt-4o`) via LangChain | Chat agent + image OCR |

### The LangChain agent

`query_openai_api()` in `services.py` runs a tool-calling agent loop (`langchain_openai.ChatOpenAI` + `bind_tools()`, max 5 iterations) with three tools:

- **`search_knowledge_base(query)`** — similarity search (top-4) over ChromaDB, respecting the active document filter.
- **`list_documents()`** — returns the names of all files currently in the knowledge base.
- **`summarize_document(document_name)`** — fetches all chunks of a file (sorted by page) for the model to summarize.

On the first turn, the agent is forced to use `search_knowledge_base` if an image is attached or a document filter is active (the user is almost certainly asking about that content); otherwise it's forced to pick *any* tool, letting it choose `list_documents`/`summarize_document` for meta-questions. Chat history is passed in for multi-turn follow-ups.

### Document ingestion

Text is split with `RecursiveCharacterTextSplitter` (1000 chars, 200 overlap, splitting on paragraph/sentence boundaries first). PDFs use `pypdf`, DOCX uses `python-docx`, images are described via `gpt-4o` Vision (20 MB limit).

### Streaming

`/api/chat/stream` returns a `text/event-stream` (SSE) response. Each event is `data: {"chunk": "..."}`, terminated by `data: [DONE]`.

## Project structure

```
.
├── api.py                  # FastAPI routes (documents, sessions, chat, export)
├── services.py             # All backend logic — ChromaDB, agent, ingestion, SQLite, export
├── app.py                  # Legacy Streamlit UI (still works, no longer primary)
├── styles.py                # Streamlit UI styling (used by app.py)
├── requirements.txt         # Python dependencies
├── chat_history.db          # SQLite chat session storage (gitignored)
├── vector_db/                # ChromaDB persisted vector store (gitignored)
├── frontend/                 # React + Vite UI
│   ├── src/
│   │   ├── api.js             # fetch wrappers + SSE streamChat() generator
│   │   ├── App.jsx             # State shell: sessions, documents, streaming, upload
│   │   ├── Sidebar.jsx          # Sessions, upload, document list/filter, export/clear
│   │   ├── Chat.jsx              # Message list, input, streaming cursor
│   │   ├── index.css              # Design tokens (OKLCH), global resets, Inter font
│   │   └── *.module.css            # Component-scoped styles
│   ├── nginx.conf            # Static file server config (used in Docker)
│   └── Dockerfile
├── Dockerfile               # Backend container (FastAPI + uvicorn)
├── docker-compose.yml       # Runs backend + frontend together
└── .env.example             # Template for OPENAI_API_KEY
```

## Running locally

Two processes run simultaneously.

**1. Backend (FastAPI):**
```bash
pip install -r requirements.txt
uvicorn api:app --reload --port 8000
```

**2. Frontend (React + Vite):**
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — Vite proxies `/api/*` to `http://localhost:8000`.

### API key

Set `OPENAI_API_KEY` as an environment variable, or copy `.env.example` to `.streamlit/secrets.toml`:
```toml
OPENAI_API_KEY = "sk-..."
```
`services.py` reads the env var first, then falls back to `st.secrets`.

## Running with Docker

```bash
docker compose up --build
```

This builds and starts both containers:
- `backend` — FastAPI/uvicorn on `:8000`
- `frontend` — Vite build served by nginx on `:5173`, built with `VITE_API_URL=http://localhost:8000` so it calls the backend directly

Requires an `.env` file in the project root with `OPENAI_API_KEY=sk-...`. `./vector_db` and `./chat_history.db` are bind-mounted so data persists across restarts — `chat_history.db` must already exist as a file before the first run.

## Deploying to Railway

Backend and frontend deploy as two separate Railway services from the same repo — see [CLAUDE.md](CLAUDE.md#deploying-to-railway) for service config and required env vars (`VITE_API_URL`, `ALLOWED_ORIGINS`).

See [CLAUDE.md](CLAUDE.md) for detailed architecture notes and design system conventions.
