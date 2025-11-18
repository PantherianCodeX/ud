# Legal Intake Intelligence Architecture

## Overview

This architecture captures the multi-service SaaS from `PLANS.md`: legal intake interviews (audio/text) are turned into a canonical `MatterAnalysis`, from which client summaries, lawyer briefs, and actionable timelines are generated. AI orchestration (LangGraph + LangSmith/Langfuse), async Celery workers, Postgres+pgvector, and a Next.js/Budibase surface keep the flows observable, testable, and secure.

## Goals & Problems (adapted from PLANS.md)

1. Turn messy interviews into canonical, queryable legal knowledge (matters, parties, relationships, issues, timelines, gaps, actions).
2. Generate multiple, audience-specific outputs from the same `MatterAnalysis`.
3. Make AI behavior observable and testable via LangGraph workflows, LangSmith evals, and Langfuse traces.
4. Protect PII-heavy data with Presidio, structlog, OpenTelemetry, and CI/ops security scanning.
5. Scale as a multi-tenant, async-first SaaS with clear architectural boundaries.

## Tech Stack

- **Backend**: Python 3.x + FastAPI, Pydantic v2, SQLAlchemy/Alembic, Postgres + pgvector, Celery + RabbitMQ, LangGraph + LangSmith + Langfuse, Microsoft Presidio.
- **Frontend & i18n**: Next.js + React + TypeScript (strict), `next-intl` for translation/localization, Jest/Vitest + React Testing Library.
- **Admin/Internal tools**: Budibase (self-hosted) with Postgres/REST, Streamlit or Next.js dashboards when Budibase is insufficient.
- **Observability & Security**: structlog for logs, OpenTelemetry → Prometheus/Grafana + Langfuse/LangSmith, Bandit, Safety, Gitleaks, Keycloak stub (OIDC/JWT planned).
- **Dev Tooling**: `uv` for envs/deps, `doit` automation, Commitizen (+AI plugin), semantic-release.

## Monorepo Structure

Each **app** owns its vertical slices (intake, analysis, compose, platform, etc.), shared logic lives in `packages/` (called `libs/` in PLANS), and supporting directories (`infra`, `ops`, `configs`, `tooling`, `docs`, `tests`, `typings`) stay predictable. The repo no longer has a `features/` directory—slices appear directly under each app’s natural subfolders (e.g., `workflow/intake`, `workflow/analysis`), so avoid referencing an obsolete `features/` tree.

### Top-level view

```text
.
├─ apps/
│   ├─ api/             # FastAPI + Celery entrypoints (replaces PLANS/`services/api`)
│   ├─ worker/          # Celery workers, async orchestrators (PLANS/`services/worker`)
│   ├─ web/             # Next.js SaaS experience (PLANS/`frontend`)
│   ├─ admin/           # Budibase / Streamlit / Next.js admin tooling (PLANS/internal tools)
│   └─ mobile/          # (future) Expo/React Native client
│
├─ packages/             # Shared libraries (see PLANS/`libs`)
│   ├─ py-domain/        # Canonical Matter, Party, Issue, Timeline, Action, MatterAnalysis models
│   ├─ py-ai-core/       # LangGraph helpers, LangSmith/Langfuse instrumentation, provider registry
│   ├─ py-worker-core/   # Celery factories, idempotency helpers, audit hooks
│   ├─ ts-api-types/     # Shared OpenAPI/SDK types for Next.js + future mobile
│   ├─ ts-ui-kit/        # Reusable UI primitives (layout, typography, modals)
│   └─ ts-utils/         # Tiny helpers (fetch wrappers, date math)
│
├─ infra/                # Helm charts, Kubernetes manifests, Terraform stubs
├─ ops/                  # Docker Compose stacks, Prometheus/Grafana + OTEL dashboards, collectors
├─ configs/              # Lint/type/security configs referenced in PLANS (Ruff, Pylint, Mypy, ESLint, Prettier, Bandit, Safety)
├─ tooling/              # `doit` recipes, semantic-release, pre-commit config
├─ docs/                 # PRDs, TDDs, architecture, runbooks, runmetrics
├─ tests/                # Shared e2e helpers + spec suites
└─ typings/              # Third-party stubs (Portkey, OPA client, etc.)
```

### Bounded contexts and slices

1. **Core Workflow** – `intake`, `analysis`, `compose`, `matters`. Every stage owns its API, LangGraph service, domain models, repository, and tests so the canonical analysis remains consistent as new outputs emerge.
2. **Delivery & Review** – Next.js + Budibase screens that guide reviewers through a matter’s analysis, summaries, and action timelines.
3. **Background & Async Work** – Celery workers orchestrate Azure Speech ingestion, heavy LangGraph runs, LangSmith evals, Presidio sweeps, and maintenance tasks (embeddings refresh, exports).
4. **Observability & Platform** – LangSmith + Langfuse traces, OpenTelemetry spans, structlog logs, and Keycloak/JWT identity guard the microservices.

Slices only become top-level directories when they own APIs, domain logic, data models, and UI surfaces; helper utilities stay in existing slices or shared packages to prevent bloat.

### Backend structure (copied + adapted from template)

```text
apps/api/
  src/
    core/
      config.py
      db.py
      security.py
      tracing.py
      mailer.py          # Email client for review notifications

    workflow/
      intake/
        api.py            # POST /intakes, upload files, start ingestion
        service.py        # Azure Speech orchestration, Celery enqueue
        models.py         # Intake, Transcript, speaker turns, matter IDs
        repository.py
        tests/

      analysis/
        api.py            # POST /matters/{id}/analyze
        graph.py          # Analyze LangGraph definition (entities, issues, timeline)
        service.py        # LangSmith + Langfuse integration
        models.py         # MatterAnalysis, parties, relationships, gaps, actions
        repository.py
        tests/

      compose/
        api.py            # POST /matters/{id}/compose
        graph.py          # Compose LangGraph (audience-aware summaries + actions)
        service.py
        tests/

      matters/
        api.py            # Matter CRUD + lifecycle events
        service.py
        models.py
        tests/

    ai/
      graphs/
      evaluations/       # LangSmith dataset runners and build scripts referenced in PLANS

    platform/
      auth/              # Keycloak stub today, JWT/OIDC roadmap
      tenants/           # Feature flags, org defaults, access bounds

    observability/
      langsmith.py
      langfuse.py
      otel.py
      presidio.py

  tests/
    integration/
      IntakePage.test.tsx
      MatterDetailPage.test.tsx
```

Mobile apps repeat only the slices they need while reusing shared typings (`ts-api-types`) and UI primitives (`ts-ui-kit`).

### Worker & background tree

```text
apps/worker/
  celery/
    tasks/
      speech/
      analysis/
      compose/
    queues/
      ingest/
      analyze/
      compose/
    maintenance/
      embeddings_refresh/
      bulk_export/
      presidio_sweep/
    tests/
```

### Intake naming note

To keep the intake pipeline terminology aligned with analyze/compose, treat the entire Celery flow as part of the `intake` slice:

- Rename `speech` task modules to `apps/worker/celery/tasks/intake/transcribe.py` (or similar) and ensure APIs live under `workflow/intake`.
- Keep the associated queue in `apps/worker/celery/queues/intake/` so all references (`intake` slice, Celery task, and queue) share the same name.
- Any helper services, DTOs, or tests live alongside `workflow/intake` (e.g., `apps/api/src/workflow/intake`, `apps/web/src/workflow/intake`).

This keeps ingest/transcription responsibilities consistent with the rest of the pipeline and avoids the loose terminology currently in use.

### Frontend tree (per template notes)

```text
apps/web/
  src/
    app/
      intake/
        page.tsx              # /intake
      matters/
        [matterId]/
          page.tsx            # /matters/:id
      settings/
        page.tsx              # /settings
      admin/
        page.tsx              # internal dashboards
      chat/
        page.tsx              # conversational review
      notifications/
        page.tsx              # audit/inbox view

    shared/
      ui/                     # ts-ui-kit primitives
      lib/                    # shared helpers
      config/
        env.ts
        routes.ts
        i18n.ts

    workflow/
      intake/
        components/
          IntakeForm.tsx
          IntakeUpload.tsx
        api/
          useCreateIntake.ts
          useIntakeStatus.ts
        tests/

      analysis/
        components/
          AnalysisTimeline.tsx
          IssuesPanel.tsx
        api/
          useAnalysis.ts
          useRunAnalysis.ts
        tests/

      compose/
        components/
          ClientSummaryCard.tsx
          ActionPlanView.tsx
        api/
          useCompose.ts
        tests/

      matters/
        components/
          MattersList.tsx
          MatterDetail.tsx
        api/
          useMatters.ts
        tests/

    governance/
      reference_data/
        components/
          EvidenceTable.tsx
        api/
          useReferenceData.ts
        tests/

    ai/
      registry/
        components/
          ProviderList.tsx
          ModelConfigForm.tsx
        api/
          useProviders.ts
          useModels.ts
        tests/

    platform/
      settings/
        components/
          OrgSettingsForm.tsx
          UserSettingsForm.tsx
        api/
          useOrgSettings.ts
          useUserSettings.ts
        tests/

    engagement/
      notifications/
        components/
          NotificationList.tsx
        api/
          useNotifications.ts
        tests/
  tests/integration/
```

### Testing & typings (from template section 6 and PLANS)

```text
tests/
  e2e/
    playwright.config.ts
    helpers/
      auth.ts
      seed.ts
    specs/
      intake_to_analysis.e2e.spec.ts
      analysis_to_compose.e2e.spec.ts
      compose_review.e2e.spec.ts
typings/
  third_party/
    portkey/
      __init__.pyi
      client.pyi
    opa_client/
      __init__.pyi
```

Tests and type stubs stay close to the code they validate to make reasoning predictable.

## Engineering Quality & Coding Standards (from PLANS.md section 6)

### Python

- **Lint & formatting**: Ruff as primary linter/formatter; Pylint for complexity/naming/docstring checks.  
- **Typing**: Mypy + Pyright in strict mode; `Any` only via config exceptions.  
- **Tests**: pytest + coverage (80–90% threshold), Hypothesis for timeline/graph invariants, pytest-asyncio for async LangGraph/Celery flows, pytest-xdist optionally for parallel runs.

### TypeScript / Frontend

- TypeScript `strict: true`, `noImplicitAny`, `strictNullChecks`, `exactOptionalPropertyTypes`.  
- ESLint + Prettier for lint/format; `tsc --noEmit` in CI.  
- Unit/component tests with Jest/Vitest + React Testing Library.  
- Playwright end-to-end suite covers sign-in/tenant switch, ingest → analysis → compose, admin flows; main/nightly runs full matrix.

### LLM-specific & Security

- LangSmith evals (datasets of transcripts → expected outputs) run in CI and release gates.  
- Langfuse feedback traces log production costs, scores, and manual flags.  
- Security scans: Bandit, Safety, Gitleaks (`configs/` holds their rules).  
- Presidio detects/anonymizes PII before persistence or UI exposure; Keycloak stub (with JWT/OIDC planned) protects endpoints.

### Git hygiene & CI/CD

- Pre-commit hooks: Ruff, Pylint, Mypy/Pyright (changed files), optional `pytest --maxfail=1`, ESLint + Prettier, Gitleaks, nightly Bandit.  
- Commitizen (+AI plugin) enforces conventional commits for compatibility with semantic-release.  
- CI gates (per PLANS.md 6.5):
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

- **New intake sources** (audio vendors, document uploads) extend `apps/api/src/workflow/intake`, Celery ingestion queues, and the corresponding Next.js pages and components under `apps/web/src/workflow/intake`.
- **Additional analysis artifacts** (timelines, gap detection, relationship graphs) live in `workflow/analysis` and the matching Next.js components/page slices, with LangGraph graphs and LangSmith evals to match.
- **More compose outputs** (e.g., action plans, internal briefs) grow `workflow/compose`, Celery runners, and the Web compose views while reusing the canonical `MatterAnalysis`.
- **Scheduled evaluations or maintenance** spawn new Celery tasks in `apps/worker/celery` (LangSmith evals, Presidio sweeps, embeddings refresh) plus integration tests.

## Summary

This document keeps the tech stack, and quality practices aligned with the vertical-monorepo template, so every new slice, app, and test map clearly to a predictable tree and to the existing rules. Please update `apps/`, `packages/`, `configs/`, and `tests/` accordingly as the product grows.
