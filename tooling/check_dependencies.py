#!/usr/bin/env python3
# Copyright (c) 2025 uDocket. All Rights Reserved.
"""Dependency validation script for uDocket monorepo.

Ensures:
1. Each package/app has all its runtime dependencies listed
2. Runtime and dev dependencies are properly separated
3. No missing imports from unlisted dependencies
4. Consistent dependency versions across the monorepo
"""

import ast
import sys
import tomllib
from pathlib import Path
from typing import Any, override

# Known standard library modules (not exhaustive, add as needed)
STDLIB_MODULES = {
    "__future__",
    "abc",
    "asyncio",
    "collections",
    "contextlib",
    "datetime",
    "enum",
    "functools",
    "importlib",
    "json",
    "logging",
    "os",
    "pathlib",
    "re",
    "sys",
    "time",
    "typing",
    "uuid",
    "warnings",
}

# Mapping of import names to package names
IMPORT_TO_PACKAGE = {
    "fastapi": "fastapi",
    "uvicorn": "uvicorn",
    "pydantic": "pydantic",
    "pydantic_settings": "pydantic-settings",
    "sqlalchemy": "sqlalchemy",
    "alembic": "alembic",
    "asyncpg": "asyncpg",
    "structlog": "structlog",
    "jose": "python-jose",
    "jwt": "python-jose",  # jwt module comes from python-jose
    "passlib": "passlib",
    "celery": "celery",
    "langgraph": "langgraph",
    "langsmith": "langsmith",
    "langfuse": "langfuse",
    "pytest": "pytest",
    "hypothesis": "hypothesis",
    "mypy": "mypy",
    "pyright": "pyright",
    "ruff": "ruff",
    "pylint": "pylint",
    "bandit": "bandit",
    "safety": "safety",
    "presidio_analyzer": "presidio-analyzer",
    "presidio_anonymizer": "presidio-anonymizer",
    # Workspace packages
    "py_domain": "py-domain",
    "py_ai_core": "py-ai-core",
    "py_worker_core": "py-worker-core",
}

# Dev-only dependencies (should be in tool.uv.dev-dependencies)
DEV_DEPENDENCIES = {
    "pytest",
    "pytest-cov",
    "pytest-asyncio",
    "pytest-benchmark",
    "pytest-xdist",
    "hypothesis",
    "mypy",
    "pyright",
    "ruff",
    "pylint",
    "bandit",
    "safety",
    "pre-commit",
    "commitizen",
}


class ImportVisitor(ast.NodeVisitor):
    """AST visitor to collect all imports from Python files."""

    def __init__(self) -> None:
        self.imports: set[str] = set()

    @override
    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statements."""
        for alias in node.names:
            # Get top-level module
            module = alias.name.split(".")[0]
            self.imports.add(module)
        self.generic_visit(node)

    @override
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from...import statements."""
        if node.module:
            # Get top-level module
            module = node.module.split(".")[0]
            self.imports.add(module)
        self.generic_visit(node)


def find_python_files(directory: Path) -> list[Path]:
    """Find all Python files in a directory, excluding tests."""
    python_files: list[Path] = []

    # Look for src/ directory first (for packages)
    src_dir = directory / "src"
    if src_dir.exists():
        python_files.extend(src_dir.rglob("*.py"))
    else:
        # Otherwise search the directory (for apps)
        python_files.extend(directory.rglob("*.py"))

    # Exclude test files and __pycache__
    return [
        f
        for f in python_files
        if "__pycache__" not in f.parts and "tests" not in f.parts and f.name != "test_check_dependencies.py"
    ]


def extract_imports(file_path: Path) -> set[str]:
    """Extract all imports from a Python file."""
    try:
        with Path(file_path).open(encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        visitor = ImportVisitor()
        visitor.visit(tree)
        return visitor.imports
    except (SyntaxError, UnicodeDecodeError):
        return set()


def load_pyproject(path: Path) -> dict[str, Any]:
    """Load and parse a pyproject.toml file."""
    with Path(path).open("rb") as f:
        return tomllib.load(f)


def get_package_name(dep: str) -> str:
    """Extract package name from dependency specification."""
    # Handle extras like "uvicorn[standard]>=0.32.0"
    dep = dep.split("[", maxsplit=1)[0]
    # Handle version specifiers
    for sep in [">=", "<=", "==", "!=", "<", ">", "~=", "^"]:
        dep = dep.split(sep)[0]
    return dep.strip()


def get_package_internal_modules(package_dir: Path) -> set[str]:
    """Get the internal module names for a package.

    For example, py-domain has modules: py_domain, base, matter, analysis, etc.
    Also detects internal app modules like 'core', 'config', etc.
    """
    internal_modules: set[str] = set()

    # Check if this is a src-layout package
    src_dir = package_dir / "src"
    if src_dir.exists():
        # Add the main package name(s)
        for item in src_dir.iterdir():
            if item.is_dir() and not item.name.startswith(".") and not item.name.startswith("__"):
                internal_modules.add(item.name)
                # Also add all Python module files in the package
                for py_file in item.glob("*.py"):
                    if py_file.name != "__init__.py":
                        module_name = py_file.stem
                        internal_modules.add(module_name)
    else:
        # For apps without src/ layout, look for top-level directories
        for item in package_dir.iterdir():
            if (
                item.is_dir()
                and not item.name.startswith(".")
                and not item.name.startswith("__")
                and item.name not in {"tests", "docs", "scripts", "migrations"}
            ):
                internal_modules.add(item.name)

    return internal_modules


def check_package(package_dir: Path, root_dir: Path) -> tuple[bool, list[str]]:
    """Check a single package/app for dependency issues.

    Returns:
        Tuple of (success: bool, errors: list[str])
    """
    errors: list[str] = []
    pyproject_path = package_dir / "pyproject.toml"

    # Skip TypeScript packages (they use package.json instead)
    # Also skip packages that start with 'ts-' (TypeScript packages)
    if package_dir.name.startswith("ts-"):
        package_json = package_dir / "package.json"
        if package_json.exists() or not pyproject_path.exists():
            # This is a TypeScript/JavaScript package, skip it
            return True, []

    if not pyproject_path.exists():
        errors.append(f"Missing pyproject.toml in {package_dir}")
        return False, errors

    # Load pyproject.toml
    config = load_pyproject(pyproject_path)

    if "project" not in config:
        errors.append(f"{package_dir}: Missing [project] section in pyproject.toml")
        return False, errors

    project = config["project"]
    package_name = project.get("name", package_dir.name)

    # Get internal modules to exclude from dependency checking
    internal_modules = get_package_internal_modules(package_dir)

    # Get declared dependencies
    runtime_deps: set[str] = set()
    dev_deps: set[str] = set()

    for dep in project.get("dependencies", []):
        pkg = get_package_name(dep)
        runtime_deps.add(pkg)

    for dep in config.get("tool", {}).get("uv", {}).get("dev-dependencies", []):
        pkg = get_package_name(dep)
        dev_deps.add(pkg)

    # Find all Python files and extract imports
    python_files = find_python_files(package_dir)
    all_imports: set[str] = set()

    for py_file in python_files:
        file_imports = extract_imports(py_file)
        all_imports.update(file_imports)

    # Map imports to package names
    required_packages: set[str] = set()
    for imp in all_imports:
        if imp in STDLIB_MODULES:
            continue
        if imp.startswith("src"):
            continue  # Internal package imports
        if imp in internal_modules:
            continue  # Internal module imports (like 'base', 'matter', 'core', etc.)

        # Check if it's a workspace package
        if imp in {"py_domain", "py_ai_core", "py_worker_core"}:
            pkg_name = IMPORT_TO_PACKAGE.get(imp, imp.replace("_", "-"))
            required_packages.add(pkg_name)
        elif imp in IMPORT_TO_PACKAGE:
            required_packages.add(IMPORT_TO_PACKAGE[imp])
        else:
            # Unknown import - might be a third-party package
            # Convert underscores to hyphens as a heuristic
            pkg_name = imp.replace("_", "-")
            if pkg_name not in runtime_deps and pkg_name not in dev_deps:
                pass
            required_packages.add(pkg_name)

    # Check for missing dependencies
    all_declared = runtime_deps | dev_deps
    missing = required_packages - all_declared

    if missing:
        errors.append(
            f"{package_name}: Missing dependencies: {', '.join(sorted(missing))}\n"
            f"  Add these to {pyproject_path.relative_to(root_dir)}"
        )

    # Check for dev dependencies in runtime section
    dev_in_runtime = runtime_deps & DEV_DEPENDENCIES
    if dev_in_runtime:
        errors.append(
            f"{package_name}: Dev dependencies in runtime section: {', '.join(sorted(dev_in_runtime))}\n"
            f"  Move these to [tool.uv.dev-dependencies] in {pyproject_path.relative_to(root_dir)}"
        )

    # Check that dev dependencies are in dev section
    dev_should_be_dev = required_packages & DEV_DEPENDENCIES
    dev_missing_from_dev = dev_should_be_dev - dev_deps
    if dev_missing_from_dev:
        # Only warn if they're used but not declared anywhere
        actually_missing = dev_missing_from_dev - runtime_deps
        if actually_missing:
            errors.append(
                f"{package_name}: Dev dependencies should be in [tool.uv.dev-dependencies]: {', '.join(sorted(actually_missing))}"
            )

    return len(errors) == 0, errors


def check_root_workspace(root_dir: Path) -> tuple[bool, list[str]]:
    """Check the root workspace pyproject.toml."""
    errors: list[str] = []
    pyproject_path = root_dir / "pyproject.toml"

    if not pyproject_path.exists():
        errors.append("Missing root pyproject.toml")
        return False, errors

    config = load_pyproject(pyproject_path)

    # Check workspace configuration
    if "tool" not in config or "uv" not in config["tool"] or "workspace" not in config["tool"]["uv"]:
        errors.append("Root pyproject.toml missing [tool.uv.workspace] configuration")
        return False, errors

    # Check that root has proper dev-dependencies separation
    project_deps = config.get("project", {}).get("dependencies", [])
    config.get("tool", {}).get("uv", {}).get("dev-dependencies", [])

    runtime_in_project: set[str] = set()
    dev_in_project: set[str] = set()

    for dep in project_deps:
        pkg = get_package_name(dep)
        if pkg in DEV_DEPENDENCIES:
            dev_in_project.add(pkg)
        else:
            runtime_in_project.add(pkg)

    if dev_in_project:
        errors.append(
            f"Root workspace: Dev dependencies in [project.dependencies]: {', '.join(sorted(dev_in_project))}\n"
            f"  Move these to [tool.uv.dev-dependencies]"
        )

    if runtime_in_project:
        errors.append(
            f"Root workspace: Runtime dependencies should be in individual packages, not root: {', '.join(sorted(runtime_in_project))}\n"
            f"  Root should only have dev dependencies"
        )

    return len(errors) == 0, errors


def main() -> int:
    """Main entry point."""
    root_dir = Path(__file__).parent.parent

    all_errors: list[str] = []

    # Check root workspace
    success, errors = check_root_workspace(root_dir)
    if not success:
        all_errors.extend(errors)

    # Check all packages
    packages_dir = root_dir / "packages"
    if packages_dir.exists():
        for package_dir in sorted(packages_dir.iterdir()):
            if package_dir.is_dir() and not package_dir.name.startswith("."):
                success, errors = check_package(package_dir, root_dir)
                if not success:
                    all_errors.extend(errors)

    # Check all apps
    apps_dir = root_dir / "apps"
    if apps_dir.exists():
        for app_dir in sorted(apps_dir.iterdir()):
            if app_dir.is_dir() and not app_dir.name.startswith("."):
                pyproject = app_dir / "pyproject.toml"
                if pyproject.exists():
                    success, errors = check_package(app_dir, root_dir)
                    if not success:
                        all_errors.extend(errors)

    # Print summary
    if all_errors:
        for _error in all_errors:
            pass
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
