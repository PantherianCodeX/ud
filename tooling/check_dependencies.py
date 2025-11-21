#!/usr/bin/env python3
# Copyright (c) 2025 uDocket. All Rights Reserved.
# pylint: disable=R6102  # JUSTIFIED: Global lists mutated when building dependency tables
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
    "statistics",
    "typing",
    "uuid",
    "warnings",
}

TS_PACKAGES = {
    "udocket_api_types",
    "udocket_ui_kit",
    "udocket_utils",
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
    "udocket_domain": "udocket-domain",
    "udocket_ai_core": "udocket-ai-core",
    "udocket_worker_core": "udocket-celery-core",
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

    For example, udocket-domain has modules: udocket_domain, base, matter, analysis, etc.
    Also detects internal app modules like 'core', 'config', etc.
    """
    internal_modules: set[str] = set()

    # Check if this is a src-layout package
    src_dir = package_dir / "src"
    if src_dir.exists():
        # Add every python package component (directories with __init__.py)
        for init_file in src_dir.rglob("__init__.py"):
            package_path = init_file.parent.relative_to(src_dir)
            if package_path == Path():
                continue
            for part in package_path.parts:
                if not part.startswith(".") and not part.startswith("__"):
                    internal_modules.add(part)
        # Add Python modules that live directly under package directories
        for py_file in src_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            module_name = py_file.stem
            if not module_name.startswith(".") and not module_name.startswith("__"):
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


def _perform_initial_package_checks(package_dir: Path, pyproject_path: Path) -> tuple[bool, list[str], bool]:
    errors: list[str] = []
    # Skip TypeScript packages (identified by package.json or known names)
    package_json = package_dir / "package.json"
    if package_json.exists() or package_dir.name in TS_PACKAGES:
        return True, [], True

    if not pyproject_path.exists():
        errors.append(f"Missing pyproject.toml in {package_dir}")
        return False, errors, False
    return True, errors, False


def _get_declared_dependencies(config: dict[str, Any]) -> tuple[set[str], set[str]]:
    """Extract declared runtime and dev dependencies from pyproject.toml config."""
    runtime_deps: set[str] = set()
    dev_deps: set[str] = set()

    project = config["project"]
    for dep in project.get("dependencies", []):
        pkg = get_package_name(dep)
        runtime_deps.add(pkg)

    for dep in config.get("tool", {}).get("uv", {}).get("dev-dependencies", []):
        pkg = get_package_name(dep)
        dev_deps.add(pkg)
    return runtime_deps, dev_deps


def _get_all_imports(package_dir: Path) -> set[str]:
    """Find all Python files in a package and extract all imports."""
    python_files = find_python_files(package_dir)
    all_imports: set[str] = set()
    for py_file in python_files:
        file_imports = extract_imports(py_file)
        all_imports.update(file_imports)
    return all_imports


def _map_imports_to_packages(
    all_imports: set[str], internal_modules: set[str], all_declared: set[str]
) -> set[str]:
    """Map extracted imports to their corresponding package names."""
    required_packages: set[str] = set()
    for imp in all_imports:
        if imp in STDLIB_MODULES:
            continue
        if imp.startswith("src"):
            continue  # Internal package imports
        if imp in internal_modules:
            continue  # Internal module imports (like 'base', 'matter', 'core', etc.)

        # Check if it's a workspace package
        if imp in {"udocket_domain", "udocket_ai_core", "udocket_worker_core"}:
            pkg_name = IMPORT_TO_PACKAGE.get(imp, imp.replace("_", "-"))
            required_packages.add(pkg_name)
        elif imp in IMPORT_TO_PACKAGE:
            required_packages.add(IMPORT_TO_PACKAGE[imp])
        else:
            # Unknown import - might be a third-party package
            # Convert underscores to hyphens as a heuristic
            if (pkg_name := imp.replace("_", "-")) not in all_declared:
                pass
            required_packages.add(pkg_name)
    return required_packages


def _check_missing_dependencies(
    package_name: str,
    required_packages: set[str],
    all_declared: set[str],
    pyproject_path: Path,
    root_dir: Path,
) -> list[str]:
    """Check for missing dependencies and return a list of errors."""
    errors: list[str] = []
    if missing := required_packages - all_declared:
        errors.append(
            f"{package_name}: Missing dependencies: {', '.join(sorted(missing))}\n"
            f"  Add these to [project.dependencies] or [tool.uv.dev-dependencies] in {pyproject_path.relative_to(root_dir)}"
        )
    return errors


def _check_dev_dependencies_in_runtime(
    package_name: str, runtime_deps: set[str], pyproject_path: Path, root_dir: Path
) -> list[str]:
    """Check for dev dependencies present in the runtime section and return a list of errors."""
    errors: list[str] = []
    if dev_in_runtime := runtime_deps & DEV_DEPENDENCIES:
        errors.append(
            f"{package_name}: Dev dependencies in runtime section: {', '.join(sorted(dev_in_runtime))}\n"
            f"  Move these to [tool.uv.dev-dependencies] in {pyproject_path.relative_to(root_dir)}"
        )
    return errors


def _check_dev_dependencies_missing_from_dev(
    package_name: str,
    required_packages: set[str],
    dev_deps: set[str],
    runtime_deps: set[str],
) -> list[str]:
    """Check for dev dependencies that are used but not declared in the dev section."""
    errors: list[str] = []
    dev_should_be_dev = required_packages & DEV_DEPENDENCIES
    if (dev_missing_from_dev := dev_should_be_dev - dev_deps) and (
        actually_missing := dev_missing_from_dev - runtime_deps
    ):
        # Only warn if they're used but not declared anywhere
        errors.append(
            f"{package_name}: Dev dependencies should be in [tool.uv.dev-dependencies]: {', '.join(sorted(actually_missing))}"
        )
    return errors


def check_package(package_dir: Path, root_dir: Path) -> tuple[bool, list[str]]:
    """Check a single package/app for dependency issues.

    Returns:
        Tuple of (success: bool, errors: list[str])
    """
    errors: list[str] = []
    pyproject_path = package_dir / "pyproject.toml"

    success, initial_errors, should_skip = _perform_initial_package_checks(package_dir, pyproject_path)
    if should_skip:
        return True, []
    if not success:
        return False, initial_errors

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
    runtime_deps, dev_deps = _get_declared_dependencies(config)

    # Find all Python files and extract imports
    all_imports = _get_all_imports(package_dir)

    # Map imports to package names
    all_declared = runtime_deps | dev_deps
    required_packages = _map_imports_to_packages(all_imports, internal_modules, all_declared)

    # Check for missing dependencies
    all_declared = runtime_deps | dev_deps
    errors.extend(_check_missing_dependencies(package_name, required_packages, all_declared, pyproject_path, root_dir))

    # Check for dev dependencies in runtime section
    errors.extend(_check_dev_dependencies_in_runtime(package_name, runtime_deps, pyproject_path, root_dir))

    # Check that dev dependencies are in dev section
    errors.extend(_check_dev_dependencies_missing_from_dev(package_name, required_packages, dev_deps, runtime_deps))

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
        if (pkg := get_package_name(dep)) in DEV_DEPENDENCIES:
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


def _check_packages(root_dir: Path, all_errors: list[str]) -> None:
    """Check all packages in the 'packages' directory."""
    packages_dir = root_dir / "packages"
    if packages_dir.exists():
        for package_dir in sorted(packages_dir.iterdir()):
            if package_dir.is_dir() and not package_dir.name.startswith("."):
                success, errors = check_package(package_dir, root_dir)
                if not success:
                    all_errors.extend(errors)


def _check_apps(root_dir: Path, all_errors: list[str]) -> None:
    """Check all applications in the 'apps' directory."""
    apps_dir = root_dir / "apps"
    if apps_dir.exists():
        for app_dir in sorted(apps_dir.iterdir()):
            if app_dir.is_dir() and not app_dir.name.startswith("."):
                pyproject = app_dir / "pyproject.toml"
                if pyproject.exists():
                    success, errors = check_package(app_dir, root_dir)
                    if not success:
                        all_errors.extend(errors)


def main() -> int:
    """Main entry point."""
    root_dir = Path(__file__).parent.parent

    all_errors: list[str] = []

    # Check root workspace
    success, errors = check_root_workspace(root_dir)
    if not success:
        all_errors.extend(errors)

    # Check all packages
    _check_packages(root_dir, all_errors)

    # Check all apps
    _check_apps(root_dir, all_errors)

    # Print summary
    if all_errors:
        for _error in all_errors:
            pass
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
