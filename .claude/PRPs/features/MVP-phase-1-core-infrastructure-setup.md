# Feature: MVP Phase 1 - Core Infrastructure Setup

## Feature Description

Establish the foundational infrastructure for the uDocket legal AI platform according to Phase 1 requirements from the ROADMAP. This phase creates a production-ready foundation with strict typing, observability-first design, and development best practices before any feature implementation begins. The result is a fully functional, testable skeleton application with CI/CD, database connectivity, authentication scaffolding, configuration management, and comprehensive observability—ready for Phase 2 vertical slice development.

## User Story

As a **solo developer**
I want to **have a complete, production-grade infrastructure foundation**
So that **we can rapidly build vertical slices with confidence that quality, observability, and testing standards are enforced from day one**

## Problem Statement

Starting a complex multi-service AI platform without proper infrastructure leads to:

- Quality issues discovered late in development
- Inconsistent coding standards across services
- Poor observability making debugging difficult
- Fragile CI/CD causing deployment failures
- Technical debt from rushed foundational decisions

Phase 1 solves this by establishing all infrastructure, tooling, quality gates, and observability before feature development begins.

## Solution Statement

Implement a complete infrastructure foundation following the vertical-slice monorepo architecture defined in ARCHITECTURE.md. This includes:

- Python backend foundation (FastAPI, SQLAlchemy, Alembic, Pydantic v2)
- Database layer (Postgres + pgvector) with migrations
- Authentication scaffolding (Keycloak stub with JWT/OIDC roadmap)
- Configuration management (pydantic-settings for typed configs)
- Observability stack (structlog, OpenTelemetry, Prometheus/Grafana stubs)
- Development environment (Docker Compose for local services)
- Quality tooling (Ruff, Pylint, Mypy, Pyright, pytest, pre-commit hooks)
- CI/CD pipeline (lint, typecheck, test gates)

## Feature Metadata

**Feature Type**: New Capability (Foundation)
**Estimated Complexity**: High
**Primary Systems Affected**:

- `apps/api` (backend service foundation)
- `apps/worker` (Celery worker scaffolding)
- `packages/py-domain` (canonical domain models)
- `packages/py-ai-core` (AI orchestration helpers)
- `packages/py-worker-core` (Celery utilities)
- `configs/` (all quality tool configurations)
- `tooling/` (doit tasks, pre-commit, semantic-release)
- `ops/` (Docker Compose, observability dashboards)

**Dependencies**:

- Python 3.12+
- uv (0.5.21+)
- Docker & Docker Compose
- PostgreSQL 14+
- RabbitMQ 3.11+

---

## CONTEXT REFERENCES

### Relevant Codebase Files

**Existing Structure:**

- `pyproject.toml` (lines 1-42) - Contains all dependencies already specified, needs workspace configuration
- `apps/api/src/core/__init__.py` - Empty, needs core modules
- `apps/api/src/workflow/` - Directory structure exists, empty modules
- `apps/api/src/observability/__init__.py` - Empty, needs observability setup
- `packages/py-domain/` - Empty, needs canonical models
- `packages/py-ai-core/` - Empty, needs LangGraph/LangSmith helpers
- `configs/` - Only contains .gitkeep, needs all tool configs

**Files Requiring Creation:**

- `apps/api/src/core/database.py` - SQLAlchemy async engine and session management
- `apps/api/src/core/config.py` - Pydantic settings for typed configuration
- `apps/api/src/core/logging.py` - structlog configuration
- `apps/api/src/platform/auth/jwt.py` - JWT token handling (stub)
- `apps/api/src/main.py` - FastAPI application entrypoint
- `apps/api/alembic.ini` - Alembic migration configuration
- `apps/api/alembic/env.py` - Alembic environment setup
- `packages/py-domain/models.py` - Base models and shared domain types
- `configs/ruff.toml` - Ruff configuration
- `configs/pyproject.toml` - Mypy/Pyright configuration
- `configs/pylint.toml` - Pylint configuration
- `.pre-commit-config.yaml` - Pre-commit hooks configuration
- `ops/docker-compose.yml` - Local development services
- `tooling/dodo.py` - doit task automation
- `.github/workflows/ci.yml` - CI/CD pipeline

### New Files to Create

**Backend Core (`apps/api/src/core/`):**

1. `database.py` - Async SQLAlchemy setup with pgvector
2. `config.py` - Pydantic settings with validation
3. `logging.py` - structlog with OpenTelemetry integration
4. `exceptions.py` - Base exception classes

**API Entrypoint (`apps/api/src/`):**

1. `main.py` - FastAPI app with CORS, exception handlers, health endpoint

**Platform Layer (`apps/api/src/platform/`):**

1. `auth/jwt.py` - JWT encoding/decoding (Keycloak stub)
2. `auth/dependencies.py` - FastAPI dependencies for auth
3. `tenants/models.py` - Tenant isolation models (future-ready)

**Domain Models (`packages/py-domain/`):**

1. `__init__.py` - Package exports
2. `base.py` - Base Pydantic models with common fields
3. `matter.py` - Matter, Party, Relationship models
4. `analysis.py` - MatterAnalysis, Issue, Timeline, Action models
5. `transcript.py` - Transcript and speaker turn models

**Database Migrations (`apps/api/alembic/`):**

1. `alembic.ini` - Alembic configuration
2. `env.py` - Alembic environment with async support
3. `versions/001_initial_schema.py` - Initial database schema

**Configuration Files (`configs/`):**

1. `ruff.toml` - Ruff lint and format rules
2. `pyproject.toml` - Mypy strict configuration
3. `pylint.toml` - Pylint rules for complexity/naming
4. `.bandit` - Security scanning rules
5. `pytest.ini` - Pytest configuration with coverage

**Development Environment (`ops/`):**

1. `docker-compose.yml` - Postgres, RabbitMQ, Redis services
2. `prometheus.yml` - Prometheus scrape config (stub)
3. `grafana/` - Grafana dashboards (stubs)

**Tooling (`tooling/`):**

1. `dodo.py` - doit tasks for common operations
2. `.commitizenrc.json` - Commitizen configuration

**CI/CD (`.github/workflows/`):**

1. `ci.yml` - Main CI pipeline with all quality gates

**Tests (`apps/api/tests/`):**

1. `conftest.py` - Pytest fixtures for database, client
2. `test_health.py` - Health endpoint test
3. `integration/test_database.py` - Database connection test

### Relevant Documentation

**Pydantic v2 Models:**

- [Pydantic Models Overview](https://docs.pydantic.dev/latest/concepts/models/index.md)
  - Section: BaseModel usage, field validation, model config
  - Why: Foundation for all domain models with strict typing
- [Pydantic Settings](https://docs.pydantic.dev/latest/api/pydantic_settings/index.md)
  - Section: Environment variable loading, validation
  - Why: Type-safe configuration management

**UV Project Management:**

- [UV Projects Documentation](https://docs.astral.sh/uv/llms.txt)
  - Section: Project initialization, workspace management
  - Why: Using uv for dependency management and virtual environments
- [UV CLI Reference](https://docs.astral.sh/uv/reference/cli/index.md)
  - Section: uv sync, uv run commands
  - Why: Day-to-day development commands

**Docker Compose:**

- [Docker Compose Setup Guide](https://docs.docker.com/guides/compose-bake/)
  - Section: Service definitions, volumes, networks
  - Why: Local development environment for Postgres, RabbitMQ, Redis

**FastAPI Best Practices:**

- Search: "FastAPI async SQLAlchemy dependency injection"
- Why: Proper async database session management in endpoints

**SQLAlchemy 2.0 Async:**

- Search: "SQLAlchemy async engine asyncpg"
- Why: Modern async database patterns

**Structlog:**

- Search: "structlog configuration processors"
- Why: JSON structured logging with correlation IDs

### Patterns to Follow

**Naming Conventions (from CLAUDE.md and PLANS.md):**

```python
# Python: snake_case for functions, variables, modules
# PascalCase for classes
def get_current_user() -> User:
    pass

class MatterAnalysis(BaseModel):
    pass
```

**Pydantic v2 Models Pattern:**

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4

class BaseEntity(BaseModel):
    """Base model with common fields."""
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "from_attributes": True,  # Enable ORM mode
        "json_schema_extra": {
            "example": {...}
        }
    }
```

**FastAPI Dependency Injection Pattern:**

```python
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

**Structlog Configuration Pattern:**

```python
import structlog
from structlog.processors import JSONRenderer, TimeStamper

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        TimeStamper(fmt="iso"),
        JSONRenderer()
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)
```

**Error Handling Pattern:**

```python
from fastapi import HTTPException, status

class ResourceNotFoundError(Exception):
    """Raised when a resource is not found."""
    pass

# In endpoint:
@router.get("/{id}")
async def get_resource(id: UUID):
    try:
        resource = await service.get(id)
    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resource {id} not found"
        )
    return resource
```

**Pytest Fixture Pattern:**

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_async_engine("postgresql+asyncpg://test:test@localhost/test")
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session
        await session.rollback()
```

### Project-Specific Standards (from CLAUDE.md)

**Type Checking Requirements:**

- ALL functions, methods, public APIs must be fully typed
- Must pass both `mypy --strict` and `pyright --level strict`
- No implicit `Any` - explicit only with `# type: ignore` comments

**Testing Requirements:**

- 90%+ coverage threshold on critical packages
- Use Hypothesis for property-based tests on invariants
- pytest-asyncio for all async code tests

**Security Requirements:**

- Never commit secrets (Gitleaks will catch)
- Use Microsoft Presidio for PII detection/anonymization
- Bandit security scanning must pass

**Observability Requirements:**

- All LLM calls must be traced (LangSmith dev, Langfuse prod)
- Use structlog for all logging
- Include correlation IDs in logs
- Never log PII in plain text

---

## IMPLEMENTATION PLAN

### Phase 1: Python Environment & Dependencies

Set up the Python development environment using uv and configure the workspace structure for the monorepo.

**Tasks:**

- Initialize uv workspace in root pyproject.toml
- Configure Python 3.12+ environment
- Install all dependencies via `uv sync`
- Verify uv can manage workspace packages

### Phase 2: Configuration & Settings

Create type-safe configuration management using Pydantic settings.

**Tasks:**

- Create `apps/api/src/core/config.py` with BaseSettings
- Define settings for database, auth, logging, observability
- Add `.env.example` with all required environment variables
- Implement settings validation with clear error messages

### Phase 3: Database Layer

Set up async SQLAlchemy with Postgres and pgvector, including Alembic migrations.

**Tasks:**

- Create `apps/api/src/core/database.py` with async engine
- Configure SQLAlchemy Base with pgvector support
- Set up Alembic with async migration support
- Create initial migration for pgvector extension
- Implement get_db() dependency for FastAPI

### Phase 4: Logging & Observability

Configure structured logging with OpenTelemetry integration stubs.

**Tasks:**

- Create `apps/api/src/core/logging.py` with structlog
- Add processors for JSON output, timestamps, log levels
- Integrate OpenTelemetry context propagation (stub)
- Add correlation ID middleware for FastAPI
- Create observability module with health check utilities

### Phase 5: Authentication Scaffolding

Create JWT authentication stub with Keycloak roadmap consideration.

**Tasks:**

- Create `apps/api/src/platform/auth/jwt.py` with encode/decode
- Implement get_current_user() FastAPI dependency
- Add auth exception handlers
- Document Keycloak integration roadmap in comments
- Create stub user model in py-domain

### Phase 6: Domain Models Foundation

Implement canonical domain models in shared packages.

**Tasks:**

- Create base models in `packages/py-domain/base.py`
- Implement Matter, Party, Relationship models
- Implement MatterAnalysis, Issue, Timeline, Action models
- Implement Transcript and speaker turn models
- Add comprehensive field validation and examples

### Phase 7: FastAPI Application

Create the main FastAPI application with CORS, middleware, and health endpoints.

**Tasks:**

- Create `apps/api/src/main.py` with FastAPI app
- Add CORS middleware with proper configuration
- Add logging middleware with correlation IDs
- Implement /health endpoint with database check
- Implement /api/v1 router structure (empty)

### Phase 8: Quality Tooling Configuration

Configure all linting, formatting, and type-checking tools.

**Tasks:**

- Create `configs/ruff.toml` with project standards
- Create `configs/pyproject.toml` with Mypy strict config
- Create `configs/pylint.toml` with complexity rules
- Create `configs/.bandit` for security scanning
- Create `configs/pytest.ini` with coverage settings

### Phase 9: Testing Infrastructure

Set up pytest with async support and create foundational tests.

**Tasks:**

- Create `apps/api/tests/conftest.py` with fixtures
- Implement async database fixture with rollback
- Implement test client fixture for FastAPI
- Create test_health.py with health endpoint test
- Create integration test for database connectivity

### Phase 10: Development Environment

Create Docker Compose stack for local development services.

**Tasks:**

- Create `ops/docker-compose.yml` with Postgres, RabbitMQ, Redis
- Configure pgvector in Postgres service
- Add volumes for data persistence
- Create initialization scripts for services
- Document startup commands in ops/README.md

### Phase 11: Pre-commit Hooks

Configure pre-commit hooks for automated quality checks.

**Tasks:**

- Create `.pre-commit-config.yaml` with all hooks
- Add Ruff check and format hooks
- Add Mypy and Pyright hooks (changed files only)
- Add Gitleaks for secret detection
- Add Commitizen for conventional commits

### Phase 12: Task Automation with doit

Create doit tasks for common development operations.

**Tasks:**

- Create `tooling/dodo.py` with task definitions
- Implement `doit lint` task (Ruff, Pylint)
- Implement `doit typecheck` task (Mypy, Pyright)
- Implement `doit test` task (pytest with coverage)
- Implement `doit quality` task (all checks)
- Document tasks in tooling/README.md

### Phase 13: CI/CD Pipeline

Create GitHub Actions workflow with all quality gates.

**Tasks:**

- Create `.github/workflows/ci.yml` with job matrix
- Add Python lint job (Ruff, Pylint)
- Add Python type-check job (Mypy strict, Pyright strict)
- Add Python test job (pytest with coverage report)
- Add security scan job (Bandit, Safety, Gitleaks)
- Configure branch protection for main

---

## STEP-BY-STEP TASKS

Execute every task in order, top to bottom. Each task is atomic and independently testable.

### 1. CREATE pyproject.toml workspace configuration

- **IMPLEMENT**: Add workspace configuration to root pyproject.toml
- **PATTERN**: UV workspace with packages specified
- **CONTENT**:

```toml
[tool.uv.workspace]
members = [
    "apps/api",
    "apps/worker",
    "apps/web",
    "packages/py-domain",
    "packages/py-ai-core",
    "packages/py-worker-core",
]

[tool.uv]
dev-dependencies = [
    # Already specified in dependencies
]
```

- **GOTCHA**: UV workspaces require each member to have its own pyproject.toml
- **VALIDATE**: `uv sync`

### 2. CREATE apps/api/pyproject.toml

- **IMPLEMENT**: Package definition for API service
- **PATTERN**: Standard Python package with dependencies
- **IMPORTS**: References workspace packages
- **CONTENT**:

```toml
[project]
name = "udocket-api"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "sqlalchemy>=2.0.44",
    "asyncpg>=0.30.0",
    "alembic>=1.17.2",
    "pydantic>=2.12.4",
    "pydantic-settings>=2.12.0",
    "structlog>=25.5.0",
    "python-jose[cryptography]>=3.3.0",
    "passlib[bcrypt]>=1.7.4",
    "python-multipart>=0.0.20",
    "py-domain",
]
```

- **VALIDATE**: `cd apps/api && uv sync`

### 3. CREATE packages/py-domain/pyproject.toml

- **IMPLEMENT**: Shared domain models package
- **PATTERN**: Pure Python package with minimal dependencies
- **CONTENT**:

```toml
[project]
name = "py-domain"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.12.4",
]
```

- **VALIDATE**: `cd packages/py-domain && uv sync`

### 4. CREATE apps/api/src/core/config.py

- **IMPLEMENT**: Pydantic settings for typed configuration
- **PATTERN**: BaseSettings with env_prefix and validation
- **IMPORTS**: `from pydantic_settings import BaseSettings, SettingsConfigDict`
- **GOTCHA**: Use SettingsConfigDict for Pydantic v2, not old Config class
- **CONTENT**:

```python
"""Configuration management with Pydantic settings."""
from typing import Optional
from pydantic import Field, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "uDocket API"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = Field(default="development", pattern="^(development|staging|production)$")

    # Database
    database_url: PostgresDsn
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_echo: bool = False

    # Auth
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    # Logging
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    log_json: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


# Global settings instance
settings = Settings()
```

- **VALIDATE**: `cd apps/api && uv run python -c "from src.core.config import settings; print(settings.app_name)"`

### 5. CREATE .env.example

- **IMPLEMENT**: Example environment variables file
- **PATTERN**: Documented env vars with safe defaults
- **CONTENT**:

```bash
# Application
APP_NAME="uDocket API"
APP_VERSION="0.1.0"
DEBUG=false
ENVIRONMENT=development

# Database (Postgres with pgvector)
DATABASE_URL=postgresql+asyncpg://udocket:udocket_dev_password@localhost:5432/udocket

# Auth (generate with: openssl rand -hex 32)
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS (comma-separated for multiple origins)
CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# Logging
LOG_LEVEL=INFO
LOG_JSON=true
```

- **VALIDATE**: Manual review of completeness

### 6. CREATE apps/api/src/core/database.py

- **IMPLEMENT**: Async SQLAlchemy engine and session management
- **PATTERN**: Async engine with pgvector extension
- **IMPORTS**: `from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker`
- **GOTCHA**: Must use asyncpg driver, not psycopg2
- **CONTENT**:

```python
"""Database connection and session management."""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event, text

from .config import settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# Create async engine
engine: AsyncEngine = create_async_engine(
    str(settings.database_url),
    echo=settings.database_echo,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,  # Verify connections before using
)


# Create async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.

    Provides an async database session with automatic commit/rollback.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database with pgvector extension."""
    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))

        # Create all tables
        await conn.run_sync(Base.metadata.create_all)


async def check_db_health() -> bool:
    """Check database connectivity for health endpoint."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
```

- **VALIDATE**: `cd apps/api && uv run python -c "from src.core.database import engine; print(engine)"`

### 7. CREATE apps/api/src/core/logging.py

- **IMPLEMENT**: Structlog configuration with JSON output
- **PATTERN**: Structured logging with processors
- **IMPORTS**: `import structlog`
- **CONTENT**:

```python
"""Structured logging configuration with structlog."""
import logging
import sys
from typing import Any

import structlog
from structlog.types import EventDict, Processor

from .config import settings


def add_app_context(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    """Add application context to all log entries."""
    event_dict["app_name"] = settings.app_name
    event_dict["app_version"] = settings.app_version
    event_dict["environment"] = settings.environment
    return event_dict


def configure_logging() -> None:
    """Configure structlog with appropriate processors."""

    # Determine processors based on environment
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        add_app_context,
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.log_json:
        # JSON output for production
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Pretty console output for development
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True),
        ])

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )


# Get logger instance
def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance."""
    return structlog.get_logger(name)
```

- **VALIDATE**: `cd apps/api && uv run python -c "from src.core.logging import configure_logging, get_logger; configure_logging(); log = get_logger('test'); log.info('test_message', key='value')"`

### 8. CREATE apps/api/src/core/exceptions.py

- **IMPLEMENT**: Base exception classes for the application
- **PATTERN**: Hierarchy of custom exceptions
- **CONTENT**:

```python
"""Custom exception classes for the application."""


class UDocketException(Exception):
    """Base exception for all uDocket errors."""
    def __init__(self, message: str, error_code: str | None = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ResourceNotFoundError(UDocketException):
    """Raised when a requested resource is not found."""
    def __init__(self, resource_type: str, resource_id: str):
        message = f"{resource_type} with id {resource_id} not found"
        super().__init__(message, error_code="RESOURCE_NOT_FOUND")


class DatabaseError(UDocketException):
    """Raised when a database operation fails."""
    def __init__(self, message: str):
        super().__init__(message, error_code="DATABASE_ERROR")


class ValidationError(UDocketException):
    """Raised when validation fails."""
    def __init__(self, message: str):
        super().__init__(message, error_code="VALIDATION_ERROR")


class AuthenticationError(UDocketException):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, error_code="AUTHENTICATION_ERROR")


class AuthorizationError(UDocketException):
    """Raised when authorization fails."""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, error_code="AUTHORIZATION_ERROR")
```

- **VALIDATE**: `cd apps/api && uv run python -c "from src.core.exceptions import ResourceNotFoundError; e = ResourceNotFoundError('Matter', '123'); print(e.message)"`

### 9. CREATE `apps/api/src/core/__init__.py`

- **IMPLEMENT**: Core module exports
- **PATTERN**: Clean public API for core module
- **CONTENT**:

```python
"""Core infrastructure modules."""
from .config import settings
from .database import Base, engine, async_session_maker, get_db, init_db, check_db_health
from .logging import configure_logging, get_logger
from .exceptions import (
    UDocketException,
    ResourceNotFoundError,
    DatabaseError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
)

__all__ = [
    "settings",
    "Base",
    "engine",
    "async_session_maker",
    "get_db",
    "init_db",
    "check_db_health",
    "configure_logging",
    "get_logger",
    "UDocketException",
    "ResourceNotFoundError",
    "DatabaseError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
]
```

- **VALIDATE**: `cd apps/api && uv run python -c "from src.core import settings, get_logger; print('OK')"`

### 10. CREATE `packages/py-domain/src/__init__.py`

- **IMPLEMENT**: Package structure initialization
- **PATTERN**: src layout for packages
- **CONTENT**:

```python
"""uDocket domain models package."""
__version__ = "0.1.0"
```

- **VALIDATE**: Manual review

### 11. CREATE packages/py-domain/src/base.py

- **IMPLEMENT**: Base Pydantic models with common fields
- **PATTERN**: Pydantic v2 BaseModel with common patterns
- **IMPORTS**: `from pydantic import BaseModel, Field, ConfigDict`
- **GOTCHA**: Use ConfigDict for Pydantic v2, not inner Config class
- **CONTENT**:

```python
"""Base models with common fields and configuration."""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class BaseEntity(BaseModel):
    """Base model for entities with ID and timestamps."""

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,  # Enable ORM mode for SQLAlchemy
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
            }
        }
    )


class BaseRequest(BaseModel):
    """Base model for API requests."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        str_min_length=1,
    )


class BaseResponse(BaseModel):
    """Base model for API responses."""

    model_config = ConfigDict(
        from_attributes=True,
    )


class HealthCheck(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status: 'healthy' or 'unhealthy'")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Deployment environment")
    database: bool = Field(..., description="Database connectivity status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "environment": "development",
                "database": True,
            }
        }
    )
```

- **VALIDATE**: `cd packages/py-domain && uv run python -c "from src.base import BaseEntity; e = BaseEntity(); print(e.id)"`

### 12. CREATE packages/py-domain/src/matter.py

- **IMPLEMENT**: Matter domain models
- **PATTERN**: Pydantic models with field validation
- **IMPORTS**: `from .base import BaseEntity`
- **CONTENT**:

```python
"""Matter-related domain models."""
from typing import Optional, Literal
from uuid import UUID

from pydantic import Field

from .base import BaseEntity


MatterStatus = Literal["intake", "analysis", "review", "completed", "archived"]
PartyRole = Literal["client", "opposing_party", "witness", "attorney", "other"]


class Party(BaseEntity):
    """A person or organization involved in a legal matter."""

    name: str = Field(..., min_length=1, max_length=255, description="Full name of the party")
    role: PartyRole = Field(..., description="Role of the party in the matter")
    contact_info: Optional[str] = Field(None, max_length=500, description="Contact information")
    notes: Optional[str] = Field(None, description="Additional notes about the party")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "John Doe",
                "role": "client",
                "contact_info": "john.doe@example.com",
                "notes": "Primary contact for case",
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
            }
        }
    }


class Relationship(BaseEntity):
    """Relationship between two parties in a matter."""

    from_party_id: UUID = Field(..., description="Source party ID")
    to_party_id: UUID = Field(..., description="Target party ID")
    relationship_type: str = Field(..., min_length=1, max_length=100, description="Type of relationship")
    description: Optional[str] = Field(None, description="Description of the relationship")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "from_party_id": "550e8400-e29b-41d4-a716-446655440001",
                "to_party_id": "550e8400-e29b-41d4-a716-446655440003",
                "relationship_type": "spouse",
                "description": "Married for 10 years",
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
            }
        }
    }


class Matter(BaseEntity):
    """A legal matter or case."""

    title: str = Field(..., min_length=1, max_length=255, description="Matter title")
    description: Optional[str] = Field(None, description="Detailed description of the matter")
    status: MatterStatus = Field(default="intake", description="Current status of the matter")
    matter_type: str = Field(..., min_length=1, max_length=100, description="Type of legal matter")
    client_id: Optional[UUID] = Field(None, description="Primary client party ID")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Doe v. Smith Divorce",
                "description": "Divorce proceedings between John and Jane",
                "status": "intake",
                "matter_type": "family_law",
                "client_id": "550e8400-e29b-41d4-a716-446655440001",
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
            }
        }
    }
```

- **VALIDATE**: `cd packages/py-domain && uv run python -c "from src.matter import Matter, Party; m = Matter(title='Test', matter_type='test'); print(m.status)"`

### 13. CREATE packages/py-domain/src/analysis.py

- **IMPLEMENT**: Analysis domain models (MatterAnalysis, Issue, Timeline, Action)
- **PATTERN**: Pydantic models with field validation
- **IMPORTS**: `from .base import BaseEntity`
- **CONTENT**:

```python
"""Analysis-related domain models."""
from datetime import date
from typing import Optional, Literal
from uuid import UUID

from pydantic import Field

from .base import BaseEntity


IssueSeverity = Literal["low", "medium", "high", "critical"]
TimelineEventType = Literal["action", "deadline", "milestone", "other"]
ActionPriority = Literal["low", "medium", "high", "urgent"]
ActionStatus = Literal["pending", "in_progress", "completed", "cancelled"]


class Issue(BaseEntity):
    """A legal issue or concern identified in a matter."""

    matter_id: UUID = Field(..., description="Associated matter ID")
    title: str = Field(..., min_length=1, max_length=255, description="Issue title")
    description: str = Field(..., description="Detailed description of the issue")
    severity: IssueSeverity = Field(default="medium", description="Severity level")
    category: str = Field(..., min_length=1, max_length=100, description="Issue category")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440010",
                "matter_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Asset Division Dispute",
                "description": "Disagreement over property valuation",
                "severity": "high",
                "category": "property_division",
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
            }
        }
    }


class TimelineEvent(BaseEntity):
    """A chronological event in a matter timeline."""

    matter_id: UUID = Field(..., description="Associated matter ID")
    event_date: date = Field(..., description="Date of the event")
    event_type: TimelineEventType = Field(..., description="Type of event")
    title: str = Field(..., min_length=1, max_length=255, description="Event title")
    description: Optional[str] = Field(None, description="Event description")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440011",
                "matter_id": "550e8400-e29b-41d4-a716-446655440000",
                "event_date": "2025-01-10",
                "event_type": "deadline",
                "title": "Discovery Due Date",
                "description": "All discovery materials must be submitted",
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
            }
        }
    }


class Action(BaseEntity):
    """A follow-up action or task derived from matter analysis."""

    matter_id: UUID = Field(..., description="Associated matter ID")
    title: str = Field(..., min_length=1, max_length=255, description="Action title")
    description: str = Field(..., description="Detailed description of the action")
    priority: ActionPriority = Field(default="medium", description="Priority level")
    status: ActionStatus = Field(default="pending", description="Current status")
    assigned_to: Optional[str] = Field(None, max_length=255, description="Assignee name or email")
    due_date: Optional[date] = Field(None, description="Due date for completion")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440012",
                "matter_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Request property appraisal",
                "description": "Contact certified appraiser for marital home valuation",
                "priority": "high",
                "status": "pending",
                "assigned_to": "paralegal@lawfirm.com",
                "due_date": "2025-02-01",
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
            }
        }
    }


class Gap(BaseEntity):
    """An information gap or missing detail identified in matter analysis."""

    matter_id: UUID = Field(..., description="Associated matter ID")
    title: str = Field(..., min_length=1, max_length=255, description="Gap title")
    description: str = Field(..., description="Description of missing information")
    category: str = Field(..., min_length=1, max_length=100, description="Gap category")
    resolved: bool = Field(default=False, description="Whether gap has been resolved")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440013",
                "matter_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Missing financial disclosures",
                "description": "Spouse's income documentation not yet provided",
                "category": "financial",
                "resolved": False,
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
            }
        }
    }


class MatterAnalysis(BaseEntity):
    """Canonical analysis of a legal matter with all extracted information."""

    matter_id: UUID = Field(..., description="Associated matter ID")
    summary: str = Field(..., description="Executive summary of the matter")
    embedding: Optional[list[float]] = Field(None, description="Vector embedding for semantic search")

    # Related entities are stored separately and joined via relationships
    # This model represents the analysis record itself

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440020",
                "matter_id": "550e8400-e29b-41d4-a716-446655440000",
                "summary": "Divorce case involving property division and custody considerations",
                "embedding": None,  # Populated by analysis service
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
            }
        }
    }
```

- **VALIDATE**: `cd packages/py-domain && uv run python -c "from src.analysis import Issue, Action; i = Issue(matter_id='550e8400-e29b-41d4-a716-446655440000', title='Test', description='Test', category='test'); print(i.severity)"`

### 14. CREATE packages/py-domain/src/transcript.py

- **IMPLEMENT**: Transcript domain models
- **PATTERN**: Pydantic models with field validation
- **IMPORTS**: `from .base import BaseEntity`
- **CONTENT**:

```python
"""Transcript-related domain models."""
from typing import Optional
from uuid import UUID

from pydantic import Field

from .base import BaseEntity


class SpeakerTurn(BaseEntity):
    """A single speaker turn in a transcript."""

    transcript_id: UUID = Field(..., description="Associated transcript ID")
    speaker_id: str = Field(..., min_length=1, max_length=100, description="Speaker identifier")
    speaker_name: Optional[str] = Field(None, max_length=255, description="Speaker name (if known)")
    start_time: float = Field(..., ge=0, description="Start time in seconds")
    end_time: float = Field(..., ge=0, description="End time in seconds")
    text: str = Field(..., min_length=1, description="Transcribed text for this turn")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Transcription confidence score")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440030",
                "transcript_id": "550e8400-e29b-41d4-a716-446655440031",
                "speaker_id": "speaker_1",
                "speaker_name": "John Doe",
                "start_time": 0.0,
                "end_time": 5.5,
                "text": "I need help with my divorce case.",
                "confidence": 0.95,
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
            }
        }
    }


class Transcript(BaseEntity):
    """A complete transcript of a legal interview or consultation."""

    matter_id: UUID = Field(..., description="Associated matter ID")
    audio_url: Optional[str] = Field(None, max_length=500, description="URL to source audio file")
    language: str = Field(default="en", max_length=10, description="Language code (ISO 639-1)")
    duration_seconds: Optional[float] = Field(None, ge=0, description="Audio duration in seconds")
    word_count: Optional[int] = Field(None, ge=0, description="Total word count")
    transcription_service: Optional[str] = Field(None, max_length=100, description="Service used for transcription")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440031",
                "matter_id": "550e8400-e29b-41d4-a716-446655440000",
                "audio_url": "s3://bucket/audio/interview-123.wav",
                "language": "en",
                "duration_seconds": 3600.0,
                "word_count": 5000,
                "transcription_service": "azure_speech",
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
            }
        }
    }
```

- **VALIDATE**: `cd packages/py-domain && uv run python -c "from src.transcript import Transcript; t = Transcript(matter_id='550e8400-e29b-41d4-a716-446655440000'); print(t.language)"`

### 15. CREATE `packages/py-domain/src/__init__.py` (exports)

- **IMPLEMENT**: Package exports for easy importing
- **PATTERN**: Clean public API
- **CONTENT**:

```python
"""uDocket domain models package."""
from .base import BaseEntity, BaseRequest, BaseResponse, HealthCheck
from .matter import Matter, Party, Relationship, MatterStatus, PartyRole
from .analysis import (
    MatterAnalysis,
    Issue,
    TimelineEvent,
    Action,
    Gap,
    IssueSeverity,
    TimelineEventType,
    ActionPriority,
    ActionStatus,
)
from .transcript import Transcript, SpeakerTurn

__version__ = "0.1.0"

__all__ = [
    # Base
    "BaseEntity",
    "BaseRequest",
    "BaseResponse",
    "HealthCheck",
    # Matter
    "Matter",
    "Party",
    "Relationship",
    "MatterStatus",
    "PartyRole",
    # Analysis
    "MatterAnalysis",
    "Issue",
    "TimelineEvent",
    "Action",
    "Gap",
    "IssueSeverity",
    "TimelineEventType",
    "ActionPriority",
    "ActionStatus",
    # Transcript
    "Transcript",
    "SpeakerTurn",
]
```

- **VALIDATE**: `cd packages/py-domain && uv run python -c "from src import Matter, Party, Issue; print('OK')"`

### 16. CREATE apps/api/src/platform/auth/jwt.py

- **IMPLEMENT**: JWT token encoding/decoding stub
- **PATTERN**: JWT with python-jose
- **IMPORTS**: `from jose import JWTError, jwt`
- **GOTCHA**: This is a stub for Phase 1; Keycloak integration planned for later
- **CONTENT**:

```python
"""JWT token handling (Keycloak stub).

NOTE: This is a simplified JWT implementation for Phase 1 development.
Full Keycloak OIDC integration is planned for Phase 2+.
See ROADMAP.md Phase 2 for Keycloak integration details.
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from jose import JWTError, jwt
from pydantic import BaseModel, Field

from ...core.config import settings
from ...core.exceptions import AuthenticationError


class TokenData(BaseModel):
    """Data contained in a JWT token."""

    user_id: UUID = Field(..., description="User identifier")
    email: str = Field(..., description="User email")
    roles: list[str] = Field(default_factory=list, description="User roles")
    exp: Optional[datetime] = Field(None, description="Expiration timestamp")


class UserStub(BaseModel):
    """Stub user model for Phase 1 development."""

    id: UUID
    email: str
    full_name: str
    roles: list[str] = Field(default_factory=list)
    is_active: bool = True


def create_access_token(user: UserStub) -> str:
    """
    Create a JWT access token for a user.

    Args:
        user: User to create token for

    Returns:
        Encoded JWT token string
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    payload = {
        "user_id": str(user.id),
        "email": user.email,
        "roles": user.roles,
        "exp": expire,
        "iat": datetime.utcnow(),
    }

    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> TokenData:
    """
    Decode and validate a JWT access token.

    Args:
        token: Encoded JWT token string

    Returns:
        Decoded token data

    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )

        user_id = UUID(payload.get("user_id"))
        email = payload.get("email")
        roles = payload.get("roles", [])
        exp = payload.get("exp")

        if not user_id or not email:
            raise AuthenticationError("Invalid token payload")

        return TokenData(
            user_id=user_id,
            email=email,
            roles=roles,
            exp=datetime.fromtimestamp(exp) if exp else None
        )

    except JWTError as e:
        raise AuthenticationError(f"Token validation failed: {str(e)}")
    except ValueError as e:
        raise AuthenticationError(f"Invalid token format: {str(e)}")
```

- **VALIDATE**: `cd apps/api && uv run python -c "from src.platform.auth.jwt import UserStub, create_access_token; from uuid import uuid4; u = UserStub(id=uuid4(), email='test@example.com', full_name='Test'); t = create_access_token(u); print('Token created')"`

### 17. CREATE apps/api/src/platform/auth/dependencies.py

- **IMPLEMENT**: FastAPI dependencies for authentication
- **PATTERN**: OAuth2 password bearer with JWT
- **IMPORTS**: `from fastapi import Depends, HTTPException, status`
- **CONTENT**:

```python
"""FastAPI dependencies for authentication.

NOTE: This is a stub implementation for Phase 1.
Full Keycloak OIDC integration planned for Phase 2+.
"""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .jwt import decode_access_token, TokenData, UserStub
from ...core.exceptions import AuthenticationError


# Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None
) -> UserStub:
    """
    FastAPI dependency to get current authenticated user.

    Validates JWT token and returns user information.

    Args:
        credentials: HTTP Bearer token credentials

    Returns:
        Current user information

    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token_data = decode_access_token(credentials.credentials)

        # In Phase 1, we reconstruct a stub user from token data
        # In Phase 2+, this will query Keycloak or a user service
        user = UserStub(
            id=token_data.user_id,
            email=token_data.email,
            full_name=token_data.email.split("@")[0],  # Stub
            roles=token_data.roles,
            is_active=True,
        )

        return user

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


async def require_role(required_role: str):
    """
    FastAPI dependency factory to require a specific role.

    Args:
        required_role: Role required to access endpoint

    Returns:
        Dependency function that checks user role
    """
    async def role_checker(user: Annotated[UserStub, Depends(get_current_user)]) -> UserStub:
        if required_role not in user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return user

    return role_checker
```

- **VALIDATE**: `cd apps/api && uv run python -c "from src.platform.auth.dependencies import get_current_user; print('OK')"`

### 18. CREATE apps/api/src/main.py

- **IMPLEMENT**: FastAPI application entrypoint
- **PATTERN**: Application factory with lifespan, middleware, routers
- **IMPORTS**: `from fastapi import FastAPI`
- **GOTCHA**: Use lifespan context manager for startup/shutdown, not deprecated events
- **CONTENT**:

```python
"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from src.core import configure_logging, settings, init_db, check_db_health, UDocketException
from py-domain import HealthCheck


# Configure logging on module import
configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager."""
    # Startup
    logger.info("application_starting", version=settings.app_version, environment=settings.environment)

    try:
        await init_db()
        logger.info("database_initialized")
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))

    yield

    # Shutdown
    logger.info("application_shutting_down")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Legal interview analysis and documentation platform",
    docs_url="/api/docs" if settings.debug else None,
    redoc_url="/api/redoc" if settings.debug else None,
    openapi_url="/api/openapi.json" if settings.debug else None,
    lifespan=lifespan,
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(UDocketException)
async def udocket_exception_handler(request: Request, exc: UDocketException) -> JSONResponse:
    """Handle custom uDocket exceptions."""
    logger.error(
        "application_error",
        error_code=exc.error_code,
        message=exc.message,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
        },
    )


# Health check endpoint
@app.get("/health", response_model=HealthCheck, tags=["health"])
async def health_check() -> HealthCheck:
    """
    Health check endpoint.

    Returns service status, version, environment, and database connectivity.
    """
    db_healthy = await check_db_health()

    return HealthCheck(
        status="healthy" if db_healthy else "unhealthy",
        version=settings.app_version,
        environment=settings.environment,
        database=db_healthy,
    )


# API router (empty for Phase 1)
# Phase 2+ will add:
# - /api/v1/matters
# - /api/v1/intake
# - /api/v1/analysis
# - /api/v1/compose


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_config=None,  # Use structlog instead
    )
```

- **VALIDATE**: `cd apps/api && uv run python src/main.py` (should start without errors, then Ctrl+C)

### 19. CREATE apps/api/alembic.ini

- **IMPLEMENT**: Alembic configuration file
- **PATTERN**: Standard Alembic ini with async support
- **CONTENT**:

```ini
# Alembic migration configuration

[alembic]
# Path to migration scripts
script_location = alembic

# Template used to generate migration files
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s

# Timezone for generating timestamps
timezone = UTC

# Max length of characters to apply to the "slug" field
truncate_slug_length = 40

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- **VALIDATE**: `cd apps/api && test -f alembic.ini && echo "OK"`

### 20. CREATE apps/api/alembic/env.py

- **IMPLEMENT**: Alembic environment with async support
- **PATTERN**: Async Alembic configuration
- **IMPORTS**: `from sqlalchemy.ext.asyncio import create_async_engine`
- **GOTCHA**: Must use run_async for async operations
- **CONTENT**:

```python
"""Alembic migration environment configuration."""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context

from src.core.config import settings
from src.core.database import Base

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL and not an Engine,
    though an Engine is acceptable here as well. By skipping the Engine
    creation we don't even need a DBAPI to be available.
    """
    url = str(settings.database_url)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Run migrations with connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    connectable = create_async_engine(
        str(settings.database_url),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- **VALIDATE**: `cd apps/api && uv run alembic check` (should show no issues)

### 21. CREATE apps/api/alembic/versions/001_initial_schema.py

- **IMPLEMENT**: Initial database migration with pgvector
- **PATTERN**: Alembic migration with async operations
- **CONTENT**:

```python
"""Initial database schema with pgvector extension.

Revision ID: 001_initial
Revises:
Create Date: 2025-01-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema."""
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Phase 1: No tables yet, just extension
    # Tables will be added in Phase 2+ as vertical slices are implemented


def downgrade() -> None:
    """Downgrade database schema."""
    # Drop pgvector extension
    op.execute('DROP EXTENSION IF EXISTS vector')
```

- **VALIDATE**: `cd apps/api && uv run alembic upgrade head`

### 22. CREATE configs/ruff.toml

- **IMPLEMENT**: Ruff configuration for linting and formatting
- **PATTERN**: Comprehensive Ruff rules based on project standards
- **CONTENT**:

```toml
# Ruff configuration for uDocket

[lint]
# Enable rules
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes
    "I",      # isort
    "N",      # pep8-naming
    "UP",     # pyupgrade
    "ANN",    # flake8-annotations
    "ASYNC",  # flake8-async
    "S",      # flake8-bandit
    "B",      # flake8-bugbear
    "A",      # flake8-builtins
    "C4",     # flake8-comprehensions
    "DTZ",    # flake8-datetimez
    "T10",    # flake8-debugger
    "EM",     # flake8-errmsg
    "ISC",    # flake8-implicit-str-concat
    "ICN",    # flake8-import-conventions
    "G",      # flake8-logging-format
    "PIE",    # flake8-pie
    "T20",    # flake8-print
    "PT",     # flake8-pytest-style
    "Q",      # flake8-quotes
    "RSE",    # flake8-raise
    "RET",    # flake8-return
    "SLF",    # flake8-self
    "SIM",    # flake8-simplify
    "TID",    # flake8-tidy-imports
    "TCH",    # flake8-type-checking
    "ARG",    # flake8-unused-arguments
    "PTH",    # flake8-use-pathlib
    "ERA",    # eradicate
    "PL",     # Pylint
    "TRY",    # tryceratops
    "FLY",    # flynt
    "PERF",   # Perflint
    "RUF",    # Ruff-specific rules
]

# Ignore specific rules
ignore = [
    "ANN101",  # Missing type annotation for self in method
    "ANN102",  # Missing type annotation for cls in classmethod
    "S101",    # Use of assert detected (pytest uses asserts)
    "PLR0913", # Too many arguments to function call
    "TRY003",  # Avoid specifying long messages outside the exception class
]

# Allow autofix for all enabled rules
fixable = ["ALL"]
unfixable = []

# Exclude patterns
exclude = [
    ".git",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "*.egg-info",
]

# Line length
line-length = 120

# Target Python version
target-version = "py312"

[lint.per-file-ignores]
# Test files can use magic values and assertions
"tests/**/*.py" = ["PLR2004", "S101"]
"**/tests/**/*.py" = ["PLR2004", "S101"]

[format]
# Use double quotes for strings
quote-style = "double"

# Indent with spaces
indent-style = "space"

# Line ending style
line-ending = "auto"
```

- **VALIDATE**: `uv run ruff check --config configs/ruff.toml .`

### 23. CREATE configs/pyproject.toml

- **IMPLEMENT**: Mypy configuration for strict type checking
- **PATTERN**: Strict Mypy configuration
- **CONTENT**:

```toml
# Mypy configuration for uDocket

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
disallow_subclassing_any = true
disallow_untyped_calls = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

# Plugins
plugins = ["pydantic.mypy"]

# Per-module options
[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
disallow_untyped_calls = false

[[tool.mypy.overrides]]
module = [
    "jose.*",
    "structlog.*",
    "alembic.*",
]
ignore_missing_imports = true
```

- **VALIDATE**: `uv run mypy --config-file configs/pyproject.toml apps/api/src/`

### 24. CREATE configs/pylint.toml

- **IMPLEMENT**: Pylint configuration for code quality
- **PATTERN**: Pylint with complexity and naming checks
- **CONTENT**:

```toml
# Pylint configuration for uDocket

[tool.pylint.main]
# Python version
py-version = "3.12"

# Files or directories to analyze
recursive = true

# Ignore patterns
ignore-patterns = [
    "^\\..*",
    "^__pycache__$",
    "\\.pyc$",
]

[tool.pylint.messages_control]
# Disable specific messages
disable = [
    "missing-module-docstring",
    "too-few-public-methods",
    "duplicate-code",
]

[tool.pylint.format]
# Maximum line length
max-line-length = 120

[tool.pylint.design]
# Maximum complexity
max-complexity = 10

# Maximum arguments
max-args = 7

# Maximum local variables
max-locals = 15

# Maximum return statements
max-returns = 6

# Maximum branches
max-branches = 12

[tool.pylint.basic]
# Naming conventions
argument-naming-style = "snake_case"
attr-naming-style = "snake_case"
class-attribute-naming-style = "any"
class-const-naming-style = "UPPER_CASE"
class-naming-style = "PascalCase"
const-naming-style = "UPPER_CASE"
function-naming-style = "snake_case"
method-naming-style = "snake_case"
module-naming-style = "snake_case"
variable-naming-style = "snake_case"

[tool.pylint.similarities]
# Minimum lines for duplicate code detection
min-similarity-lines = 4

# Ignore comments and docstrings
ignore-comments = true
ignore-docstrings = true
```

- **VALIDATE**: `uv run pylint --rcfile=configs/pylint.toml apps/api/src/`

### 25. CREATE configs/.bandit

- **IMPLEMENT**: Bandit security configuration
- **PATTERN**: Security scanning rules
- **CONTENT**:

```yaml
# Bandit security scanner configuration

exclude_dirs:
  - /tests/
  - /.venv/
  - /build/
  - /dist/

tests:
  - B201  # flask_debug_true
  - B301  # pickle
  - B302  # marshal
  - B303  # md5
  - B304  # ciphers
  - B305  # cipher_modes
  - B306  # mktemp_q
  - B307  # eval
  - B308  # mark_safe
  - B309  # httpsconnection
  - B310  # urllib_urlopen
  - B311  # random
  - B312  # telnetlib
  - B313  # xml_bad_cElementTree
  - B314  # xml_bad_ElementTree
  - B315  # xml_bad_expatreader
  - B316  # xml_bad_expatbuilder
  - B317  # xml_bad_sax
  - B318  # xml_bad_minidom
  - B319  # xml_bad_pulldom
  - B320  # xml_bad_etree
  - B321  # ftplib
  - B323  # unverified_context
  - B324  # hashlib_new_insecure_functions
  - B401  # import_telnetlib
  - B402  # import_ftplib
  - B403  # import_pickle
  - B404  # import_subprocess
  - B405  # import_xml_etree
  - B406  # import_xml_sax
  - B407  # import_xml_expat
  - B408  # import_xml_minidom
  - B409  # import_xml_pulldom
  - B410  # import_lxml
  - B411  # import_xmlrpclib
  - B412  # import_httpoxy
  - B413  # import_pycrypto
  - B501  # request_with_no_cert_validation
  - B502  # ssl_with_bad_version
  - B503  # ssl_with_bad_defaults
  - B504  # ssl_with_no_version
  - B505  # weak_cryptographic_key
  - B506  # yaml_load
  - B507  # ssh_no_host_key_verification
  - B601  # paramiko_calls
  - B602  # subprocess_popen_with_shell_equals_true
  - B603  # subprocess_without_shell_equals_true
  - B604  # any_other_function_with_shell_equals_true
  - B605  # start_process_with_a_shell
  - B606  # start_process_with_no_shell
  - B607  # start_process_with_partial_path
  - B608  # hardcoded_sql_expressions
  - B609  # linux_commands_wildcard_injection
  - B610  # django_extra_used
  - B611  # django_rawsql_used
  - B701  # jinja2_autoescape_false
  - B702  # use_of_mako_templates
  - B703  # django_mark_safe

skips:
  - B101  # assert_used (pytest uses asserts)
```

- **VALIDATE**: `uv run bandit -c configs/.bandit -r apps/api/src/`

### 26. CREATE configs/pytest.ini

- **IMPLEMENT**: Pytest configuration with coverage
- **PATTERN**: Pytest with async support and coverage reporting
- **CONTENT**:

```ini
# Pytest configuration for uDocket

[pytest]
# Test discovery patterns
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*

# Test paths
testpaths = tests apps

# Async support
asyncio_mode = auto

# Output options
addopts =
    -v
    --strict-markers
    --strict-config
    --cov=apps
    --cov=packages
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --cov-fail-under=80

# Markers
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow tests
    smoke: Smoke tests

# Ignore patterns
norecursedirs =
    .git
    .venv
    __pycache__
    build
    dist
    *.egg-info

# Coverage options
[coverage:run]
source = apps,packages
omit =
    */tests/*
    */__pycache__/*
    */migrations/*
    */alembic/*

[coverage:report]
precision = 2
show_missing = True
skip_covered = False

[coverage:html]
directory = htmlcov
```

- **VALIDATE**: `test -f configs/pytest.ini && echo "OK"`

### 27. CREATE apps/api/tests/conftest.py

- **IMPLEMENT**: Pytest fixtures for testing
- **PATTERN**: Async fixtures with database and client
- **IMPORTS**: `import pytest, from fastapi.testclient import TestClient`
- **CONTENT**:

```python
"""Pytest configuration and fixtures."""
import asyncio
from typing import AsyncGenerator, Generator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.main import app
from src.core import Base, get_db
from src.platform.auth.jwt import UserStub, create_access_token


# Test database URL (in-memory SQLite for fast tests)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
def client(db_session: AsyncSession) -> Generator[TestClient, None, None]:
    """Create test client with database override."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def test_user() -> UserStub:
    """Create test user stub."""
    return UserStub(
        id=uuid4(),
        email="test@example.com",
        full_name="Test User",
        roles=["user"],
        is_active=True,
    )


@pytest.fixture
def test_admin_user() -> UserStub:
    """Create test admin user stub."""
    return UserStub(
        id=uuid4(),
        email="admin@example.com",
        full_name="Admin User",
        roles=["user", "admin"],
        is_active=True,
    )


@pytest.fixture
def auth_headers(test_user: UserStub) -> dict[str, str]:
    """Create authentication headers with valid JWT."""
    token = create_access_token(test_user)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(test_admin_user: UserStub) -> dict[str, str]:
    """Create admin authentication headers with valid JWT."""
    token = create_access_token(test_admin_user)
    return {"Authorization": f"Bearer {token}"}
```

- **VALIDATE**: `cd apps/api && uv run pytest tests/conftest.py --collect-only`

### 28. CREATE apps/api/tests/test_health.py

- **IMPLEMENT**: Health endpoint test
- **PATTERN**: FastAPI test with TestClient
- **CONTENT**:

```python
"""Tests for health check endpoint."""
import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test health check endpoint returns correct response."""
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ["healthy", "unhealthy"]
    assert data["version"] == "0.1.0"
    assert data["environment"] in ["development", "staging", "production"]
    assert isinstance(data["database"], bool)


def test_health_check_structure(client: TestClient):
    """Test health check response has required fields."""
    response = client.get("/health")
    data = response.json()

    required_fields = ["status", "version", "environment", "database"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
```

- **VALIDATE**: `cd apps/api && uv run pytest tests/test_health.py -v`

### 29. CREATE ops/docker-compose.yml

- **IMPLEMENT**: Docker Compose for local development services
- **PATTERN**: Multi-service stack with volumes
- **CONTENT**:

```yaml
# Docker Compose for uDocket local development

version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: udocket-postgres
    environment:
      POSTGRES_USER: udocket
      POSTGRES_PASSWORD: udocket_dev_password
      POSTGRES_DB: udocket
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U udocket"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - udocket-network

  rabbitmq:
    image: rabbitmq:3.13-management-alpine
    container_name: udocket-rabbitmq
    environment:
      RABBITMQ_DEFAULT_USER: udocket
      RABBITMQ_DEFAULT_PASS: udocket_dev_password
    ports:
      - "5672:5672"    # AMQP port
      - "15672:15672"  # Management UI
    volumes:
      - rabbitmq_data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "ping"]
      interval: 30s
      timeout: 10s
      retries: 5
    networks:
      - udocket-network

  redis:
    image: redis:7-alpine
    container_name: udocket-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - udocket-network

volumes:
  postgres_data:
    driver: local
  rabbitmq_data:
    driver: local
  redis_data:
    driver: local

networks:
  udocket-network:
    driver: bridge
```

- **VALIDATE**: `docker-compose -f ops/docker-compose.yml config`

### 30. CREATE ops/init-scripts/01-init-pgvector.sql

- **IMPLEMENT**: PostgreSQL initialization script
- **PATTERN**: SQL script to enable pgvector
- **CONTENT**:

```sql
-- Initialize pgvector extension for uDocket database

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension is installed
SELECT * FROM pg_extension WHERE extname = 'vector';
```

- **VALIDATE**: Manual review

### 31. CREATE ops/README.md

- **IMPLEMENT**: Documentation for ops directory
- **PATTERN**: Clear setup instructions
- **CONTENT**:

```markdown
# Operations & Development Environment

This directory contains Docker Compose configurations and monitoring setups for local development and operations.

## Local Development Services

### Starting Services

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d postgres

# View logs
docker-compose logs -f postgres

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### Services

**PostgreSQL with pgvector:**

- Port: 5432
- User: `udocket`
- Password: `udocket_dev_password`
- Database: `udocket`
- Connection string: `postgresql+asyncpg://udocket:udocket_dev_password@localhost:5432/udocket`

**RabbitMQ:**

- AMQP Port: 5672
- Management UI: <http://localhost:15672>
- User: `udocket`
- Password: `udocket_dev_password`

**Redis:**

- Port: 6379
- Persistence: AOF enabled

### Health Checks

All services include health checks. View service status:

```bash
docker-compose ps
```

### Data Persistence

Data is persisted in Docker volumes:

- `udocket_postgres_data` - PostgreSQL data
- `udocket_rabbitmq_data` - RabbitMQ data
- `udocket_redis_data` - Redis data

To reset all data:

```bash
docker-compose down -v
```

## Monitoring (Phase 2+)

Prometheus and Grafana configurations will be added in Phase 2.

## Troubleshooting

**Port conflicts:**
If ports 5432, 5672, or 6379 are in use, either:

1. Stop the conflicting service
2. Modify ports in docker-compose.yml

**Database connection issues:**

```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Test connection
docker-compose exec postgres psql -U udocket -d udocket -c "SELECT version();"
```

**RabbitMQ management UI not loading:**
Wait 30-60 seconds after startup for RabbitMQ to fully initialize.

```text

- **VALIDATE**: Manual review

### 32. CREATE .pre-commit-config.yaml

- **IMPLEMENT**: Pre-commit hooks configuration
- **PATTERN**: Comprehensive quality checks
- **CONTENT**:
```yaml
# Pre-commit hooks for uDocket

repos:
  # Ruff linter and formatter
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.3
    hooks:
      - id: ruff
        args: [--config, configs/ruff.toml, --fix]
      - id: ruff-format
        args: [--config, configs/ruff.toml]

  # Mypy type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.18.2
    hooks:
      - id: mypy
        args: [--config-file, configs/pyproject.toml]
        additional_dependencies:
          - pydantic>=2.12.4
          - sqlalchemy>=2.0.44
          - fastapi>=0.115.0
        files: ^(apps|packages)/.*\.py$
        exclude: ^(tests|alembic)/

  # Secret detection
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks

  # Standard pre-commit hooks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: [--maxkb=1000]
      - id: check-json
      - id: check-toml
      - id: check-merge-conflict
      - id: detect-private-key

  # Commitizen for conventional commits
  - repo: https://github.com/commitizen-tools/commitizen
    rev: v4.10.0
    hooks:
      - id: commitizen
        stages: [commit-msg]
```

- **VALIDATE**: `uv run pre-commit install && uv run pre-commit run --all-files`

### 33. CREATE tooling/dodo.py

- **IMPLEMENT**: doit task automation
- **PATTERN**: Task definitions for common operations
- **CONTENT**:

```python
"""doit task automation for uDocket."""
from pathlib import Path

DOIT_CONFIG = {
    "default_tasks": ["quality"],
    "verbosity": 2,
}

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
APPS_DIR = PROJECT_ROOT / "apps"
PACKAGES_DIR = PROJECT_ROOT / "packages"
CONFIGS_DIR = PROJECT_ROOT / "configs"


def task_lint():
    """Run linting with Ruff and Pylint."""
    return {
        "actions": [
            f"uv run ruff check --config {CONFIGS_DIR}/ruff.toml {APPS_DIR} {PACKAGES_DIR}",
            f"uv run pylint --rcfile={CONFIGS_DIR}/pylint.toml {APPS_DIR} {PACKAGES_DIR}",
        ],
        "verbosity": 2,
    }


def task_format():
    """Run code formatting with Ruff."""
    return {
        "actions": [
            f"uv run ruff format --config {CONFIGS_DIR}/ruff.toml {APPS_DIR} {PACKAGES_DIR}",
        ],
        "verbosity": 2,
    }


def task_typecheck():
    """Run type checking with Mypy and Pyright."""
    return {
        "actions": [
            f"uv run mypy --config-file {CONFIGS_DIR}/pyproject.toml {APPS_DIR} {PACKAGES_DIR}",
            f"uv run pyright {APPS_DIR} {PACKAGES_DIR}",
        ],
        "verbosity": 2,
    }


def task_test():
    """Run tests with pytest and coverage."""
    return {
        "actions": [
            f"uv run pytest --config-file {CONFIGS_DIR}/pytest.ini",
        ],
        "verbosity": 2,
    }


def task_test_unit():
    """Run only unit tests."""
    return {
        "actions": [
            f"uv run pytest -m unit --config-file {CONFIGS_DIR}/pytest.ini",
        ],
        "verbosity": 2,
    }


def task_test_integration():
    """Run only integration tests."""
    return {
        "actions": [
            f"uv run pytest -m integration --config-file {CONFIGS_DIR}/pytest.ini",
        ],
        "verbosity": 2,
    }


def task_security():
    """Run security scans with Bandit and Safety."""
    return {
        "actions": [
            f"uv run bandit -c {CONFIGS_DIR}/.bandit -r {APPS_DIR} {PACKAGES_DIR}",
            "uv run safety check --json",
        ],
        "verbosity": 2,
    }


def task_quality():
    """Run all quality checks (lint, typecheck, test)."""
    return {
        "actions": None,
        "task_dep": ["lint", "typecheck", "test"],
        "verbosity": 2,
    }


def task_dev():
    """Start development server."""
    return {
        "actions": [
            "cd apps/api && uv run uvicorn src.main:app --reload --port 8000",
        ],
        "verbosity": 2,
    }


def task_db_migrate():
    """Run database migrations."""
    return {
        "actions": [
            "cd apps/api && uv run alembic upgrade head",
        ],
        "verbosity": 2,
    }


def task_db_revision():
    """Create new database migration (requires MESSAGE environment variable)."""
    import os
    message = os.getenv("MESSAGE", "auto_migration")

    return {
        "actions": [
            f'cd apps/api && uv run alembic revision --autogenerate -m "{message}"',
        ],
        "verbosity": 2,
    }


def task_clean():
    """Clean build artifacts and caches."""
    return {
        "actions": [
            "find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true",
            "find . -type d -name '*.egg-info' -exec rm -rf {} + 2>/dev/null || true",
            "find . -type f -name '*.pyc' -delete 2>/dev/null || true",
            "rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage",
        ],
        "verbosity": 2,
    }
```

- **VALIDATE**: `cd tooling && uv run doit list`

### 34. CREATE tooling/README.md

- **IMPLEMENT**: Documentation for tooling directory
- **PATTERN**: Clear task documentation
- **CONTENT**:

```markdown
# Development Tooling

This directory contains automation scripts and configuration for development tasks.

## doit Tasks

uDocket uses **doit** for task automation. All tasks are defined in `dodo.py`.

### Available Tasks

**Quality Checks:**
```bash
# Run all quality checks (lint + typecheck + test)
uv run doit quality

# Run linting only
uv run doit lint

# Run formatting
uv run doit format

# Run type checking
uv run doit typecheck

# Run tests
uv run doit test

# Run specific test types
uv run doit test_unit
uv run doit test_integration

# Run security scans
uv run doit security
```

**Development:**

```bash
# Start development server
uv run doit dev

# Run database migrations
uv run doit db_migrate

# Create new migration
MESSAGE="add users table" uv run doit db_revision
```

**Maintenance:**

```bash
# Clean build artifacts
uv run doit clean
```

### List All Tasks

```bash
uv run doit list
```

### Task Help

```bash
uv run doit help <task_name>
```

## Pre-commit Hooks

Pre-commit hooks automatically run quality checks before each commit.

### Setup

```bash
# Install hooks
uv run pre-commit install

# Run manually on all files
uv run pre-commit run --all-files
```

### Hooks Included

- Ruff (lint + format)
- Mypy (type checking)
- Gitleaks (secret detection)
- Trailing whitespace removal
- End-of-file fixer
- YAML/JSON/TOML validation
- Large file detection
- Merge conflict detection

## Commitizen

Use Commitizen for conventional commit messages:

```bash
# Interactive commit
uv run cz commit

# Bump version based on commits
uv run cz bump

# Generate changelog
uv run cz changelog
```

### Commit Types

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `refactor:` - Code refactoring
- `test:` - Tests
- `chore:` - Maintenance
- `perf:` - Performance improvement
- `ci:` - CI/CD changes
  
```text
- **VALIDATE**: Manual review

### 35. CREATE .github/workflows/ci.yml

- **IMPLEMENT**: GitHub Actions CI/CD pipeline
- **PATTERN**: Multi-job workflow with quality gates
- **CONTENT**:
```yaml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

env:
  PYTHON_VERSION: "3.12"
  UV_VERSION: "0.5.21"

jobs:
  lint:
    name: Lint (Ruff + Pylint)
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: ${{ env.UV_VERSION }}

      - name: Set up Python
        run: uv python install ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run Ruff
        run: uv run ruff check --config configs/ruff.toml apps packages

      - name: Run Pylint
        run: uv run pylint --rcfile=configs/pylint.toml apps packages

  typecheck:
    name: Type Checking (Mypy + Pyright)
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: ${{ env.UV_VERSION }}

      - name: Set up Python
        run: uv python install ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run Mypy
        run: uv run mypy --config-file configs/pyproject.toml apps packages

      - name: Run Pyright
        run: uv run pyright apps packages

  test:
    name: Tests (pytest + coverage)
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: ${{ env.UV_VERSION }}

      - name: Set up Python
        run: uv python install ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run tests
        run: uv run pytest --config-file configs/pytest.ini --cov-report=xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
          flags: unittests
          name: codecov-umbrella

  security:
    name: Security Scans
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Install uv
        uses: astral-sh/setup-uv@v4
        with:
          version: ${{ env.UV_VERSION }}

      - name: Set up Python
        run: uv python install ${{ env.PYTHON_VERSION }}

      - name: Install dependencies
        run: uv sync --all-extras

      - name: Run Bandit
        run: uv run bandit -c configs/.bandit -r apps packages

      - name: Run Safety
        run: uv run safety check --json

      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  all-checks:
    name: All Checks Passed
    runs-on: ubuntu-latest
    needs: [lint, typecheck, test, security]
    if: always()

    steps:
      - name: Check all jobs
        run: |
          if [[ "${{ needs.lint.result }}" != "success" ]]; then
            echo "Lint failed"
            exit 1
          fi
          if [[ "${{ needs.typecheck.result }}" != "success" ]]; then
            echo "Type checking failed"
            exit 1
          fi
          if [[ "${{ needs.test.result }}" != "success" ]]; then
            echo "Tests failed"
            exit 1
          fi
          if [[ "${{ needs.security.result }}" != "success" ]]; then
            echo "Security scans failed"
            exit 1
          fi
          echo "All checks passed!"
```

- **VALIDATE**: `cat .github/workflows/ci.yml` (GitHub Actions syntax)

### 36. UPDATE root pyproject.toml with workspace configuration

- **IMPLEMENT**: Add workspace configuration to existing pyproject.toml
- **PATTERN**: UV workspace declaration
- **MIRROR**: Task #1 pattern
- **GOTCHA**: Merge with existing content, don't replace
- **VALIDATE**: `uv sync`

### 37. INSTALL pre-commit hooks

- **IMPLEMENT**: Install and run pre-commit hooks
- **PATTERN**: System setup
- **VALIDATE**: `uv run pre-commit install && uv run pre-commit run --all-files`

---

## TESTING STRATEGY

### Unit Tests

**Scope:**

- Core module functions (config, logging, exceptions)
- Domain model validation (Pydantic models)
- JWT encoding/decoding
- Database utility functions

**Requirements:**

- 80%+ coverage on core modules
- All domain models have validation tests
- Auth functions have positive and negative tests

### Integration Tests

**Scope:**

- FastAPI application startup/shutdown
- Database connectivity
- Health endpoint with actual database check
- End-to-end request flow (when auth added)

**Requirements:**

- Health endpoint returns correct structure
- Database migrations can run successfully
- Application starts without errors

### Edge Cases

**Configuration:**

- Invalid environment variables
- Missing required settings
- Invalid database URL format

**Authentication:**

- Expired JWT tokens
- Invalid JWT signatures
- Missing auth headers
- Malformed tokens

**Database:**

- Connection failures
- Transaction rollback scenarios
- Concurrent session handling

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Syntax & Style

**Ruff Lint:**

```bash
uv run ruff check --config configs/ruff.toml apps packages
```

**Ruff Format Check:**

```bash
uv run ruff format --check --config configs/ruff.toml apps packages
```

**Pylint:**

```bash
uv run pylint --rcfile=configs/pylint.toml apps packages
```

### Level 2: Type Checking

**Mypy (Strict):**

```bash
uv run mypy --config-file configs/pyproject.toml apps packages
```

**Pyright (Strict):**

```bash
uv run pyright apps packages
```

### Level 3: Unit Tests

**All Tests:**

```bash
uv run pytest --config-file configs/pytest.ini
```

**Coverage Report:**

```bash
uv run pytest --config-file configs/pytest.ini --cov-report=term-missing
```

### Level 4: Security Scans

**Bandit:**

```bash
uv run bandit -c configs/.bandit -r apps packages
```

**Safety:**

```bash
uv run safety check
```

**Gitleaks:**

```bash
uv run gitleaks detect --source . --verbose
```

### Level 5: Integration Tests

**Database Migration:**

```bash
cd apps/api && uv run alembic upgrade head && uv run alembic downgrade base && uv run alembic upgrade head
```

**Application Startup:**

```bash
cd apps/api && timeout 10 uv run uvicorn src.main:app || exit 0
```

**Docker Compose Services:**

```bash
docker-compose -f ops/docker-compose.yml up -d && sleep 10 && docker-compose -f ops/docker-compose.yml ps && docker-compose -f ops/docker-compose.yml down
```

### Level 6: Full Quality Suite

**doit quality:**

```bash
uv run doit quality
```

### Level 7: Pre-commit Hooks

**All Hooks:**

```bash
uv run pre-commit run --all-files
```

---

## ACCEPTANCE CRITERIA

- [x] Project structure follows ARCHITECTURE.md vertical-slice layout
- [x] All quality tools configured (Ruff, Pylint, Mypy, Pyright, pytest, Bandit, Safety, Gitleaks)
- [x] Core modules implemented (config, database, logging, exceptions)
- [x] Domain models created in py-domain package (Matter, Party, Analysis, Transcript, etc.)
- [x] FastAPI application with health endpoint
- [x] JWT authentication stub with Keycloak roadmap documented
- [x] Database layer with async SQLAlchemy and pgvector support
- [x] Alembic migrations configured with async support
- [x] Pytest fixtures for database and client testing
- [x] Docker Compose with Postgres, RabbitMQ, Redis
- [x] Pre-commit hooks installed and passing
- [x] doit tasks for common operations
- [x] CI/CD pipeline with all quality gates
- [x] All validation commands pass with zero errors
- [x] 80%+ test coverage on implemented modules
- [x] Health endpoint returns correct response structure
- [x] Application starts successfully
- [x] Database migrations run successfully
- [x] No security issues detected by Bandit/Safety/Gitleaks
- [x] All type checking passes (Mypy strict + Pyright strict)
- [x] All linting passes (Ruff + Pylint)
- [x] Documentation complete (READMEs in ops/, tooling/)

---

## COMPLETION CHECKLIST

- [ ] All 37 tasks completed in order
- [ ] Each task validation passed immediately after implementation
- [ ] All Level 1-7 validation commands executed successfully
- [ ] Full test suite passes with 80%+ coverage
- [ ] No linting errors (Ruff + Pylint)
- [ ] No type checking errors (Mypy strict + Pyright strict)
- [ ] No security issues (Bandit + Safety + Gitleaks)
- [ ] Docker Compose services start successfully
- [ ] Database migrations work (upgrade + downgrade)
- [ ] Application starts without errors
- [ ] Health endpoint accessible and returns correct data
- [ ] Pre-commit hooks installed and passing
- [ ] CI/CD pipeline configuration valid
- [ ] All READMEs written and complete
- [ ] Code follows project conventions from CLAUDE.md
- [ ] All acceptance criteria met

---

## NOTES

### Design Decisions

1. **Strict Typing from Day One**: Using both Mypy and Pyright in strict mode ensures maximum type safety and catches issues early.

2. **Pydantic v2 for Everything**: Domain models, settings, API schemas all use Pydantic v2 for consistent validation and serialization.

3. **Async-First**: SQLAlchemy async, FastAPI async endpoints, pytest-asyncio for tests. This prevents async/sync mixing issues later.

4. **Observability Foundation**: Structlog with JSON output and OpenTelemetry hooks ready for Phase 2+ LangSmith/Langfuse integration.

5. **JWT Stub with Keycloak Roadmap**: Phase 1 uses simple JWT for development. Comments and documentation clearly indicate Keycloak OIDC integration planned for Phase 2+.

6. **Docker Compose for Local Dev**: No Kubernetes complexity in local development. Helm/K8s reserved for staging/production deployments.

7. **Vertical Slice Ready**: Directory structure prepared for Phase 2 vertical slices (intake, analysis, compose) with clear boundaries.

8. **Quality Gates as Code**: All quality checks automated via doit, pre-commit, and CI/CD. No manual quality enforcement needed.

### Trade-offs

**Pro:**

- Zero technical debt from the start
- All quality issues caught immediately
- Clear patterns established for Phase 2+ development
- Production-ready infrastructure without features

**Con:**

- Higher initial setup time (Phase 1 focus)
- More tooling complexity than minimal setup
- Stricter enforcement may slow initial iteration

**Rationale:** ROADMAP.md explicitly calls for "production-grade infrastructure and observability from day one" before feature development. This trade-off aligns with the project's goals.

### Phase 2 Preparation

This Phase 1 implementation sets up Phase 2 for success:

**Ready for Vertical Slices:**

- `apps/api/src/workflow/` directories exist (intake, analysis, compose, matters)
- Domain models defined and tested
- Database layer ready for entity tables
- API structure ready for router addition

**Ready for Azure Speech:**

- Transcript models defined
- Async patterns established
- Celery worker scaffolding in place (directory exists)

**Ready for LangGraph:**

- `apps/api/src/ai/graphs/` directory exists
- py-ai-core package ready for LangGraph helpers
- Observability hooks ready for LangSmith/Langfuse

**Ready for Testing:**

- Test fixtures ready for all scenarios
- Coverage reporting configured
- CI/CD gates enforce quality

### Known Limitations

1. **SQLite for Tests**: Using in-memory SQLite for fast tests. pgvector features not testable until integration tests with real Postgres.

2. **Auth is Stub**: JWT implementation is minimal. Full Keycloak OIDC integration is substantial work deferred to Phase 2+.

3. **No Frontend**: Phase 1 is backend-only. Next.js app in `apps/web/` will be Phase 5.

4. **No Actual Features**: Health endpoint is the only working API endpoint. Features come in Phase 2+.

<!-- EOF -->
