# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Config parsing, strictness, and baseline helpers for quality audit."""

from __future__ import annotations

import json
import re
from hashlib import sha256
from typing import TYPE_CHECKING, Any

from .models import ConfigIgnoreEntry
from .utils import ensure_json_object

TYPE_CHECKING_MODE_KEY = "typeCheckingMode"
STRICT_MODE = "strict"

if TYPE_CHECKING:
    from pathlib import Path


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of a file, returning empty string when missing.

    Args:
        file_path: File whose contents should be hashed.

    Returns:
        str: Hex digest for existing files or an empty string when missing.
    """
    if not file_path.exists():
        return ""
    return sha256(file_path.read_bytes()).hexdigest()


def check_pyright_config(config_path: Path) -> list[str]:
    """Validate that Pyright config exists and remains in strict mode.

    Args:
        config_path: Path to ``pyrightconfig.json``.

    Returns:
        list[str]: Validation errors discovered for the config.
    """
    errors: list[str] = []
    if not config_path.exists():
        errors.append(f"Pyright config not found: {config_path}")
        return errors
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{config_path}: Invalid JSON: {exc}")
        return errors
    if (type_mode := config.get(TYPE_CHECKING_MODE_KEY)) != STRICT_MODE:
        errors.append(f"{config_path}: typeCheckingMode must be strict, found {type_mode}")
    return errors


def check_mypy_config(config_path: Path) -> list[str]:
    """Validate that Mypy config exists and enforces critical strict settings.

    Args:
        config_path: Path to the ``pyproject.toml`` file containing mypy settings.

    Returns:
        list[str]: Validation errors describing missing strict options.
    """
    errors: list[str] = []
    if not config_path.exists():
        errors.append(f"Mypy config not found: {config_path}")
        return errors
    content = config_path.read_text(encoding="utf-8")
    if not re.search(r"^\s*strict\s*=\s*true", content, re.MULTILINE | re.IGNORECASE):
        errors.append(f"{config_path}: 'strict = true' must be set")
    for setting in ("disallow_untyped_defs", "disallow_any_generics"):
        if not re.search(rf"^\s*{setting}\s*=\s*true", content, re.MULTILINE):
            errors.append(f"{config_path}: '{setting} = true' must be set globally")
    return errors


def check_ruff_config(config_path: Path) -> list[str]:
    """Validate that Ruff config selects every rule (strict enforcement).

    Args:
        config_path: Path to the Ruff configuration file.

    Returns:
        list[str]: Validation errors related to rule selection.
    """
    errors: list[str] = []
    if not config_path.exists():
        errors.append(f"Ruff config not found: {config_path}")
        return errors
    content = config_path.read_text(encoding="utf-8")
    if '"ALL"' not in content:
        errors.append(f"{config_path}: select must include 'ALL'")
    return errors


def parse_ruff_config_ignores(config_path: Path) -> list[ConfigIgnoreEntry]:
    """Parse lint/per-file ignore entries from ``config_path``.

    Args:
        config_path: Path to the Ruff configuration file.

    Returns:
        list[ConfigIgnoreEntry]: Parsed ignore metadata with justifications.
    """
    entries: list[ConfigIgnoreEntry] = []
    if not config_path.exists():
        return entries

    content = config_path.read_text(encoding="utf-8")
    lines = content.split("\n")
    current_section = ""
    in_ignore_list = False
    current_file_pattern = "global"

    for line in lines:
        if section_match := re.match(r"\[([^\]]+)\]", line):
            current_section = section_match.group(1)
            in_ignore_list = False
            continue
        pattern_match = re.match(r'"([^"]+)"\s*=\s*\[', line)
        if pattern_match and "per-file-ignores" in current_section:
            current_file_pattern = pattern_match.group(1)
            in_ignore_list = True
            continue

        if re.match(r"ignore\s*=\s*\[", line):
            in_ignore_list = True
            current_file_pattern = "global"
            continue

        if in_ignore_list and "]" in line and not re.search(r'"[^"]*\]', line):
            in_ignore_list = False
            current_file_pattern = "global"
            continue

        if in_ignore_list and (code_match := re.search(r'"([A-Z0-9]+)"', line)):
            code = code_match.group(1)
            comment_match = re.search(r"#\s*JUSTIFIED:\s*(.+)", line)
            justification = comment_match.group(1).strip() if comment_match else "No justification"
            entries.append(
                ConfigIgnoreEntry(
                    file_path=str(config_path),
                    section=current_section,
                    codes=[code],
                    justification=justification,
                    applies_to=current_file_pattern,
                )
            )

    return entries


def _parse_mypy_override_section(
    config_path: Path,
    section_content: str,
    section_justification: str,
) -> list[ConfigIgnoreEntry]:
    """Parse a single mypy override block for ignored directives.

    Args:
        config_path: Path to the configuration file being parsed.
        section_content: Raw text for the override section.
        section_justification: Justification comment pulled from the config.

    Returns:
        list[ConfigIgnoreEntry]: Parsed override entries from the section.
    """
    section_lines = section_content.split("\n")
    entries: list[ConfigIgnoreEntry] = []

    if not (module_match := re.search(r"module\s*=\s*\[([^\]]+)\]", section_content, re.DOTALL)):
        if single_module := re.search(r'module\s*=\s*["\']([^"\']+)["\']', section_content):
            modules = [single_module.group(1)]
        else:
            return entries
    else:
        modules = re.findall(r'["\']([^"\']+)["\']', module_match.group(1))

    applies_to = ", ".join(modules)

    ignore_directives = (
        ("ignore_missing_imports", r"ignore_missing_imports\s*=\s*true"),
        ("ignore_errors", r"ignore_errors\s*=\s*true"),
        ("disallow_untyped_defs", r"disallow_untyped_defs\s*=\s*false"),
        ("disallow_untyped_decorators", r"disallow_untyped_decorators\s*=\s*false"),
    )

    for directive_name, pattern in ignore_directives:
        for line in section_lines:
            if re.search(pattern, line):
                if inline_match := re.search(r"#\s*JUSTIFIED:\s*(.+)", line):
                    justification = inline_match.group(1).strip()
                elif section_justification:
                    justification = section_justification
                else:
                    justification = "No justification"

                entries.append(
                    ConfigIgnoreEntry(
                        file_path=str(config_path),
                        section="tool.mypy.overrides",
                        codes=[directive_name],
                        justification=justification,
                        applies_to=applies_to,
                    )
                )
                break

    return entries


def parse_mypy_config_ignores(config_path: Path) -> list[ConfigIgnoreEntry]:
    """Extract ignore overrides from mypy configuration.

    Args:
        config_path: Path to the ``pyproject.toml`` file containing mypy config.

    Returns:
        list[ConfigIgnoreEntry]: Recorded overrides with their justifications.
    """
    entries: list[ConfigIgnoreEntry] = []
    if not config_path.exists():
        return entries

    content = config_path.read_text(encoding="utf-8")
    override_pattern = r"\[\[tool\.mypy\.overrides\]\](.*?)(?=\[\[|\[tool\.|\Z)"

    for match in re.finditer(override_pattern, content, re.DOTALL):
        section_content = match.group(1)
        start_pos = match.start()
        prev_content = content[:start_pos]
        if section_comment_match := re.search(r"#\s*JUSTIFIED:\s*(.+)\n\s*$", prev_content):
            section_justification = section_comment_match.group(1).strip()
        else:
            section_justification = ""

        entries.extend(_parse_mypy_override_section(config_path, section_content, section_justification))

    return entries


def parse_pylint_config_ignores(config_path: Path) -> list[ConfigIgnoreEntry]:
    """Gather disabled pylint rules along with justifications.

    Args:
        config_path: Path to the ``pylint`` TOML configuration.

    Returns:
        list[ConfigIgnoreEntry]: Entries covering disabled rules and scopes.
    """
    entries: list[ConfigIgnoreEntry] = []
    if not config_path.exists():
        return entries

    content = config_path.read_text(encoding="utf-8")
    lines = content.split("\n")
    in_disable_list = False

    for line in lines:
        if re.match(r"disable\s*=\s*\[", line):
            in_disable_list = True
            continue
        if in_disable_list and "]" in line and not re.search(r'"[^"]*\]', line):
            in_disable_list = False
            continue
        if in_disable_list and (rule_match := re.search(r'"([a-z0-9-]+)"', line)):
            rule = rule_match.group(1)
            comment_match = re.search(r"#\s*JUSTIFIED:\s*(.+)", line)
            justification = comment_match.group(1).strip() if comment_match else "No justification"
            entries.append(
                ConfigIgnoreEntry(
                    file_path=str(config_path),
                    section="tool.pylint.messages_control",
                    codes=[rule],
                    justification=justification,
                    applies_to="global",
                )
            )

    return entries


def _load_pyright_justifications(config_path: Path) -> dict[str, str]:
    """Load custom justifications for pyright report ignores.

    Args:
        config_path: Path to ``pyrightconfig.json`` whose sidecar file is read.

    Returns:
        dict[str, str]: Mapping of report setting to justification text.
    """
    justification_path = config_path.with_suffix(".justifications.json")
    if not justification_path.exists():
        return {}
    try:
        raw_data: Any = json.loads(justification_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}

    try:
        json_object = ensure_json_object(raw_data, context="pyright justification map")
    except ValueError:
        return {}

    return {key: value for key, value in json_object.items() if isinstance(value, str)}


def parse_pyright_config_ignores(config_path: Path) -> list[ConfigIgnoreEntry]:
    """Extract pyright report* ignores and attach stored justifications.

    Args:
        config_path: Path to ``pyrightconfig.json``.

    Returns:
        list[ConfigIgnoreEntry]: Pyright ignore entries plus justifications.
    """
    entries: list[ConfigIgnoreEntry] = []
    if not config_path.exists():
        return entries
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return entries

    justifications = _load_pyright_justifications(config_path)

    for key, value in config.items():
        if key.startswith("report") and value is False:
            justification = justifications.get(key, "No justification")
            entries.append(
                ConfigIgnoreEntry(
                    file_path=str(config_path),
                    section="pyright",
                    codes=[key],
                    justification=justification,
                    applies_to="global",
                )
            )

    return entries


def parse_bandit_config_ignores(pyproject_path: Path) -> list[ConfigIgnoreEntry]:
    """Parse allowed Bandit ignores from the workspace pyproject.

    Args:
        pyproject_path: Root ``pyproject.toml`` that stores Bandit config.

    Returns:
        list[ConfigIgnoreEntry]: Bandit ignore configuration entries.
    """
    entries: list[ConfigIgnoreEntry] = []
    if not pyproject_path.exists():
        return entries

    content = pyproject_path.read_text(encoding="utf-8")
    lines = content.split("\n")
    in_section = False
    current_list = ""

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[tool.bandit]"):
            in_section = True
            continue
        if in_section and stripped.startswith("[") and not stripped.startswith("[tool.bandit]"):
            break
        if not in_section:
            continue

        if match := re.match(r"(\w+)\s*=\s*\[", stripped):
            current_list = match.group(1)
            continue
        if current_list and stripped.startswith("]"):
            current_list = ""
            continue
        if current_list and (value_match := re.search(r'"([^"]+)"', line)):
            value = value_match.group(1)
            comment_match = re.search(r"#\s*JUSTIFIED:\s*(.+)", line)
            justification = comment_match.group(1).strip() if comment_match else "No justification"
            if current_list == "exclude_dirs":
                code = "exclude_dir"
                applies_to = value
            else:
                code = value
                applies_to = "global"
            entries.append(
                ConfigIgnoreEntry(
                    file_path=str(pyproject_path),
                    section=f"tool.bandit.{current_list}",
                    codes=[code],
                    justification=justification,
                    applies_to=applies_to,
                )
            )

    return entries


def _check_pyright_strictness(root: Path) -> list[str]:
    return check_pyright_config(root / "pyrightconfig.json")


def _check_mypy_strictness(root: Path) -> list[str]:
    return check_mypy_config(root / "configs" / "pyproject.toml")


def _check_ruff_strictness(root: Path) -> list[str]:
    return check_ruff_config(root / "configs" / "ruff.toml")


def check_config_strictness(root: Path) -> list[str]:
    """Enforce strictness policies on Pyright, Mypy, and Ruff configs.

    Args:
        root: Repository root containing the configuration files.

    Returns:
        list[str]: Aggregated strictness violations.
    """
    errors: list[str] = []
    errors.extend(_check_pyright_strictness(root))
    errors.extend(_check_mypy_strictness(root))
    errors.extend(_check_ruff_strictness(root))
    return errors


def load_baseline(baseline_path: Path) -> dict[str, str]:
    """Read the saved baseline hashes of configuration files.

    Args:
        baseline_path: Path to the JSON file storing baseline hashes.

    Returns:
        dict[str, str]: Mapping of relative file path to recorded hash.
    """
    if not baseline_path.exists():
        return {}
    try:
        return dict(json.loads(baseline_path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return {}


def save_baseline(baseline_path: Path, hashes: dict[str, str]) -> None:
    """Persist baseline hashes so drift can be detected later.

    Args:
        baseline_path: Where to write the serialized baseline data.
        hashes: Mapping of relative file paths to their hash digests.
    """
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_path.write_text(json.dumps(hashes, indent=2, sort_keys=True), encoding="utf-8")


def discover_config_files(root: Path) -> list[Path]:
    """Discover every quality-related configuration file to track.

    Args:
        root: Repository root to scan for configuration files.

    Returns:
        list[Path]: Sorted list of configuration file paths.
    """
    config_files: list[Path] = []

    pyright_config = root / "pyrightconfig.json"
    if pyright_config.exists():
        config_files.append(pyright_config)

    configs_dir = root / "configs"
    if configs_dir.exists():
        config_files.extend(configs_dir.glob("*.toml"))

    root_pyproject = root / "pyproject.toml"
    if root_pyproject.exists():
        content = root_pyproject.read_text(encoding="utf-8")
        if any(
            section in content
            for section in (
                "[tool.mypy]",
                "[tool.ruff]",
                "[tool.pylint]",
                "[tool.pyright]",
            )
        ):
            config_files.append(root_pyproject)

    return sorted(config_files)


def check_baseline_drift(root: Path, baseline_path: Path) -> tuple[tuple[str, ...], dict[str, str]]:
    """Detect if tracked configuration files differ from the saved baseline.

    Args:
        root: Repository root that owns the configuration files.
        baseline_path: Path to the saved baseline JSON file.

    Returns:
        tuple[tuple[str, ...], dict[str, str]]: Drift messages and updated hashes.
    """
    drift: list[str] = []
    current_hashes: dict[str, str] = {}

    config_files = discover_config_files(root)

    for config_file in config_files:
        if config_file.exists():
            rel_path = str(config_file.relative_to(root))
            current_hashes[rel_path] = compute_file_hash(config_file)

    if baseline := load_baseline(baseline_path):
        for file_path, current_hash in current_hashes.items():
            baseline_hash = baseline.get(file_path)
            if baseline_hash and baseline_hash != current_hash:
                drift.append(f"{file_path}: Config has been modified since baseline was recorded")
            elif not baseline_hash:
                drift.append(f"{file_path}: New config file not in baseline")

        for file_path in baseline:
            if file_path not in current_hashes:
                drift.append(f"{file_path}: Config file in baseline but not found")

    return (tuple(drift), current_hashes)
