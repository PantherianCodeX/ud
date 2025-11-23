# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Shared runtime helpers for quality audit modules."""

from __future__ import annotations

from pathlib import Path

from udocket_utils import ensure_json_object

# Determine repo root from this file's location (tooling/quality_audit_lib/utils.py)
ROOT = Path(__file__).resolve().parent.parent.parent

__all__ = ["ROOT", "ensure_json_object"]
