#!/usr/bin/env python3
# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Tests for the dependency validation script."""

import ast
import tempfile
from pathlib import Path

import pytest

import tooling.check_dependencies as check_dependencies_module
from tooling.check_dependencies import (
    IMPORT_TO_PACKAGE,
    ImportVisitor,
    _check_apps,
    _check_dev_dependencies_missing_from_dev,
    _check_packages,
    _load_workspace_package_names,
    _map_imports_to_packages,
    check_package,
    check_root_workspace,
    extract_imports,
    find_python_files,
    get_package_internal_modules,
    get_package_name,
    main,
)


class TestGetPackageName:
    """Test package name extraction from dependency specifications."""

    def test_simple_package(self) -> None:
        """Test simple package name."""
        assert get_package_name("fastapi") == "fastapi"

    def test_package_with_version(self) -> None:
        """Test package with version constraint."""
        assert get_package_name("fastapi>=0.121.3") == "fastapi"
        assert get_package_name("pydantic>=2.12.4<3.0.0") == "pydantic"
        assert get_package_name("pytest~=8.0") == "pytest"

    def test_package_with_extras(self) -> None:
        """Test package with extras."""
        assert get_package_name("uvicorn[standard]>=0.32.0") == "uvicorn"
        assert get_package_name("pyjwt[crypto]") == "pyjwt"


class TestImportVisitor:
    """Test the AST-based import visitor."""

    def test_extract_simple_import(self) -> None:
        """Test extraction of simple import."""
        code = "import os\nimport sys"
        visitor = ImportVisitor()
        tree = ast.parse(code)
        visitor.visit(tree)
        assert "os" in visitor.imports
        assert "sys" in visitor.imports

    def test_extract_from_import(self) -> None:
        """Test extraction of from...import."""
        code = "from pathlib import Path\nfrom typing import Any"
        visitor = ImportVisitor()
        tree = ast.parse(code)
        visitor.visit(tree)
        assert "pathlib" in visitor.imports
        assert "typing" in visitor.imports

    def test_extract_nested_import(self) -> None:
        """Test extraction of nested module imports."""
        code = "from fastapi.middleware.cors import CORSMiddleware"
        visitor = ImportVisitor()
        tree = ast.parse(code)
        visitor.visit(tree)
        assert "fastapi" in visitor.imports

    def test_extract_local_import(self) -> None:
        """Test extraction of local package imports."""
        code = "from udocket_domain import Matter\nfrom udocket_ai_core import analyze"
        visitor = ImportVisitor()
        tree = ast.parse(code)
        visitor.visit(tree)
        assert "udocket_domain" in visitor.imports
        assert "udocket_ai_core" in visitor.imports

    def test_relative_from_import_is_ignored(self) -> None:
        """Relative imports without module names should not be recorded."""
        code = "from . import local_module"
        visitor = ImportVisitor()
        tree = ast.parse(code)
        visitor.visit(tree)
        assert visitor.imports == set()


class TestFindPythonFiles:
    """Test Python file discovery."""

    def test_find_in_src_directory(self) -> None:
        """Test finding files in src/ directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create src structure
            src_dir = tmp_path / "src" / "mypackage"
            src_dir.mkdir(parents=True)
            (src_dir / "__init__.py").touch()
            (src_dir / "module.py").touch()

            # Create test directory (should be excluded)
            test_dir = src_dir / "tests"
            test_dir.mkdir()
            (test_dir / "test_module.py").touch()

            files = find_python_files(tmp_path)
            file_names = {f.name for f in files}

            assert "__init__.py" in file_names
            assert "module.py" in file_names
            assert "test_module.py" not in file_names

    def test_exclude_pycache(self) -> None:
        """Test that __pycache__ directories are excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create structure with __pycache__
            src_dir = tmp_path / "src"
            src_dir.mkdir()
            (src_dir / "module.py").touch()

            cache_dir = src_dir / "__pycache__"
            cache_dir.mkdir()
            (cache_dir / "module.cpython-312.pyc").touch()

            files = find_python_files(tmp_path)
            assert all("__pycache__" not in str(f) for f in files)

    def test_find_falls_back_to_root_when_src_missing(self) -> None:
        """Apps without a src/ directory should still be scanned."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            app_dir = tmp_path / "app"
            app_dir.mkdir()
            (app_dir / "handlers.py").touch()
            (app_dir / "tests").mkdir()

            files = find_python_files(app_dir)
            assert any(f.name == "handlers.py" for f in files)


class TestExtractImports:
    """Test import extraction from files."""

    def test_extract_from_file(self) -> None:
        """Test extracting imports from a Python file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"

            test_file.write_text(
                "import os\n"
                "import sys\n"
                "from pathlib import Path\n"
                "from typing import Any, Dict\n"
                "from fastapi import FastAPI\n"
                "from pydantic import BaseModel\n"
            )

            imports = extract_imports(test_file)
            assert "os" in imports
            assert "sys" in imports
            assert "pathlib" in imports
            assert "typing" in imports
            assert "fastapi" in imports
            assert "pydantic" in imports

    def test_handle_syntax_error(self) -> None:
        """Test handling of files with syntax errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "invalid.py"

            test_file.write_text("def invalid syntax here")

            imports = extract_imports(test_file)
        assert imports == set()  # Should return empty set, not crash


class TestGetPackageInternalModules:
    """Tests for detecting internal modules within package layouts."""

    def test_collects_nested_src_modules(self, tmp_path: Path) -> None:
        """src-style packages should enumerate nested packages and modules."""
        package_dir = tmp_path / "pkg"
        src_root = package_dir / "src"
        nested_pkg = src_root / "service" / "subpkg"
        nested_pkg.mkdir(parents=True)
        (src_root / "__init__.py").touch()
        (nested_pkg / "__init__.py").touch()
        (nested_pkg / "helpers.py").write_text("VALUE = 1")

        modules = get_package_internal_modules(package_dir)
        assert {"service", "subpkg", "helpers"}.issubset(modules)

    def test_collects_flat_modules_when_src_missing(self, tmp_path: Path) -> None:
        """App-style layouts without src/ should include valid child directories."""
        package_dir = tmp_path / "app"
        (package_dir / "services").mkdir(parents=True)
        (package_dir / "tests").mkdir()
        (package_dir / ".git").mkdir()

        modules = get_package_internal_modules(package_dir)
        assert modules == {"services"}


class TestCheckPackage:
    """Test package dependency checking."""

    def test_valid_package(self) -> None:
        """Test a valid package with correct dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            root_dir = tmp_path

            # Create package structure
            pkg_dir = tmp_path / "mypackage"
            pkg_dir.mkdir()

            # Create pyproject.toml
            pyproject = pkg_dir / "pyproject.toml"
            pyproject.write_text(
                "[project]\n"
                'name = "mypackage"\n'
                'version = "0.1.0"\n'
                'dependencies = ["pydantic>=2.0.0,<3.0.0"]\n'
                "\n"
                "[tool.uv.dev-dependencies]\n"
                'pytest = ">=8.0.0"\n'
            )

            # Create source file
            src_dir = pkg_dir / "src" / "mypackage"
            src_dir.mkdir(parents=True)
            (src_dir / "__init__.py").write_text("from pydantic import BaseModel")

            success, errors = check_package(pkg_dir, root_dir, workspace_packages=set())
            assert success is True
            assert len(errors) == 0

    def test_missing_dependency(self) -> None:
        """Test detection of missing dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            root_dir = tmp_path

            # Create package structure
            pkg_dir = tmp_path / "mypackage"
            pkg_dir.mkdir()

            # Create pyproject.toml WITHOUT fastapi
            pyproject = pkg_dir / "pyproject.toml"
            pyproject.write_text('[project]\nname = "mypackage"\nversion = "0.1.0"\ndependencies = []\n')

            # Create source file that imports fastapi
            src_dir = pkg_dir / "src" / "mypackage"
            src_dir.mkdir(parents=True)
            (src_dir / "__init__.py").write_text("from fastapi import FastAPI")

            success, errors = check_package(pkg_dir, root_dir, workspace_packages=set())
            assert success is False
            assert len(errors) > 0
            assert any("fastapi" in error.lower() for error in errors)

    def test_dev_dependency_in_runtime(self) -> None:
        """Test detection of dev dependencies in runtime section."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            root_dir = tmp_path

            # Create package structure
            pkg_dir = tmp_path / "mypackage"
            pkg_dir.mkdir()

            # Create pyproject.toml with pytest in runtime deps
            pyproject = pkg_dir / "pyproject.toml"
            pyproject.write_text(
                '[project]\nname = "mypackage"\nversion = "0.1.0"\ndependencies = ["pytest>=8.0.0,<9.0.0"]\n'
            )

            # Create empty source
            src_dir = pkg_dir / "src" / "mypackage"
            src_dir.mkdir(parents=True)
            (src_dir / "__init__.py").write_text("")

            success, errors = check_package(pkg_dir, root_dir, workspace_packages=set())
            assert success is False
            assert any("dev dependencies in runtime" in error.lower() for error in errors)

    def test_missing_pyproject_file(self, tmp_path: Path) -> None:
        """Packages without a pyproject should fail validation."""
        pkg_dir = tmp_path / "missing_config"
        pkg_dir.mkdir()

        success, errors = check_package(pkg_dir, tmp_path, workspace_packages=set())
        assert success is False
        assert any("missing pyproject.toml" in error.lower() for error in errors)

    def test_missing_project_section(self, tmp_path: Path) -> None:
        """Packages missing a [project] stanza should fail validation."""
        pkg_dir = tmp_path / "broken"
        pkg_dir.mkdir()
        (pkg_dir / "pyproject.toml").write_text("[tool]\nname = 'noop'\n")

        success, errors = check_package(pkg_dir, tmp_path, workspace_packages=set())
        assert success is False
        assert any("missing [project]" in error.lower() for error in errors)

    def test_typescript_packages_are_skipped(self, tmp_path: Path) -> None:
        """Packages with package.json should be skipped (TS packages)."""
        pkg_dir = tmp_path / "udocket-ui-kit"
        pkg_dir.mkdir()
        (pkg_dir / "package.json").write_text("{}")

        success, errors = check_package(pkg_dir, tmp_path, workspace_packages=set())
        assert success is True
        assert errors == []


class TestCheckRootWorkspace:
    """Test root workspace checking."""

    def test_valid_root_workspace(self) -> None:
        """Test a valid root workspace configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create root pyproject.toml
            pyproject = tmp_path / "pyproject.toml"
            pyproject.write_text(
                "[project]\n"
                'name = "myproject"\n'
                'version = "0.1.0"\n'
                "dependencies = []\n"
                "\n"
                "[tool.uv.workspace]\n"
                'members = ["packages/*", "apps/*"]\n'
                "\n"
                "[tool.uv.dev-dependencies]\n"
                'pytest = ">=8.0.0"\n'
                'mypy = ">=1.0.0"\n'
                'ruff = ">=0.14.0"\n'
            )

            success, errors = check_root_workspace(tmp_path)
            assert success is True
            assert len(errors) == 0

    def test_dev_deps_in_project_dependencies(self) -> None:
        """Test detection of dev deps in project.dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create root pyproject.toml with dev deps in wrong place
            pyproject = tmp_path / "pyproject.toml"
            pyproject.write_text(
                "[project]\n"
                'name = "myproject"\n'
                'version = "0.1.0"\n'
                'dependencies = ["pytest>=8.0.0", "mypy>=1.0.0"]\n'
                "\n"
                "[tool.uv.workspace]\n"
                'members = ["packages/*"]\n'
            )

            success, errors = check_root_workspace(tmp_path)
            assert success is False
            assert any("dev dependencies in [project.dependencies]" in error.lower() for error in errors)

    def test_runtime_deps_in_root(self) -> None:
        """Test detection of runtime deps in root workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create root pyproject.toml with runtime deps
            pyproject = tmp_path / "pyproject.toml"
            pyproject.write_text(
                "[project]\n"
                'name = "myproject"\n'
                'version = "0.1.0"\n'
                'dependencies = ["fastapi>=0.115.0", "pydantic>=2.0.0"]\n'
                "\n"
                "[tool.uv.workspace]\n"
                'members = ["packages/*"]\n'
            )

            success, errors = check_root_workspace(tmp_path)
            assert success is False
            assert any("runtime dependencies should be in individual packages" in error.lower() for error in errors)

    def test_missing_workspace_config(self) -> None:
        """Test detection of missing workspace configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create root pyproject.toml without workspace config
            pyproject = tmp_path / "pyproject.toml"
            pyproject.write_text('[project]\nname = "myproject"\nversion = "0.1.0"\ndependencies = []\n')

            success, errors = check_root_workspace(tmp_path)
            assert success is False
            assert any("workspace" in error.lower() for error in errors)

    def test_missing_root_pyproject_is_reported(self, tmp_path: Path) -> None:
        """Missing pyproject at the root should be reported explicitly."""
        success, errors = check_root_workspace(tmp_path)
        assert success is False
        assert any("missing root pyproject.toml" in error.lower() for error in errors)


def _create_package_with_dependencies(base_dir: Path, dependencies: list[str]) -> Path:
    """Build a temp package with explicit dependency bounds.

    Args:
        base_dir: Directory where the package will be created.
        dependencies: Dependencies to declare for the package.

    Returns:
        Path: Directory of the created package.
    """
    pkg_dir = base_dir / "mypackage"
    pkg_dir.mkdir()
    deps_block = ",\n".join(f'    "{dep}"' for dep in dependencies)
    pyproject = pkg_dir / "pyproject.toml"
    pyproject.write_text(f'[project]\nname = "mypackage"\nversion = "0.1.0"\ndependencies = [\n{deps_block}\n]\n')

    src_dir = pkg_dir / "src" / "mypackage"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text("")

    return pkg_dir


def test_missing_upper_bound_is_reported(tmp_path: Path) -> None:
    """Ensure missing upper bounds trigger validation errors."""
    pkg_dir = _create_package_with_dependencies(tmp_path, ["requests>=2.0.0"])
    success, errors = check_package(pkg_dir, tmp_path, workspace_packages=set())
    assert success is False
    assert any("missing upper bound" in error.lower() for error in errors)


def test_missing_lower_bound_is_reported(tmp_path: Path) -> None:
    """Ensure missing lower bounds trigger validation errors."""
    pkg_dir = _create_package_with_dependencies(tmp_path, ["requests<3.0.0"])
    success, errors = check_package(pkg_dir, tmp_path, workspace_packages=set())
    assert success is False
    assert any("missing lower bound" in error.lower() for error in errors)


def test_workspace_dependency_skips_version_bounds(tmp_path: Path) -> None:
    """Workspace dependencies without bounds should bypass bound checks."""
    pkg_dir = _create_package_with_dependencies(tmp_path, ["udocket-domain"])
    success, errors = check_package(pkg_dir, tmp_path, workspace_packages={"udocket-domain"})
    assert success is True
    assert not errors


def test_dev_dependency_missing_from_dev_section_is_reported() -> None:
    """Dev-only dependencies should trigger helpful errors when omitted."""
    errors = _check_dev_dependencies_missing_from_dev(
        "mypackage",
        required_packages={"pytest"},
        dev_deps=set(),
        runtime_deps=set(),
    )
    assert len(errors) == 1
    assert "pytest" in errors[0]


def test_import_to_package_mapping() -> None:
    """Test that common import mappings are correct."""
    assert IMPORT_TO_PACKAGE["fastapi"] == "fastapi"
    assert IMPORT_TO_PACKAGE["pydantic"] == "pydantic"
    assert IMPORT_TO_PACKAGE["pydantic_settings"] == "pydantic-settings"
    assert IMPORT_TO_PACKAGE["jwt"] == "pyjwt"
    assert IMPORT_TO_PACKAGE["udocket_domain"] == "udocket-domain"
    assert IMPORT_TO_PACKAGE["udocket_ai_core"] == "udocket-ai-core"
    assert IMPORT_TO_PACKAGE["udocket_worker_core"] == "udocket-celery-core"


def test_map_imports_to_packages_handles_special_cases() -> None:
    """Ensure mapping skips stdlib/internal modules and handles workspace packages."""
    imports = {"os", "src_internal", "internal_mod", "udocket_domain", "fastapi", "custom_lib"}
    required = _map_imports_to_packages(imports, {"internal_mod"}, {"custom-lib"})
    assert required == {"udocket-domain", "fastapi", "custom-lib"}


class TestLoadWorkspacePackageNames:
    """Tests for the helper that gathers workspace package names."""

    def test_load_workspace_package_names(self, tmp_path: Path) -> None:
        """Ensure package names from workspace members are returned."""
        root_pyproject = tmp_path / "pyproject.toml"
        root_pyproject.write_text('[tool.uv.workspace]\nmembers = ["packages/pkg_a", "apps/app_a"]\n')

        pkg_dir = tmp_path / "packages" / "pkg_a"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "pyproject.toml").write_text('[project]\nname = "pkg-a"\nversion = "0.1.0"\n')

        app_dir = tmp_path / "apps" / "app_a"
        app_dir.mkdir(parents=True)
        (app_dir / "pyproject.toml").write_text('[project]\nname = "app-a"\nversion = "0.1.0"\n')

        names = _load_workspace_package_names(tmp_path)
        assert names == {"pkg-a", "app-a"}

    def test_skips_missing_members(self, tmp_path: Path) -> None:
        """Members without pyproject.toml should be ignored."""
        root_pyproject = tmp_path / "pyproject.toml"
        root_pyproject.write_text('[tool.uv.workspace]\nmembers = ["packages/pkg_b"]\n')

        names = _load_workspace_package_names(tmp_path)
        assert names == set()

    def test_skips_members_without_project_name(self, tmp_path: Path) -> None:
        """Members lacking a [project] name should not contribute."""
        root_pyproject = tmp_path / "pyproject.toml"
        root_pyproject.write_text('[tool.uv.workspace]\nmembers = ["packages/pkg_c"]\n')

        pkg_dir = tmp_path / "packages" / "pkg_c"
        pkg_dir.mkdir(parents=True)
        (pkg_dir / "pyproject.toml").write_text('[project]\nversion = "0.1.0"\n')

        names = _load_workspace_package_names(tmp_path)
        assert names == set()


def test_check_packages_collects_errors(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """_check_packages should aggregate validation errors from child packages."""
    packages_dir = tmp_path / "packages" / "pkg_a"
    packages_dir.mkdir(parents=True)
    errors: list[str] = []

    def fake_check_package(package_dir: Path, root_dir: Path, workspace_packages: set[str]) -> tuple[bool, list[str]]:
        assert package_dir == packages_dir
        assert root_dir == tmp_path
        assert workspace_packages == {"workspace-pkg"}
        return False, ["pkg error"]

    monkeypatch.setattr(check_dependencies_module, "check_package", fake_check_package)
    _check_packages(tmp_path, {"workspace-pkg"}, errors)
    assert errors == ["pkg error"]


def test_check_apps_collects_errors(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """_check_apps should aggregate validation errors from child apps."""
    apps_dir = tmp_path / "apps" / "app_a"
    apps_dir.mkdir(parents=True)
    (apps_dir / "pyproject.toml").write_text("[project]\nname = 'app-a'\n")
    errors: list[str] = []

    def fake_check_package(package_dir: Path, root_dir: Path, workspace_packages: set[str]) -> tuple[bool, list[str]]:
        assert package_dir == apps_dir
        assert root_dir == tmp_path
        assert workspace_packages == set()
        return False, ["app error"]

    monkeypatch.setattr(check_dependencies_module, "check_package", fake_check_package)
    _check_apps(tmp_path, set(), errors)
    assert errors == ["app error"]


def test_main_returns_success_when_no_issues(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """main() should report success when no validation errors are found."""
    repo_root = tmp_path / "repo"
    tooling_dir = repo_root / "tooling"
    tooling_dir.mkdir(parents=True)
    fake_file = tooling_dir / "check_dependencies.py"
    fake_file.write_text("print('noop')")

    printed: list[str] = []

    def fake_print(*args: object, **_: object) -> None:
        printed.append(" ".join(str(arg) for arg in args))

    monkeypatch.setattr(check_dependencies_module, "__file__", str(fake_file))
    monkeypatch.setattr(check_dependencies_module, "check_root_workspace", lambda _root: (True, []))
    monkeypatch.setattr(check_dependencies_module, "_load_workspace_package_names", lambda _root: {"pkg"})
    monkeypatch.setattr(check_dependencies_module, "_check_packages", lambda _root, _pkgs, _errors: None)
    monkeypatch.setattr(check_dependencies_module, "_check_apps", lambda _root, _pkgs, _errors: None)
    monkeypatch.setattr("builtins.print", fake_print)

    assert main() == 0
    assert any("completed successfully" in line for line in printed)


def test_main_returns_failure_when_errors_exist(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """main() should emit a summary and return 1 when errors occur."""
    repo_root = tmp_path / "repo"
    tooling_dir = repo_root / "tooling"
    tooling_dir.mkdir(parents=True)
    fake_file = tooling_dir / "check_dependencies.py"
    fake_file.write_text("print('noop')")

    printed: list[str] = []

    def fake_print(*args: object, **_: object) -> None:
        printed.append(" ".join(str(arg) for arg in args))

    def fake_check_root(_: Path) -> tuple[bool, list[str]]:
        return False, ["root error"]

    def fake_check_packages(_: Path, __: set[str], errors: list[str]) -> None:
        errors.append("package error")

    def fake_check_apps(_: Path, __: set[str], errors: list[str]) -> None:
        errors.append("app error")

    monkeypatch.setattr(check_dependencies_module, "__file__", str(fake_file))
    monkeypatch.setattr(check_dependencies_module, "check_root_workspace", fake_check_root)
    monkeypatch.setattr(check_dependencies_module, "_load_workspace_package_names", lambda _root: set())
    monkeypatch.setattr(check_dependencies_module, "_check_packages", fake_check_packages)
    monkeypatch.setattr(check_dependencies_module, "_check_apps", fake_check_apps)
    monkeypatch.setattr("builtins.print", fake_print)

    assert main() == 1
    assert any("Dependency configuration issues detected" in line for line in printed)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
