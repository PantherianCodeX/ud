# Copyright (c) 2025 uDocket. All Rights Reserved.
# PROPRIETARY AND CONFIDENTIAL
"""Request/response schemas for matter operations."""

from __future__ import annotations

from pydantic import BaseModel, Field


class MatterCreateRequest(BaseModel):
    """Payload for creating a matter.

    Attributes:
        title: Display title for the matter.
        description: Optional detailed description.
        matter_type: Classification of legal matter type.
    """

    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=2000)
    matter_type: str = Field(..., min_length=1, max_length=100)
