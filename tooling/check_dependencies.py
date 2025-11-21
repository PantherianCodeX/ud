#!/usr/bin/env python3
# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
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
from dataclasses import dataclass
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
    "jwt": "pyjwt",
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
    """Collect unique top-level imports from parsed Python modules."""

    def __init__(self) -> None:
        self.imports: set[str] = set()

    @override
    def visit_Import(self, node: ast.Import) -> None:  # pylint: disable=invalid-name  # required: AST visitor interface enforces mixed case handlers
        """Record top-level module names imported via ``import`` statements."""
        self.imports.update(alias.name.split(".")[0] for alias in node.names)
        self.generic_visit(node)

    @override
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:  # pylint: disable=invalid-name  # required: AST visitor interface enforces mixed case handlers
        """Record the originating module for ``from ... import`` statements."""
        if node.module:
            self.imports.add(node.module.split(".")[0])
        self.generic_visit(node)


def find_python_files(directory: Path) -> list[Path]:
    """Return Python files for ``directory`` while excluding tests.

    Args:
        directory: Package or app directory to inspect.

    Returns:
        list[Path]: Python source files relative to the provided ``directory``.
    """
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
    """Extract all import targets from ``file_path``.

    Args:
        file_path: Python module to parse.

    Returns:
        set[str]: Unique top-level module names imported by ``file_path``.
    """
    try:
        with Path(file_path).open(encoding="utf-8") as file_handle:
            tree = ast.parse(file_handle.read(), filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError):
        return set()

    visitor = ImportVisitor()
    visitor.visit(tree)
    return visitor.imports


def load_pyproject(path: Path) -> dict[str, Any]:
    """Load and parse a ``pyproject.toml`` file.

    Args:
        path: Path to the TOML configuration file.

    Returns:
        dict[str, Any]: Parsed pyproject configuration.
    """
    with Path(path).open("rb") as f:
        return tomllib.load(f)


def get_package_name(dep: str) -> str:
    """Extract the canonical package name from a dependency specification.

    Args:
        dep: Dependency string including optional extras or version specifiers.

    Returns:
        str: Normalized package name.
    """
    # Handle extras like "uvicorn[standard]>=0.32.0"
    dep = dep.split("[", maxsplit=1)[0]
    # Handle version specifiers
    for sep in (">=", "<=", "==", "!=", "<", ">", "~=", "^"):
        dep = dep.split(sep)[0]
    return dep.strip()


def _is_valid_module_name(name: str) -> bool:
    return not name.startswith(".") and not name.startswith("__")


def _collect_src_modules(src_dir: Path) -> set[str]:
    modules: set[str] = set()
    for init_file in src_dir.rglob("__init__.py"):
        package_path = init_file.parent.relative_to(src_dir)
        if not package_path.parts:
            continue
        for part in package_path.parts:
            if _is_valid_module_name(part):
                modules.add(part)
    for py_file in src_dir.rglob("*.py"):
        if py_file.name == "__init__.py":
            continue
        module_name = py_file.stem
        if _is_valid_module_name(module_name):
            modules.add(module_name)
    return modules


def _collect_flat_modules(package_dir: Path) -> set[str]:
    modules: set[str] = set()
    for item in package_dir.iterdir():
        if (
            item.is_dir()
            and _is_valid_module_name(item.name)
            and item.name not in {"tests", "docs", "scripts", "migrations"}
        ):
            modules.add(item.name)
    return modules


def get_package_internal_modules(package_dir: Path) -> set[str]:
    """Return the set of internal Python modules for ``package_dir``.

    Args:
        package_dir: Package root whose modules should be enumerated.

    Returns:
        set[str]: Module names defined within the package.
    """
    src_dir = package_dir / "src"
    if src_dir.exists():
        return _collect_src_modules(src_dir)
    return _collect_flat_modules(package_dir)


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


@dataclass(slots=True)
class PackageContext:
    """Container of per-package metadata used during dependency validation."""

    package_dir: Path
    root_dir: Path
    pyproject_path: Path
    package_name: str
    runtime_deps: set[str]
    dev_deps: set[str]
    internal_modules: set[str]


def _prepare_package_context(
    package_dir: Path,
    root_dir: Path,
) -> tuple[PackageContext | None, list[str], bool]:
    pyproject_path = package_dir / "pyproject.toml"
    success, errors, should_skip = _perform_initial_package_checks(package_dir, pyproject_path)
    if should_skip:
        return None, [], True
    if not success:
        return None, errors, False

    config = load_pyproject(pyproject_path)
    if "project" not in config:
        return None, [f"{package_dir}: Missing [project] section in pyproject.toml"], False

    project = config["project"]
    package_name = project.get("name", package_dir.name)
    runtime_deps, dev_deps = _get_declared_dependencies(config)
    internal_modules = get_package_internal_modules(package_dir)

    context = PackageContext(
        package_dir=package_dir,
        root_dir=root_dir,
        pyproject_path=pyproject_path,
        package_name=package_name,
        runtime_deps=runtime_deps,
        dev_deps=dev_deps,
        internal_modules=internal_modules,
    )
    return context, [], False


def _get_all_imports(package_dir: Path) -> set[str]:
    """Find all Python files in a package and extract all imports."""
    python_files = find_python_files(package_dir)
    all_imports: set[str] = set()
    for py_file in python_files:
        file_imports = extract_imports(py_file)
        all_imports.update(file_imports)
    return all_imports


def _map_imports_to_packages(all_imports: set[str], internal_modules: set[str], all_declared: set[str]) -> set[str]:
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
        missing_display = ", ".join(sorted(missing))
        errors.append(
            f"{package_name}: Missing dependencies: {missing_display}\n"
            f"  Add these to [project.dependencies] or [tool.uv.dev-dependencies] in {pyproject_path.relative_to(root_dir)}"
        )
    return errors


def _check_dev_dependencies_in_runtime(
    package_name: str, runtime_deps: set[str], pyproject_path: Path, root_dir: Path
) -> list[str]:
    """Check for dev dependencies present in the runtime section and return a list of errors."""
    errors: list[str] = []
    if dev_in_runtime := runtime_deps & DEV_DEPENDENCIES:
        runtime_display = ", ".join(sorted(dev_in_runtime))
        errors.append(
            f"{package_name}: Dev dependencies in runtime section: {runtime_display}\n"
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
        missing_display = ", ".join(sorted(actually_missing))
        errors.append(f"{package_name}: Dev dependencies should be in [tool.uv.dev-dependencies]: {missing_display}")
    return errors


def check_package(package_dir: Path, root_dir: Path) -> tuple[bool, list[str]]:
    """Check a single package/app for dependency issues.

    Args:
        package_dir: Directory containing the package or application.
        root_dir: Repository root used for relative error reporting.

    Returns:
        tuple[bool, list[str]]: Success flag and any error messages.
    """
    context, prep_errors, should_skip = _prepare_package_context(package_dir, root_dir)
    if should_skip:
        return True, []
    if prep_errors:
        return False, prep_errors
    assert context is not None

    errors: list[str] = []
    all_imports = _get_all_imports(context.package_dir)
    all_declared = context.runtime_deps | context.dev_deps
    required_packages = _map_imports_to_packages(all_imports, context.internal_modules, all_declared)

    errors.extend(
        _check_missing_dependencies(
            context.package_name,
            required_packages,
            all_declared,
            context.pyproject_path,
            context.root_dir,
        )
    )
    errors.extend(
        _check_dev_dependencies_in_runtime(
            context.package_name,
            context.runtime_deps,
            context.pyproject_path,
            context.root_dir,
        )
    )
    errors.extend(
        _check_dev_dependencies_missing_from_dev(
            context.package_name,
            required_packages,
            context.dev_deps,
            context.runtime_deps,
        )
    )

    return not errors, errors


def check_root_workspace(root_dir: Path) -> tuple[bool, list[str]]:
    """Validate the root workspace ``pyproject.toml`` file.

    Args:
        root_dir: Repository root used to locate ``pyproject.toml``.

    Returns:
        tuple[bool, list[str]]: Success flag and validation errors.
    """
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
        dev_display = ", ".join(sorted(dev_in_project))
        errors.append(
            f"Root workspace: Dev dependencies in [project.dependencies]: {dev_display}\n"
            f"  Move these to [tool.uv.dev-dependencies]"
        )

    if runtime_in_project:
        runtime_display = ", ".join(sorted(runtime_in_project))
        errors.append(
            f"Root workspace: Runtime dependencies should be in individual packages, not root: {runtime_display}\n"
            f"  Root should only have dev dependencies"
        )

    return not errors, errors


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
    """Entry point for the dependency configuration checker.

    Returns:
        int: Process exit code (0 on success, non-zero on failures).
    """
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
        print("Dependency configuration issues detected:\n")
        for error in all_errors:
            print(f"- {error}")
        print(f"\nTotal issues found: {len(all_errors)}")
        return 1

    print("Dependency configuration check completed successfully (no issues found).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
