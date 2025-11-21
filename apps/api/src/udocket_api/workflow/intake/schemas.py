# Copyright (c) 2025 uDocket. All Rights Reserved.
# PROPRIETARY AND CONFIDENTIAL
"""Pydantic schemas for the intake workflow slice."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

IntakeStatusLiteral = Literal["pending", "in_review", "complete"]


class IntakeRequest(BaseModel):
    """Request payload for starting an intake."""

    matter_title: str = Field(..., min_length=1, max_length=255)
    summary: str = Field(..., min_length=1, max_length=2000)
    client_name: str = Field(..., min_length=1, max_length=255)


class IntakeRecord(BaseModel):
    """Persistent intake record."""

    id: UUID = Field(default_factory=uuid4)
    matter_title: str
    client_name: str
    summary: str
    status: IntakeStatusLiteral = Field(default="pending")
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))


class IntakeStatus(BaseModel):
    """Aggregate status for the slice."""

    total_records: int
    pending_records: int
    completed_records: int
