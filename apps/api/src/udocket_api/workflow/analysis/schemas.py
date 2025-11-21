# Copyright (c) 2025 uDocket. All Rights Reserved.
# PROPRIETARY AND CONFIDENTIAL
"""Analysis workflow schemas."""

from __future__ import annotations

import uuid  # noqa: TC003 - Pydantic uses UUID at runtime

from pydantic import BaseModel, Field


class AnalysisRequest(BaseModel):
    """Request payload for running an analysis."""

    matter_id: uuid.UUID
    transcript: str = Field(..., min_length=20, max_length=10000)
