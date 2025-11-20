# Quality Ignores Manifest

Generated: 2025-11-20T00:22:26.260384+00:00

## Summary

- Total code ignores: 5
- Ignores without justification: 0
- Blanket ignores (warning): 0
- Properly justified ignores: 5
- Config ignores: 1

## Code Ignores

### ✅ Properly Justified

| File | Line | Type | Codes | Justification |
|------|------|------|-------|---------------|
| apps/api/tests/conftest.py | 57 | noqa | ANN401 | pytest fixture type |
| apps/api/alembic/env.py | 51 | noqa | ANN401 | Alembic passes Connection dynamically |
| apps/api/src/main.py | 156 | noqa | S104 | Required for container networking |
| apps/api/src/core/config.py | 67 | pyright_ignore | reportCallIssue | making constructor arguments optional at instantia |
| apps/api/src/core/database.py | 84 | noqa | BLE001 | Health check should catch all connection errors |

## Config File Ignores

| File | Section | Codes | Applies To | Justification |
|------|---------|-------|------------|---------------|
| /home/user/Code/ud/configs/ruff.toml | lint | COM812, ISC001, D100, D104, S101... (+6) | global | No justification |
