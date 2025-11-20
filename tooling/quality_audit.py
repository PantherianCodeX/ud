# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Comprehensive quality audit: ignores manifest, config baseline enforcement, and reporting.

This script provides:
1. Scanning all Python files for ignores (noqa, type: ignore, etc.)
2. Validating justifications for all ignores
3. Compiling a manifest of all ignores (code + config)
4. Comparing configs against recorded baselines
5. Generating reports in multiple formats (terminal, markdown)
6. Dry-run mode for CI/pre-commit integration

Usage:
    # Full audit with terminal output
    uv run python tooling/quality_audit.py

    # Generate markdown manifest
    uv run python tooling/quality_audit.py --manifest

    # Check and update baseline
    uv run python tooling/quality_audit.py --update-baseline

    # Dry-run for CI
    uv run python tooling/quality_audit.py --dry-run
"""

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class IgnoreEntry:
    """Represents a single ignore directive found in code or config."""

    file_path: str
    line_number: int
    ignore_type: str  # e.g., noqa_directive, type_ignore, pylint_disable
    ignore_codes: list[str]  # Specific codes if present, empty list if blanket
    content: str  # The line content
    has_justification: bool
    justification: str  # The justification text if found
    severity: str  # "error" (no justification), "warning" (blanket ignore), "info" (justified)


@dataclass
class ConfigIgnoreEntry:
    """Represents an ignore directive in config files (ruff.toml, pyproject.toml)."""

    file_path: str
    section: str  # e.g., "lint.ignore", "lint.per-file-ignores"
    codes: list[str]
    justification: str
    applies_to: str  # "global" or specific file pattern


def _empty_ignore_list() -> list[IgnoreEntry]:
    return []


def _empty_config_ignore_list() -> list[ConfigIgnoreEntry]:
    return []


def _empty_str_list() -> list[str]:
    return []


def _empty_summary() -> dict[str, int]:
    return {}


@dataclass
class AuditReport:
    """Complete audit report with all findings."""

    timestamp: str
    code_ignores: list[IgnoreEntry] = field(default_factory=_empty_ignore_list)
    config_ignores: list[ConfigIgnoreEntry] = field(default_factory=_empty_config_ignore_list)
    config_errors: list[str] = field(default_factory=_empty_str_list)
    baseline_drift: list[str] = field(default_factory=_empty_str_list)
    summary: dict[str, int] = field(default_factory=_empty_summary)


# Patterns for inline ignores
IGNORE_PATTERNS: dict[str, str] = {
    "type_ignore": r"#\s*type:\s*ignore(?:\[([^\]]+)\])?",
    "noqa": r"#\s*noqa(?::\s*([A-Z0-9,\s]+))?",
    "pylint_disable": r"#\s*pylint:\s*disable=([a-z0-9-,\s]+)",
    "pyright_ignore": r"#\s*pyright:\s*ignore(?:\[([^\]]+)\])?",
}

# Patterns indicating justification
JUSTIFICATION_PATTERNS: list[str] = [
    r"\b(because|since|due to|reason|justified|required|necessary|needed|TODO|FIXME)\b",
    r"#.*-\s*\w{3,}",  # Dash followed by explanation text
]


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file."""
    if not file_path.exists():
        return ""
    content = file_path.read_bytes()
    return hashlib.sha256(content).hexdigest()


def find_python_files(root: Path, exclude_test_files: bool = True) -> list[Path]:
    """Find all Python files, excluding virtual environments and caches.

    Args:
        root: Root directory to search
        exclude_test_files: If True, exclude test_*.py files (they contain test fixture data)
    """
    exclude_dirs = {
        ".venv",
        "venv",
        "__pycache__",
        ".git",
        "node_modules",
        "build",
        "dist",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        "htmlcov",
    }

    files = [path for path in root.rglob("*.py") if not any(excluded in path.parts for excluded in exclude_dirs)]

    if exclude_test_files:
        # Exclude test files as they contain test fixture data with intentional ignores
        files = [f for f in files if not f.name.startswith("test_")]

    return files


def extract_justification(line: str, prev_line: str | None) -> tuple[bool, str]:
    """Extract justification from current or previous line."""
    # Check current line for inline justification
    for pattern in JUSTIFICATION_PATTERNS:
        match = re.search(pattern, line, re.IGNORECASE)
        if match:
            # Extract text after the ignore directive
            ignore_end = max(
                (m.end() for p in IGNORE_PATTERNS.values() for m in [re.search(p, line, re.IGNORECASE)] if m),
                default=0,
            )
            justification = line[ignore_end:].strip(" #-")
            if justification:
                return (True, justification)

    # Check previous line for comment justification
    if prev_line and prev_line.strip().startswith("#"):
        comment_text = prev_line.strip()[1:].strip()
        for pattern in JUSTIFICATION_PATTERNS:
            if re.search(pattern, comment_text, re.IGNORECASE):
                return (True, comment_text)

    return (False, "")


def scan_file_for_ignores(file_path: Path, root: Path) -> list[IgnoreEntry]:
    """Scan a Python file for all ignore directives."""
    entries: list[IgnoreEntry] = []

    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return entries

    lines = content.split("\n")
    rel_path = str(file_path.relative_to(root))

    for line_num, line in enumerate(lines, 1):
        for ignore_type, pattern in IGNORE_PATTERNS.items():
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                # Extract specific codes if present
                codes_str = match.group(1) if match.lastindex and match.group(1) else ""
                codes = [c.strip() for c in codes_str.split(",") if c.strip()] if codes_str else []

                # Get previous line for justification check
                prev_line = lines[line_num - 2] if line_num > 1 else None

                has_justification, justification = extract_justification(line, prev_line)

                # Determine severity
                if not has_justification:
                    severity = "error"
                elif not codes:  # Blanket ignore without specific codes
                    severity = "warning"
                else:
                    severity = "info"

                entries.append(
                    IgnoreEntry(
                        file_path=rel_path,
                        line_number=line_num,
                        ignore_type=ignore_type,
                        ignore_codes=codes,
                        content=line.strip()[:100],
                        has_justification=has_justification,
                        justification=justification[:200] if justification else "",
                        severity=severity,
                    )
                )

    return entries


def parse_ruff_config_ignores(config_path: Path) -> list[ConfigIgnoreEntry]:
    """Parse ignore directives from ruff.toml."""
    entries: list[ConfigIgnoreEntry] = []

    if not config_path.exists():
        return entries

    content = config_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    current_section = ""
    in_ignore_list = False
    current_codes: list[str] = []
    current_justifications: list[str] = []
    current_file_pattern = "global"

    for line in lines:
        # Track section changes
        section_match = re.match(r"\[([\w.]+)\]", line)
        if section_match:
            current_section = section_match.group(1)
            continue

        # Track per-file-ignores patterns
        pattern_match = re.match(r'"([^"]+)"\s*=\s*\[', line)
        if pattern_match and "per-file-ignores" in current_section:
            current_file_pattern = pattern_match.group(1)
            in_ignore_list = True
            continue

        # Global ignore list start
        if re.match(r"ignore\s*=\s*\[", line):
            in_ignore_list = True
            current_file_pattern = "global"
            continue

        # Inside an ignore list
        if in_ignore_list:
            # Check for end of list
            if "]" in line and not re.search(r'"[^"]*\]', line):
                # Save accumulated ignores
                if current_codes:
                    entries.append(
                        ConfigIgnoreEntry(
                            file_path=str(config_path),
                            section=current_section,
                            codes=current_codes.copy(),
                            justification="; ".join(current_justifications) if current_justifications else "No justification",
                            applies_to=current_file_pattern,
                        )
                    )
                current_codes = []
                current_justifications = []
                in_ignore_list = False
                continue

            # Extract code and justification
            code_match = re.search(r'"([A-Z0-9]+)"', line)
            if code_match:
                current_codes.append(code_match.group(1))
                # Look for justification comment
                comment_match = re.search(r"#\s*JUSTIFIED:\s*(.+)", line)
                if comment_match:
                    current_justifications.append(f"{code_match.group(1)}: {comment_match.group(1).strip()}")

    return entries


def parse_mypy_config_ignores(config_path: Path) -> list[ConfigIgnoreEntry]:
    """Parse ignore directives from mypy config in pyproject.toml."""
    entries: list[ConfigIgnoreEntry] = []

    if not config_path.exists():
        return entries

    content = config_path.read_text(encoding="utf-8")

    # Find override sections with ignores
    override_pattern = r"\[\[tool\.mypy\.overrides\]\]([^[]+)"
    for match in re.finditer(override_pattern, content, re.DOTALL):
        section_content = match.group(1)

        # Check for ignore_missing_imports or ignore_errors
        if "ignore_missing_imports = true" in section_content or "ignore_errors = true" in section_content:
            # Extract module patterns
            module_match = re.search(r"module\s*=\s*\[([^\]]+)\]", section_content)
            if module_match:
                modules_str = module_match.group(1)
                modules = [m.strip().strip('"').strip("'") for m in modules_str.split(",")]

                # Look for justification comment before the override
                start_pos = match.start()
                prev_content = content[:start_pos]
                comment_match = re.search(r"#\s*(.+)\n\s*$", prev_content)
                justification = comment_match.group(1).strip() if comment_match else "No justification"

                ignore_type = "ignore_errors" if "ignore_errors = true" in section_content else "ignore_missing_imports"

                entries.append(
                    ConfigIgnoreEntry(
                        file_path=str(config_path),
                        section="tool.mypy.overrides",
                        codes=[ignore_type],
                        justification=justification,
                        applies_to=", ".join(modules),
                    )
                )

    return entries


def check_config_strictness(root: Path) -> list[str]:
    """Check that config files maintain required strictness settings."""
    errors: list[str] = []

    # Check pyright config
    pyright_config = root / "pyrightconfig.json"
    if pyright_config.exists():
        try:
            config = json.loads(pyright_config.read_text(encoding="utf-8"))
            if config.get("typeCheckingMode") != "strict":
                errors.append(f"{pyright_config}: typeCheckingMode must be 'strict'")
        except json.JSONDecodeError as e:
            errors.append(f"{pyright_config}: Invalid JSON: {e}")
    else:
        errors.append(f"{pyright_config}: Config file not found")

    # Check mypy config
    mypy_config = root / "configs" / "pyproject.toml"
    if mypy_config.exists():
        content = mypy_config.read_text(encoding="utf-8")
        if not re.search(r"^\s*strict\s*=\s*true", content, re.MULTILINE | re.IGNORECASE):
            errors.append(f"{mypy_config}: 'strict = true' must be set")

        required_settings = ["disallow_untyped_defs", "disallow_any_generics"]
        for setting in required_settings:
            if not re.search(rf"^\s*{setting}\s*=\s*true", content, re.MULTILINE):
                errors.append(f"{mypy_config}: '{setting} = true' must be set")
    else:
        errors.append(f"{mypy_config}: Config file not found")

    # Check ruff config
    ruff_config = root / "configs" / "ruff.toml"
    if ruff_config.exists():
        content = ruff_config.read_text(encoding="utf-8")
        if '"ALL"' not in content:
            errors.append(f"{ruff_config}: select must include 'ALL'")
    else:
        errors.append(f"{ruff_config}: Config file not found")

    return errors


def load_baseline(baseline_path: Path) -> dict[str, str]:
    """Load baseline config hashes from file."""
    if not baseline_path.exists():
        return {}
    try:
        return dict(json.loads(baseline_path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return {}


def save_baseline(baseline_path: Path, hashes: dict[str, str]) -> None:
    """Save baseline config hashes to file."""
    baseline_path.write_text(json.dumps(hashes, indent=2, sort_keys=True), encoding="utf-8")


def check_baseline_drift(root: Path, baseline_path: Path) -> tuple[list[str], dict[str, str]]:
    """Check if config files have drifted from baseline."""
    drift: list[str] = []
    current_hashes: dict[str, str] = {}

    config_files = [
        root / "pyrightconfig.json",
        root / "configs" / "pyproject.toml",
        root / "configs" / "ruff.toml",
        root / "configs" / "pylint.toml",
    ]

    for config_file in config_files:
        if config_file.exists():
            rel_path = str(config_file.relative_to(root))
            current_hash = compute_file_hash(config_file)
            current_hashes[rel_path] = current_hash

    baseline = load_baseline(baseline_path)

    if baseline:
        for file_path, current_hash in current_hashes.items():
            baseline_hash = baseline.get(file_path)
            if baseline_hash and baseline_hash != current_hash:
                drift.append(f"{file_path}: Config has been modified since baseline was recorded")
            elif not baseline_hash:
                drift.append(f"{file_path}: New config file not in baseline")

        for file_path in baseline:
            if file_path not in current_hashes:
                drift.append(f"{file_path}: Config file in baseline but not found")

    return (drift, current_hashes)


def generate_markdown_manifest(report: AuditReport, output_path: Path) -> None:
    """Generate a markdown manifest of all ignores."""
    lines = [
        "# Quality Ignores Manifest",
        "",
        f"Generated: {report.timestamp}",
        "",
        "## Summary",
        "",
        f"- Total code ignores: {report.summary.get('total_code_ignores', 0)}",
        f"- Ignores without justification: {report.summary.get('errors', 0)}",
        f"- Blanket ignores (warning): {report.summary.get('warnings', 0)}",
        f"- Properly justified ignores: {report.summary.get('info', 0)}",
        f"- Config ignores: {report.summary.get('config_ignores', 0)}",
        "",
    ]

    # Code ignores by severity
    if report.code_ignores:
        lines.extend([
            "## Code Ignores",
            "",
        ])

        # Group by severity
        errors = [e for e in report.code_ignores if e.severity == "error"]
        warnings = [e for e in report.code_ignores if e.severity == "warning"]
        info = [e for e in report.code_ignores if e.severity == "info"]

        if errors:
            lines.extend([
                "### ❌ Missing Justification (Must Fix)",
                "",
                "| File | Line | Type | Content |",
                "|------|------|------|---------|",
            ])
            for e in errors:
                lines.append(f"| {e.file_path} | {e.line_number} | {e.ignore_type} | `{e.content[:60]}` |")
            lines.append("")

        if warnings:
            lines.extend([
                "### ⚠️ Blanket Ignores (Should Specify Codes)",
                "",
                "| File | Line | Type | Content |",
                "|------|------|------|---------|",
            ])
            for e in warnings:
                lines.append(f"| {e.file_path} | {e.line_number} | {e.ignore_type} | `{e.content[:60]}` |")
            lines.append("")

        if info:
            lines.extend([
                "### ✅ Properly Justified",
                "",
                "| File | Line | Type | Codes | Justification |",
                "|------|------|------|-------|---------------|",
            ])
            for e in info:
                codes_str = ", ".join(e.ignore_codes) if e.ignore_codes else "all"
                lines.append(f"| {e.file_path} | {e.line_number} | {e.ignore_type} | {codes_str} | {e.justification[:50]} |")
            lines.append("")

    # Config ignores
    if report.config_ignores:
        lines.extend([
            "## Config File Ignores",
            "",
            "| File | Section | Codes | Applies To | Justification |",
            "|------|---------|-------|------------|---------------|",
        ])
        for cfg in report.config_ignores:
            codes_str = ", ".join(cfg.codes[:5])
            if len(cfg.codes) > 5:
                codes_str += f"... (+{len(cfg.codes) - 5})"
            lines.append(f"| {cfg.file_path} | {cfg.section} | {codes_str} | {cfg.applies_to} | {cfg.justification[:50]} |")
        lines.append("")

    # Baseline drift
    if report.baseline_drift:
        lines.extend([
            "## ⚠️ Baseline Drift Detected",
            "",
        ])
        for drift in report.baseline_drift:
            lines.append(f"- {drift}")
        lines.append("")

    # Config errors
    if report.config_errors:
        lines.extend([
            "## ❌ Configuration Errors",
            "",
        ])
        for error in report.config_errors:
            lines.append(f"- {error}")
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")


def print_terminal_report(report: AuditReport) -> None:
    """Print report to terminal."""
    print("\n" + "=" * 60)
    print("QUALITY AUDIT REPORT")
    print("=" * 60)
    print(f"\nTimestamp: {report.timestamp}")
    print("\nSummary:")
    print(f"  Total code ignores: {report.summary.get('total_code_ignores', 0)}")
    print(f"  Missing justification: {report.summary.get('errors', 0)}")
    print(f"  Blanket ignores: {report.summary.get('warnings', 0)}")
    print(f"  Properly justified: {report.summary.get('info', 0)}")
    print(f"  Config ignores: {report.summary.get('config_ignores', 0)}")

    if report.config_errors:
        print("\n❌ Configuration Errors:")
        for error in report.config_errors:
            print(f"  - {error}")

    if report.baseline_drift:
        print("\n⚠️ Baseline Drift:")
        for drift in report.baseline_drift:
            print(f"  - {drift}")

    errors = [e for e in report.code_ignores if e.severity == "error"]
    if errors:
        print("\n❌ Ignores Missing Justification:")
        for e in errors:
            print(f"  {e.file_path}:{e.line_number} - {e.ignore_type}")
            print(f"    {e.content[:80]}")

    warnings = [e for e in report.code_ignores if e.severity == "warning"]
    if warnings:
        print(f"\n⚠️ Blanket Ignores (first 10 of {len(warnings)}):")
        for e in warnings[:10]:
            print(f"  {e.file_path}:{e.line_number} - {e.ignore_type}")


def run_audit(
    root: Path,
    generate_manifest: bool = False,
    update_baseline: bool = False,
    dry_run: bool = False,
) -> int:
    """Run the complete quality audit."""
    report = AuditReport(timestamp=datetime.now(tz=UTC).isoformat())

    print("Running quality audit...")

    # 1. Scan code for ignores
    print("  Scanning Python files for ignores...")
    python_files = find_python_files(root)
    for py_file in python_files:
        report.code_ignores.extend(scan_file_for_ignores(py_file, root))

    # 2. Parse config ignores
    print("  Parsing config file ignores...")
    report.config_ignores.extend(parse_ruff_config_ignores(root / "configs" / "ruff.toml"))
    report.config_ignores.extend(parse_mypy_config_ignores(root / "configs" / "pyproject.toml"))

    # 3. Check config strictness
    print("  Checking config strictness...")
    report.config_errors = check_config_strictness(root)

    # 4. Check baseline drift
    baseline_path = root / "tooling" / ".quality_baseline.json"
    print("  Checking baseline drift...")
    report.baseline_drift, current_hashes = check_baseline_drift(root, baseline_path)

    # 5. Update baseline if requested
    if update_baseline and not dry_run:
        print("  Updating baseline...")
        save_baseline(baseline_path, current_hashes)
        print(f"  Baseline saved to {baseline_path}")

    # 6. Calculate summary
    report.summary = {
        "total_code_ignores": len(report.code_ignores),
        "errors": len([e for e in report.code_ignores if e.severity == "error"]),
        "warnings": len([e for e in report.code_ignores if e.severity == "warning"]),
        "info": len([e for e in report.code_ignores if e.severity == "info"]),
        "config_ignores": len(report.config_ignores),
        "config_errors": len(report.config_errors),
        "baseline_drift": len(report.baseline_drift),
    }

    # 7. Generate outputs
    print_terminal_report(report)

    if generate_manifest and not dry_run:
        manifest_path = root / "tooling" / "IGNORES_MANIFEST.md"
        generate_markdown_manifest(report, manifest_path)
        print(f"\nManifest saved to {manifest_path}")

    # 8. Return exit code
    has_errors = report.summary["errors"] > 0 or report.summary["config_errors"] > 0
    has_drift = report.summary["baseline_drift"] > 0

    if has_errors:
        print("\n❌ Audit FAILED: Fix errors above")
        return 1
    if has_drift and not update_baseline:
        print("\n⚠️ Audit WARNING: Config baseline drift detected")
        print("  Run with --update-baseline to accept current configs")
        return 1

    print("\n✅ Audit PASSED")
    return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Quality audit: ignores manifest and config baseline enforcement")
    parser.add_argument("--manifest", action="store_true", help="Generate markdown manifest of all ignores")
    parser.add_argument("--update-baseline", action="store_true", help="Update config baseline with current hashes")
    parser.add_argument("--dry-run", action="store_true", help="Run checks without writing files")
    parser.add_argument("--root", type=Path, default=None, help="Project root directory")

    args = parser.parse_args()

    root = args.root or Path(__file__).parent.parent

    return run_audit(
        root=root,
        generate_manifest=args.manifest,
        update_baseline=args.update_baseline,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
