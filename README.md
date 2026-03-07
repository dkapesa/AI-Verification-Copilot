# AI Verification Copilot

**AI Verification Copilot** is a production-style internal fraud triage and decisioning system designed to simulate the type of tooling used by identity verification and trust & safety teams to review potentially suspicious verification cases.

The project is being built as a full-stack engineering portfolio piece with a strong focus on backend systems, structured tool execution, agent-based orchestration, human-in-the-loop workflows, auditability, and evaluation discipline. The current implementation includes a working FastAPI backend, PostgreSQL persistence, SQLAlchemy models, Alembic migrations, paginated case APIs, and audit logging. The next phase introduces a deterministic tooling layer for fraud checks before moving into LLM-based orchestration.

---

## Current Status

**Project status:** Ongoing  
**Current phase:** Tooling Layer (Days 5–9)

### Completed so far
- Repo setup + local development workflow
- Backend foundation
  - FastAPI API
  - PostgreSQL persistence
  - SQLAlchemy ORM models
  - Alembic migrations
  - Pydantic request/response schemas
  - CRUD case workflows
  - audit logging
  - pagination
  - 404 handling
  - latency instrumentation

### In progress
- Deterministic tool execution layer
- Structured tool outputs
- Tool result persistence
- Preparation for agent orchestration

---

## Why this project exists

Most portfolio AI projects jump straight to model calls. This project takes a more production-oriented approach.

The goal is to build a realistic internal system that:
- persists verification cases
- runs deterministic risk checks
- records audit trails
- supports structured AI decisions
- enables human review and override
- can later be evaluated on synthetic case datasets

This makes the project relevant for roles across:
- Backend Engineering
- Applied AI / ML Engineering
- Product Engineering
- LLM Systems Engineering
- Trust & Safety / decisioning platform work

---

## Core Features Implemented

### Backend API
- `POST /api/v1/cases` — create a verification case
- `GET /api/v1/cases` — list cases with pagination
- `GET /api/v1/cases/{case_id}` — retrieve a case by ID
- Stub routes for:
  - `POST /api/v1/cases/{id}/ai-review`
  - `POST /api/v1/cases/{id}/human-override`

### Persistence & Data Modeling
- PostgreSQL database running locally in Docker
- SQLAlchemy ORM models for:
  - `cases`
  - `audit_logs`
- Alembic migration-based schema management

### Reliability & Observability
- Structured audit logging for key backend actions
- Latency tracking for selected API operations
- Pagination for list endpoints
- Proper `404` handling for missing cases
- OpenAPI / Swagger docs for local testing

---

## Architecture Diagram

```mermaid
flowchart TD
    A[Browser / Swagger UI / Future Frontend] --> B[FastAPI App]
    B --> C[API Routers]
    C --> D[Pydantic Schemas]
    C --> E[CRUD Layer]
    E --> F[SQLAlchemy ORM]
    F --> G[(PostgreSQL)]
    B --> H[Audit Logging]
    H --> G
    I[Alembic Migrations] --> G

    J[Future Tooling Layer] -.-> B
    J -.-> G
    K[Future Agent Orchestration] -.-> J
    K -.-> G
