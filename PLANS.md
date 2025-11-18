# 1. Product Summary

This project is a **multi-service SaaS platform** for legal teams that:

* Ingests **legal intake interviews / consultations** (audio or text).
* Performs deep **legal-domain analysis** to extract:

  * parties and relationships
  * issues and risks
  * timelines
  * gaps / missing information
  * concrete **Actions** (follow-ups / tasks)
* Uses a single **canonical analysis object** to generate multiple outputs:

  * client-friendly summaries
  * lawyer/internal briefs
  * structured issue/timeline/action views

Architecture-wise, it is:

* **Microservice-based** (target ~18 services over time).
* AI-heavy (LangGraph + LangSmith + Langfuse).
* **Async-first** via Celery (Redis/RabbitMQ) for long-running tasks.
* Built on **Postgres + pgvector** for structured + semantic data.
* Exposed via a **Next.js + React + TypeScript** SaaS app with built-in i18n (English first, more locales later).
* Using **Budibase** as a self-hosted low-code layer for fast internal/admin tools.

---

# 2. Goals & Problems

## 2.1 Problem

Legal interviews are rich but messy. Manually turning them into:

* structured facts and relationships
* clear issues and risks
* prioritized follow-ups

is slow, inconsistent, and hard to audit — especially given **privileged, PII-heavy content**.

## 2.2 Goals

1. **Turn interviews into structured, queryable legal knowledge**

   * Domain models for matters, parties, relationships, issues, timelines, gaps, and **Actions**.
   * Semantic search with **pgvector** inside Postgres.

2. **Generate multiple outputs from one analysis**

   * One `MatterAnalysis` → client summary, lawyer brief, internal report, etc.

3. **Make AI behavior observable & testable**

   * LangGraph for explicit workflows.
   * LangSmith + Langfuse for tracing/evals and LLM observability.

4. **Handle sensitive legal data safely**

   * PII detection & anonymization via **Microsoft Presidio**.
   * Security scanning and secret detection in CI.

5. **Scale as a multi-tenant SaaS**

   * Microservices with clear domains, async workloads via Celery.

---

# 3. High-Level System Overview

## 3.1 Core Flows

1. **Ingest**

   * Audio or text in → `speech-service`.
   * Audio is sent to **Azure Speech** batch transcribe + diarize, orchestrated via Celery.
   * Normalized into a canonical `Transcript` model (speaker turns, timestamps, matter IDs).

2. **Analyze**

   * `analysis-service` runs an **Analyze LangGraph**:

     * entity & party extraction
     * issue & risk identification
     * relationship graph (adjacency lists)
     * timeline reconstruction
     * gap detection
     * Actions derivation
   * Persists `MatterAnalysis` + embeddings (Postgres + pgvector).

3. **Compose**

   * `compose-service` runs a **Compose LangGraph**:

     * Input: `MatterAnalysis` + audience profile(s)
     * Generates:

       * client-friendly summary
       * lawyer/internal brief
       * internal issues+Actions views
   * All outputs link back to the same analysis.

4. **Delivery & Review**

   * Exposed via:

     * **Next.js + React + TS** SaaS UI.
     * Internal **Streamlit** dashboards.
     * **Budibase** internal apps for admin & ops.

5. **Background Work**

   * Celery workers (`worker-service`) handle:

     * speech batch orchestration
     * heavy Analyze/Compose runs
     * bulk exports
     * PII sweeps, eval jobs, maintenance tasks

6. **Evaluation & Observability**

   * LangSmith: datasets, traces, evals, CI integration.
   * Langfuse: LLM traces, metrics, costs, feedback, built on OTEL.

---

# 4. Tech Stack Overview (recap)

## 4.1 Backend

* **Python 3.x + FastAPI**
* **Pydantic v2** for domain & API models.
* **SQLAlchemy + Alembic** for ORM + migrations.
* **Postgres + pgvector** for relational + semantic search.
* **Celery** with Redis (initially) as broker/result backend.
* **LangGraph + LangSmith + Langfuse** for AI workflow orchestration & observability.
* **Presidio** for PII detection/anonymization.

## 4.2 Frontend & i18n

* **Next.js + React + TypeScript** (strict).
* **Next.js i18n routing** configured with `locales: ['en']`, `defaultLocale: 'en'` to be ready for multiple locales later.
* **next-intl** for translations and locale-aware formatting (messages, dates, numbers).
* Initial release: English-only, but all user-facing text goes through the i18n layer.

## 4.3 Admin & Internal Tools

* **Budibase** (self-hosted) as initial internal/admin GUI:

  * Connects to Postgres and REST APIs.
  * Auto-generates CRUD UIs & workflows for internal tools.

## 4.4 Observability & Security

* **structlog** for structured logging.

* **OpenTelemetry** for traces & metrics, exported to:

  * **Prometheus + Grafana** for infra metrics.
  * Langfuse / LangSmith for LLM-level traces.

* **Security tools** in CI:

  * **Bandit** (Python static security analysis).
  * **Safety** (Python dependency vulnerability scanner).
  * **Gitleaks** (secret detection in git history).

* **Auth & identity:** Keycloak stub; full OIDC/JWT integration planned.

## 4.5 Dev tooling recap

* **uv** for Python env & dependency management.
* **doit** for task automation.
* **Commitizen** (+ AI plugin) for conventional commits.
* **semantic-release** for automatic versioning & changelogs.

---

# 5. Monorepo Structure (high level)

Very briefly:

* `services/` – each microservice (FastAPI/Celery/Streamlit/etc.).
* `libs/` – shared Python + TS packages (domain models, db-core, logging-core, ai-core, celery-core, api-types, ui-components).
* `frontend/` – Next.js web app and future admin console.
* `infra/` – Helm charts, K8s templates.
* `ops/` – Docker Compose, Prometheus, Grafana, OTEL collector.
* `configs/` – shared lint/type/security configs.
* `tooling/` – doit tasks, semantic-release config, pre-commit config.
* `docs/` – PRD/TDD, architecture, runbooks.

---

# 6. Engineering Quality & Coding Standards

This is the part you were missing — all the **coding, linting, type-checking, testing, hooks, and CI rules** that keep the whole thing healthy.

## 6.1 Python: linting, formatting, static analysis

### Linting & formatting

* **Ruff** as the *primary linter*:

  * Extremely fast Python linter and code formatter, written in Rust.
  * Configured to:

    * enforce PEP8-style conventions,
    * run rules equivalent to flake8, isort, pyupgrade, black, etc. where useful.

* **Pylint** as a *secondary static analysis pass*:

  * Pylint is a static code analyser that enforces coding standards and checks for code smells and potential errors without running code.
  * We configure it to focus on:

    * potential bugs (unused variables, redefinitions, etc.),
    * design smells (too complex functions, large classes),
    * naming conventions and docstring presence where needed.

**Policy:**

* Ruff + Pylint must all pass locally (`pre-commit`) and in CI.
* No manual style arguments in code review — “let the tools fight it out.”

### Static typing (Python)

We intentionally use **two static type checkers**:

* **Mypy**
* **Pyright**

Both are static type checkers that verify code against type annotations and catch type-related issues.

* **Mypy**:

  * Canonical Python type checker, integrated into many projects.
  * Configured in *strict* mode for core libraries and services.

* **Pyright**:

  * Microsoft’s high-performance static type checker, designed for large codebases and modern Python features.
  * Also configured in **strict** mode for main packages.

Running both provides redundancy and catches slightly different classes of issues.

**Typing rules:**

* All non-trivial functions, methods, and public APIs **must** be fully typed.
* `Any` is only allowed behind explicit `# type: ignore` or config-based exceptions.
* New modules must pass `mypy --strict` and `pyright --level strict` (or equivalent).

## 6.2 TypeScript & frontend standards

* **TypeScript strict mode**:

  * `strict: true`, `noImplicitAny`, `strictNullChecks`, `exactOptionalPropertyTypes`, etc.
* **ESLint** (Next.js/TS config) and **Prettier**:

  * ESLint for correctness & best practices.
  * Prettier for consistent formatting.
* **Type-check only build**:

  * `tsc --noEmit` is run in CI to ensure types stay sound.

## 6.3 Testing stack

### Python tests

* **pytest** as the primary test runner.
* **coverage.py / pytest-cov** to collect coverage:

  * Enforced coverage threshold (e.g. 80–90%) for critical packages.
* **Hypothesis** for property-based tests:

  * Hypothesis generates randomized inputs to test properties of your code and finds minimal failing examples, ideal for catching edge cases.
  * Used for critical core logic:

    * timeline ordering
    * relationship graph invariants
    * certain PII detection/normalization properties
* **pytest-asyncio** (or equivalent) for async FastAPI & LangGraph node tests.
* **pytest-xdist** for parallel test execution (optional, but recommended as the test suite grows).

### Frontend tests

* **Unit/component:** Jest or Vitest + React Testing Library.
* **E2E/functional:** **Playwright**:

  * Playwright is an open-source end-to-end testing framework for modern web apps that supports Chromium, WebKit, and Firefox across platforms.
  * We use **Playwright Test**, which bundles the runner, assertions, parallelization, HTML reports, and debugging tooling.
  * Key flows covered:

    * sign-in & tenant switch
    * upload transcript → see analysis results
    * run compose → view multiple audience outputs
    * basic admin flows surfaced through Budibase or Next.js

Playwright is configured to run headless on CI with a minimal but representative browser matrix (Chromium-only initially, expand as needed).

### LLM-specific evals

* **LangSmith evals**:

  * dataset-based eval suites (golden transcripts → expected structured outputs).
  * run regularly in CI and as part of release pipelines.

* **Langfuse feedback**:

  * production feedback, scores, and error flags feed back into datasets and dashboards.

## 6.4 Pre-commit hooks & Git hygiene

We use **pre-commit** as the hook manager:

* pre-commit is a framework for managing multi-language git hooks that run before every commit.

**Hooks include (non-exhaustive):**

* `ruff check` (lint + format)
* `pylint` (selected rulesets)
* `mypy` and/or `pyright` (fast mode) for changed files
* `pytest --maxfail=1 --quick` (optional smoke tests)
* `eslint` + `prettier --check` for TS/JS
* `gitleaks` (pre-commit or pre-push)
* `bandit` (optionally as a nightly/CI job instead of per-commit)

**Commit process:**

* Commits must pass all pre-commit hooks.
* **Commitizen** (with AI plugin) enforces conventional commits and helps authors write structured messages.

## 6.5 CI/CD gates

On each PR:

1. **Python lint & format**

   * Ruff, Pylint.
2. **Python type-check**

   * Mypy (`--strict` for critical libs/services).
   * Pyright (`typeCheckingMode = "strict"`).
3. **Python tests**

   * pytest + coverage.
   * Hypothesis tests included (in non-flaky configs).
4. **TS/Frontend quality**

   * ESLint, Prettier, `tsc --noEmit`.
   * Unit/component tests.
5. **E2E**

   * Playwright test suite (subset for PRs, full for main-branch or nightly).
6. **Security & secrets**

   * Bandit, Safety, and Gitleaks as CI jobs (some per-PR, some scheduled).

On **main / release branches**:

* All of the above **plus**:

  * LangSmith eval runs on key datasets.
  * Build & push Docker images.
  * Helm chart packaging.
  * semantic-release to bump versions & publish changelog.

## 6.6 Coding conventions & review

* **Python**

  * PEP8 via Ruff(Black); docstrings for public APIs.
  * Strong typing throughout; `Any` is discouraged.
* **TS**

  * Type-first mindset: hooks, components, and API calls are fully typed.
* **Reviews**

  * At least one senior reviewer for core-domain or cross-cutting changes.
  * No direct pushes to main; branch protection enforces green CI and review approval.

---

# 7. How This Helps the Project “Start and Stay Good”

With all of the above in place:

* New code can’t land without:

  * passing **static analysis** (Ruff, Pylint, Bandit),
  * **type checks** (Mypy, Pyright, TypeScript strict),
  * **tests** (pytest + coverage, Hypothesis where it matters, frontend unit tests, and Playwright E2E on main paths),
  * and **security/secret checks** (Safety, Gitleaks).
* Style debates are offloaded to tools; humans focus on architecture and domain correctness.
* Strong typing + property-based testing make it much harder for subtle regressions in your LangGraph workflows and domain logic to sneak in.
* The same standards apply across services, shared libs, and frontends — enforced by pre-commit and CI from day one.

If you’d like, I can now turn **section 6** into an explicit “Engineering Quality Requirements” block with numbered requirements (MUST/SHOULD) that you can paste *verbatim* into your TDD.
