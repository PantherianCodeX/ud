# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Validate quality configuration integrity and ignore justifications.

This script ensures:
1. Critical typing/linting settings haven't been weakened
2. All inline ignores have accompanying justification comments
"""

import ast
import json
import re
import sys
from pathlib import Path

StringNode = ast.Constant | ast.JoinedStr

# Patterns for finding inline ignores

IGNORE_PATTERNS = [
    r"#\s*type:\s*ignore",
    r"#\s*noqa",
    r"#\s*pylint:\s*disable",
    r"#\s*pyright:\s*ignore",
]


# Patterns that indicate justification (case-insensitive)

JUSTIFICATION_INDICATORS = [
    r"\b(because|since|due to|reason|justified|required|necessary|needed)\b",
    r"-\s*\w",  # Dash followed by explanation (e.g., "
]


def check_pyright_config(config_path: Path) -> list[str]:
    """Check pyright configuration for strictness requirements."""
    errors: list[str] = []

    if not config_path.exists():
        errors.append(f"Pyright config not found: {config_path}")

        return errors

    with config_path.open(encoding="utf-8") as f:
        config = json.load(f)

    # Check strict mode

    if config.get("typeCheckingMode") != "strict":
        errors.append(f"{config_path}: typeCheckingMode must be 'strict', found '{config.get('typeCheckingMode')}'")

    return errors


def check_mypy_config(config_path: Path) -> list[str]:
    """Check mypy configuration for strictness requirements."""
    errors: list[str] = []

    if not config_path.exists():
        errors.append(f"Mypy config not found: {config_path}")

        return errors

    content = config_path.read_text(encoding="utf-8")

    # Check strict mode is enabled

    if not re.search(r"^\s*strict\s*=\s*true", content, re.MULTILINE | re.IGNORECASE):
        errors.append(f"{config_path}: 'strict = true' must be set")

    # Check critical disallow settings (should be true at global level)

    critical_settings = [
        "disallow_untyped_defs",
        "disallow_any_generics",
    ]

    for setting in critical_settings:
        # Look for global setting (not in overrides)

        pattern = rf"^\s*{setting}\s*=\s*true"

        if not re.search(pattern, content, re.MULTILINE):
            errors.append(f"{config_path}: '{setting} = true' must be set globally")

    return errors


def check_ruff_config(config_path: Path) -> list[str]:
    """Check ruff configuration for maximum strictness."""
    errors: list[str] = []

    if not config_path.exists():
        errors.append(f"Ruff config not found: {config_path}")

        return errors

    content = config_path.read_text(encoding="utf-8")

    # Check that ALL is in select

    if '"ALL"' not in content:
        errors.append(f"{config_path}: select must include 'ALL'")

    return errors


def find_python_files(root: Path) -> list[Path]:
    """Find all Python files, excluding virtual environments and caches."""
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
    }

    python_files: list[Path] = [
        path for path in root.rglob("*.py") if not any(excluded in path.parts for excluded in exclude_dirs)
    ]

    return python_files


def _has_justification_on_line(line: str) -> bool:
    """Check if a line contains a justification indicator."""
    return any(re.search(indicator, line, re.IGNORECASE) for indicator in JUSTIFICATION_INDICATORS)


def _check_justification(line: str, line_num: int, lines: list[str]) -> bool:
    """Check if a line or its previous line has a justification."""
    has_justification = False
    if _has_justification_on_line(line):
        has_justification = True
    if (
        not has_justification
        and line_num > 1
        and (prev_line := lines[line_num - 2]).strip().startswith("#")
        and _has_justification_on_line(prev_line)
    ):
        has_justification = True
    return has_justification


def check_inline_ignores(file_path: Path) -> list[str]:
    """Check that inline ignores have justifications."""
    errors: list[str] = []

    try:
        content = file_path.read_text(encoding="utf-8")

        tree = ast.parse(content)

    except (OSError, UnicodeDecodeError, SyntaxError) as e:
        errors.append(f"{file_path}: Could not read or parse file: {e}")

        return errors

    # Get line numbers of all string literals

    string_literal_lines: set[int] = set()

    for node in ast.walk(tree):
        string_node: StringNode | None = None
        if (isinstance(node, ast.Constant) and isinstance(node.value, str)) or isinstance(node, ast.JoinedStr):
            string_node = node
        if string_node is None:
            continue

        start_line = string_node.lineno
        end_line = getattr(string_node, "end_lineno", string_node.lineno) or string_node.lineno
        if end_line > start_line:
            string_literal_lines.update(range(start_line, end_line + 1))

    lines = content.split("\n")

    for line_num, line in enumerate(lines, 1):
        # If the line is part of a string literal, skip it.

        # This is a heuristic to avoid flagging ignores in test data.

        if line_num in string_literal_lines:
            continue

        # Check if line contains an ignore pattern

        has_ignore = any(re.search(pattern, line, re.IGNORECASE) for pattern in IGNORE_PATTERNS)
        if has_ignore and not _check_justification(line, line_num, lines):
            errors.append(f"{file_path}:{line_num}: Inline ignore without justification: {line.strip()[:80]}")

    return errors


def main() -> int:
    """Run all quality configuration checks."""
    root = Path(__file__).parent.parent
    errors: list[str] = []

    print("Checking quality configuration integrity...")

    # Check type checker configs
    errors.extend(check_pyright_config(root / "pyrightconfig.json"))
    errors.extend(check_mypy_config(root / "configs" / "pyproject.toml"))
    errors.extend(check_ruff_config(root / "configs" / "ruff.toml"))

    # Check inline ignores in Python files
    print("Checking inline ignores for justifications...")
    python_files = find_python_files(root)

    for py_file in python_files:
        errors.extend(check_inline_ignores(py_file))

    # Report results
    if errors:
        print("\nQuality configuration errors found:\n")
        for error in errors:
            print(f"  - {error}")
        print(f"\nTotal errors: {len(errors)}")
        print("\nPlease fix these issues or add proper justifications.")
        print("See PRPs/ai_docs/CODE_QA.md for ignore justification requirements.")
        return 1

    print("All quality configuration checks passed!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
