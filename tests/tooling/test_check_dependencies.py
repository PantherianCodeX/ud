#!/usr/bin/env python3
# Copyright (c) 2025 uDocket. All Rights Reserved.
"""Tests for the dependency validation script."""

import ast
import tempfile
from pathlib import Path

import pytest

from tooling.check_dependencies import (
    IMPORT_TO_PACKAGE,
    ImportVisitor,
    check_package,
    check_root_workspace,
    extract_imports,
    find_python_files,
    get_package_name,
)


class TestGetPackageName:
    """Test package name extraction from dependency specifications."""

    def test_simple_package(self) -> None:
        """Test simple package name."""
        assert get_package_name("fastapi") == "fastapi"

    def test_package_with_version(self) -> None:
        """Test package with version constraint."""
        assert get_package_name("fastapi>=0.115.0") == "fastapi"
        assert get_package_name("pydantic>=2.12.4<3.0.0") == "pydantic"
        assert get_package_name("pytest~=8.0") == "pytest"

    def test_package_with_extras(self) -> None:
        """Test package with extras."""
        assert get_package_name("uvicorn[standard]>=0.32.0") == "uvicorn"
        assert get_package_name("python-jose[cryptography]") == "python-jose"


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


class TestExtractImports:
    """Test import extraction from files."""

    def test_extract_from_file(self) -> None:
        """Test extracting imports from a Python file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"

            test_file.write_text("""
import os
import sys
from pathlib import Path
from typing import Any, Dict
from fastapi import FastAPI
from pydantic import BaseModel
""")

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
            pyproject.write_text("""
[project]
name = "mypackage"
version = "0.1.0"
dependencies = ["pydantic>=2.0.0"]

[tool.uv.dev-dependencies]
pytest = ">=8.0.0"
""")

            # Create source file
            src_dir = pkg_dir / "src" / "mypackage"
            src_dir.mkdir(parents=True)
            (src_dir / "__init__.py").write_text("from pydantic import BaseModel")

            success, errors = check_package(pkg_dir, root_dir)
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
            pyproject.write_text("""
[project]
name = "mypackage"
version = "0.1.0"
dependencies = []
""")

            # Create source file that imports fastapi
            src_dir = pkg_dir / "src" / "mypackage"
            src_dir.mkdir(parents=True)
            (src_dir / "__init__.py").write_text("from fastapi import FastAPI")

            success, errors = check_package(pkg_dir, root_dir)
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
            pyproject.write_text("""
[project]
name = "mypackage"
version = "0.1.0"
dependencies = ["pytest>=8.0.0"]
""")

            # Create empty source
            src_dir = pkg_dir / "src" / "mypackage"
            src_dir.mkdir(parents=True)
            (src_dir / "__init__.py").write_text("")

            success, errors = check_package(pkg_dir, root_dir)
            assert success is False
            assert any("dev dependencies in runtime" in error.lower() for error in errors)


class TestCheckRootWorkspace:
    """Test root workspace checking."""

    def test_valid_root_workspace(self) -> None:
        """Test a valid root workspace configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create root pyproject.toml
            pyproject = tmp_path / "pyproject.toml"
            pyproject.write_text("""
[project]
name = "myproject"
version = "0.1.0"
dependencies = []

[tool.uv.workspace]
members = ["packages/*", "apps/*"]

[tool.uv.dev-dependencies]
pytest = ">=8.0.0"
mypy = ">=1.0.0"
ruff = ">=0.14.0"
""")

            success, errors = check_root_workspace(tmp_path)
            assert success is True
            assert len(errors) == 0

    def test_dev_deps_in_project_dependencies(self) -> None:
        """Test detection of dev deps in project.dependencies."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create root pyproject.toml with dev deps in wrong place
            pyproject = tmp_path / "pyproject.toml"
            pyproject.write_text("""
[project]
name = "myproject"
version = "0.1.0"
dependencies = ["pytest>=8.0.0", "mypy>=1.0.0"]

[tool.uv.workspace]
members = ["packages/*"]
""")

            success, errors = check_root_workspace(tmp_path)
            assert success is False
            assert any("dev dependencies in [project.dependencies]" in error.lower() for error in errors)

    def test_runtime_deps_in_root(self) -> None:
        """Test detection of runtime deps in root workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create root pyproject.toml with runtime deps
            pyproject = tmp_path / "pyproject.toml"
            pyproject.write_text("""
[project]
name = "myproject"
version = "0.1.0"
dependencies = ["fastapi>=0.115.0", "pydantic>=2.0.0"]

[tool.uv.workspace]
members = ["packages/*"]
""")

            success, errors = check_root_workspace(tmp_path)
            assert success is False
            assert any("runtime dependencies should be in individual packages" in error.lower() for error in errors)

    def test_missing_workspace_config(self) -> None:
        """Test detection of missing workspace configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create root pyproject.toml without workspace config
            pyproject = tmp_path / "pyproject.toml"
            pyproject.write_text("""
[project]
name = "myproject"
version = "0.1.0"
dependencies = []
""")

            success, errors = check_root_workspace(tmp_path)
            assert success is False
            assert any("workspace" in error.lower() for error in errors)


def test_import_to_package_mapping() -> None:
    """Test that common import mappings are correct."""
    assert IMPORT_TO_PACKAGE["fastapi"] == "fastapi"
    assert IMPORT_TO_PACKAGE["pydantic"] == "pydantic"
    assert IMPORT_TO_PACKAGE["pydantic_settings"] == "pydantic-settings"
    assert IMPORT_TO_PACKAGE["jose"] == "python-jose"
    assert IMPORT_TO_PACKAGE["udocket_domain"] == "udocket-domain"
    assert IMPORT_TO_PACKAGE["udocket_ai_core"] == "udocket-ai-core"
    assert IMPORT_TO_PACKAGE["udocket_worker_core"] == "udocket-celery-core"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
