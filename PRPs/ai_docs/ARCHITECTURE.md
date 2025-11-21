# uDocket Architecture

## Overview

This architecture captures the multi-service uDocket SaaS: legal intake interviews (audio/text) are turned into a canonical `MatterAnalysis`, from which client summaries, lawyer briefs, and actionable timelines are generated. AI orchestration (LangGraph + LangSmith/Langfuse), async Celery workers, Postgres+pgvector, and a Next.js/Budibase surface keep the flows observable, testable, and secure.

## Goals & Problems

1. Turn messy interviews into canonical, queryable legal knowledge (matters, parties, relationships, issues, timelines, gaps, actions).
2. Generate multiple, audience-specific outputs from the same `MatterAnalysis`.
3. Make AI behavior observable and testable via LangGraph workflows, LangSmith evals, and Langfuse traces.
4. Protect PII-heavy data with Presidio, structlog, OpenTelemetry, and CI/ops security scanning.
5. Scale as a multi-tenant, async-first SaaS with clear architectural boundaries.

## Tech Stack

- **Backend**: Python 3.12 + FastAPI, Pydantic v2, SQLAlchemy/Alembic, Postgres + pgvector, Celery + RabbitMQ, LangGraph + LangSmith + Langfuse, Microsoft Presidio.
- **Frontend & i18n**: Next.js + React + TypeScript (strict), `next-intl` for translation/localization, Jest/Vitest + React Testing Library.
- **Admin/Internal tools**: Budibase (self-hosted) with Postgres/REST, Streamlit or Next.js dashboards when Budibase is insufficient.
- **Observability & Security**: structlog for logs, OpenTelemetry → Prometheus/Grafana + Langfuse/LangSmith, Bandit, Safety, Gitleaks, Keycloak stub (OIDC/JWT planned).
- **Dev Tooling**: `uv` for envs/deps, `doit` automation, Commitizen (+AI plugin), semantic-release.

## Monorepo Structure

- Each **app** owns its vertical slices (intake, analysis, compose, platform, etc.).
- Shared logic lives in `packages/`.
- Supporting directories stay predictable (`infra`, `ops`, `configs`, `tooling`, `docs`, `tests`, `typings`).
- Slices appear directly under each app’s natural feature group (e.g., `workflow/intake`, `workflow/analysis`).

### Top-level view

```text
.
├─ apps/
│   ├─ api/             # FastAPI + Celery entrypoints
│   ├─ worker/          # Celery workers, async orchestrators
│   ├─ web/             # Next.js SaaS experience
│   ├─ admin/           # Budibase / Streamlit / Next.js admin tooling
│   └─ mobile/          # (future) Expo/React Native client
│
├─ packages/             # Shared libraries
│   ├─ udocket-domain/        # Canonical Matter, Party, Issue, Timeline, Action, MatterAnalysis models
│   ├─ udocket-ai-core/       # LangGraph helpers, LangSmith/Langfuse instrumentation, provider registry
│   ├─ udocket-celery-core/   # Celery factories, idempotency helpers, audit hooks
│   ├─ udocket_api_types/     # Shared OpenAPI/SDK types for Next.js + future mobile
│   ├─ udocket_ui_kit/        # Reusable UI primitives (layout, typography, modals)
│   └─ udocket_utils/         # Tiny helpers (fetch wrappers, date math)
│
├─ infra/                # Helm charts, Kubernetes manifests, Terraform stubs
├─ ops/                  # Docker Compose stacks, Prometheus/Grafana + OTEL dashboards, collectors
├─ configs/              # Lint/type/security configs (Ruff, Pylint, Mypy, ESLint, Prettier, Bandit, Safety)
├─ tooling/              # `doit` recipes, semantic-release, pre-commit config
├─ docs/                 # PRDs, TDDs, architecture, runbooks, runmetrics
├─ tests/                # Shared e2e helpers + spec suites
└─ typings/              # Third-party stubs
```

### Bounded contexts and slices

1. **Core Workflow** – `intake`, `analysis`, `compose`, `matters`. Every stage owns its API, LangGraph service, domain models, repository, and tests so the canonical analysis remains consistent as new outputs emerge.
2. **Delivery & Review** – Next.js + Budibase screens that guide reviewers through a matter’s analysis, summaries, and action timelines.
3. **Background & Async Work** – Celery workers orchestrate Azure Speech intakeion, heavy LangGraph runs, LangSmith evals, Presidio sweeps, and maintenance tasks (embeddings refresh, exports).
4. **Observability & Platform** – LangSmith + Langfuse traces, OpenTelemetry spans, structlog logs, and Keycloak/JWT identity guard the microservices.

Slices only become top-level directories when they own APIs, domain logic, data models, and UI surfaces; helper utilities stay in existing slices or shared packages to prevent bloat.

### Backend structure (copied + adapted from template)

```text
apps/api/
  src/
    core/
    workflow/
      intake/
        tests/
      analysis/
        tests/
      compose/
        tests/
      matters/
        tests/
    ai/
      graphs/
      evaluations/       # LangSmith dataset runners and build scripts
    platform/
      auth/              # Keycloak stub today, JWT/OIDC roadmap
      tenants/           # Feature flags, org defaults, access bounds
    observability/

  tests/
    integration/
```

Mobile apps repeat only the slices they need while reusing shared typings (`udocket_api_types`) and UI primitives (`udocket_ui_kit`).

### Worker & background tree

```text
apps/worker/
  celery/
    tasks/
      speech/
      analysis/
      compose/
    queues/
      intake/
      analyze/
      compose/
    maintenance/
      embeddings_refresh/
      bulk_export/
      presidio_sweep/
    tests/
```

### Frontend tree

```text
apps/web/
  src/
    app/
      intake/
      matters/
        [matterId]/
      settings/
      admin/
      chat/
      notifications/
    shared/
      ui/                     # udocket_ui_kit primitives
      lib/                    # shared helpers
      config/
    workflow/
      intake/
        components/
        api/
        tests/
      analysis/
        components/
        api/
        tests/
      compose/
        components/
        api/
        tests/
      matters/
        components/
        api/
        tests/
    governance/
      reference_data/
        components/
        api/
        tests/
    ai/
      registry/
        components/
        api/
        tests/
    platform/
      settings/
        components/
        api/
        tests/
    engagement/
      notifications/
        components/
        api/
        tests/
  tests/integration/
```

### Testing & typings

```text
tests/
  e2e/
    helpers/
    specs/
typings/
  third_party/
```

Tests and type stubs stay close to the code they validate to make reasoning predictable.

## Engineering Quality & Coding Standards

### Python

- **Lint & formatting**: Ruff as primary linter/formatter; Pylint for complexity/naming/docstring checks.  
- **Typing**: Mypy + Pyright in strict mode; `Any` only via config exceptions.  
- **Tests**: pytest + coverage (80–90% threshold), Hypothesis for timeline/graph invariants, pytest-asyncio for async LangGraph/Celery flows, pytest-xdist optionally for parallel runs.

### TypeScript / Frontend

- TypeScript `strict: true`, `noImplicitAny`, `strictNullChecks`, `exactOptionalPropertyTypes`.  
- ESLint + Prettier for lint/format; `tsc --noEmit` in CI.  
- Unit/component tests with Jest/Vitest + React Testing Library.  
- Playwright end-to-end suite covers sign-in/tenant switch, intake → analysis → compose, admin flows; main/nightly runs full matrix.

### LLM-specific & Security

- LangSmith evals (datasets of transcripts → expected outputs) run in CI and release gates.  
- Langfuse feedback traces log production costs, scores, and manual flags.  
- Security scans: Bandit, Safety, Gitleaks (`configs/` holds their rules).  
- Presidio detects/anonymizes PII before persistence or UI exposure; Keycloak stub (with JWT/OIDC planned) protects endpoints.

### Git hygiene & CI/CD

- Pre-commit hooks: Ruff, Pylint, Mypy/Pyright (changed files), optional `pytest --maxfail=1`, ESLint + Prettier, Gitleaks, nightly Bandit.  
- Commitizen (+AI plugin) enforces conventional commits for compatibility with semantic-release.  
- CI gates
  1. Python lint & format (Ruff, Pylint)
  2. Python type checks (Mypy strict, Pyright strict)
  3. Python tests + coverage (pytest + Hypothesis)
  4. TS quality (ESLint, Prettier, `tsc --noEmit`, unit tests)
  5. Playwright subset (full suite on main/nightly)
  6. Bandit, Safety, Gitleaks
  7. Main/release branches add LangSmith evals, Docker image builds, Helm packaging, semantic-release

## Avoiding Folder Bloat (template rules)

1. Promote a new top-level slice only when it has API surface, domain logic, and visible UI.  
2. Shared code goes in `packages/` (not scattered `core/` folders).  
3. Tests live beside slices.  
4. Limit directory depth to ~3–4 levels.  
5. Reuse slice names across apps (backend, worker, web, mobile) to keep the mental map consistent.

## Adding New Capabilities

- **New intake sources** (audio vendors, document uploads) extend `apps/api/src/workflow/intake`, Celery intakeion queues, and the corresponding Next.js pages and components under `apps/web/src/workflow/intake`.
- **Additional analysis artifacts** (timelines, gap detection, relationship graphs) live in `workflow/analysis` and the matching Next.js components/page slices, with LangGraph graphs and LangSmith evals to match.
- **More compose outputs** (e.g., action plans, internal briefs) grow `workflow/compose`, Celery runners, and the Web compose views while reusing the canonical `MatterAnalysis`.
- **Scheduled evaluations or maintenance** spawn new Celery tasks in `apps/worker/celery` (LangSmith evals, Presidio sweeps, embeddings refresh) plus integration tests.

## Summary

This document keeps the tech stack, and quality practices aligned with the vertical-monorepo template, so every new slice, app, and test map clearly to a predictable tree and to the existing rules. Please update `apps/`, `packages/`, `configs/`, and `tests/` accordingly as the product grows.
