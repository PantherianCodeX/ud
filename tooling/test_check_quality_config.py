# Copyright (c) 2025 uDocket. All Rights Reserved.
"""Tests for the quality config validation script."""

import tempfile
from pathlib import Path

import pytest
from check_quality_config import (
    check_inline_ignores,
    check_mypy_config,
    check_pyright_config,
    check_ruff_config,
    find_python_files,
)


class TestCheckPyrightConfig:
    """Test pyright configuration validation."""

    def test_valid_strict_config(self) -> None:
        """Test validation of valid strict config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pyrightconfig.json"
            config_file.write_text('{"typeCheckingMode": "strict"}')

            errors = check_pyright_config(config_file)
            assert len(errors) == 0

    def test_invalid_basic_mode(self) -> None:
        """Test detection of basic mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pyrightconfig.json"
            config_file.write_text('{"typeCheckingMode": "basic"}')

            errors = check_pyright_config(config_file)
            assert len(errors) == 1
            assert "strict" in errors[0]

    def test_missing_config_file(self) -> None:
        """Test handling of missing config file."""
        errors = check_pyright_config(Path("/nonexistent/pyrightconfig.json"))
        assert len(errors) == 1
        assert "not found" in errors[0]


class TestCheckMypyConfig:
    """Test mypy configuration validation."""

    def test_valid_strict_config(self) -> None:
        """Test validation of valid strict config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pyproject.toml"
            config_file.write_text("""
[tool.mypy]
strict = true
disallow_untyped_defs = true
disallow_any_generics = true
""")

            errors = check_mypy_config(config_file)
            assert len(errors) == 0

    def test_missing_strict_mode(self) -> None:
        """Test detection of missing strict mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pyproject.toml"
            config_file.write_text("""
[tool.mypy]
disallow_untyped_defs = true
disallow_any_generics = true
""")

            errors = check_mypy_config(config_file)
            assert any("strict = true" in e for e in errors)

    def test_missing_disallow_settings(self) -> None:
        """Test detection of missing disallow settings."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pyproject.toml"
            config_file.write_text("""
[tool.mypy]
strict = true
""")

            errors = check_mypy_config(config_file)
            assert any("disallow_untyped_defs" in e for e in errors)
            assert any("disallow_any_generics" in e for e in errors)


class TestCheckRuffConfig:
    """Test ruff configuration validation."""

    def test_valid_all_select(self) -> None:
        """Test validation of config with ALL in select."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "ruff.toml"
            config_file.write_text("""
[lint]
select = ["ALL"]
""")

            errors = check_ruff_config(config_file)
            assert len(errors) == 0

    def test_missing_all_select(self) -> None:
        """Test detection of missing ALL in select."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "ruff.toml"
            config_file.write_text("""
[lint]
select = ["E", "F", "W"]
""")

            errors = check_ruff_config(config_file)
            assert len(errors) == 1
            assert "ALL" in errors[0]


class TestFindPythonFiles:
    """Test Python file discovery."""

    def test_find_files_in_directory(self) -> None:
        """Test finding Python files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            (tmp_path / "module.py").touch()
            subdir = tmp_path / "subdir"
            subdir.mkdir()
            (subdir / "nested.py").touch()

            files = find_python_files(tmp_path)
            assert len(files) == 2

    def test_exclude_venv(self) -> None:
        """Test exclusion of .venv directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            (tmp_path / "module.py").touch()
            venv = tmp_path / ".venv"
            venv.mkdir()
            (venv / "lib.py").touch()

            files = find_python_files(tmp_path)
            assert len(files) == 1

    def test_exclude_pycache(self) -> None:
        """Test exclusion of __pycache__ directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            (tmp_path / "module.py").touch()
            cache = tmp_path / "__pycache__"
            cache.mkdir()
            (cache / "module.pyc").touch()

            files = find_python_files(tmp_path)
            assert len(files) == 1


class TestCheckInlineIgnores:
    """Test inline ignore validation."""

    def test_justified_type_ignore(self) -> None:
        """Test that justified type: ignore passes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"
            test_file.write_text("x = 1  # type: ignore  # because legacy API\n")

            errors = check_inline_ignores(test_file)
            assert len(errors) == 0

    def test_unjustified_type_ignore(self) -> None:
        """Test that unjustified type: ignore fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"
            test_file.write_text("x = 1  # type: ignore\n")

            errors = check_inline_ignores(test_file)
            assert len(errors) == 1
            assert "without justification" in errors[0]

    def test_justified_noqa(self) -> None:
        """Test that justified noqa passes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"
            test_file.write_text("x = 'long'  # noqa: E501  # reason: URL\n")

            errors = check_inline_ignores(test_file)
            assert len(errors) == 0

    def test_unjustified_noqa(self) -> None:
        """Test that unjustified noqa fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"
            test_file.write_text("x = 'long'  # noqa: E501\n")

            errors = check_inline_ignores(test_file)
            assert len(errors) == 1

    def test_justified_pylint_disable(self) -> None:
        """Test that justified pylint: disable passes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"
            test_file.write_text(
                "x = 1  # pylint: disable=invalid-name  # because legacy\n"
            )

            errors = check_inline_ignores(test_file)
            assert len(errors) == 0

    def test_justification_on_previous_line(self) -> None:
        """Test that justification on previous line is accepted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"
            test_file.write_text(
                "# JUSTIFIED: This is necessary for compatibility\nx = 1  # type: ignore\n"
            )

            errors = check_inline_ignores(test_file)
            assert len(errors) == 0

    def test_multiple_ignores_mixed_validity(self) -> None:
        """Test file with both valid and invalid ignores."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"
            test_file.write_text(
                "x = 1  # type: ignore  # because legacy\n"
                "y = 2  # type: ignore\n"  # No justification
                "z = 3  # noqa: E501  # reason: URL\n"
            )

            errors = check_inline_ignores(test_file)
            assert len(errors) == 1


class TestIntegration:
    """Integration tests for the full validation workflow."""

    def test_complete_valid_setup(self) -> None:
        """Test complete valid project setup passes all checks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create pyright config
            pyright_config = tmp_path / "pyrightconfig.json"
            pyright_config.write_text('{"typeCheckingMode": "strict"}')

            # Create mypy config
            configs_dir = tmp_path / "configs"
            configs_dir.mkdir()
            mypy_config = configs_dir / "pyproject.toml"
            mypy_config.write_text("""
[tool.mypy]
strict = true
disallow_untyped_defs = true
disallow_any_generics = true
""")

            # Create ruff config
            ruff_config = configs_dir / "ruff.toml"
            ruff_config.write_text('[lint]\nselect = ["ALL"]')

            # Validate all configs
            pyright_errors = check_pyright_config(pyright_config)
            mypy_errors = check_mypy_config(mypy_config)
            ruff_errors = check_ruff_config(ruff_config)

            assert len(pyright_errors) == 0
            assert len(mypy_errors) == 0
            assert len(ruff_errors) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
