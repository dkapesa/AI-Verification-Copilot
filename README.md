# AI Verification Copilot

AI Verification Copilot is a production-style internal fraud triage and decisioning system designed to simulate the type of tooling used by identity verification and trust & safety teams to review potentially suspicious verification cases.

The project is being built as a full-stack engineering portfolio piece with a strong focus on backend systems, structured tool execution, agent-based orchestration, human-in-the-loop workflows, auditability, and evaluation discipline. The current implementation includes a working FastAPI backend, PostgreSQL persistence, SQLAlchemy models, Alembic migrations, paginated case APIs, and audit logging. The next phase introduces a deterministic tooling layer for fraud checks before moving into LLM-based orchestration.

Current Status

Project status: Ongoing
Current phase: Tooling Layer (Days 5–9)

Completed so far

Repo setup + local development workflow

Backend foundation

FastAPI API

PostgreSQL persistence

SQLAlchemy ORM models

Alembic migrations

Pydantic request/response schemas

CRUD case workflows

audit logging

pagination

404 handling

latency instrumentation

In progress

Deterministic tool execution layer

Structured tool outputs

Tool result persistence

Preparation for agent orchestration

Why this project exists

Most portfolio AI projects jump straight to model calls. This project takes a more production-oriented approach.

The goal is to build a realistic internal system that:

persists verification cases

runs deterministic risk checks

records audit trails

supports structured AI decisions

enables human review and override

can later be evaluated on synthetic case datasets

Core Features Implemented
Backend API

POST /api/v1/cases — create a verification case

GET /api/v1/cases — list cases with pagination

GET /api/v1/cases/{case_id} — retrieve a case by ID

Stub routes for:

POST /api/v1/cases/{id}/ai-review

POST /api/v1/cases/{id}/human-override

Persistence & Data Modeling

PostgreSQL database running locally in Docker

SQLAlchemy ORM models for:

cases

audit_logs

Alembic migration-based schema management

Reliability & Observability

Structured audit logging for key backend actions

Latency tracking for selected API operations

Pagination for list endpoints

Proper 404 handling for missing cases

OpenAPI / Swagger docs for local testing

Architecture Diagram
Backend Architecture

The current backend is designed using a layered architecture so that each part of the system remains independently understandable, testable, and extensible.

API Layer

FastAPI provides the HTTP interface and automatic OpenAPI documentation.

Schema Layer

Pydantic models define request validation and response serialization.

CRUD Layer

Database access is separated into CRUD functions to keep route handlers thin and maintainable.

Persistence Layer

SQLAlchemy ORM maps Python models to PostgreSQL tables.

Migration Layer

Alembic manages database schema evolution through version-controlled migrations.

Audit Layer

Audit events are written to audit_logs to capture backend actions, metadata, and latency.

Data Model
cases

Represents a verification case under review.

Fields include:

id (UUID)

user_id

email

device_info (JSONB)

document_check_result (JSONB)

behaviour_summary (JSONB)

status (PENDING, REVIEWED, ESCALATED)

created_at

updated_at

audit_logs

Stores backend and workflow events for observability and traceability.

Fields include:

id (UUID)

case_id (nullable)

event_type

actor_type

subject

latency_ms

metadata (JSONB)

created_at

Tech Stack
Backend

Python

FastAPI

Pydantic / pydantic-settings

SQLAlchemy

Alembic

Uvicorn

Database

PostgreSQL

Docker / Docker Compose

Frontend (planned)

Next.js

TypeScript

Tailwind

AI / Orchestration (planned)

LangGraph

OpenAI API

optional Ollama fallback

Local Development
Prerequisites

Python 3.11+

Node.js 18+

Docker Desktop

Git

VS Code recommended

Roadmap
1) Repo setup + dev workflow

 Monorepo structure

 Backend, frontend, and database runnable locally

2) Backend foundation

 FastAPI backend

 PostgreSQL persistence

 SQLAlchemy models

 Alembic migrations

 Audit logging

 Pagination and 404 handling

3) Tooling layer

 Shared tool output schema

 tool_runs persistence model

 Deterministic fraud checks

 Tool registry

 Parallel tool execution

4) Agent orchestration

 LangGraph workflow

 Structured AI review output

 Decision persistence

 Retry on invalid structured output

5) Frontend dashboard

 Case list view

 Case detail view

 Tool outputs

 AI review panel

 Audit timeline

6) Evaluation harness

 Synthetic dataset

 Expected labels

 Decision metrics

 Latency and coverage metrics

7) Production polish

 Full Docker Compose stack

 .env.example

 Logging improvements

 Better developer onboarding

8) Deployment + portfolio packaging

 Hosted backend

 Hosted frontend

 Hosted Postgres

 Demo video

 Evaluation write-up
