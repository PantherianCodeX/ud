# Code Quality Assurance Standards

This document defines the code quality standards, tool configurations, and policies for the uDocket project.

## Quality Philosophy

uDocket enforces **maximum strictness** across all quality tools. The goal is to catch errors early, maintain consistency, and ensure production-grade code quality from day one.

**Core Principles:**
1. Enable all checks by default
2. Disable only with documented justification
3. Minimize scope of any ignores
4. Prefer fixing over ignoring

## Tool Configuration

### Type Checking

#### Pyright (`pyrightconfig.json`)
- **Mode**: `typeCheckingMode: "strict"`
- **All strict inference enabled**: `strictListInference`, `strictDictionaryInference`, `strictSetInference`, `strictParameterNoneValue`
- **All report options enabled** except:
  - `reportMissingTypeStubs: false` - Third-party libraries may lack stubs
  - `reportImplicitStringConcatenation: false` - Not a correctness issue
  - `reportUnusedCallResult: false` - Many functions have side effects
  - `reportMissingSuperCall: false` - Not all classes require super().__init__()

#### Mypy (`configs/pyproject.toml`)
- **Mode**: `strict = true`
- **All disallow options enabled**: `disallow_untyped_defs`, `disallow_any_generics`, `disallow_subclassing_any`, etc.
- **All warn options enabled**: `warn_return_any`, `warn_unused_ignores`, `warn_unreachable`, etc.
- **Pydantic plugin enabled** with strict settings

### Linting

#### Ruff (`configs/ruff.toml`)
- **Rule Selection**: `select = ["ALL"]` - Every available rule enabled
- **Preview Mode**: Enabled for cutting-edge rules
- **Line Length**: 120 characters
- **Docstring Style**: Google convention

#### Pylint (`configs/pylint.toml`)
- **All Extensions Loaded**: Including `mccabe`, `typing`, `docparams`, etc.
- **All Messages Enabled**: `enable = "all"`
- **Complexity Limits**:
  - `max-complexity = 10`
  - `max-args = 7`
  - `max-branches = 12`
  - `max-statements = 50`

### Security

#### Bandit (`configs/.bandit`)
- **All Security Checks Enabled** (B201-B703)
- **Only Skip**: `B101` (assert_used) - Required for pytest

### Testing

#### Pytest (`configs/pytest.ini`)
- **Coverage Threshold**: 80% minimum (`--cov-fail-under=80`)
- **Strict Markers**: `--strict-markers`, `--strict-config`
- **Async Mode**: Auto-detection enabled

## Global Ignores with Justifications

### Ruff Global Ignores

| Rule | Justification |
|------|---------------|
| `COM812` | Conflicts with Ruff's own formatter |
| `ISC001` | Conflicts with Ruff's own formatter |
| `D100`, `D104` | Module/package docstrings handled via per-file ignores |
| `ANN101`, `ANN102` | `self`/`cls` types are obvious by definition; mypy/pyright handle better |
| `S101` | pytest requires assert statements for testing |
| `TRY003` | Detailed error messages improve debuggability |
| `DJ` | Django rules not applicable (FastAPI project) |
| `FIX002`, `TD002`, `TD003` | TODOs tracked externally in issue system |

### Pylint Global Ignores

| Rule | Justification |
|------|---------------|
| `line-too-long`, `bad-indentation`, `bad-continuation` | Formatting handled by Ruff |
| `too-few-public-methods` | Pydantic models are data classes |
| `no-self-argument`, `no-self-use` | Pydantic validators require these patterns |
| `redefined-outer-name` | pytest fixture injection pattern |
| `duplicate-code` | High false positive rate; enable for periodic scans |
| Docstring rules | Handled by Ruff with Google style |

### Mypy Third-Party Ignores

The following third-party libraries have `ignore_missing_imports = true`:
- `jwt`, `passlib`, `structlog`, `alembic`, `celery`, `rabbitmq`, `fastapi`, `uvicorn`

**Justification**: These libraries lack complete type stubs. We accept the tradeoff of reduced type safety for these imports.

## Test-Specific Relaxations

Tests have minimal relaxations to accommodate testing patterns while maintaining quality:

### Ruff Test Ignores

| Rule | Justification |
|------|---------------|
| `PLR2004` | Magic values in tests are often test fixtures/expected values |
| `D103` | Test functions are self-documenting via descriptive names |

### Mypy Test Relaxations

| Setting | Justification |
|---------|---------------|
| `disallow_untyped_defs = false` | Test functions use pytest fixtures with implicit types |
| `disallow_untyped_decorators = false` | pytest.mark decorators don't have complete type stubs |

## Migration File Ignores

Alembic migration files have specific ignores:

| Rule | Justification |
|------|---------------|
| `D100`, `D103` | Auto-generated files have standard format |
| `INP001` | Migration directory is an implicit namespace package |

## Inline Ignore Policy

### When to Use Inline Ignores

Inline ignores (`# noqa`, `# type: ignore`, `# pyright: ignore`) should be:
1. **Last resort** - Try to fix the issue first
2. **Specific** - Use exact error codes (e.g., `# noqa: E501`, `# type: ignore[arg-type]`)
3. **Justified** - Include a comment explaining why

### Required Format

Every inline ignore MUST include justification:

```python
# Correct - specific code and justification
value = some_call()  # noqa: E501 - URL exceeds line length but cannot be split

# Correct - specific type ignore with justification
# pyright: ignore[reportCallIssue] - Pydantic Settings loads from env vars
settings = Settings()

# Incorrect - generic ignore without justification
value = some_call()  # type: ignore
```

### Current Inline Ignores

| File | Line | Ignore | Justification |
|------|------|--------|---------------|
| `apps/api/src/core/config.py` | 57-58 | `pyright: ignore[reportCallIssue]` | Pydantic Settings loads required fields from environment variables, making constructor arguments optional |

## Pre-commit Validation

A pre-commit hook validates:

1. **Config Integrity**: Critical typing/linting settings haven't been weakened
2. **Ignore Justifications**: All inline ignores have accompanying justification comments

### Protected Settings

The following settings are protected from regression:

**Pyright:**
- `typeCheckingMode` must be `"strict"`

**Mypy:**
- `strict` must be `true`
- `disallow_untyped_defs` must be `true` (global)
- `disallow_any_generics` must be `true`

**Ruff:**
- Must include `"ALL"` in `select`

## Adding New Ignores

### Process

1. **Try to fix first** - Most issues can be resolved properly
2. **Check if truly necessary** - Some rules have legitimate conflicts
3. **Use minimum scope** - Prefer per-file over global, inline over per-file
4. **Document justification** - Add comment explaining why
5. **Update this document** - Add to appropriate table if global/per-file

### Review Checklist

Before adding an ignore:
- [ ] Attempted to fix the underlying issue?
- [ ] Used the most specific error code?
- [ ] Scoped to minimum necessary (inline > per-file > global)?
- [ ] Added justification comment?
- [ ] Updated CODE_QA.md if not inline?

## Running Quality Checks

### Full Quality Suite

```bash
# Run all checks
uv run pre-commit run --all-files

# Individual tools
uv run ruff check . --config=configs/ruff.toml
uv run ruff format . --config=configs/ruff.toml --check
uv run mypy --config-file=configs/pyproject.toml apps packages
uv run pyright
uv run pylint --rcfile=configs/pylint.toml apps packages
uv run bandit -c configs/.bandit -r apps packages
uv run pytest -c configs/pytest.ini
```

### CI/CD Gates

All PRs must pass:
1. Ruff lint and format
2. Mypy (strict)
3. Pyright (strict)
4. Pylint
5. Bandit security scan
6. pytest with 80% coverage

## Monitoring Quality Metrics

Track these metrics over time:
- Type coverage percentage
- Number of inline ignores (should decrease or stay stable)
- Test coverage percentage
- Cyclomatic complexity distribution
- Security vulnerability count

## References

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Mypy Documentation](https://mypy.readthedocs.io/)
- [Pyright Documentation](https://microsoft.github.io/pyright/)
- [Pylint Documentation](https://pylint.readthedocs.io/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
