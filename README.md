# AI Verification Copilot

**AI Verification Copilot** is a production-style internal fraud triage and decisioning system designed to simulate the type of tooling used by identity verification and trust & safety teams to review potentially suspicious verification cases.

The project is being built as a full-stack engineering portfolio piece with a strong focus on backend systems, structured tool execution, agent-based orchestration, human-in-the-loop workflows, auditability, and evaluation discipline.

The current implementation includes:

- a working FastAPI backend
- PostgreSQL persistence
- SQLAlchemy ORM models
- Alembic migrations
- paginated case APIs
- structured audit logging
- a deterministic fraud tooling layer capable of executing multiple risk analysis tools in parallel

The next phase introduces agent-based orchestration for automated decision making.

---

## Backend Architecture

The current backend is designed using a layered architecture so that each part of the system remains independently understandable, testable, and extensible.

### **API Layer**

FastAPI provides the HTTP interface and automatic OpenAPI documentation.

### **Schema Layer**

Pydantic models define request validation and response serialization.

### **CRUD Layer**

Database access is separated into CRUD functions to keep route handlers thin and maintainable.

### **Persistence Layer**

SQLAlchemy ORM maps Python models to PostgreSQL tables.

### **Migration Layer**

Alembic manages database schema evolution through version-controlled migrations.

### **Audit Layer**

Audit events are written to `audit_logs` to capture backend actions, metadata, and latency.

## System Workflow

The current system processes verification cases using the following workflow:

1. A verification case is created through the API.
2. The case is persisted in PostgreSQL.
3. Risk analysis tools can be executed for the case.
4. Each tool produces structured risk signals.
5. Tool results are stored in the `tool_runs` table.
6. The API returns aggregated tool results for review.

This workflow forms the foundation for the upcoming agent orchestration layer, which will automatically interpret tool results and produce risk decisions.

---

## Data Model

### **`cases`**

Represents a verification case under review.

Fields include:

- `id` (UUID)
- `user_id`
- `email`
- `device_info` (JSONB)
- `document_check_result` (JSONB)
- `behaviour_summary` (JSONB)
- `status` (`PENDING`, `REVIEWED`, `ESCALATED`)
- `created_at`
- `updated_at`

### **`audit_logs`**

Stores backend and workflow events for observability and traceability.

Fields include:

- `id` (UUID)
- `case_id` (nullable)
- `event_type`
- `actor_type`
- `subject`
- `latency_ms`
- `metadata` (JSONB)
- `created_at`

### **`tool_runs`**

Stores the results of deterministic risk tools executed against a verification case.

Fields include:

- `id` (UUID)
- `case_id`
- `tool_name`
- `status`
- `score`
- `confidence`
- `summary`
- `signals` (JSONB)
- `output` (JSONB)
- `error_message`
- `latency_ms`
- `started_at`
- `completed_at`
  
---

## Tech Stack

### **Backend**

- Python
- FastAPI
- Pydantic / pydantic-settings
- SQLAlchemy
- Alembic
- Uvicorn

### **Database**

- PostgreSQL
- Docker / Docker Compose

### **Frontend (planned)**

- Next.js
- TypeScript
- Tailwind

### **AI / Orchestration (planned)**

- LangGraph
- OpenAI API
- optional Ollama fallback

---

## Local Development

### **Prerequisites**

- Python 3.11+
- Node.js 18+
- Docker Desktop
- Git
- VS Code recommended

---

## Roadmap

### **1) Repo setup + dev workflow**

- [x]  Monorepo structure
- [x]  Backend, frontend, and database runnable locally

### **2) Backend foundation**

- [x]  FastAPI backend
- [x]  PostgreSQL persistence
- [x]  SQLAlchemy models
- [x]  Alembic migrations
- [x]  Audit logging
- [x]  Pagination and 404 handling

### **3) Tooling layer**

- [x]  Shared tool output schema
- [x]  `tool_runs` persistence model
- [x]  Deterministic fraud checks
- [x]  Tool registry
- [x]  Parallel tool execution
- [x]  Tool execution API endpoint

### **4) Agent orchestration**

- [ ]  LangGraph workflow
- [ ]  Structured AI review output
- [ ]  Decision persistence
- [ ]  Retry on invalid structured output

### **5) Frontend dashboard**

- [ ]  Case list view
- [ ]  Case detail view
- [ ]  Tool outputs
- [ ]  AI review panel
- [ ]  Audit timeline

### **6) Evaluation harness**

- [ ]  Synthetic dataset
- [ ]  Expected labels
- [ ]  Decision metrics
- [ ]  Latency and coverage metrics

### **7) Production polish**

- [ ]  Full Docker Compose stack
- [ ]  `.env.example`
- [ ]  Logging improvements
- [ ]  Better developer onboarding

### **8) Deployment + portfolio packaging**

- [ ]  Hosted backend
- [ ]  Hosted frontend
- [ ]  Hosted Postgres
- [ ]  Demo video
- [ ]  Evaluation write-up

## Current Status

**Project status:** Ongoing  
**Current phase:** Agent Orchestration

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

- Tooling layer
  - structured tool result schemas
  - tool registry pattern
  - deterministic fraud checks
  - parallel tool execution
  - tool execution API endpoint

### In progress
- Agent orchestration layer
- Structured decision outputs
- risk aggregation logic

---

## Demo Evidence

### API Overview
Swagger/OpenAPI overview of the current backend foundation, showing the core case management endpoints.

![Swagger overview](images/api/swagger-overview.png)

### Successful Case Creation
Successful case creation through the FastAPI API, returning a persisted verification case with generated UUID, status, and timestamps.

![Create case response](images/api/create-case-response.png)

### 404 Error Handling
Missing-case lookup returning a structured `404` response instead of an internal server error.

![Case not found 404](images/errors/case-not-found-404.png)

### Audit Logging
Audit log query showing backend events, latency measurements, and structured metadata captured during case workflows.

![Audit logs table](images/database/audit-logs-table.png)

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

---

## Core Features Implemented

### Backend API
- `POST /api/v1/cases` — create a verification case
- `GET /api/v1/cases` — list cases with pagination
- `GET /api/v1/cases/{case_id}` — retrieve a case by ID
### Tool Execution
- `POST /api/v1/cases/{case_id}/run-tools` — execute deterministic fraud analysis tools against a case
- Stub routes for:
  - `POST /api/v1/cases/{id}/ai-review`
  - `POST /api/v1/cases/{id}/human-override`
### Deterministic Risk Tooling

The system includes a modular tooling layer capable of executing multiple fraud detection tools in parallel.

Currently implemented tools include:

- `behaviour_anomaly_check`
- `device_risk_check`
- `rules_risk_score`
- `watchlist_screening`

Each tool returns structured results including:

- risk score
- confidence level
- summary explanation

The system uses a **tool registry pattern** to dynamically discover and execute tools without hardcoding them in API endpoints.

Parallel execution allows the system to scale as new tools are added while keeping latency low.

---

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

    B --> I[Tool Runner Service]
    I --> J[Tool Registry]
    J --> K[Fraud Analysis Tools]

    K --> L[Tool Results]
    L --> G

    M[Alembic Migrations] --> G

    N[Future Agent Layer] -.-> I
    N -.-> G
