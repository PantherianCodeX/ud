# Quality Ignores Manifest

Generated: 2025-11-20T22:15:26.146871+00:00

## Summary

- Total code ignores: 5
- Ignores without justification: 0
- Blanket ignores (warning): 0
- Properly justified ignores: 5
- Config ignores: 72

## Code Ignores

### ✅ Properly Justified

| File | Line | Type | Codes | Justification |
|------|------|------|-------|---------------|
| apps/api/tests/conftest.py | 57 | noqa | ANN401 | pytest fixture type |
| apps/api/alembic/env.py | 51 | noqa | ANN401 | Alembic passes Connection dynamically |
| apps/api/src/main.py | 156 | noqa | S104 | Required for container networking |
| apps/api/src/core/config.py | 67 | pyright_ignore | reportCallIssue | making constructor arguments optional at instantia |
| apps/api/src/core/database.py | 84 | noqa | BLE001 | Health check should catch all connection errors |

## ✅ Config Ignores (Justified)

| File | Section | Code | Applies To | Justification |
|------|---------|------|------------|---------------|
| ruff.toml | lint | COM812 | global | Trailing comma conflicts with ruff formatter |
| ruff.toml | lint | ISC001 | global | Implicit string concatenation conflicts with formatter |
| ruff.toml | lint | D100 | global | Module docstrings enforced via per-file ignores where appropriate |
| ruff.toml | lint | D104 | global | Package docstrings enforced via per-file ignores where appropriate |
| ruff.toml | lint | S101 | global | Assert required by pytest testing framework |
| ruff.toml | lint | TRY003 | global | Detailed error messages improve debuggability |
| ruff.toml | lint | DJ | global | Django rules not applicable to FastAPI project |
| ruff.toml | lint | FIX002 | global | TODOs tracked in issue system not inline |
| ruff.toml | lint | TD002 | global | TODO authors tracked in git history |
| ruff.toml | lint | TD003 | global | TODO issue links tracked externally |
| ruff.toml | lint | RUF012 | global | Pydantic model_config is intentionally mutable class attribute |
| ruff.toml | lint.per-file-ignores | PLR2004 | tests/**/*.py | Magic values in tests are often test fixtures/expected values |
| ruff.toml | lint.per-file-ignores | D103 | tests/**/*.py | Test functions are self-documenting via descriptive names |
| ruff.toml | lint.per-file-ignores | PLR6301 | tests/**/*.py | Test methods don't need to be static for test organization |
| ruff.toml | lint.per-file-ignores | PLR2004 | **/tests/**/*.py | Magic values in tests are often test fixtures/expected values |
| ruff.toml | lint.per-file-ignores | D103 | **/tests/**/*.py | Test functions are self-documenting via descriptive names |
| ruff.toml | lint.per-file-ignores | PLR6301 | **/tests/**/*.py | Test methods don't need to be static for test organization |
| ruff.toml | lint.per-file-ignores | PLR2004 | **/test_*.py | Magic values in tests are often test fixtures/expected values |
| ruff.toml | lint.per-file-ignores | D103 | **/test_*.py | Test functions are self-documenting via descriptive names |
| ruff.toml | lint.per-file-ignores | PLR6301 | **/test_*.py | Test methods don't need to be static for test organization |
| ruff.toml | lint.per-file-ignores | INP001 | **/test_*.py | Test files don't need to be in packages |
| ruff.toml | lint.per-file-ignores | CPY001 | **/test_*.py | Test files don't need copyright headers |
| ruff.toml | lint.per-file-ignores | PLC0415 | **/test_*.py | Test methods may import in function body for isolation |
| ruff.toml | lint.per-file-ignores | D103 | **/conftest.py | Pytest fixtures are self-documenting via descriptive names |
| ruff.toml | lint.per-file-ignores | ANN001 | **/conftest.py | Pytest fixtures use dependency injection |
| ruff.toml | lint.per-file-ignores | ANN201 | **/conftest.py | Pytest fixtures use dependency injection |
| ruff.toml | lint.per-file-ignores | DOC402 | **/conftest.py | Pytest fixtures yield values implicitly |
| ruff.toml | lint.per-file-ignores | DOC201 | **/conftest.py | Pytest fixtures return values implicitly |
| ruff.toml | lint.per-file-ignores | INP001 | **/conftest.py | Test directories don't need to be packages |
| ruff.toml | lint.per-file-ignores | CPY001 | tooling/*.py | Internal tooling scripts don't need copyright |
| ruff.toml | lint.per-file-ignores | T201 | tooling/*.py | Tooling scripts need print for user output |
| ruff.toml | lint.per-file-ignores | DOC201 | tooling/*.py | Internal tooling docstrings can be simplified |
| ruff.toml | lint.per-file-ignores | D107 | tooling/*.py | Internal tooling __init__ methods don't need docstrings |
| ruff.toml | lint.per-file-ignores | C901 | tooling/*.py | Tooling scripts may have complex functions |
| ruff.toml | lint.per-file-ignores | PLR0912 | tooling/*.py | Tooling scripts may have many branches |
| ruff.toml | lint.per-file-ignores | PLR0915 | tooling/*.py | Tooling scripts may have many statements |
| ruff.toml | lint.per-file-ignores | PLR0914 | tooling/*.py | Tooling scripts may have many local variables |
| ruff.toml | lint.per-file-ignores | PLR1702 | tooling/*.py | Tooling scripts may have nested blocks |
| ruff.toml | lint.per-file-ignores | PLR2004 | tooling/*.py | Tooling scripts may use magic values for display limits |
| ruff.toml | lint.per-file-ignores | TRY300 | tooling/*.py | Tooling scripts may use try/except for control flow |
| ruff.toml | lint.per-file-ignores | E501 | tooling/*.py | Tooling scripts may have long lines for readability |
| ruff.toml | lint.per-file-ignores | INP001 | tooling/*.py | Tooling directory is not a package |
| ruff.toml | lint.per-file-ignores | PERF401 | tooling/*.py | Tooling scripts prioritize readability over micro-optimization |
| ruff.toml | lint.per-file-ignores | FBT001 | tooling/*.py | Tooling scripts use boolean flags for CLI clarity |
| ruff.toml | lint.per-file-ignores | FBT002 | tooling/*.py | Tooling scripts use boolean defaults for CLI options |
| ruff.toml | lint.per-file-ignores | D100 | **/alembic/versions/*.py | Auto-generated migration files have standard format |
| ruff.toml | lint.per-file-ignores | D103 | **/alembic/versions/*.py | Auto-generated functions (upgrade/downgrade) are self-documenting |
| ruff.toml | lint.per-file-ignores | INP001 | **/alembic/versions/*.py | Migration directory is implicit namespace package |
| ruff.toml | lint.per-file-ignores | ANN001 | **/alembic/versions/*.py | Auto-generated code doesn't have type annotations |
| ruff.toml | lint.per-file-ignores | ANN201 | **/alembic/versions/*.py | Auto-generated code doesn't have type annotations |
| ruff.toml | lint.per-file-ignores | INP001 | **/alembic/env.py | Alembic directory is implicit namespace package |
| ruff.toml | lint.per-file-ignores | ANN001 | **/alembic/env.py | Alembic boilerplate functions |
| ruff.toml | lint.per-file-ignores | ANN201 | **/alembic/env.py | Alembic boilerplate functions |
| pyproject.toml | tool.mypy.overrides | disallow_untyped_defs | tests.*, */tests/* | Test functions use pytest fixtures with implicit types |
| pyproject.toml | tool.mypy.overrides | disallow_untyped_decorators | tests.*, */tests/* | pytest.mark decorators don't have type stubs |
| pyproject.toml | tool.mypy.overrides | ignore_missing_imports | jose.*, passlib.*, structlog.*, alembic.*, celery.*, rabbitmq.*, fastapi.*, uvicorn.* | Third-party libraries without type stubs |
| pyproject.toml | tool.mypy.overrides | ignore_errors | alembic.versions.* | Auto-generated migration files have dynamic patterns |
| pylint.toml | tool.pylint.messages_control | line-too-long | global | Ruff handles line length enforcement |
| pylint.toml | tool.pylint.messages_control | bad-indentation | global | Ruff handles indentation |
| pylint.toml | tool.pylint.messages_control | bad-continuation | global | Ruff handles continuation style |
| pylint.toml | tool.pylint.messages_control | too-few-public-methods | global | Pydantic models are data classes with few methods |
| pylint.toml | tool.pylint.messages_control | no-self-argument | global | Pydantic validators use cls as first argument |
| pylint.toml | tool.pylint.messages_control | no-self-use | global | Pydantic validators may not use self |
| pylint.toml | tool.pylint.messages_control | redefined-outer-name | global | pytest fixtures intentionally shadow outer names |
| pylint.toml | tool.pylint.messages_control | duplicate-code | global | High false positive rate, better suited for periodic scans |
| pylint.toml | tool.pylint.messages_control | missing-module-docstring | global | Docstring rules handled by Ruff with Google style |
| pylint.toml | tool.pylint.messages_control | missing-class-docstring | global | Docstring rules handled by Ruff with Google style |
| pylint.toml | tool.pylint.messages_control | missing-function-docstring | global | Docstring rules handled by Ruff with Google style |
| pyrightconfig.json | pyright | reportMissingTypeStubs | global | Third-party libraries without stubs should not block development |
| pyrightconfig.json | pyright | reportImplicitStringConcatenation | global | Conflicts with ruff formatter concatenation style |
| pyrightconfig.json | pyright | reportUnusedCallResult | global | Many functions return values for optional chaining |
| pyrightconfig.json | pyright | reportMissingSuperCall | global | Not all classes require super().__init__ calls |
