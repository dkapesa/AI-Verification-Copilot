# AI Verification Copilot

AI Verification Copilot is a production-style internal fraud and identity verification review dashboard designed to simulate the kind of tooling used by trust & safety, fraud operations, and identity verification teams.

The project is intentionally built as a full-stack portfolio and learning project with a strong focus on:
- realistic internal-tool UX
- structured fraud signal inspection
- deterministic tool execution
- AI-assisted review and decisioning
- persistence and auditability
- human-in-the-loop workflow design

It is designed to be something you can both build and explain clearly in an interview.

---

## Current Project Status

**Status:** In active development  
**Current phase:** Frontend dashboard cleanup and production-minded polish

### Working today

- FastAPI backend running locally
- PostgreSQL running locally in Docker
- Next.js frontend dashboard running locally
- Paginated case queue at `/cases`
- Case detail page at `/cases/[id]`
- Deterministic tool execution from the UI
- Persisted tool results auto-loading on refresh
- AI review execution from the UI
- Persisted latest AI review auto-loading on refresh
- Audit timeline showing case, tool, and AI events
- Human override placeholder workflow visible in the UI
- Local frontend API configuration consolidated in one place
- Local dev CORS tightened to explicit frontend origins

---

## What the Project Simulates

This project simulates an internal analyst dashboard where a reviewer can:

- browse verification cases
- open a case detail page
- inspect structured identity and fraud signals
- run deterministic fraud tools
- run an AI review / decisioning step
- inspect explainability and aggregated signals
- review audit history
- see a human override placeholder workflow

This mirrors the structure of a realistic internal operations console rather than a consumer-facing product.

---

## Tech Stack

## Backend
- Python
- FastAPI
- SQLAlchemy ORM
- Pydantic
- Uvicorn
- Alembic

## Database
- PostgreSQL
- Docker

## Frontend
- Next.js
- TypeScript
- Tailwind CSS
- App Router

## AI / Review Orchestration
- LangGraph-based AI review flow
- structured AI decision outputs
- deterministic fraud tools
- persisted AI review results
- persisted tool execution results

---

## High-Level Architecture

The system is split into a backend API, a PostgreSQL persistence layer, and a frontend analyst dashboard.

### Backend
The backend exposes REST endpoints for:
- cases
- deterministic tool execution
- persisted tool runs
- AI review execution
- persisted AI reviews
- audit logs
- human override stub workflow

### Frontend
The frontend consumes those endpoints and renders an internal analyst-style dashboard with:
- case queue
- case detail screen
- deterministic tool results panel
- AI review panel
- human override panel
- audit timeline

### Persistence
The system persists:
- verification cases
- tool runs
- AI reviews
- audit logs

This means the dashboard reflects saved operational state rather than only temporary browser session state.

---

## Repo Structure

This is the current working structure documented at a high level:

```text
backend/
  app/
  alembic/
  requirements.txt

frontend/
  src/
  public/
  package.json
