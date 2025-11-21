# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Reporting helpers for quality audit scripts."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .utils import ROOT

if TYPE_CHECKING:
    from .models import AuditReport, ConfigIgnoreEntry, IgnoreEntry


def _append_code_ignores_to_manifest(lines: list[str], code_ignores: list[IgnoreEntry]) -> None:
    lines.extend(["## Code Ignores", ""])

    errors = [entry for entry in code_ignores if entry.severity == "error"]
    if errors:
        lines.extend([
            "### ❌ Missing Justification (Must Fix)",
            "",
            "| File | Line | Type | Content |",
            "|------|------|------|---------|",
        ])
        for entry in errors:
            lines.append(f"| {entry.file_path} | {entry.line_number} | {entry.ignore_type} | `{entry.content[:60]}` |")
        lines.append("")

    warnings = [entry for entry in code_ignores if entry.severity == "warning"]
    if warnings:
        lines.extend([
            "### ⚠️ Blanket Ignores (Should Specify Codes)",
            "",
            "| File | Line | Type | Content |",
            "|------|------|------|---------|",
        ])
        for entry in warnings:
            lines.append(f"| {entry.file_path} | {entry.line_number} | {entry.ignore_type} | `{entry.content[:60]}` |")
        lines.append("")

    info = [entry for entry in code_ignores if entry.severity == "info"]
    if info:
        lines.extend([
            "### ✅ Properly Justified",
            "",
            "| File | Line | Type | Codes | Justification |",
            "|------|------|------|-------|---------------|",
        ])
        for entry in info:
            codes_str = ", ".join(entry.ignore_codes) if entry.ignore_codes else "all"
            lines.append(
                f"| {entry.file_path} | {entry.line_number} | {entry.ignore_type} | {codes_str} | {entry.justification[:50]} |"
            )
        lines.append("")


def _format_config_path_for_manifest(path_str: str) -> str:
    path = Path(path_str)
    if path.is_absolute():
        try:
            return str(path.relative_to(ROOT))
        except ValueError:
            return path.as_posix()
    return path.as_posix()


def _append_config_ignores_to_manifest(lines: list[str], config_ignores: list[ConfigIgnoreEntry]) -> None:
    if not config_ignores:
        return

    lines.extend(["## Config Ignores by File", ""])

    if any(entry.justification == "No justification" for entry in config_ignores):
        lines.extend(["> ⚠️ Entries showing `No justification` require follow-up.", ""])

    grouped: dict[str, list[ConfigIgnoreEntry]] = {}
    for entry in config_ignores:
        display_path = _format_config_path_for_manifest(entry.file_path)
        grouped.setdefault(display_path, []).append(entry)

    for file_path in sorted(grouped):
        lines.extend([
            f"### {file_path}",
            "",
            "| Section | Code | Applies To | Justification |",
            "|---------|------|------------|---------------|",
        ])
        for entry in sorted(grouped[file_path], key=lambda e: (e.section, ", ".join(e.codes), e.applies_to)):
            code = ", ".join(entry.codes) if entry.codes else "unknown"
            justification = entry.justification or "No justification"
            if justification == "No justification":
                justification = "No justification ⚠️"
            lines.append(f"| {entry.section} | {code} | {entry.applies_to} | {justification} |")
        lines.append("")


def _append_baseline_drift_to_manifest(lines: list[str], baseline_drift: tuple[str, ...]) -> None:
    lines.extend(["## ⚠️ Baseline Drift Detected", ""])
    for drift in baseline_drift:
        lines.append(f"- {drift}")
    lines.append("")


def _append_config_errors_to_manifest(lines: list[str], config_errors: list[str]) -> None:
    lines.extend(["## ❌ Configuration Errors", ""])
    for error in config_errors:
        lines.append(f"- {error}")
    lines.append("")


def generate_markdown_manifest(report: AuditReport, output_path: Path) -> None:
    """Create the markdown manifest summarizing ignore metadata."""
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

    if report.code_ignores:
        _append_code_ignores_to_manifest(lines, report.code_ignores)
    if report.config_ignores:
        _append_config_ignores_to_manifest(lines, report.config_ignores)
    if report.baseline_drift:
        _append_baseline_drift_to_manifest(lines, report.baseline_drift)
    if report.config_errors:
        _append_config_errors_to_manifest(lines, report.config_errors)

    output_path.write_text("\n".join(lines), encoding="utf-8")


def print_terminal_report(report: AuditReport) -> None:
    """Render a human-readable quality audit summary to the terminal."""
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

    errors = [entry for entry in report.code_ignores if entry.severity == "error"]
    if errors:
        print("\n❌ Ignores Missing Justification:")
        for entry in errors:
            print(f"  {entry.file_path}:{entry.line_number} - {entry.ignore_type}")
            print(f"    {entry.content[:80]}")

    warnings = [entry for entry in report.code_ignores if entry.severity == "warning"]
    if warnings:
        print(f"\n⚠️ Blanket Ignores (first 10 of {len(warnings)}):")
        for entry in warnings[:10]:
            print(f"  {entry.file_path}:{entry.line_number} - {entry.ignore_type}")


__all__ = [
    "generate_markdown_manifest",
    "print_terminal_report",
]
