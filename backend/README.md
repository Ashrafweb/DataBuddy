# Backend

## Overview

A FastAPI backend for the SQL Agent. Converts natural-language questions into safe PostgreSQL `SELECT` queries (via Gemini if available, with a rule-based fallback), executes them against a local PostgreSQL DB, and exposes simple endpoints for health, schema, and queries.

## Files

- server.py — Main FastAPI app and logic (DB connection, Gemini integration/fallback, SQL validation/execution, API routes).
- requirements.txt — Python dependencies used to install the environment.
- .env — Environment variables (API keys, DB paths, Mongo URL, CORS origins).
- init_db.py — (If present) helper to initialize the PostgreSQL database.
- README.md — This file.

## Key environment variables

Set these in .env or your shell:

- `MONGO_URL` — Mongo connection string (used by `motor` client).
- `DB_NAME` — Mongo database name.
- `CORS_ORIGINS` — Comma-separated origins for CORS (default `*`).
- `GEMINI_API_KEY` — (Recommended) Google Gemini API key for generative SQL.
- `POSTGRES_URL` — PostgreSQL connection string (e.g., `postgresql://user:password@localhost:5432/sql_agent`).

## Setup (Windows / PowerShell)

```powershell
cd "C:\Users\USER\Documents\Sql-agent\backend"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r .\requirements.txt
# Optional: install only essentials
# pip install fastapi "uvicorn[standard]" python-dotenv google-generativeai psycopg2-binary
```

## Run (development)

Start using the venv Python so modules resolve correctly:

```powershell
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload
```

## HTTP endpoints

- `GET /api/health` — returns `{ "status": "healthy", "database": "connected" }`
- `GET /api/tables` — lists tables and their columns (response model `TableInfo`)
- `POST /api/query` — accepts `{ "question": "...", "session_id": "optional" }`, returns SQL, results, row count and execution time (response model `QueryResponse`)
- `GET /api/` — basic root message.

## How it works (high level)

- Loads env vars from .env.
- Creates a Mongo client (motor) with `MONGO_URL` and `DB_NAME`.
- Connects to PostgreSQL using `POSTGRES_URL`.
- `generate_sql_with_gemini()` tries to call Google Gemini SDK (`google.generativeai`) when a `GEMINI_API_KEY` is present. If not available or fails, a conservative rule-based fallback generates simple safe queries.
- `validate_sql()` blocks dangerous keywords (DROP, DELETE, INSERT, UPDATE, ALTER, TRUNCATE, CREATE, GRANT, REVOKE).
- `execute_sql()` runs the SQL against PostgreSQL and returns rows and timing.

## Security & safety notes

- Do NOT commit API keys. Use .env and keep it out of source control.
- SQL validation is defensive but not exhaustive — avoid exposing this service to untrusted networks without additional hardening.
