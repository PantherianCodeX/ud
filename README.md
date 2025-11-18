# uDocket Legal AI Platform

> **AI-native, observability-first legal interview analysis platform**  
> Transcribe → Analyze → Compose — from one canonical legal analysis, for multiple audiences.

---

## 🔎 Overview

uDocket is a multi-service SaaS platform for legal teams. It ingests **legal intake interviews / consultations** (audio or text), performs deep **legal-domain analysis**, and produces multiple **audience-specific outputs** from a single structured analysis:

- **Structured knowledge graph** of the consultation:
  - Matters, parties, relationships
  - Legal issues & risks
  - Timelines & events
  - Gaps / missing information
  - Concrete **Actions** (follow-ups & tasks)
- **Parallel outputs** from the same analysis:
  - Client-friendly summary  
  - Lawyer / internal brief  
  - Internal issues + Actions view  

The system is:

- **Microservice-based** (target ≈18 services)
- **AI-heavy & type-safe** (LangGraph + Pydantic v2)
- **Observability-first** (LangSmith, Langfuse, OpenTelemetry)
- **Strictly linted, typed & tested** across Python and TypeScript

---

## ✨ Key Features

- **Interview → Insight pipeline**
  - Ingest audio or transcript
  - Batch transcription + diarization via external speech services (Azure first target)
  - Canonical `Transcript` and `MatterAnalysis` domain models

- **3 AI graphs (LangGraph)**
  - **Transcribe graph** – orchestrates external batch transcription + diarization
  - **Analyze graph** – builds structured `MatterAnalysis` (issues, relationships, timeline, gaps, Actions)
  - **Compose graph** – generates multiple documents (client, lawyer, internal) from the same analysis

- **Legal-ready data model**
  - Matters, parties, roles
  - Issues & risk flags
  - Relationship graph (adjacency lists)
  - Timeline events
  - Gaps & Actions

- **Strong observability & evals**
  - LangGraph + **LangSmith** for LLM tracing and evaluation
  - **Langfuse** as open-source LLM observability (traces, metrics, costs) built on OpenTelemetry
  - System metrics via Prometheus + Grafana

- **Production-grade foundations**
  - Postgres + **pgvector** for combined relational & vector search
  - Celery for async & scheduled work
  - Kubernetes + Helm for deployment
  - **Budibase** for rapid internal/admin tools

---

## 🏗️ High-Level Architecture

**Core flow:**

1. **Ingest**
   - User uploads audio or provides a transcript
   - `speech-service`:
     - For audio: submits batch transcription + diarization jobs to external provider(s)
     - Uses Celery workers to poll & ingest results
   - Stores canonical `Transcript` in Postgres

2. **Analyze**
   - `analysis-service` runs the **Analyze LangGraph**:
     - Entity & party extraction
     - Issue & risk detection
     - Relationship graph (adjacency lists)
     - Timeline reconstruction
     - Gaps & Actions derivation
   - Persists `MatterAnalysis` + embeddings (pgvector)

3. **Compose**
   - `compose-service` runs the **Compose LangGraph**:
     - Inputs: `MatterAnalysis` + audience profile(s)
     - Outputs: client summary, lawyer brief, internal issues+Actions report

4. **Deliver & review**
   - **Next.js + React + TypeScript** SaaS UI
   - Streamlit dashboards for internal analytics/ops
   - Budibase-built internal tools for admin & ops

5. **Observe & evaluate**
   - LangGraph graphs instrumented with:
     - **LangSmith** for tracing/evals
     - **Langfuse** for LLM observability
   - System telemetry via OpenTelemetry → OTEL Collector → Prometheus/Grafana

---

## 🧰 Tech Stack

### Backend (Python)

- **Language / Framework**
  - Python 3.x
  - FastAPI (ASGI, async, OpenAPI)

- **Domain & data**
  - Pydantic v2 for domain and API models
  - SQLAlchemy + Alembic for ORM & migrations
  - PostgreSQL for relational data
  - **pgvector** for vector similarity search inside Postgres

- **AI orchestration & observability**
  - **LangGraph** for durable, graph-based AI workflows
  - **LangSmith** for tracing, debugging, and evaluating LLM apps
  - **Langfuse** for open-source LLM engineering & observability (traces, evals, metrics)

- **Async & background**
  - Celery for distributed task queue (speech jobs, heavy analysis, bulk compose, maintenance)

- **Config, logging, PII**
  - pydantic-settings for typed configuration
  - structlog for structured logging
  - Microsoft Presidio for PII detection & anonymization

### Frontend (TypeScript)

- **Main app**
  - Next.js + React + TypeScript (strict)
  - `next-intl` for i18n: translations, date/number formatting, and i18n routing for Next.js

- **Testing**
  - Jest/Vitest + React Testing Library for unit/component tests
  - **Playwright** for E2E tests (cross-browser, cross-platform)

### Admin / Internal tools

- **Budibase** self-hosted for internal/admin apps & CRUD dashboards over Postgres + APIs

### Observability & Infra

- OpenTelemetry for traces & metrics
- Prometheus + Grafana for system metrics and dashboards
- OTEL Collector for routing telemetry
- Docker (multi-stage, BuildKit) for containers
- Kubernetes + Helm for deployments

### Dev Tooling

- **uv** – extremely fast Python package & project manager, written in Rust
- doit – task automation
- Commitizen (+ AI plugin) – conventional commits
- semantic-release – automated versioning & changelogs

---

## 🧱 Repository Structure (high-level)

> Vertical layout. To be determined.
