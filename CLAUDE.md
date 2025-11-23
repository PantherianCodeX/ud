# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

uDocket is an AI-native legal interview analysis platform that transforms legal intake interviews (audio or text) into structured legal knowledge graphs and multiple audience-specific outputs. The system uses a **vertical-slice monorepo architecture** with strict typing, observability-first design, and production-grade quality standards from day one.

**Core Flow**: Intake → Transcribe → Analyze → Compose → Deliver

## Repository Structure

This is a **vertical-slice monorepo** where features are organized by domain, not technical layer:

```text
apps/
  api/          # FastAPI backend with vertical slices
  worker/       # Celery async workers
  web/          # Next.js SaaS frontend
  admin/        # Budibase/Streamlit internal tools
  mobile/       # (future) React Native app

packages/       # Shared libraries
  udocket-domain/        # Canonical domain models (Matter, Party, Issue, Timeline, Action)
  udocket-ai-core/       # LangGraph helpers, LangSmith/Langfuse instrumentation
  udocket-celery-core/   # Celery factories, idempotency helpers
  udocket_api_types/     # Shared TypeScript API types
  udocket_ui_kit/        # Reusable UI primitives
  udocket_utils/         # Shared TypeScript utilities

configs/        # Lint, type-check, and security tool configs
tooling/        # doit tasks, semantic-release, pre-commit
infra/          # Helm charts, K8s manifests, Terraform
ops/            # Docker Compose, Prometheus/Grafana, OTEL collectors
docs/           # PRDs, architecture, runbooks
tests/          # Shared e2e helpers and specs
```

### Key Architectural Principles

1. **Vertical Slices**: Each feature owns its API, domain logic, data models, repository, and tests
2. **Bounded Contexts**: Core workflow slices are `intake`, `analysis`, `compose`, and `matters`
3. **No Layer Cake**: Avoid organizing by technical layer (controllers/, services/, models/)
4. **Promote Sparingly**: Only create top-level slices when they have API surface, domain logic, and UI

## Backend Structure (Python)

The backend follows vertical-slice architecture under `apps/api/src/`:

```text
core/               # Cross-cutting: DB, config, logging, shared utilities
workflow/
  intake/           # Interview ingestion, Azure Speech orchestration
  analysis/         # LangGraph-based legal analysis (entities, issues, timelines)
  compose/          # Multi-audience output generation
  matters/          # Matter domain logic and CRUD
ai/
  graphs/           # LangGraph workflow definitions
  evaluations/      # LangSmith dataset runners
platform/
  auth/             # Keycloak stub, JWT/OIDC (roadmap)
  tenants/          # Multi-tenant boundaries, feature flags
observability/      # Structlog, OpenTelemetry, tracing setup
```

Each workflow slice contains its own `tests/` subdirectory with unit and integration tests.

## Frontend Structure (TypeScript)

Next.js app under `apps/web/src/`:

```text
app/                # Next.js 15 App Router pages
  intake/
  matters/[matterId]/
  settings/
  admin/
workflow/           # Feature slices mirroring backend
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
shared/
  ui/               # Shared components (from udocket_ui_kit)
  lib/              # Client utilities
  config/
```

## Tech Stack

### Backend

- **Python 3.12+** with `uv` for dependency management
- **FastAPI** for async REST APIs
- **Pydantic v2** for domain and API models (strict mode)
- **SQLAlchemy + Alembic** for ORM and migrations
- **Postgres + pgvector** for relational + vector similarity search
- **Celery + RabbitMQ** for async background work
- **LangGraph** for AI workflow orchestration
- **LangSmith + Langfuse** for LLM tracing, evals, and observability
- **Microsoft Presidio** for PII detection/anonymization
- **structlog** for structured logging

### Frontend

- **Next.js 15** with App Router + React + TypeScript (strict)
- **next-intl** for i18n (English first, multi-locale ready)
- **Jest/Vitest** + React Testing Library for unit/component tests
- **Playwright** for E2E tests

### Quality & Security Tools

- **Ruff** (primary linter/formatter)
- **Pylint** (secondary static analysis for complexity/naming)
- **Mypy + Pyright** (both in strict mode for type checking)
- **ESLint + Prettier** (TypeScript linting/formatting)
- **pytest + pytest-cov** (80-90% coverage threshold)
- **Hypothesis** (property-based testing for core invariants)
- **Bandit, Safety, Gitleaks** (security scanning)

### Observability

- **OpenTelemetry** → Prometheus + Grafana
- **LangSmith** for LLM debugging and evaluation
- **Langfuse** for production LLM observability (traces, costs, feedback)

## Common Development Tasks

### Python Environment Setup

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv sync

# Activate environment
source .venv/bin/activate
```

### Task Automation with doit

The repo ships a root-level `dodo.py` so you can replicate CI locally with simple commands:

```bash
# List available tasks
uv run doit list

# Re-run Prettier, Ruff, and Pylint
uv run doit lint

# Strict type checking (mypy + pyright)
uv run doit typecheck

# Run pytest with coverage reports in out/test_reports/...
uv run doit tests

# Apply the full CI-quality gate (lint + typecheck + tests + audit)
uv run doit quality

# Security scans
uv run doit security

# Clean cached artifacts/reports
uv run doit clean_artifacts
```

### Docker and Container Development

```bash
# Start all services with docker-compose
docker-compose up -d

# Start specific services
docker-compose up -d postgres rabbitmq

# View logs
docker-compose logs -f api worker

# Stop all services
docker-compose down

# Rebuild and start services
docker-compose up -d --build
```

### Running Tests

```bash
# Python tests (all - parallel by default via pytest-xdist)
uv run pytest

# Python tests with coverage
uv run pytest --cov=apps --cov=packages --cov-report=term-missing

# Python tests (specific module)
uv run pytest apps/api/src/workflow/analysis/tests/

# Python tests in parallel (explicit)
uv run pytest -n auto

# TypeScript tests (from web app)
cd apps/web
npm test

# E2E tests with Playwright
cd apps/web
npx playwright test

# Run specific E2E test
npx playwright test tests/e2e/intake-flow.spec.ts
```

### Type Checking

```bash
# Python - Mypy (strict mode)
uv run mypy apps/api/src

# Python - Pyright (strict mode)
uv run pyright apps/api/src

# TypeScript - type check only (no emit)
cd apps/web
npx tsc --noEmit
```

### Linting and Formatting

```bash
# Python - Ruff check and fix
uv run ruff check . --fix
uv run ruff format .

# Python - Pylint
uv run pylint apps/ packages/

# TypeScript - ESLint and Prettier
cd apps/web
npm run lint
npm run format
```

### Running the Application

```bash
# Backend API (FastAPI)
cd apps/api
uv run uvicorn src.main:app --reload --port 8000

# Celery worker
cd apps/worker
uv run celery -A celery.app worker --loglevel=info

# Celery worker for specific queue
uv run celery -A celery.app worker --loglevel=info -Q intake,analyze

# Flower (Celery monitoring UI)
uv run celery -A celery.app flower --port=5555

# Frontend (Next.js)
cd apps/web
npm run dev
```

### Database Migrations

```bash
# Create new migration
cd apps/api
uv run alembic revision --autogenerate -m "Description of changes"

# Apply migrations
uv run alembic upgrade head

# Rollback one migration
uv run alembic downgrade -1

# View migration history
uv run alembic history

# View current revision
uv run alembic current
```

### Background Workers

Celery workers are organized by queue under `apps/worker/celery/`:

- `tasks/speech/` - Azure Speech transcription orchestration
- `tasks/analysis/` - Heavy LangGraph analysis runs
- `tasks/compose/` - Bulk output generation
- `maintenance/` - Scheduled jobs (embeddings refresh, PII sweeps)

### Azure Speech Integration

The project integrates with **Azure Cognitive Services Speech API** for batch transcription and diarization:

- **Production**: Real Azure Speech batch transcription and speaker diarization
- **Development**: Mock transcription service (controlled via environment variables)
- **Location**: `apps/api/src/workflow/intake/`
- **Orchestration**: Celery workers poll Azure batch jobs and ingest results

Environment flags control whether to use real Azure Speech or mocked transcription, allowing local development without constant API calls.

### Portkey AI Gateway

**Portkey AI** is used as the production LLM gateway:

- **Purpose**: Unified gateway for routing LLM calls across multiple providers
- **Benefits**:
  - Simplifies switching between models
  - Built-in retry and fallback logic
  - Request/response logging and monitoring
  - Cost tracking across providers
- **Development**: Can route to local models for fast testing
- **Production**: Routes to production LLM APIs with observability

All LLM API calls should go through Portkey endpoints for consistency and observability.

### Pre-commit Hooks

The project uses **pre-commit** to enforce quality checks before commits:

```bash
# Install pre-commit hooks
uv run pre-commit install --config configs/pre-commit-config.yaml

# Run pre-commit on all files
uv run pre-commit run --config configs/pre-commit-config.yaml --all-files

# Run specific hook
uv run pre-commit run --config configs/pre-commit-config.yaml ruff --all-files

# Update hooks to latest versions
uv run pre-commit autoupdate --config configs/pre-commit-config.yaml
```

Pre-commit hooks automatically run:

- Ruff (lint + format)
- Pylint (on changed files)
- Mypy/Pyright (on changed files)
- ESLint + Prettier (TypeScript/JavaScript)
- Gitleaks (secret detection)
- Bandit (security scans, optionally)

### Conventional Commits with Commitizen

Use **Commitizen** for standardized commit messages:

```bash
# Interactive commit (recommended)
uv run cz commit

# Or use the alias
uv run cz c

# Bump version automatically based on commits
uv run cz bump

# Generate changelog
uv run cz changelog
```

Commit types:

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Test additions or changes
- `chore:` - Maintenance tasks
- `perf:` - Performance improvements
- `ci:` - CI/CD changes

### Semantic Release

**semantic-release** automatically handles versioning and changelogs:

- Analyzes commit messages (conventional commits)
- Determines version bump (major/minor/patch)
- Generates changelog
- Creates git tags
- Runs in CI on main/release branches

### Security Scanning

Run security scans manually or let CI handle them:

```bash
# Bandit - Python security static analysis
uv run bandit -r apps/ packages/ -f json -o out/test_reports/security/bandit-report.json

# Safety - Check Python dependencies for known vulnerabilities
uv run safety scan --json --policy-file configs/safety-policy.yml

# Gitleaks - Scan for secrets in git history
uv run gitleaks detect --source . --verbose

# Gitleaks - Scan for secrets in uncommitted changes
uv run gitleaks protect --verbose
```

**Important**: Never commit secrets. Gitleaks will catch them, but prevention is better than remediation.

## Code Quality Standards

### Python

1. **Type Everything**: All functions, methods, and public APIs must be fully typed. `Any` only via explicit `# type: ignore` or config exceptions.

2. **Pass Both Type Checkers**: Code must pass both `mypy --strict` and `pyright --level strict`.

3. **Lint Clean**: Must pass Ruff (primary) and Pylint (complexity/naming/docstrings).

4. **Test Coverage**: Maintain 80-90% coverage on critical packages. Use Hypothesis for property-based testing on:
   - Timeline ordering invariants
   - Relationship graph properties
   - PII detection edge cases

5. **Async Patterns**: Use `pytest-asyncio` for testing async FastAPI endpoints and LangGraph nodes.

### TypeScript

1. **Strict Mode**: All TypeScript uses `strict: true`, `noImplicitAny`, `strictNullChecks`, `exactOptionalPropertyTypes`.

2. **Lint + Format**: ESLint and Prettier must pass. No manual style debates.

3. **Type Everything**: No implicit `any`. All components, hooks, and API calls fully typed.

4. **E2E Coverage**: Critical user flows covered by Playwright tests:
   - Sign-in and tenant switching
   - Upload interview → view analysis
   - Generate outputs → review results
   - Admin operations

### LLM-Specific Quality

1. **LangSmith Evals**: Maintain evaluation datasets with golden transcripts → expected outputs. Run in CI before release.

2. **Langfuse Traces**: All production LLM calls must be traced with Langfuse for cost tracking, error monitoring, and feedback collection.

3. **Instrumentation**: Every LangGraph node should emit OpenTelemetry spans for observability.

### Security

1. **PII Protection**: Use Microsoft Presidio to detect/anonymize PII before persistence or UI exposure.

2. **Secret Scanning**: Gitleaks runs in CI. Never commit API keys, tokens, or credentials.

3. **Security Scans**: Bandit (Python) and Safety (dependencies) must pass in CI.

4. **Auth**: All API endpoints protected by JWT (Keycloak stub currently, full OIDC planned).

## Git Workflow

### Commits

- Use **Commitizen** with conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`
- Pre-commit hooks run automatically:
  - Ruff check + format
  - Pylint (changed files)
  - Mypy/Pyright (changed files)
  - ESLint + Prettier
  - Gitleaks (secret detection)

### CI/CD Gates

Every PR must pass:
1. Python lint & format (Ruff, Pylint)
2. Python type checks (Mypy strict, Pyright strict)
3. Python tests + coverage (pytest + Hypothesis)
4. TypeScript quality (ESLint, Prettier, `tsc --noEmit`)
5. Frontend unit tests (Jest/Vitest)
6. E2E tests (Playwright subset)
7. Security scans (Bandit, Safety, Gitleaks)

Quality checks are orchestrated as parallel GitHub Actions matrix jobs so every individual lint/type/test/security tool runs on its own runner and reports independently even when another track fails.

Main/release branches additionally run:
- Full Playwright suite
- LangSmith evaluation datasets
- Docker image builds
- Helm chart packaging
- semantic-release for versioning

### Branch Protection

- No direct pushes to `main`
- All checks must pass
- Requires review approval

## AI Workflow Development

### LangGraph Workflows

1. **Define Graphs in `ai/graphs/`**: Keep workflow definitions separate from business logic.

2. **Instrument Every Node**: Use LangSmith decorators and Langfuse tracing.

3. **Test Graphs**: Write unit tests for individual nodes and integration tests for full graph execution.

4. **Version Evals**: When modifying LangGraph workflows, update corresponding LangSmith eval datasets.

### Adding New Analysis Features

1. Extend domain models in `packages/udocket-domain/`
2. Add LangGraph nodes in `apps/api/src/ai/graphs/`
3. Create service logic in `apps/api/src/workflow/analysis/`
4. Add frontend components in `apps/web/src/workflow/analysis/`
5. Write tests at each layer
6. Create LangSmith eval dataset
7. Add Langfuse instrumentation

### Adding New Output Types

1. Extend `compose` workflow slice in backend
2. Create new LangGraph compose nodes if needed
3. Add frontend display components
4. Test with golden analysis examples
5. Update eval datasets

## Observability

### Logging

- Use **structlog** for all logging
- Include correlation IDs for request tracing
- Never log PII in plain text (use Presidio)
- Log levels: DEBUG (dev), INFO (prod), WARN (issues), ERROR (failures)

### Tracing

- **LangSmith**: Development tracing, prompt debugging, eval runs
- **Langfuse**: Production LLM observability, cost tracking, feedback
- **OpenTelemetry**: System-level traces exported to Prometheus/Grafana

### Monitoring

- Prometheus + Grafana dashboards in `ops/`
- Alert on: error rates, high latency, cost spikes, model failures
- Define SLOs for critical flows (e.g., "90% of interviews processed in < X minutes")

## Common Patterns

### Domain Models

Use Pydantic v2 for all domain models:

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class Party(BaseModel):
    """Legal party in a matter."""
    id: str
    name: str
    role: str  # e.g., "client", "opposing_party"
    contact_info: Optional[str] = None
```

### API Endpoints

FastAPI with async patterns:

```python
from fastapi import APIRouter, Depends
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/matters")

@router.post("/", response_model=MatterResponse)
async def create_matter(
    matter: MatterCreate,
    db: AsyncSession = Depends(get_db)
) -> MatterResponse:
    # Implementation
    pass
```

### LangGraph Nodes

```python
from langgraph.graph import StateGraph
from langsmith import traceable

@traceable(name="extract_entities")
async def extract_entities_node(state: AnalysisState) -> AnalysisState:
    """Extract legal entities from transcript."""
    # Implementation with LLM call
    return updated_state
```

### Frontend Components

```typescript
import { useTranslations } from 'next-intl';
import { MatterAnalysis } from '@/packages/udocket_api_types';

interface AnalysisViewProps {
  analysis: MatterAnalysis;
}

export function AnalysisView({ analysis }: AnalysisViewProps) {
  const t = useTranslations('Analysis');

  return (
    <div>
      <h1>{t('title')}</h1>
      {/* Implementation */}
    </div>
  );
}
```

## Internationalization (i18n)

- **next-intl** configured for Next.js routing and translations
- Current locale: `en` (English)
- All user-facing strings must go through translation layer
- Message files: `apps/web/messages/en.json`
- Ready for multi-locale expansion

## Dependencies

- **uv** manages Python dependencies via `pyproject.toml`
- **npm/pnpm** manages JavaScript dependencies
- Keep dependencies up to date but test thoroughly
- Lock files (`uv.lock`, `package-lock.json`) must be committed

## Adding New Services

When adding a new microservice:

1. Create under `apps/` (e.g., `apps/new-service/`)
2. Follow vertical-slice structure inside
3. Add shared logic to appropriate `packages/` library
4. Update `infra/` with Helm charts and K8s manifests
5. Add Docker Compose config in `ops/`
6. Document in architecture docs
7. Add CI/CD pipeline

## Key Differences from Typical Projects

1. **Two Type Checkers**: We run both Mypy and Pyright for maximum type safety
2. **Vertical Slices**: No traditional MVC or layered architecture
3. **Observability First**: Instrumentation is not optional—every LLM call must be traced
4. **Multi-Tool Linting**: Ruff (fast) + Pylint (thorough) for Python
5. **Property-Based Testing**: Hypothesis tests on core invariants, not just examples
6. **Strict PII Handling**: Presidio must be used before persisting/displaying interview data

## Documentation Locations

- **Architecture**: [PRPs/ai_docs/ARCHITECTURE.md](PRPs/ai_docs/ARCHITECTURE.md)
- **Roadmap**: [PRPs/ai_docs/ROADMAP.md](PRPs/ai_docs/ROADMAP.md)
- **Engineering Plans**: [PRPs/ai_docs/PLANS.md](PRPs/ai_docs/PLANS.md)
- **Project README**: [README.md](README.md)
- **Package READMEs**: Each package and app has its own README

## Critical Reminders

- **Never commit secrets**: Gitleaks will catch it, but prevention is better
- **Test before pushing**: Pre-commit hooks enforce quality
- **Type everything**: Both Python (Mypy+Pyright) and TypeScript (strict mode)
- **Instrument all LLM calls**: LangSmith (dev) + Langfuse (prod)
- **Follow vertical slices**: Don't create new top-level directories unless absolutely necessary
- **Protect PII**: Use Presidio for any legal interview data
- **Maintain coverage**: 80-90% on critical paths
- **Document complexity**: If it's clever, it needs a comment or docstring
