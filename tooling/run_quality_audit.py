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
import sys
from pathlib import Path


def _load_main() -> importlib.Callable:
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:  # Ensure repo root is importable when run as a script
        sys.path.insert(0, str(repo_root))
    module = importlib.import_module("tooling.quality_audit.cli")
    return module.main


main = _load_main()

if __name__ == "__main__":  # pragma: no cover - thin wrapper
    raise SystemExit(main())
