#!/usr/bin/env python3
# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Convenience runner for the quality audit CLI."""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from collections.abc import Callable


def main() -> int:
    """Entry point that delegates to the quality audit CLI.

    Returns:
        int: Exit status propagated from the CLI implementation.

    Raises:
        SystemExit: If the module is executed directly instead of via ``python -m``.
        ModuleNotFoundError: Propagated for unexpected import failures.
    """
    try:
        cli_module = importlib.import_module("tooling.quality_audit.cli")
    except ModuleNotFoundError as exc:
        if exc.name == "tooling":
            message = (
                "Quality audit runner must be executed as a module so the repository root is importable.\n"
                "Run it via `uv run python -m tooling.run_quality_audit --help`."
            )
            raise SystemExit(message) from exc
        raise
    cli_main = cast("Callable[[], int]", cli_module.main)
    return cli_main()


if __name__ == "__main__":  # pragma: no cover - thin wrapper
    raise SystemExit(main())
