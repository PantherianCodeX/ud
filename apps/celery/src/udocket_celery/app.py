# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Celery worker application entry point.

This module initializes the Celery app and imports all task modules
for auto-discovery and registration.

Usage:
    # Start worker with all queues
    celery -A udocket_celery.app worker --loglevel=info

    # Start worker for specific queue
    celery -A udocket_celery.app worker --loglevel=info -Q intake

    # Start Flower monitoring UI
    celery -A udocket_celery.app flower --port=5555
"""

from __future__ import annotations

# Phase 2 placeholder: the Celery app will be configured here with broker
# settings, task autodiscovery, and queue routing once background workers
# move beyond the current stub implementation.

__all__: list[str] = []  # Will export 'app' once implemented
