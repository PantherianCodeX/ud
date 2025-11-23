# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Matters workflow slice."""

from importlib import import_module

from fastapi import FastAPI

__all__ = ["register_routes"]


def register_routes(app: FastAPI) -> None:
    """Register matters API routes with the application.

    Args:
        app: FastAPI application instance.
    """
    router_module = import_module("udocket_api.workflow.matters.api.router")
    app.include_router(router_module.router)
