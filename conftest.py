# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Global pytest configuration used across the repository.

This file seeds required environment variables so that the API settings model
can be instantiated during test collection without depending on a developer's
local ``.env`` or CI secrets. Real deployments override these values via the
environment before importing ``udocket_api.core.config``.
"""

from __future__ import annotations

import os

_TEST_DEFAULT_ENV = {
    "DATABASE_URL": "postgresql+asyncpg://udocket:udocket@localhost:5432/udocket",
    "JWT_SECRET_KEY": "local-development-secret",
}

for key, value in _TEST_DEFAULT_ENV.items():
    os.environ.setdefault(key, value)
