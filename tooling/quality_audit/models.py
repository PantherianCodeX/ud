# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Dataclasses shared by the quality audit tooling."""

from __future__ import annotations

from dataclasses import dataclass, field


def _empty_ignore_list() -> list[IgnoreEntry]:
    return []


def _empty_config_ignore_list() -> list[ConfigIgnoreEntry]:
    return []


def _empty_str_list() -> list[str]:
    return []


def _empty_str_tuple() -> tuple[str, ...]:
    return ()


def _empty_summary() -> dict[str, int]:
    return {}


@dataclass
class LineContext:
    """File/line context used when reporting inline ignores."""

    file_path: str
    line_number: int
    line_content: str


@dataclass
class IgnoreEntry:
    """Represents a single ignore directive found in code or config."""

    file_path: str
    line_number: int
    ignore_type: str
    ignore_codes: list[str]
    content: str
    has_justification: bool
    justification: str
    severity: str


@dataclass
class ConfigIgnoreEntry:
    """Represents an ignore directive in config files (ruff, pyproject, etc.)."""

    file_path: str
    section: str
    codes: list[str]
    justification: str
    applies_to: str


@dataclass
class AuditReport:
    """Complete audit report with all findings."""

    timestamp: str
    code_ignores: list[IgnoreEntry] = field(default_factory=_empty_ignore_list)
    config_ignores: list[ConfigIgnoreEntry] = field(default_factory=_empty_config_ignore_list)
    config_errors: list[str] = field(default_factory=_empty_str_list)
    baseline_drift: tuple[str, ...] = field(default_factory=_empty_str_tuple)
    summary: dict[str, int] = field(default_factory=_empty_summary)


__all__ = [
    "AuditReport",
    "ConfigIgnoreEntry",
    "IgnoreEntry",
    "LineContext",
]
