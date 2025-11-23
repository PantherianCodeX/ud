# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""doit tasks mirroring CI quality checks with consistent report locations."""

from __future__ import annotations

import json
import os
import shutil
import subprocess  # noqa: S404  # nosec B404 - Doit tasks must shell out to trusted CLIs
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from doit.exceptions import TaskFailed

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

TaskConfig = dict[str, Any]
ActionResult = TaskFailed | None

# pylint: disable=missing-return-doc  # JUSTIFIED: Doit mandates specific return schemas

ROOT = Path(__file__).resolve().parent
CONFIG_DIR = ROOT / "configs"
OUT_DIR = ROOT / "out" / "test_reports"
LINT_DIR = OUT_DIR / "lint"
TYPECHECK_DIR = OUT_DIR / "typecheck"
TEST_DIR = OUT_DIR / "tests"
SECURITY_DIR = OUT_DIR / "security"
QUALITY_DIR = OUT_DIR / "quality"
COVERAGE_DIR = OUT_DIR / "coverage"
PRETTIER_BIN = ROOT / "node_modules" / ".bin" / "prettier"


def _task_label(func_name: str) -> str:
    return func_name.removeprefix("task_")


def _log(message: str) -> None:
    sys.stdout.write(message + "\n")
    sys.stdout.flush()


def _with_task_logging(task_name: str, action: Callable[[], ActionResult]) -> Callable[[], ActionResult]:
    def _wrapper() -> ActionResult:
        _log(f"[doit] Starting task '{task_name}'")
        try:
            result = action()
        except Exception:
            _log(f"[doit] Task '{task_name}' failed with exception.")
            raise
        if isinstance(result, TaskFailed):
            _log(f"[doit] Task '{task_name}' failed.")
        else:
            _log(f"[doit] Finished task '{task_name}'.")
        return result

    return _wrapper


def _task_config(task_func_name: str, action: Callable[[], ActionResult]) -> TaskConfig:
    task_name = _task_label(task_func_name)
    return {"actions": [_with_task_logging(task_name, action)], "verbosity": 2}


def _ensure_dirs(directories: Iterable[Path]) -> None:
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def _run(cmd: list[str], *, env: dict[str, str] | None = None) -> int:
    final_env = os.environ | (env or {})
    result = subprocess.run(  # noqa: S603  # nosec B603 - Commands are static strings defined in repo
        cmd,
        check=False,
        cwd=ROOT,
        env=final_env,
    )
    return result.returncode


def _run_task_action(cmd: list[str], *, env: dict[str, str] | None = None) -> TaskFailed | None:
    exit_code = _run(cmd, env=env)
    if exit_code:
        return _task_failure(cmd, exit_code)
    return None


def _run_capture(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603  # nosec B603 - Controlled command list
        cmd,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _emit(result: subprocess.CompletedProcess[str]) -> None:
    if result.stdout:
        sys.stdout.write(result.stdout)
    if result.stderr:
        sys.stderr.write(result.stderr)


def _raise_on_error(result: subprocess.CompletedProcess[str], cmd: list[str]) -> TaskFailed | None:
    if result.returncode:
        return _task_failure(cmd, result.returncode)
    return None


def _command_failure_message(cmd: list[str], exit_code: int) -> str:
    rendered_cmd = " ".join(cmd)
    return f"Command `{rendered_cmd}` failed with exit code {exit_code}. See logs above for details."


def _task_failure(cmd: list[str], exit_code: int) -> TaskFailed:
    msg = _command_failure_message(cmd, exit_code)
    return TaskFailed(msg)


def _summarize_bandit(report_path: Path) -> str:
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return f"Bandit: scan complete. See {report_path}"
    findings = data.get("results", [])
    if not findings:
        return f"Bandit: 0 findings (report: {report_path})"
    severity_counts: dict[str, int] = {}
    for finding in findings:
        severity = str(finding.get("issue_severity", "UNKNOWN")).upper()
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    summary = ", ".join(f"{level}:{count}" for level, count in sorted(severity_counts.items()))
    return f"Bandit: {len(findings)} findings ({summary}). Report: {report_path}"


def _summarize_safety(report_path: Path) -> str:
    try:
        text = report_path.read_text(encoding="utf-8")
    except OSError:
        return f"Safety: scan complete. See {report_path}"
    summary_line = next(
        (line.strip() for line in text.splitlines() if "security issues" in line.lower()),
        "Safety scan complete",
    )
    return f"{summary_line} (report: {report_path})"


def task_prettier_check() -> TaskConfig:
    """Run the Prettier formatting check used in CI.

    Returns:
        TaskConfig: doit task definition for Prettier.
    """

    def _action() -> ActionResult:
        if not PRETTIER_BIN.exists():
            msg = "Prettier not installed. Run `npm install` before invoking this task."
            raise RuntimeError(msg)
        targets = ["apps", "packages", "apps/web"]
        cmd = [
            str(PRETTIER_BIN),
            "--config",
            str(CONFIG_DIR / "prettier.config.mjs"),
            "--check",
            *targets,
        ]
        task_result = _run_task_action(cmd)
        if task_result:
            return task_result
        return None

    return _task_config(task_prettier_check.__name__, _action)


def task_ruff_check() -> TaskConfig:
    """Run ruff check with output captured under out/test_reports.

    Returns:
        TaskConfig: doit task definition for the lint job.
    """

    def _action() -> ActionResult:
        _ensure_dirs([LINT_DIR])
        output = LINT_DIR / "ruff-check.txt"
        cmd = [
            "uv",
            "run",
            "ruff",
            "check",
            ".",
        ]
        result = _run_capture(cmd)
        with output.open("w", encoding="utf-8") as log_file:
            log_file.write(result.stdout)
            if result.stderr:
                log_file.write(result.stderr)
        _emit(result)
        task_result = _raise_on_error(result, cmd)
        if task_result:
            return task_result
        return None

    return _task_config(task_ruff_check.__name__, _action)


def task_ruff_format_check() -> TaskConfig:
    """Ensure ruff format check matches CI behavior.

    Returns:
        TaskConfig: doit task definition for the format check.
    """

    def _action() -> ActionResult:
        _ensure_dirs([LINT_DIR])
        output = LINT_DIR / "ruff-format-check.txt"
        cmd = [
            "uv",
            "run",
            "ruff",
            "format",
            "--check",
            ".",
        ]
        result = subprocess.run(  # noqa: S603  # nosec B603 - Capturing known CLI output for reporting
            cmd,
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        output.write_text(result.stdout + result.stderr)
        if result.returncode:
            msg = _command_failure_message(cmd, result.returncode)
            return TaskFailed(msg)
        return None

    return _task_config(task_ruff_format_check.__name__, _action)


def task_ruff_format() -> TaskConfig:
    """Format the repository using ruff.

    Returns:
        TaskConfig: doit task definition for formatting.
    """

    def _action() -> ActionResult:
        cmd = ["uv", "run", "ruff", "format", "."]
        return _run_task_action(cmd)

    return _task_config(task_ruff_format.__name__, _action)


def task_pylint() -> TaskConfig:
    """Run pylint with logs stored under out/test_reports.

    Returns:
        TaskConfig: doit task definition for pylint.
    """

    def _action() -> ActionResult:
        _ensure_dirs([LINT_DIR])
        log_path = LINT_DIR / "pylint.json"
        cmd = [
            "uv",
            "run",
            "pylint",
            "--rcfile",
            str(CONFIG_DIR / "pylint.toml"),
            "--output-format=json",
            "--reports=n",
            "apps/",
            "packages/",
            "tooling/",
        ]
        with log_path.open("w", encoding="utf-8") as log_file:
            result = subprocess.run(  # noqa: S603  # nosec B603 - Running trusted pylint CLI for reports
                cmd,
                check=False,
                cwd=ROOT,
                stdout=log_file,
            )
        if result.returncode:
            msg = _command_failure_message(cmd, result.returncode)
            return TaskFailed(msg)
        return None

    return _task_config(task_pylint.__name__, _action)


def task_mypy() -> TaskConfig:
    """Strict mypy check mirroring CI.

    Returns:
        TaskConfig: doit task definition for mypy.
    """

    def _action() -> ActionResult:
        _ensure_dirs([TYPECHECK_DIR])
        junit_path = TYPECHECK_DIR / "mypy-junit.xml"
        cmd = [
            "uv",
            "run",
            "mypy",
            "apps/",
            "packages/",
            "tooling/",
            f"--junit-xml={junit_path}",
        ]
        task_result = _run_task_action(cmd)
        if task_result:
            return task_result
        return None

    return _task_config(task_mypy.__name__, _action)


def task_pyright() -> TaskConfig:
    """Pyright strict type checking with JSON output.

    Returns:
        TaskConfig: doit task definition for pyright.
    """

    def _action() -> ActionResult:
        _ensure_dirs([TYPECHECK_DIR])
        output = TYPECHECK_DIR / "pyright.json"
        cmd = ["uv", "run", "pyright", "--project", "configs/pyrightconfig.json"]
        result = _run_capture(cmd)
        output.write_text(result.stdout)
        _emit(result)
        task_result = _raise_on_error(result, cmd)
        if task_result:
            return task_result
        return None

    return _task_config(task_pyright.__name__, _action)


def task_quality_audit_config() -> TaskConfig:
    """Run the lightweight quality audit config validation.

    Returns:
        TaskConfig: doit task definition for the config audit.
    """

    def _action() -> ActionResult:
        _ensure_dirs([QUALITY_DIR])
        cmd = [
            "uv",
            "run",
            "python",
            "-m",
            "tooling.run_quality_audit",
            "--config-only",
        ]
        task_result = _run_task_action(cmd)
        if task_result:
            return task_result
        return None

    return _task_config(task_quality_audit_config.__name__, _action)


def task_tests() -> TaskConfig:
    """Execute pytest with coverage artifacts in out/test_reports.

    Returns:
        TaskConfig: doit task definition for pytest.
    """

    def _action() -> ActionResult:
        _ensure_dirs([COVERAGE_DIR, TEST_DIR])
        coverage_xml = COVERAGE_DIR / "coverage.xml"
        coverage_html = COVERAGE_DIR / "htmlcov"
        junit_xml = TEST_DIR / "pytest-junit.xml"
        env = {
            "COVERAGE_FILE": str(COVERAGE_DIR / ".coverage"),
        }
        cmd = [
            "uv",
            "run",
            "pytest",
            "--cov=apps",
            "--cov=packages",
            "--cov=tooling",
            f"--cov-report=xml:{coverage_xml}",
            f"--cov-report=html:{coverage_html}",
            "--cov-report=term-missing",
            "-v",
            f"--junitxml={junit_xml}",
        ]
        task_result = _run_task_action(cmd, env=env)
        if task_result:
            return task_result
        return None

    return _task_config(task_tests.__name__, _action)


def task_dependency_check() -> TaskConfig:
    """Check python dependency configuration consistency.

    Returns:
        TaskConfig: doit task definition for the dependency checker.
    """

    def _action() -> ActionResult:
        cmd = ["uv", "run", "python", "tooling/check_dependencies.py"]
        return _run_task_action(cmd)

    return _task_config(task_dependency_check.__name__, _action)


def task_bandit() -> TaskConfig:
    """Security scanning via bandit with reports under out/test_reports.

    Returns:
        TaskConfig: doit task definition for bandit.
    """

    def _action() -> ActionResult:
        _ensure_dirs([SECURITY_DIR])
        report_path = SECURITY_DIR / "bandit-report.json"
        cmd = [
            "uv",
            "run",
            "bandit",
            "-c",
            "pyproject.toml",
            "-r",
            "apps/",
            "packages/",
            "tooling/",
            "-f",
            "json",
            "-o",
            str(report_path),
        ]
        result = _run_capture(cmd)
        _emit(result)
        task_result = _raise_on_error(result, cmd)
        if task_result:
            return task_result
        sys.stdout.write(_summarize_bandit(report_path) + "\n")
        return None

    return _task_config(task_bandit.__name__, _action)


def task_safety() -> TaskConfig:
    """Safety scan replicating the CI job.

    Returns:
        TaskConfig: doit task definition for the Safety scan.
    """

    def _action() -> ActionResult:
        _ensure_dirs([SECURITY_DIR])
        report_path = SECURITY_DIR / "safety-report.json"
        cmd = [
            "uv",
            "run",
            "safety",
            "scan",
            "--json",
            "--policy-file",
            "configs/safety-policy.yml",
        ]
        result = _run_capture(cmd)
        report_path.write_text(result.stdout)
        _emit(result)
        task_result = _raise_on_error(result, cmd)
        if task_result:
            return task_result
        sys.stdout.write(_summarize_safety(report_path) + "\n")
        return None

    return _task_config(task_safety.__name__, _action)


def task_precommit() -> TaskConfig:
    """Run all pre-commit hooks.

    Returns:
        TaskConfig: doit task definition for running hooks.
    """

    def _action() -> ActionResult:
        cmd = [
            "uv",
            "run",
            "pre-commit",
            "run",
            "--config",
            "configs/pre-commit-config.yaml",
            "--all-files",
        ]
        return _run_task_action(cmd)

    return _task_config(task_precommit.__name__, _action)


def task_lint() -> TaskConfig:
    """Aggregate lint tasks for convenience.

    Returns:
        TaskConfig: doit task definition for the lint bundle.
    """
    return {"actions": [], "task_dep": ["prettier_check", "ruff_check", "ruff_format_check", "pylint"]}


def task_typecheck() -> TaskConfig:
    """Aggregate strict type checking tasks.

    Returns:
        TaskConfig: doit task definition for the typecheck bundle.
    """
    return {"actions": [], "task_dep": ["mypy", "pyright"]}


def task_security() -> TaskConfig:
    """Run all security-related checks.

    Returns:
        TaskConfig: doit task definition for the security bundle.
    """
    return {"actions": [], "task_dep": ["bandit", "safety"]}


def task_quality() -> TaskConfig:
    """Full quality gate matching CI.

    Returns:
        TaskConfig: doit task definition for the full quality suite.
    """
    return {
        "actions": [],
        "task_dep": [
            "lint",
            "typecheck",
            "tests",
            "quality_audit_config",
            "dependency_check",
        ],
    }


def task_clean_artifacts() -> TaskConfig:
    """Clean cached artifacts and test outputs.

    Returns:
        TaskConfig: doit task definition for cleaning artifacts.
    """

    def _action() -> ActionResult:
        paths = [
            ROOT / ".pytest_cache",
            ROOT / ".ruff_cache",
            ROOT / ".mypy_cache",
            ROOT / ".coverage",
            ROOT / "htmlcov",
            ROOT / "coverage.xml",
            OUT_DIR,
        ]
        for path in paths:
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
        return None

    return _task_config(task_clean_artifacts.__name__, _action)
