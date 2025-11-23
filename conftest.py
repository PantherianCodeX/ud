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
environment before importing ``udocket_api.core.config``. It also centralizes
pytest plugin toggles so we can keep noise down during parallel runs.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.config.argparsing import Parser

_TEST_DEFAULT_ENV = {
    "DATABASE_URL": "postgresql+asyncpg://udocket:udocket@localhost:5432/udocket",
    "JWT_SECRET_KEY": "local-development-secret",
}

for key, value in _TEST_DEFAULT_ENV.items():
    os.environ.setdefault(key, value)


def pytest_addoption(parser: Parser) -> None:
    """Register repository-wide custom CLI flags."""
    parser.addoption(
        "--enable-benchmarks",
        action="store_true",
        default=False,
        help="Allow pytest-benchmark to run (otherwise disabled when xdist is active).",
    )


def pytest_configure(config: Config) -> None:
    """Disable pytest-benchmark automatically when running tests in parallel.

    pytest-benchmark emits noisy warnings when pytest-xdist is enabled. Instead of
    relying on the plugin to disable itself, we proactively unregister it unless
    --enable-benchmarks is passed (e.g., for CI performance runs).
    """
    if config.getoption("--enable-benchmarks"):
        return
    plugin_manager = config.pluginmanager
    if plugin_manager.hasplugin("benchmark") and plugin_manager.hasplugin("xdist"):
        benchmark_plugin = plugin_manager.getplugin("benchmark")
        if benchmark_plugin is not None:
            plugin_manager.unregister(benchmark_plugin, name="benchmark")
