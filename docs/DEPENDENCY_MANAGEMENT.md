# Dependency Management Guide

This document describes the dependency management strategy for the uDocket monorepo.

## Overview

uDocket uses a **strict dependency scoping** approach where:

1. Each package/app declares ALL its dependencies locally
2. Runtime and dev dependencies are clearly separated
3. The root workspace only contains dev dependencies
4. Automated validation ensures compliance

## Dependency Structure

### Root Workspace (`pyproject.toml`)

The root workspace should contain:
- **NO runtime dependencies** - all runtime deps belong in individual packages/apps
- **ONLY dev dependencies** - tools used for development, testing, linting, etc.

```toml
[project]
dependencies = []  # Always empty!

[tool.uv]
dev-dependencies = [
    # Testing
    "pytest>=8.4.2,<9.0.0",
    "pytest-cov>=7.0.0,<8.0.0",

    # Type checking
    "mypy>=1.18.2,<2.0.0",
    "pyright>=1.1.407,<2.0.0",

    # Linting
    "ruff>=0.14.3,<0.15.0",
    # ... etc
]
```

### Package-Level (`packages/*/pyproject.toml`)

Each package declares its own dependencies:

```toml
[project]
name = "udocket-domain"
dependencies = [
    "pydantic>=2.12.4,<3.0.0",
]

[tool.uv]
dev-dependencies = [
    # Inherits from root workspace
    # Add package-specific dev deps here if needed
]
```

### App-Level (`apps/*/pyproject.toml`)

Each app declares all dependencies it uses:

```toml
[project]
name = "udocket-api"
dependencies = [
    # Web framework
    "fastapi>=0.121.3,<0.122.0",
    "uvicorn[standard]>=0.32.0,<0.33.0",

    # Database
    "sqlalchemy>=2.0.44,<3.0.0",
    "asyncpg>=0.30.0,<0.31.0",

    # Workspace packages
    "udocket-domain",
    "udocket-ai-core",
]

[tool.uv.sources]
udocket-domain = { workspace = true }
udocket-ai-core = { workspace = true }
```

## Dependency Categories

### Runtime Dependencies (`[project.dependencies]`)

Use for:
- Application frameworks (FastAPI, Celery)
- Database drivers (asyncpg, SQLAlchemy)
- Core libraries (Pydantic, structlog)
- AI/ML libraries (LangGraph, LangSmith)
- Workspace packages (`udocket-domain`, `udocket-ai-core`, etc.)

### Dev Dependencies (`[tool.uv.dev-dependencies]`)

Use for:
- Testing tools (pytest, hypothesis)
- Type checkers (mypy, pyright)
- Linters/formatters (ruff, pylint, prettier)
- Security scanners (bandit, gitleaks); Safety is consumed by CI via `uv run safety scan --policy-file configs/safety-policy.yml` with the repository secret and is not part of the workspace dev dependencies.
- Build tools (doit, pre-commit)
- Version management (commitizen, semantic-release)

## Validation

### Automated Dependency Checker

Run the dependency checker manually:

```bash
uv run python tooling/check_dependencies.py
```

The checker validates:

1. ✅ Each package has all required dependencies listed
2. ✅ Runtime vs dev dependencies are properly separated
3. ✅ Root workspace has no runtime dependencies
4. ✅ No missing dependencies based on actual imports
5. ✅ Workspace package references are correct

### Pre-commit Hook

The dependency checker runs automatically on commit:

```bash
# Install pre-commit hooks (one-time)
uv run pre-commit install --config configs/pre-commit-config.yaml

# Run manually
uv run pre-commit run --config configs/pre-commit-config.yaml check-dependencies --all-files
```

### CI/CD Pipeline

GitHub Actions runs dependency validation on every PR:

- **Job**: `dependency-check`
- **Runs**: Before all other jobs
- **Blocks**: PR merge if dependencies are misconfigured

See: [`.github/workflows/quality.yml`](.github/workflows/quality.yml)

## Common Patterns

### Adding a New Dependency

1. **Identify where it's needed**:
   - Runtime dependency? → Add to the package/app that uses it
   - Dev dependency? → Add to root workspace

2. **Add with version constraints**:
   ```toml
   dependencies = [
       "new-package>=1.0.0,<2.0.0",
   ]
   ```

3. **Sync dependencies**:
   ```bash
   uv sync
   ```

4. **Verify**:
   ```bash
   uv run python tooling/check_dependencies.py
   ```

### Creating a New Package

1. Create the package directory structure
2. Add `pyproject.toml` with proper sections:
   ```toml
   [project]
   name = "my-package"
   version = "0.1.0"
   requires-python = ">=3.12"
   dependencies = [
       # Runtime dependencies only
   ]

   [tool.uv]
   dev-dependencies = [
       # Inherited from root
   ]

   [build-system]
   requires = ["hatchling"]
   build-backend = "hatchling.build"
   ```

3. Add to workspace members in root `pyproject.toml`:
   ```toml
   [tool.uv.workspace]
   members = [
       # ...
       "packages/my-package",
   ]
   ```

4. Run validation:
   ```bash
   uv sync
   uv run python tooling/check_dependencies.py
   ```

### Using Workspace Packages

When one workspace package depends on another:

```toml
[project]
dependencies = [
    "udocket-domain",  # Workspace package
]

[tool.uv.sources]
udocket-domain = { workspace = true }
```

## Version Constraints

Use **compatible release** constraints:

- ✅ `"package>=1.2.0,<2.0.0"` - Allow patches and minors, block majors
- ✅ `"package>=1.2.0,<1.3.0"` - Only allow patches
- ❌ `"package>=1.2.0"` - Too loose, could break on majors
- ❌ `"package==1.2.0"` - Too strict, prevents security patches

## Troubleshooting

### "Missing dependencies" Error

The checker found imports without corresponding dependencies:

```
udocket-api: Missing dependencies: some-package
  Add these to apps/api/pyproject.toml
```

**Solution**: Add the missing package to the correct `pyproject.toml`:

```toml
dependencies = [
    "some-package>=1.0.0,<2.0.0",
]
```

### "Dev dependencies in runtime section" Error

A development tool is listed in `[project.dependencies]`:

```
my-package: Dev dependencies in runtime section: pytest
  Move these to [tool.uv.dev-dependencies]
```

**Solution**: Move to the dev section:

```toml
[project]
dependencies = []  # Remove pytest from here

[tool.uv]
dev-dependencies = [
    # Inherited from root workspace
]
```

### "Runtime dependencies in root" Error

The root workspace has runtime dependencies:

```
Root workspace: Runtime dependencies should be in individual packages
```

**Solution**: Move dependencies to the package/app that actually uses them.

### Import Not Recognized

If you get a warning about unknown imports:

```
Warning: Unknown import 'mymodule' in my-package, assuming package 'mymodule'
```

This is informational. If it's:
- **External package**: Add it to dependencies
- **Internal module**: Update `IMPORT_TO_PACKAGE` in `check_dependencies.py`
- **Standard library**: Add to `STDLIB_MODULES` in `check_dependencies.py`

## Testing the Dependency Checker

The validation script has comprehensive tests:

```bash
# Run the test suite
uv run pytest tests/tooling/test_check_dependencies.py -v

# Run with coverage
uv run pytest tests/tooling/test_check_dependencies.py --cov=tooling --cov-report=term-missing
```

Tests cover:
- Package name extraction from version specs
- Import detection from Python files
- Missing dependency detection
- Dev vs runtime separation
- Root workspace validation
- Internal module filtering

## Files

- [`pyproject.toml`](../pyproject.toml) - Root workspace config
- [`tooling/check_dependencies.py`](../tooling/check_dependencies.py) - Validation script
- [`tests/tooling/test_check_dependencies.py`](../tests/tooling/test_check_dependencies.py) - Test suite
- [`configs/pre-commit-config.yaml`](../configs/pre-commit-config.yaml) - Pre-commit hooks
- [`.github/workflows/quality.yml`](../.github/workflows/quality.yml) - CI configuration

## Best Practices

1. ✅ **Always validate after adding dependencies**
   ```bash
   uv run python tooling/check_dependencies.py
   ```

2. ✅ **Use version constraints on all dependencies**
   - Prevents unexpected breaking changes
   - Makes dependency resolution faster
   - Documents compatibility

3. ✅ **Group related dependencies with comments**
   ```toml
   dependencies = [
       # Web framework
       "fastapi>=0.121.3,<0.122.0",
       "uvicorn[standard]>=0.32.0,<0.33.0",

       # Database
       "sqlalchemy>=2.0.44,<3.0.0",
   ]
   ```

4. ✅ **Keep each package self-contained**
   - If a package is removed, it shouldn't break others
   - Each package can be tested in isolation
   - Clear dependency boundaries

5. ✅ **Run tests after dependency changes**
   ```bash
   uv sync
   uv run pytest
   ```

6. ✅ **Document why unusual dependencies exist**
   ```toml
   dependencies = [
       # Needed for Azure Speech API integration (Phase 2)
       "azure-cognitiveservices-speech>=1.30.0,<2.0.0",
   ]
   ```

## Integration with uv

The `uv` tool handles:
- Dependency resolution across the workspace
- Lockfile generation (`uv.lock`)
- Virtual environment management
- Fast parallel installs

Commands:
```bash
# Install all dependencies
uv sync

# Install with extras
uv sync --all-extras

# Install dev dependencies
uv sync --dev

# Update dependencies
uv lock --upgrade-package package-name

# Add a dependency
uv add package-name

# Remove a dependency
uv remove package-name
```

## Summary

**Golden Rules**:
1. Root workspace = dev deps only
2. Each package = its own runtime deps
3. Use version constraints
4. Validate before committing
5. Keep packages self-contained

This approach ensures:
- ✅ Clean dependency boundaries
- ✅ Easy package removal
- ✅ Clear separation of concerns
- ✅ Prevention of dependency drift
- ✅ Fast CI/CD validation
