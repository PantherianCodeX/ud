# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Workflow slice registration helpers."""

from fastapi import FastAPI

from .analysis import register_routes as register_analysis_routes
from .intake import register_routes as register_intake_routes
from .matters import register_routes as register_matter_routes

__all__ = ["register_workflows"]


def register_workflows(app: FastAPI) -> None:
    """Attach all workflow routers to the FastAPI app.

    Registers intake, matters, and analysis workflow slices
    with their respective API routes.

    Args:
        app: FastAPI application instance.
    """
    register_intake_routes(app)
    register_matter_routes(app)
    register_analysis_routes(app)
