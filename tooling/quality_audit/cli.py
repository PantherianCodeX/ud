# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Command-line interface for quality audit tools."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path

from .config_analyzers import (
    check_baseline_drift,
    check_config_strictness,
    check_mypy_config,
    check_pyright_config,
    check_ruff_config,
    parse_bandit_config_ignores,
    parse_mypy_config_ignores,
    parse_pylint_config_ignores,
    parse_pyright_config_ignores,
    parse_ruff_config_ignores,
    save_baseline,
)
from .models import AuditReport
from .reporting import generate_markdown_manifest, print_terminal_report
from .scanning import check_inline_ignores, find_python_files, scan_file_for_ignores


def _baseline_path(root: Path) -> Path:
    return root / ".udocket_cache" / "quality_audit" / "quality_baseline.json"


def _manifest_path(root: Path) -> Path:
    return root / "out" / "test_reports" / "quality_audit" / "IGNORES_MANIFEST.md"


def run_audit(
    *,
    root: Path,
    generate_manifest: bool = False,
    update_baseline: bool = False,
    dry_run: bool = False,
) -> int:
    """Run the comprehensive quality audit and return an exit code.

    Args:
        root: Repository root used to locate configs and source files.
        generate_manifest: When ``True``, write the markdown manifest.
        update_baseline: When ``True``, persist new config hashes after scanning.
        dry_run: Skip all filesystem writes while still printing results.

    Returns:
        int: Zero on success, non-zero when errors or drift are detected.
    """
    report = AuditReport(timestamp=datetime.now(tz=UTC).isoformat())
    print("Running quality audit...")

    print("  Scanning Python files for ignores...")
    for py_file in find_python_files(root):
        report.code_ignores.extend(scan_file_for_ignores(py_file, root))

    print("  Parsing config file ignores...")
    report.config_ignores.extend(parse_ruff_config_ignores(root / "configs" / "ruff.toml"))
    report.config_ignores.extend(parse_mypy_config_ignores(root / "configs" / "pyproject.toml"))
    report.config_ignores.extend(parse_pylint_config_ignores(root / "configs" / "pylint.toml"))
    report.config_ignores.extend(parse_pyright_config_ignores(root / "pyrightconfig.json"))
    report.config_ignores.extend(parse_bandit_config_ignores(root / "pyproject.toml"))

    print("  Checking config strictness...")
    report.config_errors = check_config_strictness(root)

    baseline_path = _baseline_path(root)
    print("  Checking baseline drift...")
    report.baseline_drift, current_hashes = check_baseline_drift(root, baseline_path)

    if update_baseline and not dry_run:
        print("  Updating baseline...")
        save_baseline(baseline_path, current_hashes)
        print(f"  Baseline saved to {baseline_path}")

    report.summary = {
        "total_code_ignores": len(report.code_ignores),
        "errors": len([entry for entry in report.code_ignores if entry.severity == "error"]),
        "warnings": len([entry for entry in report.code_ignores if entry.severity == "warning"]),
        "info": len([entry for entry in report.code_ignores if entry.severity == "info"]),
        "config_ignores": len(report.config_ignores),
        "config_errors": len(report.config_errors),
        "baseline_drift": len(report.baseline_drift),
    }

    print_terminal_report(report)

    if generate_manifest and not dry_run:
        manifest_path = _manifest_path(root)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        generate_markdown_manifest(report, manifest_path)
        print(f"\nManifest saved to {manifest_path}")

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


def run_config_check(*, root: Path) -> int:
    """Run the lightweight config + inline ignore validation.

    Args:
        root: Repository root used to locate configuration files and sources.

    Returns:
        int: Zero when checks pass, otherwise non-zero.
    """
    errors: list[str] = []
    errors.extend(check_pyright_config(root / "pyrightconfig.json"))
    errors.extend(check_mypy_config(root / "configs" / "pyproject.toml"))
    errors.extend(check_ruff_config(root / "configs" / "ruff.toml"))

    print("Checking inline ignores for justifications...")
    for py_file in find_python_files(root):
        errors.extend(check_inline_ignores(py_file))

    if errors:
        print("\nQuality configuration errors found:\n")
        for error in errors:
            print(f"  - {error}")
        print(f"\nTotal errors: {len(errors)}")
        print("\nPlease fix these issues or add proper justifications.")
        return 1

    print("All quality configuration checks passed!")
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Quality audit tooling")
    parser.add_argument("--root", type=Path, default=None, help="Project root directory")
    parser.add_argument("--manifest", action="store_true", help="Generate markdown manifest of ignores")
    parser.add_argument("--update-baseline", action="store_true", help="Update config baseline with current hashes")
    parser.add_argument("--dry-run", action="store_true", help="Run checks without writing files")
    parser.add_argument(
        "--config-only",
        action="store_true",
        help="Run only strictness + inline ignore checks (replacement for check_quality_config.py)",
    )
    return parser


def main() -> int:
    """Parse CLI flags and execute the requested quality audit workflow.

    Returns:
        int: Exit status propagated from the invoked workflow.
    """
    parser = _build_parser()
    args = parser.parse_args()
    root = args.root or Path(__file__).resolve().parents[2]

    if args.config_only:
        return run_config_check(root=root)

    return run_audit(
        root=root,
        generate_manifest=args.manifest,
        update_baseline=args.update_baseline,
        dry_run=args.dry_run,
    )


__all__ = ["main", "run_audit", "run_config_check"]
