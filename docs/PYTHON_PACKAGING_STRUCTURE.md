# Python Packaging Structure Guide

**Status**: Standardized
**Last Updated**: 2025-11-19
**Owner**: Engineering Team

## Overview

This document defines the standardized Python packaging structure for the uDocket monorepo. All Python packages and applications must follow these conventions for proper type checking (mypy/pyright), testing, and deployment.

---

## Table of Contents

1. [Core Principles](#core-principles)
2. [Package Structure: Src Layout](#package-structure-src-layout)
3. [Naming Conventions](#naming-conventions)
4. [Configuration Files](#configuration-files)
5. [Type Checker Integration](#type-checker-integration)
6. [Common Issues and Solutions](#common-issues-and-solutions)
7. [Migration Guide](#migration-guide)

---

## Core Principles

### 1. **Use Src/ Layout for All Packages**

The src/ layout is the **required standard** for all shared packages under `packages/`. This is a Python packaging best practice that:

- Prevents accidental imports from the working directory
- Forces proper package installation before testing
- Catches packaging bugs early in development
- Provides clear separation between package code and development files
- Works seamlessly with modern tooling (mypy, pyright, pytest, uv)

### 2. **Consistency Over Flexibility**

All packages must follow the same structure. No exceptions unless documented and approved.

### 3. **Type Safety First**

All code must pass both mypy (strict) and pyright (strict) type checking. The packaging structure must support this.

### 4. **Workspace-Based Development**

We use `uv` workspaces for monorepo management. All packages are installed in editable mode for local development.

---

## Package Structure: Src Layout

### Standard Structure for Shared Packages (`packages/`)

```text
packages/
├── py-domain/                      # Package distribution name (PyPI-friendly)
│   ├── pyproject.toml             # Package metadata and build config
│   ├── README.md                  # Package documentation
│   ├── src/                       # Source root (REQUIRED)
│   │   └── py_domain/             # Actual Python package (import name)
│   │       ├── __init__.py        # Package exports (REQUIRED, must not be empty)
│   │       ├── base.py            # Module files
│   │       ├── matter.py
│   │       └── analysis.py
│   └── tests/                     # Tests outside src/
│       ├── __init__.py
│       ├── test_matter.py
│       └── test_analysis.py
```

**Key Points:**
- **Distribution name** (in pyproject.toml): Can use hyphens (`py-domain`)
- **Import name** (directory in src/): Must use underscores (`py_domain`)
- **src/ directory**: REQUIRED for all shared packages
- **__init__.py**: MUST export public API (not empty placeholder)
- **tests/**: Lives at package root, not inside src/

### Standard Structure for Applications (`apps/`)

```text
apps/
├── api/                           # Application name
│   ├── pyproject.toml            # App metadata and dependencies
│   ├── README.md
│   ├── alembic/                  # App-specific tooling (DB migrations)
│   ├── alembic.ini
│   ├── src/                      # Source root (REQUIRED)
│   │   ├── __init__.py           # Makes src/ a package (RECOMMENDED)
│   │   ├── main.py               # Application entrypoint
│   │   ├── core/                 # Core modules
│   │   │   ├── __init__.py       # Module exports
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── logging.py
│   │   ├── workflow/             # Feature slices
│   │   │   ├── __init__.py       # Module exports (REQUIRED)
│   │   │   ├── intake/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── router.py
│   │   │   │   └── service.py
│   │   │   └── analysis/
│   │   │       ├── __init__.py
│   │   │       └── ...
│   │   └── platform/
│   │       ├── auth/
│   │       │   └── __init__.py
│   │       └── tenants/
│   │           └── __init__.py
│   └── tests/                    # App tests
│       ├── __init__.py
│       ├── conftest.py
│       ├── unit/
│       ├── integration/
│       └── e2e/
```

**Key Points:**
- Applications use src/ layout for consistency
- Import pattern: `from src.core import settings`
- PYTHONPATH includes `apps/api/` during development
- Each module directory MUST have `__init__.py`

---

## Naming Conventions

### Package Names

| Type | Format | Example | Used In |
|------|--------|---------|---------|
| **Distribution Name** | kebab-case | `py-domain` | pyproject.toml `[project] name` |
| **Import Name** | snake_case | `py_domain` | Directory name, Python imports |
| **PyPI Prefix** | `udocket-` | `udocket-py-ai-core` | Public packages only |

**Rules:**
1. Distribution names (PyPI) should use hyphens: `py-domain`, `py-ai-core`
2. Import names (Python) MUST use underscores: `py_domain`, `py_ai_core`
3. Keep names short but descriptive
4. Use `udocket-` prefix only for packages intended for PyPI publication

**Examples:**

```toml
# pyproject.toml
[project]
name = "py-domain"              # Distribution name (hyphens OK)
```

```python
# Python imports
from py_domain import Matter    # Import name (underscores required)
```

---

## Configuration Files

### Package pyproject.toml (Shared Libraries)

```toml
[project]
name = "py-domain"                    # Distribution name
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.12.4",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/py_domain"]          # ⚠️ CRITICAL: Use underscore, not hyphen
                                       # Must match actual directory name
```

**Critical Configuration:**
- `packages = ["src/py_domain"]` - **MUST use underscores** to match directory name
- Common error: `packages = ["src/py-domain"]` ❌ (hyphens don't match directory)

### Application pyproject.toml

```toml
[project]
name = "udocket-api"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "py-domain",                      # Reference by distribution name
]

[tool.uv.sources]
py-domain = { workspace = true }      # Enable workspace resolution
```

### Root Workspace pyproject.toml

```toml
[tool.uv.workspace]
members = [
    "apps/api",
    "apps/worker",
    "packages/py-domain",
    "packages/py-ai-core",
    "packages/py-worker-core",
]
```

---

## Type Checker Integration

### Pyright Configuration (pyrightconfig.json)

```json
{
  "typeCheckingMode": "strict",
  "pythonVersion": "3.12",
  "venvPath": ".",
  "venv": ".venv",
  "executionEnvironments": [
    {
      "root": "apps/api",
      "pythonVersion": "3.12",
      "extraPaths": [
        "packages/py-domain/src",
        "packages/py-ai-core/src",
        "packages/py-worker-core/src"
      ]
    },
    {
      "root": "packages/py-domain",
      "pythonVersion": "3.12"
    }
  ]
}
```

**Key Configuration:**
- `extraPaths`: Points to `src/` directories of workspace packages
- Separate execution environment per app/package root
- Enables strict type checking across workspace

### Mypy Configuration (configs/pyproject.toml)

```toml
[tool.mypy]
python_version = "3.12"
strict = true

# Import discovery
namespace_packages = true
explicit_package_bases = true

# Module search paths
mypy_path = ".:apps/api:packages/py-domain/src:packages/py-ai-core/src:packages/py-worker-core/src"

# Plugins
plugins = ["pydantic.mypy"]
```

**Key Configuration:**
- `mypy_path`: Colon-separated list of search paths
- Must include each package's `src/` directory
- `namespace_packages = true` for workspace support

---

## Common Issues and Solutions

### Issue 1: "ModuleNotFoundError: No module named 'py_domain'"

**Cause:** Package not installed in editable mode, or hatchling config error

**Solution:**
```bash
# Check hatchling configuration
# In packages/py-domain/pyproject.toml, verify:
[tool.hatch.build.targets.wheel]
packages = ["src/py_domain"]  # Must match directory name exactly

# Reinstall package
uv pip uninstall py-domain
uv pip install -e packages/py-domain

# Verify .pth file is populated
cat .venv/lib/python3.12/site-packages/_py_domain.pth
# Should contain: /path/to/packages/py-domain/src
```

### Issue 2: Mypy/Pyright Can't Resolve Imports

**Cause:** Type checker doesn't know about package src/ directories

**Solution:**
1. Check `pyrightconfig.json` has correct `extraPaths`
2. Check `configs/pyproject.toml` has correct `mypy_path`
3. Ensure paths point to `src/` directories, not package root
4. Restart language server (VSCode: Cmd+Shift+P → "Reload Window")

### Issue 3: Empty .pth File After Install

**Cause:** Hatchling config specifies wrong package path

**Solution:**
```toml
# WRONG - uses hyphens (doesn't match directory)
[tool.hatch.build.targets.wheel]
packages = ["src/py-domain"]

# CORRECT - uses underscores (matches directory)
[tool.hatch.build.targets.wheel]
packages = ["src/py_domain"]
```

### Issue 4: Tests Can't Import from src/

**Cause:** pytest doesn't know about src/ layout

**Solution:**
Ensure `pytest.ini` or `pyproject.toml` has:
```toml
[tool.pytest.ini_options]
pythonpath = [".", "apps/api/src", "packages/py-domain/src"]
```

### Issue 5: Imports Work Locally But Fail in CI

**Cause:** Local imports working from CWD, not installed package

**Solution:**
This is exactly why we use src/ layout! It forces proper installation.
1. Ensure `uv sync` runs in CI before tests
2. Check that workspace packages are properly installed
3. Never add src/ directories to PYTHONPATH manually (breaks the safety)

---

## Migration Guide

### Converting Existing Package to Src Layout

**Before:**
```text
packages/my-package/
├── pyproject.toml
├── my_package/
│   ├── __init__.py
│   └── module.py
└── tests/
```

**After:**
```text
packages/my-package/
├── pyproject.toml
├── src/
│   └── my_package/      # Moved inside src/
│       ├── __init__.py
│       └── module.py
└── tests/
```

**Steps:**

1. **Create src/ directory:**
   ```bash
   cd packages/my-package
   mkdir src
   ```

2. **Move package directory into src/:**
   ```bash
   mv my_package src/
   ```

3. **Update pyproject.toml:**
   ```toml
   [tool.hatch.build.targets.wheel]
   packages = ["src/my_package"]  # Add this
   ```

4. **Update type checker configs:**
   - Add `packages/my-package/src` to `pyrightconfig.json` extraPaths
   - Add `packages/my-package/src` to `configs/pyproject.toml` mypy_path

5. **Reinstall package:**
   ```bash
   cd /home/user/Code/ud
   uv pip uninstall my-package
   uv pip install -e packages/my-package
   ```

6. **Verify:**
   ```bash
   python -c "from my_package import MyClass; print('Success')"
   ```

### Converting Application to Src Layout

**Before:**
```text
apps/myapp/
├── pyproject.toml
├── myapp/
│   ├── main.py
│   └── core/
└── tests/
```

**After:**
```text
apps/myapp/
├── pyproject.toml
├── src/                # Add this
│   ├── __init__.py     # Add this (optional but recommended)
│   ├── main.py         # Move files here
│   └── core/
└── tests/
```

**Steps:**

1. **Create src/ directory and move code:**
   ```bash
   cd apps/myapp
   mkdir src
   mv myapp/* src/
   rmdir myapp
   ```

2. **Create src/__init__.py:**
   ```bash
   touch src/__init__.py
   ```

3. **Update imports to use `from src.` prefix:**
   ```python
   # Before
   from myapp.core import settings

   # After
   from src.core import settings
   ```

4. **Update pyrightconfig.json:**
   ```json
   {
     "executionEnvironments": [
       {
         "root": "apps/myapp",
         "extraPaths": ["packages/py-domain/src", ...]
       }
     ]
   }
   ```

5. **Test the application:**
   ```bash
   cd apps/myapp
   python -m src.main  # Or however you run it
   ```

---

## Package Development Workflow

### Creating a New Shared Package

```bash
# 1. Create package structure
mkdir -p packages/py-newpkg/src/py_newpkg
touch packages/py-newpkg/src/py_newpkg/__init__.py

# 2. Create pyproject.toml
cat > packages/py-newpkg/pyproject.toml <<EOF
[project]
name = "py-newpkg"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/py_newpkg"]
EOF

# 3. Add to workspace (pyproject.toml at root)
# Add "packages/py-newpkg" to [tool.uv.workspace] members

# 4. Install in editable mode
uv pip install -e packages/py-newpkg

# 5. Update type checker configs
# - Add packages/py-newpkg/src to pyrightconfig.json extraPaths
# - Add packages/py-newpkg/src to configs/pyproject.toml mypy_path

# 6. Verify
python -c "import py_newpkg; print('Success')"
```

### Daily Development Commands

```bash
# Install/sync all workspace packages
uv sync

# Install single package in editable mode
uv pip install -e packages/py-domain

# Check what's installed
uv pip list | grep -E "(py-|udocket-)"

# Verify package imports
python -c "from py_domain import Matter; print(Matter)"

# Run type checks
mypy apps/api/src
pyright apps/api

# Run tests
pytest packages/py-domain/tests
pytest apps/api/tests
```

---

## Checklist for New Packages

Use this checklist when creating or migrating packages:

### Shared Package (`packages/`)

- [ ] Package uses src/ layout: `packages/pkg-name/src/pkg_name/`
- [ ] `__init__.py` exists and exports public API
- [ ] `pyproject.toml` has correct `[tool.hatch.build.targets.wheel]` config
- [ ] Package name uses underscores in directory, can use hyphens in project name
- [ ] Added to root `pyproject.toml` workspace members
- [ ] Added to `pyrightconfig.json` extraPaths (with `/src` suffix)
- [ ] Added to `configs/pyproject.toml` mypy_path (with `/src` suffix)
- [ ] Installed in editable mode: `uv pip install -e packages/pkg-name`
- [ ] Imports work: `python -c "import pkg_name"`
- [ ] Type checking passes: `pyright packages/pkg-name`

### Application (`apps/`)

- [ ] Application uses src/ layout: `apps/app-name/src/`
- [ ] `src/__init__.py` exists (optional but recommended)
- [ ] All module directories have `__init__.py`
- [ ] Imports use `from src.` prefix
- [ ] Dependencies declared in `pyproject.toml` with workspace sources
- [ ] Added to `pyrightconfig.json` execution environments
- [ ] Type checking passes: `pyright apps/app-name`
- [ ] Tests import correctly from `src.`

---

## Reference: Complete Example

### Shared Package (py-domain)

**File: `packages/py-domain/pyproject.toml`**
```toml
[project]
name = "py-domain"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["pydantic>=2.12.4"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/py_domain"]
```

**File: `packages/py-domain/src/py_domain/__init__.py`**
```python
"""uDocket domain models."""
from .matter import Matter, Party, Relationship
from .analysis import MatterAnalysis, Issue, TimelineEvent

__all__ = [
    "Matter",
    "Party",
    "Relationship",
    "MatterAnalysis",
    "Issue",
    "TimelineEvent",
]
```

**Usage:**
```python
from py_domain import Matter, Party
```

### Application (API)

**File: `apps/api/pyproject.toml`**
```toml
[project]
name = "udocket-api"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.0",
    "py-domain",
]

[tool.uv.sources]
py-domain = { workspace = true }
```

**File: `apps/api/src/main.py`**
```python
from fastapi import FastAPI
from src.core import settings, configure_logging
from py_domain import HealthCheck

app = FastAPI()

@app.get("/health", response_model=HealthCheck)
async def health():
    return HealthCheck(status="healthy", version="0.1.0")
```

---

## FAQ

### Q: Why can't I use a flat layout?

**A:** Flat layout allows importing from working directory instead of installed package, which masks packaging bugs. The src/ layout forces proper installation and catches issues early.

### Q: Do I need src/ for one-off scripts?

**A:** No. Scripts under `tooling/` or standalone files don't need src/ layout. Only packages and applications should use it.

### Q: Can I have both my_package and my-package?

**A:** Yes, but they mean different things:
- `my-package` is the distribution name (PyPI, pyproject.toml)
- `my_package` is the import name (Python code)
- They're often different because Python identifiers can't have hyphens

### Q: What if my package has no dependencies?

**A:** Still use src/ layout. The benefits (import safety, consistency) apply regardless of dependencies.

### Q: Should tests go in src/?

**A:** No. Tests should be at package root (`packages/pkg/tests/`), not in src/. This prevents tests from being packaged with distribution.

### Q: How do I know if my package is installed correctly?

**A:** Check these:
```bash
# 1. Check .pth file exists and has content
cat .venv/lib/python3.12/site-packages/_my_package.pth
# Should show: /path/to/packages/my-package/src

# 2. Test import
python -c "import my_package; print(my_package.__file__)"
# Should show: /path/to/packages/my-package/src/my_package/__init__.py
```

---

## Troubleshooting Decision Tree

```
Import not working?
├─ Check: Is package installed?
│  └─ Run: uv pip list | grep package-name
│     ├─ Not listed → Install: uv pip install -e packages/package-name
│     └─ Listed → Continue
├─ Check: Is .pth file populated?
│  └─ Run: cat .venv/lib/python3.12/site-packages/_package_name.pth
│     ├─ Empty or missing → Fix hatchling config in pyproject.toml
│     └─ Has path → Continue
├─ Check: Does src/package_name exist?
│  └─ Run: ls packages/package-name/src/
│     ├─ Not found → Create src/ directory and move code
│     └─ Exists → Continue
├─ Check: Does __init__.py exist and export symbols?
│  └─ Run: cat packages/package-name/src/package_name/__init__.py
│     ├─ Empty or missing → Add exports
│     └─ Has exports → Continue
├─ Check: Are type checkers configured?
│  └─ Verify extraPaths in pyrightconfig.json
│     └─ Verify mypy_path in configs/pyproject.toml
└─ Still broken?
   └─ Restart language server (VSCode: Reload Window)
```

---

## Summary

**Golden Rules:**
1. ✅ Always use src/ layout for packages
2. ✅ Distribution names can use hyphens (`py-domain`)
3. ✅ Import names must use underscores (`py_domain`)
4. ✅ Hatchling config must match directory name exactly
5. ✅ Every package needs a non-empty `__init__.py`
6. ✅ Type checkers need paths to `src/` directories
7. ✅ Install packages with `uv pip install -e packages/pkg-name`
8. ✅ Verify .pth file is populated after install

**This structure ensures:**
- ✅ Proper type checking (mypy + pyright strict)
- ✅ Reliable imports across workspace
- ✅ Early detection of packaging issues
- ✅ Consistency across all packages
- ✅ Industry best practices

For questions or issues, refer to this document first, then consult the team.
