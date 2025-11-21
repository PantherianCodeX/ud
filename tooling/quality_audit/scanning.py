# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Functions for discovering ignores in source files."""

from __future__ import annotations

import io
import re
import tokenize
from pathlib import Path
from typing import TYPE_CHECKING

from .models import IgnoreEntry, LineContext

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

IGNORE_PATTERNS: dict[str, str] = {
    "type_ignore": r"#\s*type:\s*ignore(?:\[([^\]]+)\])?",
    "noqa": r"#\s*noqa(?::\s*([A-Z0-9,\s]+))?",
    "pylint_disable": r"#\s*pylint:\s*disable=([a-z0-9-,\s]+)",
    "pyright_ignore": r"#\s*pyright:\s*ignore(?:\[([^\]]+)\])?",
    "nosec": r"#\s*nosec(?:\s*([A-Z0-9,\s]+))?",
}

JUSTIFICATION_PATTERNS: list[str] = [
    r"\b(because|since|due to|reason|justified|required|necessary|needed|TODO|FIXME|HACK|WORKAROUND|TEMP)\b",
    r"#.*-\s+\w{3,}",
]

EXCLUDED_DIRS = {
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
}


def find_python_files(root: Path, exclude_test_files: bool = False) -> list[Path]:
    """Return python files from ``root`` respecting exclusion rules."""

    def _should_include(path: Path) -> bool:
        if any(part in EXCLUDED_DIRS for part in path.parts):
            return False
        if exclude_test_files and path.name.startswith("test_"):  # noqa: SIM103 - readability prioritized over inline negation
            return False
        return True

    python_files: list[Path] = [path for path in root.rglob("*.py") if _should_include(path)]
    return python_files


def extract_justification(line: str, prev_line: str | None) -> tuple[bool, str]:
    """Return whether justification exists and the extracted text."""

    def _match(text: str) -> str | None:
        for pattern in JUSTIFICATION_PATTERNS:
            if match := re.search(pattern, text, re.IGNORECASE):
                return match.group(0)
        return None

    if match := _match(line):
        return True, match.strip()
    if prev_line and prev_line.strip().startswith("#") and (match := _match(prev_line)):
        return True, match.strip()
    return False, ""


def _create_ignore_entry(
    line_context: LineContext,
    ignore_type: str,
    match: re.Match[str],
    prev_line: str | None,
) -> IgnoreEntry:
    codes_str = match.group(1) if match.lastindex and match.group(1) else ""
    codes = [code.strip() for code in codes_str.split(",") if code.strip()]
    has_justification, justification = extract_justification(line_context.line_content, prev_line)

    if not has_justification or (not codes and ignore_type in {"noqa", "nosec"}):
        severity = "error"
    elif not codes:
        severity = "warning"
    else:
        severity = "info"

    return IgnoreEntry(
        file_path=line_context.file_path,
        line_number=line_context.line_number,
        ignore_type=ignore_type,
        ignore_codes=codes,
        content=line_context.line_content.strip()[:100],
        has_justification=has_justification,
        justification=justification[:200] if justification else "",
        severity=severity,
    )


def _comment_tokens(content: str) -> Iterator[tuple[str, int]]:
    reader = io.StringIO(content).readline
    try:
        for token in tokenize.generate_tokens(reader):
            if token.type == tokenize.COMMENT:
                yield token.string, token.start[0]
    except tokenize.TokenError:
        return


def scan_file_for_ignores(file_path: Path, root: Path) -> list[IgnoreEntry]:
    """Scan ``file_path`` and return ignore entries relative to ``root``."""
    entries: list[IgnoreEntry] = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return entries

    lines = content.split("\n")
    rel_path = str(file_path.relative_to(root))

    for token_text, line_num in _comment_tokens(content):
        if not 0 < line_num <= len(lines):
            continue
        line_content = lines[line_num - 1]
        prev_line = lines[line_num - 2] if line_num > 1 else None
        context = LineContext(file_path=rel_path, line_number=line_num, line_content=line_content)
        for ignore_type, pattern in IGNORE_PATTERNS.items():
            if match := re.search(pattern, token_text, re.IGNORECASE):
                entries.append(_create_ignore_entry(context, ignore_type, match, prev_line))

    return entries


def check_inline_ignores(file_path: Path) -> list[str]:
    """Return human-readable errors for inline ignores lacking justification."""
    root = file_path.parent if file_path.parent.exists() else file_path
    entries = scan_file_for_ignores(file_path, root)
    errors: list[str] = []
    for entry in entries:
        if entry.severity != "error":
            continue
        errors.append(
            f"{file_path}:{entry.line_number}: {entry.ignore_type} missing justification: {entry.content.strip()[:80]}"
        )
    return errors


__all__ = [
    "IGNORE_PATTERNS",
    "JUSTIFICATION_PATTERNS",
    "check_inline_ignores",
    "extract_justification",
    "find_python_files",
    "scan_file_for_ignores",
]
