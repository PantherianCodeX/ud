# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Shared runtime helpers for quality audit modules."""

from __future__ import annotations

import sys
from pathlib import Path

# Determine repo root from this file's location (tooling/quality_audit_lib/utils.py)
ROOT = Path(__file__).resolve().parent.parent.parent

_EXTRA_IMPORT_PATHS = [
    "apps/api/src",
    "apps/celery/src",
    "apps/web/src",
    "packages/udocket_domain/src",
    "packages/udocket_ai_core/src",
    "packages/udocket_utils/src",
    "packages/udocket_worker_core/src",
]


def _ensure_repo_paths() -> None:
    for relative_path in _EXTRA_IMPORT_PATHS:
        candidate = ROOT / relative_path
        candidate_str = str(candidate)
        if candidate.exists() and candidate_str not in sys.path:
            sys.path.append(candidate_str)


try:  # pragma: no cover - import guard mirrors existing script behavior
    from udocket_utils import ensure_json_object
except ModuleNotFoundError:  # pragma: no cover
    _ensure_repo_paths()
    from udocket_utils import ensure_json_object

__all__ = ["ROOT", "ensure_json_object"]
