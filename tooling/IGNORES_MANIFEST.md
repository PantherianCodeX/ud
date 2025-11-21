# Quality Ignores Manifest

Generated: 2025-11-21T10:38:15.366598+00:00

## Summary

- Total code ignores: 14
- Ignores without justification: 0
- Blanket ignores (warning): 0
- Properly justified ignores: 14
- Config ignores: 78

## Code Ignores

### ✅ Properly Justified

| File | Line | Type | Codes | Justification |
|------|------|------|-------|---------------|
| tooling/quality_audit.py | 2 | pylint_disable | R6102 | JUSTIFIED: Lists are mutated during CLI option ass |
| tooling/quality_audit.py | 958 | pylint_disable | R6102 | JUSTIFIED: Tuple unpacking keeps API stable |
| tooling/check_dependencies.py | 3 | pylint_disable | R6102 | JUSTIFIED: Global lists mutated when building depe |
| apps/api/conftest.py | 60 | noqa | ANN401 | pytest fixture type |
| apps/api/src/udocket_api/main.py | 153 | noqa | S104 | Required for container networking |
| apps/api/src/udocket_api/main.py | 153 | nosec | B104 | Required for container networking |
| apps/api/src/udocket_api/core/config.py | 52 | pyright_ignore | reportCallIssue | making constructor arguments optional at instantia |
| apps/api/src/udocket_api/core/database.py | 84 | noqa | BLE001 | Health check should catch all connection errors |
| apps/api/src/udocket_api/workflow/analysis/schemas.py | 7 | noqa | TC003 | Pydantic uses UUID at runtime |
| apps/api/src/udocket_api/workflow/analysis/api/router.py | 7 | noqa | TC003 | FastAPI path params rely on runtime UUID parsing |
| apps/api/src/udocket_api/workflow/analysis/api/router.py | 12 | noqa | TC001 | FastAPI requires runtime schema |
| apps/api/src/udocket_api/workflow/matters/api/router.py | 7 | noqa | TC003 | FastAPI path params rely on runtime UUID parsing |
| apps/api/src/udocket_api/workflow/matters/api/router.py | 12 | noqa | TC001 | FastAPI requires runtime schema |
| apps/api/src/udocket_api/workflow/intake/api/router.py | 7 | noqa | TC003 | FastAPI path params rely on runtime UUID parsing |

## Config Ignores by File

### configs/pylint.toml

| Section | Code | Applies To | Justification |
|---------|------|------------|---------------|
| tool.pylint.messages_control | bad-indentation | global | Ruff handles indentation |
| tool.pylint.messages_control | duplicate-code | global | High false positive rate, better suited for periodic scans |
| tool.pylint.messages_control | line-too-long | global | Ruff handles line length enforcement |
| tool.pylint.messages_control | missing-class-docstring | global | Docstring rules handled by Ruff with Google style |
| tool.pylint.messages_control | missing-function-docstring | global | Docstring rules handled by Ruff with Google style |
| tool.pylint.messages_control | missing-module-docstring | global | Docstring rules handled by Ruff with Google style |
| tool.pylint.messages_control | no-self-argument | global | Pydantic validators use cls as first argument |
| tool.pylint.messages_control | redefined-outer-name | global | pytest fixtures intentionally shadow outer names |
| tool.pylint.messages_control | too-few-public-methods | global | Pydantic models are data classes with few methods |

### configs/pyproject.toml

| Section | Code | Applies To | Justification |
|---------|------|------------|---------------|
| tool.mypy.overrides | disallow_untyped_decorators | tests.*, */tests/* | pytest.mark decorators don't have type stubs |
| tool.mypy.overrides | disallow_untyped_defs | tests.*, */tests/* | Test functions use pytest fixtures with implicit types |
| tool.mypy.overrides | ignore_errors | alembic.versions.* | Auto-generated migration files have dynamic patterns |
| tool.mypy.overrides | ignore_missing_imports | jose.*, passlib.*, structlog.*, alembic.*, celery.*, rabbitmq.*, fastapi.*, uvicorn.* | Third-party libraries without type stubs |

### configs/ruff.toml

| Section | Code | Applies To | Justification |
|---------|------|------------|---------------|
| lint | COM812 | global | Trailing comma conflicts with ruff formatter |
| lint | D100 | global | Module docstrings enforced via per-file ignores where appropriate |
| lint | D104 | global | Package docstrings enforced via per-file ignores where appropriate |
| lint | DJ | global | Django rules not applicable to FastAPI project |
| lint | FIX002 | global | TODOs tracked in issue system not inline |
| lint | ISC001 | global | Implicit string concatenation conflicts with formatter |
| lint | RUF012 | global | Pydantic model_config is intentionally mutable class attribute |
| lint | S101 | global | Assert required by pytest testing framework |
| lint | TD002 | global | TODO authors tracked in git history |
| lint | TD003 | global | TODO issue links tracked externally |
| lint | TRY003 | global | Detailed error messages improve debuggability |
| lint.per-file-ignores | ANN001 | **/alembic/env.py | Alembic boilerplate functions |
| lint.per-file-ignores | ANN001 | **/alembic/versions/*.py | Auto-generated code doesn't have type annotations |
| lint.per-file-ignores | ANN001 | **/conftest.py | Pytest fixtures use dependency injection |
| lint.per-file-ignores | ANN201 | **/alembic/env.py | Alembic boilerplate functions |
| lint.per-file-ignores | ANN201 | **/alembic/versions/*.py | Auto-generated code doesn't have type annotations |
| lint.per-file-ignores | ANN201 | **/conftest.py | Pytest fixtures use dependency injection |
| lint.per-file-ignores | C901 | tooling/*.py | Tooling scripts may have complex functions |
| lint.per-file-ignores | CPY001 | **/test_*.py | Test files don't need copyright headers |
| lint.per-file-ignores | CPY001 | tooling/*.py | Internal tooling scripts don't need copyright |
| lint.per-file-ignores | D100 | **/alembic/versions/*.py | Auto-generated migration files have standard format |
| lint.per-file-ignores | D103 | **/alembic/versions/*.py | Auto-generated functions (upgrade/downgrade) are self-documenting |
| lint.per-file-ignores | D103 | **/conftest.py | Pytest fixtures are self-documenting via descriptive names |
| lint.per-file-ignores | D103 | **/test_*.py | Test functions are self-documenting via descriptive names |
| lint.per-file-ignores | D103 | **/tests/**/*.py | Test functions are self-documenting via descriptive names |
| lint.per-file-ignores | D103 | tests/**/*.py | Test functions are self-documenting via descriptive names |
| lint.per-file-ignores | D107 | tooling/*.py | Internal tooling __init__ methods don't need docstrings |
| lint.per-file-ignores | DOC201 | **/conftest.py | Pytest fixtures return values implicitly |
| lint.per-file-ignores | DOC201 | tooling/*.py | Internal tooling docstrings can be simplified |
| lint.per-file-ignores | DOC402 | **/conftest.py | Pytest fixtures yield values implicitly |
| lint.per-file-ignores | E501 | tooling/*.py | Tooling scripts may have long lines for readability |
| lint.per-file-ignores | FBT001 | tooling/*.py | Tooling scripts use boolean flags for CLI clarity |
| lint.per-file-ignores | FBT002 | tooling/*.py | Tooling scripts use boolean defaults for CLI options |
| lint.per-file-ignores | INP001 | **/alembic/env.py | Alembic directory is implicit namespace package |
| lint.per-file-ignores | INP001 | **/alembic/versions/*.py | Migration directory is implicit namespace package |
| lint.per-file-ignores | INP001 | **/conftest.py | Test directories don't need to be packages |
| lint.per-file-ignores | INP001 | **/test_*.py | Test files don't need to be in packages |
| lint.per-file-ignores | INP001 | tooling/*.py | Tooling directory is not a package |
| lint.per-file-ignores | PERF401 | tooling/*.py | Tooling scripts prioritize readability over micro-optimization |
| lint.per-file-ignores | PLC0415 | **/test_*.py | Test methods may import in function body for isolation |
| lint.per-file-ignores | PLR0912 | tooling/*.py | Tooling scripts may have many branches |
| lint.per-file-ignores | PLR0914 | tooling/*.py | Tooling scripts may have many local variables |
| lint.per-file-ignores | PLR0915 | tooling/*.py | Tooling scripts may have many statements |
| lint.per-file-ignores | PLR1702 | tooling/*.py | Tooling scripts may have nested blocks |
| lint.per-file-ignores | PLR2004 | **/test_*.py | Magic values in tests are often test fixtures/expected values |
| lint.per-file-ignores | PLR2004 | **/tests/**/*.py | Magic values in tests are often test fixtures/expected values |
| lint.per-file-ignores | PLR2004 | tests/**/*.py | Magic values in tests are often test fixtures/expected values |
| lint.per-file-ignores | PLR2004 | tooling/*.py | Tooling scripts may use magic values for display limits |
| lint.per-file-ignores | PLR6301 | **/test_*.py | Test methods don't need to be static for test organization |
| lint.per-file-ignores | PLR6301 | **/tests/**/*.py | Test methods don't need to be static for test organization |
| lint.per-file-ignores | PLR6301 | tests/**/*.py | Test methods don't need to be static for test organization |
| lint.per-file-ignores | T201 | tooling/*.py | Tooling scripts need print for user output |
| lint.per-file-ignores | TRY300 | tooling/*.py | Tooling scripts may use try/except for control flow |

### pyproject.toml

| Section | Code | Applies To | Justification |
|---------|------|------------|---------------|
| tool.bandit.exclude_dirs | exclude_dir | **/tests | Security scanner noise in nested test suites |
| tool.bandit.exclude_dirs | exclude_dir | .venv | Virtualenv contains third-party code outside our control |
| tool.bandit.exclude_dirs | exclude_dir | build | Generated build artifacts contain no source logic |
| tool.bandit.exclude_dirs | exclude_dir | dist | Generated distribution artifacts contain no source logic |
| tool.bandit.exclude_dirs | exclude_dir | node_modules | Third-party JavaScript deps scanned separately |
| tool.bandit.exclude_dirs | exclude_dir | tests | Security scanner noise in unit test fixtures |
| tool.bandit.exclude_dirs | exclude_dir | tooling/test_* | Tooling tests rely on asserts and fixtures |
| tool.bandit.skips | B101 | global | pytest uses assert statements for validation |

### pyrightconfig.json

| Section | Code | Applies To | Justification |
|---------|------|------------|---------------|
| pyright | reportImplicitStringConcatenation | global | Conflicts with ruff formatter concatenation style |
| pyright | reportMissingSuperCall | global | Not all classes require super().__init__ calls |
| pyright | reportMissingTypeStubs | global | Third-party libraries without stubs should not block development |
| pyright | reportUnusedCallResult | global | Many functions return values for optional chaining |
