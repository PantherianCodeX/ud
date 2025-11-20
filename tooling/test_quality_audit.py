# Copyright (c) 2025 uDocket. All Rights Reserved.
"""Tests for the quality audit script."""

import tempfile
from pathlib import Path

import pytest
from quality_audit import (
    AuditReport,
    ConfigIgnoreEntry,
    IgnoreEntry,
    check_baseline_drift,
    check_config_strictness,
    compute_file_hash,
    extract_justification,
    find_python_files,
    generate_markdown_manifest,
    load_baseline,
    parse_mypy_config_ignores,
    parse_pylint_config_ignores,
    parse_ruff_config_ignores,
    save_baseline,
    scan_file_for_ignores,
)


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
        line = "x = 1  # type: ignore"
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
            test_file.write_text(
                "x = 1  # type: ignore[arg-type]  # because API mismatch\n"
            )

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

    def test_scan_pylint_disable(self) -> None:
        """Test scanning for pylint: disable comments."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            test_file = tmp_path / "test.py"
            test_file.write_text(
                "x = 1  # pylint: disable=invalid-name  # because legacy\n"
            )

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
            assert (
                "Assert" in s101_entry.justification
                or "pytest" in s101_entry.justification
            )

    def test_parse_nonexistent_config(self) -> None:
        """Test parsing nonexistent config returns empty list."""
        entries = parse_ruff_config_ignores(Path("/nonexistent/ruff.toml"))
        assert entries == []

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
            assert (
                "No justification" in e501_entry.justification
                or not e501_entry.justification
            )


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
    "jose.*",
    "passlib.*",
]
ignore_missing_imports = true
""")

            entries = parse_mypy_config_ignores(config_file)
            assert len(entries) >= 1
            imports_entry = next(
                (e for e in entries if "ignore_missing_imports" in e.codes), None
            )
            assert imports_entry is not None
            assert "jose.*" in imports_entry.applies_to
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
            errors_entry = next(
                (e for e in entries if "ignore_errors" in e.codes), None
            )
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
            defs_entry = next(
                (e for e in entries if "disallow_untyped_defs" in e.codes), None
            )
            decorators_entry = next(
                (e for e in entries if "disallow_untyped_decorators" in e.codes), None
            )
            assert defs_entry is not None
            assert decorators_entry is not None
            assert "tests.*" in defs_entry.applies_to
            assert (
                "pytest" in defs_entry.justification.lower()
                or "test" in defs_entry.justification.lower()
            )

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
module = ["jose.*", "passlib.*"]
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
module = ["jose.*"]
ignore_missing_imports = true
""")

            entries = parse_mypy_config_ignores(config_file)
            assert len(entries) >= 1
            # Should have "No justification" or similar
            assert any(
                "No justification" in e.justification or not e.justification
                for e in entries
            )


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
            line_too_long = next(
                (e for e in entries if "line-too-long" in e.codes), None
            )
            assert line_too_long is not None
            assert "Ruff" in line_too_long.justification

            pydantic = next(
                (e for e in entries if "too-few-public-methods" in e.codes), None
            )
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
        assert entries == []

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
        assert loaded == {}


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
                baseline_drift=[],
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
                baseline_drift=[],
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
            assert "Config Ignores (Justified)" in content
            assert "ruff.toml" in content


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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
