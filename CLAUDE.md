# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Yapper is an AI-powered journaling app. Users record audio or type entries, which get transcribed (Whisper), refined (GPT-4o-mini), embedded (text-embedding-3-large), and stored in Supabase PostgreSQL. Two conversation modes: **Yap** (guided journaling) and **Chat** (free-form with semantic context retrieval via HNSW vector search). Monthly summaries are auto-generated via APScheduler.

## Architecture

- **Backend**: Flask (Python 3.11) REST API at `/api/*`, deployed on Railway via gunicorn
- **Frontend**: React 18 + Vite SPA, deployed on Vercel
- **Database/Auth**: Supabase (PostgreSQL + pgvector + JWT auth)
- **AI**: OpenAI SDK for chat completions, Whisper transcription, and embeddings

Frontend authenticates via Supabase Auth, passes JWT in `Authorization: Bearer` header. Backend creates user-scoped Supabase clients per request. Guest mode falls back to localStorage.

## Commands

### Backend
```bash
python app.py                    # Run Flask dev server (port 5002)
flask vectorize-entries          # Generate embeddings for unprocessed entries
flask generate-monthly-summary --user-id UUID --month M --year Y
```

### Frontend
```bash
cd frontend
npm run dev                      # Vite dev server (port 3000)
npm run build                    # Production build → dist/
```

No test suite exists currently.

## Key File Locations

**Backend entry point**: `app.py` — registers blueprints, CORS, scheduler, CLI commands

**Routes** (`backend/routes/`):
- `converse.py` — Yap mode (guided conversation with context injection)
- `chat.py` — Chat mode with semantic search context retrieval
- `audio.py` — Whisper audio transcription
- `entries.py` — Journal entry CRUD
- `monthly_summaries.py` — Summary generation and retrieval

**Services** (`backend/services/`):
- `embedding.py` — OpenAI embedding generation + Supabase storage
- `context_retrieval.py` — Semantic search using HNSW index
- `hnsw_index.py` — hnswlib vector index management
- `initial_processing.py` — GPT-4o-mini text refinement

**Frontend** (`frontend/src/`):
- `App.jsx` — Custom client-side router (no react-router)
- `components/JournalPage.jsx` — Main UI with Yap/Chat/Entries/Summaries tabs
- `context/AuthContext.jsx` — Global auth state
- `context/supabase.js` — Supabase client init

## Environment Variables

**Backend** (`.env`): `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, `OPENAI_API_KEY`, `DATABASE_URL`, `FRONTEND_URL`, `ENCRYPTION_MASTER_KEY`, `CORS_ORIGINS`

**Frontend** (`.env.local`): `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY`, `VITE_BACKEND_URL`, `VITE_API_URL`

Vite proxies `/api` requests to `VITE_API_URL` (default `http://127.0.0.1:5000`) in dev.

## Data Flow

1. User input (audio/text) → Whisper transcription → GPT-4o-mini refinement → stored in `entries` table
2. `flask vectorize-entries` generates embeddings → stored in `entries.vectors` column
3. Chat/Yap queries: embed query → HNSW similarity search → inject top-K entries as context → OpenAI completion → streamed response

## Deployment

- **Frontend**: Vercel (`vercel.json` — builds frontend, rewrites all routes to `index.html`)
- **Backend**: Railway/Nixpacks (`.nixpacks.toml` — Python 3.11, gunicorn start)
- **Branch workflow**: `dev` branch → `main` for production
