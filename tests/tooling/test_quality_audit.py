# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Tests for the quality audit script."""

import json
import tempfile
from collections.abc import Callable
from pathlib import Path

import pytest

import tooling.quality_audit.cli as qa_cli
from tooling.quality_audit import (
    AuditReport,
    ConfigIgnoreEntry,
    IgnoreEntry,
    check_baseline_drift,
    check_config_strictness,
    check_inline_ignores,
    check_mypy_config,
    check_pyright_config,
    check_ruff_config,
    compute_file_hash,
    discover_config_files,
    extract_justification,
    find_python_files,
    generate_markdown_manifest,
    load_baseline,
    parse_bandit_config_ignores,
    parse_mypy_config_ignores,
    parse_pylint_config_ignores,
    parse_pyright_config_ignores,
    parse_ruff_config_ignores,
    print_terminal_report,
    save_baseline,
    scan_file_for_ignores,
)
from tooling.quality_audit.cli import run_audit, run_config_check

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = PROJECT_ROOT / ".udocket_cache" / "quality_audit" / "quality_baseline.json"


def _empty_path_list(_: Path) -> list[Path]:
    return []


def _empty_code_ignore_entries(*_args: object, **_kwargs: object) -> list[IgnoreEntry]:
    return []


def _empty_config_ignore_entries(*_args: object, **_kwargs: object) -> list[ConfigIgnoreEntry]:
    return []


def _empty_config_errors(_: Path) -> list[str]:
    return []


def _baseline_stub(
    drift: tuple[str, ...],
) -> Callable[[Path, Path], tuple[tuple[str, ...], dict[str, str]]]:
    def _inner(_root: Path, _baseline_path: Path) -> tuple[tuple[str, ...], dict[str, str]]:
        return drift, {}

    return _inner


def _empty_checker_result(_: Path) -> list[str]:
    return []


def _noop_report(_: AuditReport) -> None:
    return None


def _empty_inline_issues(_path: Path) -> list[str]:
    return []


def _constant_error(message: str) -> Callable[[Path], list[str]]:
    def _inner(_path: Path) -> list[str]:
        return [message]

    return _inner


class TestComputeFileHash:
    """Test file hash computation."""

    def test_compute_hash_for_file(self) -> None:
        """Test hash computation for a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.txt"
            test_file.write_text("hello world")

            hash_value = compute_file_hash(test_file)
            assert len(hash_value) == 64  # SHA256 hex digest
            assert hash_value

    def test_compute_hash_nonexistent_file(self) -> None:
        """Test hash computation for nonexistent file."""
        hash_value = compute_file_hash(Path("/nonexistent/file.txt"))
        assert not hash_value

    def test_same_content_same_hash(self) -> None:
        """Test that same content produces same hash."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            file1 = tmp_path / "file1.txt"
            file2 = tmp_path / "file2.txt"
            file1.write_text("identical content")
            file2.write_text("identical content")

            assert compute_file_hash(file1) == compute_file_hash(file2)


class TestFindPythonFiles:
    """Test Python file discovery."""

    def test_find_python_files(self) -> None:
        """Test finding Python files in directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create Python files
            (tmp_path / "module.py").touch()
            (tmp_path / "subdir").mkdir()
            (tmp_path / "subdir" / "nested.py").touch()

            files = find_python_files(tmp_path)
            assert len(files) == 2

    def test_includes_test_files_by_default(self) -> None:
        """Test that test_*.py files are included by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            test_file = tmp_path / "test_example.py"
            test_file.touch()

            files = find_python_files(tmp_path)
            assert any(file.name == "test_example.py" for file in files)

    def test_can_exclude_test_files_when_requested(self) -> None:
        """Test that callers can opt-out of scanning test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            (tmp_path / "module.py").touch()
            (tmp_path / "test_example.py").touch()

            files = find_python_files(tmp_path, exclude_test_files=True)
            assert all(file.name != "test_example.py" for file in files)

    def test_exclude_venv(self) -> None:
        """Test that .venv directory is excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            (tmp_path / "module.py").touch()
            venv_dir = tmp_path / ".venv"
            venv_dir.mkdir()
            (venv_dir / "lib.py").touch()

            files = find_python_files(tmp_path)
            assert len(files) == 1
            assert all(".venv" not in str(f) for f in files)

    def test_exclude_pycache(self) -> None:
        """Test that __pycache__ is excluded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            (tmp_path / "module.py").touch()
            cache_dir = tmp_path / "__pycache__"
            cache_dir.mkdir()
            (cache_dir / "module.cpython-312.pyc").touch()

            files = find_python_files(tmp_path)
            assert len(files) == 1


class TestExtractJustification:
    """Test justification extraction from comments."""

    def test_justification_with_because(self) -> None:
        """Test extraction with 'because' keyword."""
        line = "x = 1  # type: ignore  # because legacy API"
        has_just, _just = extract_justification(line, None)
        assert has_just is True

    def test_justification_with_reason(self) -> None:
        """Test extraction with 'reason' keyword."""
        line = "x = 1  # noqa: E501  # reason: long URL"
        has_just, _just = extract_justification(line, None)
        assert has_just is True

    def test_justification_in_previous_line(self) -> None:
        """Test justification in previous line comment."""
        prev_line = "# JUSTIFIED: This is necessary for compatibility"
        line = "x = 1  # type: ignore  # JUSTIFIED: test data"
        has_just, _just = extract_justification(line, prev_line)
        assert has_just is True

    def test_no_justification(self) -> None:
        """Test detection of missing justification."""
        line = "x = 1  # type: ignore"
        has_just, _just = extract_justification(line, None)
        assert has_just is False

    def test_justification_with_todo(self) -> None:
        """Test extraction with TODO keyword."""
        line = "x = 1  # noqa  # TODO: fix this later"
        has_just, _just = extract_justification(line, None)
        assert has_just is True


class TestScanFileForIgnores:
    """Test scanning files for ignore directives."""

    def test_scan_type_ignore(self) -> None:
        """Test scanning for type: ignore comments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"
            test_file.write_text("x = 1  # type: ignore  # because legacy\n")

            entries = scan_file_for_ignores(test_file, tmp_path)
            assert len(entries) == 1
            assert entries[0].ignore_type == "type_ignore"
            assert entries[0].has_justification is True
            assert entries[0].severity == "warning"  # No specific codes

    def test_scan_type_ignore_with_codes(self) -> None:
        """Test scanning for type: ignore with specific codes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"
            test_file.write_text("x = 1  # type: ignore[arg-type]  # because API mismatch\n")

            entries = scan_file_for_ignores(test_file, tmp_path)
            assert len(entries) == 1
            assert entries[0].ignore_codes == ["arg-type"]
            assert entries[0].severity == "info"  # Has codes and justification

    def test_scan_noqa(self) -> None:
        """Test scanning for noqa comments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"
            test_file.write_text("x = 'long line'  # noqa: E501  # reason: URL\n")

            entries = scan_file_for_ignores(test_file, tmp_path)
            assert len(entries) == 1
            assert entries[0].ignore_type == "noqa"
            assert "E501" in entries[0].ignore_codes

    def test_scan_nosec(self) -> None:
        """Test scanning for bandit nosec comments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"
            test_file.write_text("uvicorn.run(host='0.0.0.0')  # nosec B104 - required for networking\n")

            entries = scan_file_for_ignores(test_file, tmp_path)
            assert len(entries) == 1
            assert entries[0].ignore_type == "nosec"
            assert entries[0].ignore_codes == ["B104"]
            assert entries[0].has_justification is True

    def test_scan_pylint_disable(self) -> None:
        """Test scanning for pylint: disable comments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"
            test_file.write_text("x = 1  # pylint: disable=invalid-name  # because legacy\n")

            entries = scan_file_for_ignores(test_file, tmp_path)
            assert len(entries) == 1
            assert entries[0].ignore_type == "pylint_disable"

    def test_scan_no_justification_is_error(self) -> None:
        """Test that missing justification results in error severity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"
            test_file.write_text("x = 1  # type: ignore\n")

            entries = scan_file_for_ignores(test_file, tmp_path)
            assert len(entries) == 1
            assert entries[0].severity == "error"
            assert entries[0].has_justification is False

    def test_scan_multiple_ignores(self) -> None:
        """Test scanning file with multiple ignore directives."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"
            test_file.write_text(
                "x = 1  # type: ignore  # because legacy\n"
                "y = 2  # noqa: E501  # reason: long\n"
                "z = 3  # pylint: disable=invalid-name\n"  # No justification
            )

            entries = scan_file_for_ignores(test_file, tmp_path)
            assert len(entries) == 3
            error_count = sum(1 for e in entries if e.severity == "error")
            assert error_count == 1


class TestParseRuffConfigIgnores:
    """Test parsing of ruff.toml config ignores."""

    def test_parse_global_ignores_with_justifications(self) -> None:
        """Test parsing global ignore list extracts per-code justifications."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "ruff.toml"
            config_file.write_text("""
[lint]
ignore = [
    "E501",  # JUSTIFIED: Long lines allowed for URLs
    "W503",  # JUSTIFIED: Line break preference for readability
]
""")

            entries = parse_ruff_config_ignores(config_file)
            assert len(entries) == 2
            # Each code should have its own entry with justification
            e501_entry = next((e for e in entries if "E501" in e.codes), None)
            w503_entry = next((e for e in entries if "W503" in e.codes), None)
            assert e501_entry is not None
            assert "Long lines" in e501_entry.justification
            assert w503_entry is not None
            assert "Line break" in w503_entry.justification

    def test_parse_per_file_ignores_with_justifications(self) -> None:
        """Test parsing per-file ignore patterns extracts justifications."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "ruff.toml"
            config_file.write_text("""
[lint.per-file-ignores]
"tests/*.py" = [
    "S101",  # JUSTIFIED: Assert in tests is required by pytest
    "PLR2004",  # JUSTIFIED: Magic values in tests are test fixtures
]
""")

            entries = parse_ruff_config_ignores(config_file)
            assert len(entries) == 2
            # Each code should have its own entry
            s101_entry = next((e for e in entries if "S101" in e.codes), None)
            assert s101_entry is not None
            assert s101_entry.applies_to == "tests/*.py"
            assert "Assert" in s101_entry.justification or "pytest" in s101_entry.justification

    def test_parse_nonexistent_config(self) -> None:
        """Test parsing nonexistent config returns empty list."""
        entries = parse_ruff_config_ignores(Path("/nonexistent/ruff.toml"))
        assert not entries

    def test_parse_ignore_without_justification_reports_missing(self) -> None:
        """Test that ignores without justification are flagged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "ruff.toml"
            config_file.write_text("""
[lint]
ignore = [
    "E501",
    "W503",  # JUSTIFIED: Has justification
]
""")

            entries = parse_ruff_config_ignores(config_file)
            e501_entry = next((e for e in entries if "E501" in e.codes), None)
            assert e501_entry is not None
            # Should indicate missing justification
            assert "No justification" in e501_entry.justification or not e501_entry.justification


class TestParseMypyConfigIgnores:
    """Test parsing of mypy config ignores."""

    def test_parse_ignore_missing_imports(self) -> None:
        """Test parsing ignore_missing_imports overrides."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pyproject.toml"
            config_file.write_text("""
[tool.mypy]
strict = true

# JUSTIFIED: Third-party libraries without stubs
[[tool.mypy.overrides]]
module = [
    "jwt.*",
    "passlib.*",
]
ignore_missing_imports = true
""")

            entries = parse_mypy_config_ignores(config_file)
            assert len(entries) >= 1
            imports_entry = next((e for e in entries if "ignore_missing_imports" in e.codes), None)
            assert imports_entry is not None
            assert "jwt.*" in imports_entry.applies_to
            assert "passlib.*" in imports_entry.applies_to
            assert "Third-party" in imports_entry.justification

    def test_parse_ignore_errors(self) -> None:
        """Test parsing ignore_errors overrides."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pyproject.toml"
            config_file.write_text("""
[tool.mypy]
strict = true

# JUSTIFIED: Auto-generated migration files
[[tool.mypy.overrides]]
module = ["alembic.versions.*"]
ignore_errors = true
""")

            entries = parse_mypy_config_ignores(config_file)
            assert len(entries) >= 1
            errors_entry = next((e for e in entries if "ignore_errors" in e.codes), None)
            assert errors_entry is not None
            assert "alembic.versions.*" in errors_entry.applies_to
            assert "Auto-generated" in errors_entry.justification

    def test_parse_disallow_untyped_defs_false(self) -> None:
        """Test parsing disallow_untyped_defs = false overrides."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pyproject.toml"
            config_file.write_text("""
[tool.mypy]
strict = true

# JUSTIFIED: Test functions use pytest fixtures
[[tool.mypy.overrides]]
module = ["tests.*", "*/tests/*"]
disallow_untyped_defs = false  # JUSTIFIED: Test functions use pytest fixtures with implicit types
disallow_untyped_decorators = false  # JUSTIFIED: pytest.mark decorators don't have type stubs
""")

            entries = parse_mypy_config_ignores(config_file)
            # Should find both disallow_untyped_defs and disallow_untyped_decorators
            defs_entry = next((e for e in entries if "disallow_untyped_defs" in e.codes), None)
            decorators_entry = next((e for e in entries if "disallow_untyped_decorators" in e.codes), None)
            assert defs_entry is not None
            assert decorators_entry is not None
            assert "tests.*" in defs_entry.applies_to
            assert "pytest" in defs_entry.justification.lower() or "test" in defs_entry.justification.lower()

    def test_parse_multiple_overrides(self) -> None:
        """Test parsing multiple override sections."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pyproject.toml"
            config_file.write_text("""
[tool.mypy]
strict = true

# JUSTIFIED: Test relaxations
[[tool.mypy.overrides]]
module = ["tests.*"]
disallow_untyped_defs = false  # JUSTIFIED: pytest fixtures

# JUSTIFIED: Third-party stubs missing
[[tool.mypy.overrides]]
module = ["jwt.*", "passlib.*"]
ignore_missing_imports = true

# JUSTIFIED: Migration files are auto-generated
[[tool.mypy.overrides]]
module = ["alembic.versions.*"]
ignore_errors = true
""")

            entries = parse_mypy_config_ignores(config_file)
            # Should find at least 3 entries
            assert len(entries) >= 3
            # Verify different types found
            codes = {e.codes[0] for e in entries}
            assert "disallow_untyped_defs" in codes
            assert "ignore_missing_imports" in codes
            assert "ignore_errors" in codes

    def test_missing_justification_reported(self) -> None:
        """Test that missing justifications are reported."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pyproject.toml"
            config_file.write_text("""
[tool.mypy]
strict = true

[[tool.mypy.overrides]]
module = ["jwt.*"]
ignore_missing_imports = true
""")

            entries = parse_mypy_config_ignores(config_file)
            assert len(entries) >= 1
            # Should have "No justification" or similar
            assert any("No justification" in e.justification or not e.justification for e in entries)


class TestParsePylintConfigIgnores:
    """Test parsing of pylint config ignores."""

    def test_parse_disabled_rules(self) -> None:
        """Test parsing disabled rules from pylint config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pylint.toml"
            config_file.write_text("""
[tool.pylint.messages_control]
disable = [
    # JUSTIFIED: Formatting handled by Ruff
    "line-too-long",  # JUSTIFIED: Ruff handles line length
    "bad-indentation",  # JUSTIFIED: Ruff handles indentation

    # JUSTIFIED: Pydantic patterns
    "too-few-public-methods",  # JUSTIFIED: Pydantic models
]
""")

            entries = parse_pylint_config_ignores(config_file)
            assert len(entries) == 3

            # Check each rule has its own justification
            line_too_long = next((e for e in entries if "line-too-long" in e.codes), None)
            assert line_too_long is not None
            assert "Ruff" in line_too_long.justification

            pydantic = next((e for e in entries if "too-few-public-methods" in e.codes), None)
            assert pydantic is not None
            assert "Pydantic" in pydantic.justification

    def test_parse_without_justifications(self) -> None:
        """Test detection of rules without justifications."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pylint.toml"
            config_file.write_text("""
[tool.pylint.messages_control]
disable = [
    "line-too-long",
    "bad-indentation",
]
""")

            entries = parse_pylint_config_ignores(config_file)
            assert len(entries) == 2
            # All should have "No justification"
            assert all(e.justification == "No justification" for e in entries)

    def test_parse_mixed_justifications(self) -> None:
        """Test parsing with some rules justified and some not."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pylint.toml"
            config_file.write_text("""
[tool.pylint.messages_control]
disable = [
    "line-too-long",  # JUSTIFIED: Ruff handles this
    "bad-indentation",
    "too-few-public-methods",  # JUSTIFIED: Pydantic models
]
""")

            entries = parse_pylint_config_ignores(config_file)
            assert len(entries) == 3

            justified = [e for e in entries if e.justification != "No justification"]
            unjustified = [e for e in entries if e.justification == "No justification"]

            assert len(justified) == 2
            assert len(unjustified) == 1

    def test_nonexistent_config(self) -> None:
        """Test handling of nonexistent config file."""
        entries = parse_pylint_config_ignores(Path("/nonexistent/pylint.toml"))
        assert not entries

    def test_empty_disable_list(self) -> None:
        """Test parsing empty disable list."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pylint.toml"
            config_file.write_text("""
[tool.pylint.messages_control]
disable = []
""")

            entries = parse_pylint_config_ignores(config_file)
            assert len(entries) == 0


class TestParsePyrightConfigIgnores:
    """Test parsing of pyright config ignores."""

    def test_parse_disabled_reports(self) -> None:
        """Test parsing report* settings set to false."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pyrightconfig.json"
            config_file.write_text("""{
  "typeCheckingMode": "strict",
  "reportMissingTypeStubs": false,
  "reportUnusedCallResult": false,
  "reportUnusedImport": true
}""")
            justification_file = tmp_path / "pyrightconfig.justifications.json"
            justification_file.write_text(
                json.dumps({
                    "reportMissingTypeStubs": "Third-party libs without stubs",
                    "reportUnusedCallResult": "Optional chaining pattern",
                })
            )

            entries = parse_pyright_config_ignores(config_file)
            assert len(entries) == 2

            stubs_entry = next((e for e in entries if "reportMissingTypeStubs" in e.codes), None)
            assert stubs_entry is not None
            assert "Third-party" in stubs_entry.justification

            call_entry = next((e for e in entries if "reportUnusedCallResult" in e.codes), None)
            assert call_entry is not None
            assert "chaining" in call_entry.justification

    def test_parse_without_justifications(self) -> None:
        """Test detection of disabled reports without justifications."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pyrightconfig.json"
            config_file.write_text("""{
  "typeCheckingMode": "strict",
  "reportMissingTypeStubs": false,
  "reportUnusedCallResult": false
}""")

            entries = parse_pyright_config_ignores(config_file)
            assert len(entries) == 2
            assert all(e.justification == "No justification" for e in entries)

    def test_nonexistent_config(self) -> None:
        """Test handling of nonexistent config file."""
        entries = parse_pyright_config_ignores(Path("/nonexistent/pyrightconfig.json"))
        assert not entries

    def test_ignore_true_settings(self) -> None:
        """Test that report* = true settings are not tracked as ignores."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pyrightconfig.json"
            config_file.write_text("""{
  "typeCheckingMode": "strict",
  "reportUnusedImport": true,
  "reportUnusedVariable": true
}""")

            entries = parse_pyright_config_ignores(config_file)
            assert len(entries) == 0


class TestParseBanditConfigIgnores:
    """Test parsing of bandit config entries."""

    def test_parse_bandit_lists(self) -> None:
        """Test parsing exclude_dirs and skips with justifications."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pyproject.toml"
            config_file.write_text(
                """
[tool.bandit]
exclude_dirs = [
    "tests",  # JUSTIFIED: Skip tests
    "build",  # JUSTIFIED: Generated artifacts
]
skips = [
    "B101",  # JUSTIFIED: Pytest asserts
]
"""
            )

            entries = parse_bandit_config_ignores(config_file)
            assert len(entries) == 3
            exclude_entries = [e for e in entries if e.section.endswith("exclude_dirs")]
            skip_entries = [e for e in entries if e.section.endswith("skips")]
            assert len(exclude_entries) == 2
            assert len(skip_entries) == 1
            assert exclude_entries[0].applies_to == "tests"
            assert skip_entries[0].codes == ["B101"]

    def test_parse_missing_bandit_config(self) -> None:
        """Test parsing when bandit config is absent."""
        entries = parse_bandit_config_ignores(Path("/nonexistent/pyproject.toml"))
        assert not entries


class TestCheckConfigStrictness:
    """Test config strictness validation."""

    def test_valid_pyright_config(self) -> None:
        """Test validation of valid pyright config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pyrightconfig.json"
            config_file.write_text('{"typeCheckingMode": "strict"}')

            errors = check_config_strictness(tmp_path)
            pyright_errors = [e for e in errors if "pyrightconfig" in e]
            assert len(pyright_errors) == 0

    def test_invalid_pyright_mode(self) -> None:
        """Test detection of non-strict pyright mode."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pyrightconfig.json"
            config_file.write_text('{"typeCheckingMode": "basic"}')

            errors = check_config_strictness(tmp_path)
            assert any("strict" in e for e in errors)

    def test_valid_mypy_config(self) -> None:
        """Test validation of valid mypy config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            configs_dir = tmp_path / "configs"
            configs_dir.mkdir()
            config_file = configs_dir / "pyproject.toml"
            config_file.write_text("""
[tool.mypy]
strict = true
disallow_untyped_defs = true
disallow_any_generics = true
""")

            errors = check_config_strictness(tmp_path)
            mypy_errors = [e for e in errors if "pyproject.toml" in e]
            assert len(mypy_errors) == 0

    def test_missing_mypy_strict(self) -> None:
        """Test detection of missing strict mode in mypy."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            configs_dir = tmp_path / "configs"
            configs_dir.mkdir()
            config_file = configs_dir / "pyproject.toml"
            config_file.write_text("""
[tool.mypy]
disallow_untyped_defs = true
""")

            errors = check_config_strictness(tmp_path)
            assert any("strict = true" in e for e in errors)

    def test_valid_ruff_config(self) -> None:
        """Test validation of valid ruff config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            configs_dir = tmp_path / "configs"
            configs_dir.mkdir()
            config_file = configs_dir / "ruff.toml"
            config_file.write_text("""
[lint]
select = ["ALL"]
""")

            errors = check_config_strictness(tmp_path)
            ruff_errors = [e for e in errors if "ruff.toml" in e]
            assert len(ruff_errors) == 0

    def test_missing_all_in_ruff(self) -> None:
        """Test detection of missing ALL in ruff select."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            configs_dir = tmp_path / "configs"
            configs_dir.mkdir()
            config_file = configs_dir / "ruff.toml"
            config_file.write_text("""
[lint]
select = ["E", "F"]
""")

            errors = check_config_strictness(tmp_path)
            assert any("ALL" in e for e in errors)


class TestBaselineDrift:
    """Test baseline drift detection."""

    def test_no_drift_when_unchanged(self) -> None:
        """Test no drift when configs unchanged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create config
            config_file = tmp_path / "pyrightconfig.json"
            config_file.write_text('{"typeCheckingMode": "strict"}')

            # Create baseline with same hash
            baseline_path = tmp_path / ".baseline.json"
            current_hash = compute_file_hash(config_file)
            save_baseline(baseline_path, {"pyrightconfig.json": current_hash})

            drift, _ = check_baseline_drift(tmp_path, baseline_path)
            assert len(drift) == 0

    def test_drift_when_changed(self) -> None:
        """Test drift detection when config changed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create config
            config_file = tmp_path / "pyrightconfig.json"
            config_file.write_text('{"typeCheckingMode": "strict"}')

            # Create baseline with different hash
            baseline_path = tmp_path / ".baseline.json"
            save_baseline(baseline_path, {"pyrightconfig.json": "different_hash"})

            drift, _ = check_baseline_drift(tmp_path, baseline_path)
            assert len(drift) > 0
            assert any("modified" in d for d in drift)

    def test_new_config_not_in_baseline(self) -> None:
        """Test detection of new config not in baseline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create config in expected location
            config_file = tmp_path / "pyrightconfig.json"
            config_file.write_text('{"typeCheckingMode": "strict"}')

            # Create baseline with different file
            baseline_path = tmp_path / ".baseline.json"
            save_baseline(baseline_path, {"other_config.json": "somehash"})

            drift, current = check_baseline_drift(tmp_path, baseline_path)
            # Should detect that baseline has a file that doesn't exist
            assert len(drift) > 0 or len(current) > 0


class TestBaselinePersistence:
    """Test baseline save/load functionality."""

    def test_save_and_load_baseline(self) -> None:
        """Test saving and loading baseline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            baseline_path = tmp_path / ".baseline.json"

            test_data = {"file1.json": "hash1", "file2.toml": "hash2"}
            save_baseline(baseline_path, test_data)

            loaded = load_baseline(baseline_path)
            assert loaded == test_data

    def test_load_nonexistent_baseline(self) -> None:
        """Test loading nonexistent baseline returns empty dict."""
        loaded = load_baseline(Path("/nonexistent/.baseline.json"))
        assert not loaded


class TestGenerateMarkdownManifest:
    """Test markdown manifest generation."""

    def test_generate_manifest_with_errors(self) -> None:
        """Test generating manifest with errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            output_path = tmp_path / "manifest.md"

            report = AuditReport(
                timestamp="2025-01-01T00:00:00Z",
                code_ignores=[
                    IgnoreEntry(
                        file_path="test.py",
                        line_number=10,
                        ignore_type="type_ignore",
                        ignore_codes=[],
                        content="x = 1  # type: ignore",
                        has_justification=False,
                        justification="",
                        severity="error",
                    )
                ],
                config_ignores=[],
                config_errors=[],
                baseline_drift=(),
                summary={
                    "total_code_ignores": 1,
                    "errors": 1,
                    "warnings": 0,
                    "info": 0,
                    "config_ignores": 0,
                },
            )

            generate_markdown_manifest(report, output_path)

            content = output_path.read_text()
            assert "# Quality Ignores Manifest" in content
            assert "Missing Justification" in content
            assert "test.py" in content

    def test_generate_manifest_with_config_ignores(self) -> None:
        """Test generating manifest with config ignores."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            output_path = tmp_path / "manifest.md"

            report = AuditReport(
                timestamp="2025-01-01T00:00:00Z",
                code_ignores=[],
                config_ignores=[
                    ConfigIgnoreEntry(
                        file_path="ruff.toml",
                        section="lint.ignore",
                        codes=["E501", "W503"],
                        justification="Long lines allowed",
                        applies_to="global",
                    )
                ],
                config_errors=[],
                baseline_drift=(),
                summary={
                    "total_code_ignores": 0,
                    "errors": 0,
                    "warnings": 0,
                    "info": 0,
                    "config_ignores": 1,
                },
            )

            generate_markdown_manifest(report, output_path)

            content = output_path.read_text()
            assert "## Config Ignores by File" in content
            assert "### ruff.toml" in content
            assert "| lint.ignore | E501, W503 | global | Long lines allowed |" in content

    def test_generate_manifest_with_full_sections(self) -> None:
        """Test that the manifest includes all sections."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            output_path = tmp_path / "manifest.md"

            warning_entry = IgnoreEntry(
                file_path="module.py",
                line_number=10,
                ignore_type="noqa",
                ignore_codes=[],
                content="x = 1  # noqa  # reason: readability",
                has_justification=True,
                justification="reason: readability",
                severity="warning",
            )
            info_entry = IgnoreEntry(
                file_path="module.py",
                line_number=20,
                ignore_type="type_ignore",
                ignore_codes=["E501"],
                content="x = 1  # type: ignore[E501]  # reason: legacy api",
                has_justification=True,
                justification="reason: legacy api",
                severity="info",
            )

            external_config = tmp_path / "outside" / "ruff.toml"
            external_config.parent.mkdir(exist_ok=True)
            report = AuditReport(
                timestamp="2025-01-02T00:00:00Z",
                code_ignores=[warning_entry, info_entry],
                config_ignores=[
                    ConfigIgnoreEntry(
                        file_path=str(external_config),
                        section="lint.ignore",
                        codes=[],
                        justification="External skip allowed",
                        applies_to="global",
                    )
                ],
                config_errors=["lint.ignore missing strict settings"],
                baseline_drift=("pyproject.toml drifted from baseline",),
                summary={
                    "total_code_ignores": 2,
                    "errors": 0,
                    "warnings": 1,
                    "info": 1,
                    "config_ignores": 1,
                },
            )

            generate_markdown_manifest(report, output_path)

            content = output_path.read_text()
            assert "⚠️ Blanket Ignores" in content
            assert "Properly Justified" in content
            assert str(external_config) in content
            assert "## ⚠️ Baseline Drift Detected" in content
            assert "## ❌ Configuration Errors" in content


class TestPrintTerminalReport:
    """Test terminal reporting of audit summaries."""

    def test_print_terminal_report_outputs_expected_sections(self, capsys: pytest.CaptureFixture[str]) -> None:
        report = AuditReport(
            timestamp="2025-01-03T00:00:00Z",
            code_ignores=[
                IgnoreEntry(
                    file_path="module.py",
                    line_number=5,
                    ignore_type="noqa",
                    ignore_codes=[],
                    content="x = 1  # noqa",
                    has_justification=False,
                    justification="",
                    severity="error",
                ),
                IgnoreEntry(
                    file_path="module.py",
                    line_number=10,
                    ignore_type="type_ignore",
                    ignore_codes=["E501"],
                    content="x = 1  # type: ignore[E501]  # reason: long line",
                    has_justification=True,
                    justification="reason: long line",
                    severity="warning",
                ),
            ],
            config_ignores=[],
            config_errors=["pytest.ini missing strict markers"],
            baseline_drift=("pyproject drifted from baseline",),
            summary={
                "total_code_ignores": 2,
                "errors": 1,
                "warnings": 1,
                "info": 0,
                "config_ignores": 0,
            },
        )

        print_terminal_report(report)
        captured = capsys.readouterr()
        assert "Baseline Drift" in captured.out
        assert "Configuration Errors" in captured.out
        assert "Ignores Missing Justification" in captured.out
        assert "Blanket Ignores" in captured.out


class TestCliRunner:
    """Validate the CLI runner helpers."""

    def _patch_cli_dependencies(
        self,
        monkeypatch: pytest.MonkeyPatch,
        manifest_calls: list[Path],
        baseline_reads: list[Path],
        drift: tuple[str, ...] = (),
    ) -> None:
        """Helper to stub CLI dependencies for deterministic coverage."""
        monkeypatch.setattr(qa_cli, "find_python_files", _empty_path_list)
        monkeypatch.setattr(qa_cli, "scan_file_for_ignores", _empty_code_ignore_entries)
        for parser in (
            "parse_ruff_config_ignores",
            "parse_mypy_config_ignores",
            "parse_pylint_config_ignores",
            "parse_pyright_config_ignores",
            "parse_bandit_config_ignores",
        ):
            monkeypatch.setattr(qa_cli, parser, _empty_config_ignore_entries)
        monkeypatch.setattr(qa_cli, "check_config_strictness", _empty_config_errors)
        monkeypatch.setattr(qa_cli, "check_baseline_drift", _baseline_stub(drift))
        monkeypatch.setattr(qa_cli, "print_terminal_report", _noop_report)

        def _save_baseline(path: Path, _data: dict[str, str]) -> None:
            baseline_reads.append(path)

        monkeypatch.setattr(qa_cli, "save_baseline", _save_baseline)

        def _manifest_stub(_report: AuditReport, path: Path) -> None:
            manifest_calls.append(path)

        monkeypatch.setattr(qa_cli, "generate_markdown_manifest", _manifest_stub)

    def test_run_audit_generates_manifest_and_baseline(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        root = tmp_path / "repo"
        root.mkdir()
        manifest_calls: list[Path] = []
        baseline_tracks: list[Path] = []
        self._patch_cli_dependencies(monkeypatch, manifest_calls, baseline_tracks)

        result = run_audit(root=root, generate_manifest=True, update_baseline=True)

        assert result == 0
        assert manifest_calls, "Manifest should be generated when requested"
        assert baseline_tracks, "Baseline should be saved when update_baseline=True"
        assert baseline_tracks[0].name == "quality_baseline.json"
        assert manifest_calls[0].name == "IGNORES_MANIFEST.md"

    def test_run_audit_detects_baseline_drift(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        root = tmp_path / "repo"
        root.mkdir()
        manifest_calls: list[Path] = []
        baseline_tracks: list[Path] = []
        self._patch_cli_dependencies(monkeypatch, manifest_calls, baseline_tracks, drift=("drifted",))

        result = run_audit(root=root)

        assert result == 1
        assert manifest_calls == [], "Manifest should not be created when audit fails before manifest stage"
        assert not baseline_tracks, "Baseline should not be saved when update_baseline=False"

    def test_run_config_check_reports_errors(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        root = tmp_path / "repo"
        root.mkdir()
        monkeypatch.setattr(qa_cli, "check_pyright_config", _constant_error("pyright error"))
        monkeypatch.setattr(qa_cli, "check_mypy_config", _constant_error("mypy error"))
        monkeypatch.setattr(qa_cli, "check_ruff_config", _constant_error("ruff error"))
        monkeypatch.setattr(qa_cli, "find_python_files", _empty_path_list)
        monkeypatch.setattr(qa_cli, "check_inline_ignores", _empty_inline_issues)

        result = run_config_check(root=root)

        captured = capsys.readouterr()
        assert result == 1
        assert "Quality configuration errors found" in captured.out

    def test_run_config_check_passes(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        root = tmp_path / "repo"
        root.mkdir()
        for checker in ("check_pyright_config", "check_mypy_config", "check_ruff_config"):
            monkeypatch.setattr(qa_cli, checker, _empty_checker_result)
        monkeypatch.setattr(qa_cli, "find_python_files", _empty_path_list)
        monkeypatch.setattr(qa_cli, "check_inline_ignores", _empty_inline_issues)

        result = run_config_check(root=root)

        assert result == 0


class TestCheckPyrightConfig:
    """Test pyright configuration validation."""

    def test_valid_strict_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pyrightconfig.json"
            config_file.write_text('{"typeCheckingMode": "strict"}')

            errors = check_pyright_config(config_file)
            assert errors == []

    def test_invalid_basic_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pyrightconfig.json"
            config_file.write_text('{"typeCheckingMode": "basic"}')

            errors = check_pyright_config(config_file)
            assert len(errors) == 1
            assert "strict" in errors[0]

    def test_missing_config_file(self) -> None:
        errors = check_pyright_config(Path("/nonexistent/pyrightconfig.json"))
        assert len(errors) == 1
        assert "not found" in errors[0]


class TestCheckMypyConfig:
    """Test mypy configuration validation."""

    def test_valid_strict_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pyproject.toml"
            config_file.write_text(
                """
[tool.mypy]
strict = true
disallow_untyped_defs = true
disallow_any_generics = true
"""
            )

            errors = check_mypy_config(config_file)
            assert errors == []

    def test_missing_strict_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pyproject.toml"
            config_file.write_text(
                """
[tool.mypy]
disallow_untyped_defs = true
disallow_any_generics = true
"""
            )

            errors = check_mypy_config(config_file)
            assert any("strict = true" in err for err in errors)

    def test_missing_disallow_settings(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "pyproject.toml"
            config_file.write_text(
                """
[tool.mypy]
strict = true
"""
            )

            errors = check_mypy_config(config_file)
            assert any("disallow_untyped_defs" in err for err in errors)
            assert any("disallow_any_generics" in err for err in errors)


class TestCheckRuffConfig:
    """Test ruff configuration validation."""

    def test_valid_all_select(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "ruff.toml"
            config_file.write_text(
                """
[lint]
select = ["ALL"]
"""
            )

            errors = check_ruff_config(config_file)
            assert errors == []

    def test_missing_all_select(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            config_file = tmp_path / "ruff.toml"
            config_file.write_text(
                """
[lint]
select = ["E", "F", "W"]
"""
            )

            errors = check_ruff_config(config_file)
            assert len(errors) == 1
            assert "ALL" in errors[0]


class TestCheckInlineIgnores:
    """Test inline ignore validation helper."""

    def test_justified_type_ignore(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"
            test_file.write_text("x = 1  # type: ignore  # because legacy API\n")

            errors = check_inline_ignores(test_file)
            assert errors == []

    def test_unjustified_type_ignore(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"
            test_file.write_text("x = 1  # type: ignore\n")

            errors = check_inline_ignores(test_file)
            assert len(errors) == 1
            assert "missing justification" in errors[0]

    def test_unjustified_noqa(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"
            test_file.write_text("x = 'long'  # noqa: E501\n")

            errors = check_inline_ignores(test_file)
            assert len(errors) == 1

    def test_justification_on_previous_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"
            test_file.write_text("# JUSTIFIED: This is necessary for compatibility\nx = 1  # type: ignore\n")

            errors = check_inline_ignores(test_file)
            assert errors == []


class TestIntegration:
    """Integration tests for the full audit workflow."""

    def test_full_audit_passes_clean_project(self) -> None:
        """Test full audit passes on a clean project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create minimal valid config structure
            config_file = tmp_path / "pyrightconfig.json"
            config_file.write_text('{"typeCheckingMode": "strict"}')

            configs_dir = tmp_path / "configs"
            configs_dir.mkdir()

            mypy_config = configs_dir / "pyproject.toml"
            mypy_config.write_text("""
[tool.mypy]
strict = true
disallow_untyped_defs = true
disallow_any_generics = true
""")

            ruff_config = configs_dir / "ruff.toml"
            ruff_config.write_text('[lint]\nselect = ["ALL"]')

            # Create a clean Python file (no ignores)
            (tmp_path / "clean.py").write_text("x: int = 1\n")

            errors = check_config_strictness(tmp_path)
            assert len(errors) == 0

    def test_full_audit_detects_issues(self) -> None:
        """Test full audit detects issues in project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create invalid config (non-strict)
            config_file = tmp_path / "pyrightconfig.json"
            config_file.write_text('{"typeCheckingMode": "basic"}')

            errors = check_config_strictness(tmp_path)
            assert len(errors) > 0


class TestDiscoverConfigFiles:
    """Test dynamic config file discovery."""

    def test_discover_all_config_files(self) -> None:
        """Test discovery of all config file types."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create pyright config
            (tmp_path / "pyrightconfig.json").write_text('{"typeCheckingMode": "strict"}')

            # Create configs directory with all toml files
            configs_dir = tmp_path / "configs"
            configs_dir.mkdir()
            (configs_dir / "pyproject.toml").write_text("[tool.mypy]\nstrict = true")
            (configs_dir / "ruff.toml").write_text('[lint]\nselect = ["ALL"]')
            (configs_dir / "pylint.toml").write_text("[tool.pylint]")

            discovered = discover_config_files(tmp_path)
            rel_paths = [str(f.relative_to(tmp_path)) for f in discovered]

            assert "pyrightconfig.json" in rel_paths
            assert "configs/pyproject.toml" in rel_paths
            assert "configs/ruff.toml" in rel_paths
            assert "configs/pylint.toml" in rel_paths

    def test_discover_root_pyproject_with_quality_tools(self) -> None:
        """Test that root pyproject.toml is discovered if it has quality configs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create root pyproject with mypy config
            (tmp_path / "pyproject.toml").write_text("[tool.mypy]\nstrict = true")

            discovered = discover_config_files(tmp_path)
            rel_paths = [str(f.relative_to(tmp_path)) for f in discovered]

            assert "pyproject.toml" in rel_paths

    def test_ignore_root_pyproject_without_quality_tools(self) -> None:
        """Test that root pyproject.toml is ignored if no quality configs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create root pyproject with only uv config
            (tmp_path / "pyproject.toml").write_text("[tool.uv]\ndev-dependencies = []")

            discovered = discover_config_files(tmp_path)
            rel_paths = [str(f.relative_to(tmp_path)) for f in discovered]

            assert "pyproject.toml" not in rel_paths

    def test_discover_handles_missing_configs_dir(self) -> None:
        """Test discovery when configs directory doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Only create pyright config, no configs dir
            (tmp_path / "pyrightconfig.json").write_text('{"typeCheckingMode": "strict"}')

            discovered = discover_config_files(tmp_path)
            assert len(discovered) == 1
            assert discovered[0].name == "pyrightconfig.json"


class TestBaselineEnforcement:
    """Test baseline enforcement - these tests must fail on uncommitted drift."""

    def test_actual_codebase_baseline_no_drift(self) -> None:
        """CRITICAL: Verify actual codebase configs match baseline.

        This test runs against the REAL codebase, not a temp directory.
        If this fails, someone modified quality configs without updating baseline.
        This is intentional - baseline updates require explicit approval.
        """
        root = PROJECT_ROOT
        baseline_path = BASELINE_PATH

        if not baseline_path.exists():
            pytest.skip("No baseline file exists yet")

        drift, _current_hashes = check_baseline_drift(root, baseline_path)

        # This test MUST pass for CI to succeed
        # If it fails, you must either:
        # 1. Revert unauthorized config changes
        # 2. Get approval and run: uv run python -m tooling.run_quality_audit --update-baseline
        assert not drift, (
            f"BASELINE DRIFT DETECTED - Config files modified without approval:\n"
            f"{chr(10).join(f'  - {d}' for d in drift)}\n\n"
            f"To fix: Either revert changes or get approval and update baseline with:\n"
            f"  uv run python -m tooling.run_quality_audit --update-baseline"
        )

    def test_actual_codebase_configs_pass_strictness(self) -> None:
        """CRITICAL: Verify actual codebase configs maintain strictness.

        This test runs against the REAL codebase to ensure:
        - Pyright is in strict mode
        - Mypy is in strict mode with required settings
        - Ruff selects ALL rules
        """
        root = PROJECT_ROOT

        errors = check_config_strictness(root)

        assert not errors, f"CONFIG STRICTNESS VIOLATIONS:\n{chr(10).join(f'  - {e}' for e in errors)}"

    def test_actual_codebase_no_unjustified_ignores(self) -> None:
        """CRITICAL: Verify no inline ignores without justification.

        This test runs against the REAL codebase to ensure all inline
        ignores (type: ignore, noqa, pylint: disable) have justifications.
        """
        root = PROJECT_ROOT
        python_files = find_python_files(root)

        all_entries: list[IgnoreEntry] = []
        for py_file in python_files:
            all_entries.extend(scan_file_for_ignores(py_file, root))

        unjustified = [e for e in all_entries if e.severity == "error"]

        assert not unjustified, (
            f"UNJUSTIFIED IGNORES DETECTED:\n"
            f"{chr(10).join(f'  - {e.file_path}:{e.line_number}: {e.content[:60]}' for e in unjustified)}"
        )


class TestConfigFileCompleteness:
    """Test that all config files are dynamically indexed."""

    def test_all_config_files_tracked_for_baseline(self) -> None:
        """Test that baseline drift tracks all expected config files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create all config files
            (tmp_path / "pyrightconfig.json").write_text('{"typeCheckingMode": "strict"}')

            configs_dir = tmp_path / "configs"
            configs_dir.mkdir()

            (configs_dir / "pyproject.toml").write_text("""
[tool.mypy]
strict = true
disallow_untyped_defs = true
disallow_any_generics = true
""")
            (configs_dir / "ruff.toml").write_text('[lint]\nselect = ["ALL"]')
            (configs_dir / "pylint.toml").write_text("""
[tool.pylint.messages_control]
disable = []
""")

            # Check baseline drift - should track all 4 config files
            baseline_path = tmp_path / ".baseline.json"
            _drift, current_hashes = check_baseline_drift(tmp_path, baseline_path)

            # Verify all expected config files are tracked
            expected_files = {
                "pyrightconfig.json",
                "configs/pyproject.toml",
                "configs/ruff.toml",
                "configs/pylint.toml",
            }
            assert set(current_hashes.keys()) == expected_files

    def test_all_config_parsers_called(self) -> None:
        """Test that all config file parsers are invoked during audit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Create all config files with ignores
            (tmp_path / "pyrightconfig.json").write_text("""{
  "typeCheckingMode": "strict",
  "reportMissingTypeStubs": false
}""")
            (tmp_path / "pyrightconfig.justifications.json").write_text(
                json.dumps({"reportMissingTypeStubs": "Test justification"})
            )

            configs_dir = tmp_path / "configs"
            configs_dir.mkdir()

            (configs_dir / "pyproject.toml").write_text("""
[tool.mypy]
strict = true
disallow_untyped_defs = true
disallow_any_generics = true

[[tool.mypy.overrides]]
module = ["test.*"]
ignore_missing_imports = true  # JUSTIFIED: Test modules
""")
            (configs_dir / "ruff.toml").write_text("""
[lint]
select = ["ALL"]
ignore = [
    "E501",  # JUSTIFIED: Test ignore
]
""")
            (configs_dir / "pylint.toml").write_text("""
[tool.pylint.messages_control]
disable = [
    "line-too-long",  # JUSTIFIED: Test disable
]
""")

            # Parse all configs
            pyright_entries = parse_pyright_config_ignores(tmp_path / "pyrightconfig.json")
            mypy_entries = parse_mypy_config_ignores(configs_dir / "pyproject.toml")
            ruff_entries = parse_ruff_config_ignores(configs_dir / "ruff.toml")
            pylint_entries = parse_pylint_config_ignores(configs_dir / "pylint.toml")

            # Verify each parser found ignores
            assert len(pyright_entries) == 1, "Pyright parser should find 1 ignore"
            assert len(mypy_entries) == 1, "Mypy parser should find 1 ignore"
            assert len(ruff_entries) == 1, "Ruff parser should find 1 ignore"
            assert len(pylint_entries) == 1, "Pylint parser should find 1 ignore"

    def test_missing_config_file_not_fatal(self) -> None:
        """Test that missing config files don't cause fatal errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            # Only create some config files
            (tmp_path / "pyrightconfig.json").write_text('{"typeCheckingMode": "strict"}')

            configs_dir = tmp_path / "configs"
            configs_dir.mkdir()
            (configs_dir / "ruff.toml").write_text('[lint]\nselect = ["ALL"]')

            # Parsers should handle missing files gracefully
            mypy_entries = parse_mypy_config_ignores(configs_dir / "pyproject.toml")
            pylint_entries = parse_pylint_config_ignores(configs_dir / "pylint.toml")

            assert not mypy_entries
            assert not pylint_entries


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
