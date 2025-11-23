# Copyright (c) 2025 uDocket. All Rights Reserved.
# PROPRIETARY AND CONFIDENTIAL
"""Pydantic schemas for the intake workflow slice."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class IntakeWorkflowStatus(StrEnum):
    """Workflow stages for intake records.

    Defines the progression of an intake submission through the
    review and completion workflow.
    """

    PENDING = "pending"
    IN_REVIEW = "in_review"
    COMPLETE = "complete"


class IntakeRequest(BaseModel):
    """Request payload for starting an intake.

    Attributes:
        matter_title: Title of the legal matter being created.
        summary: Brief description of the intake content.
        client_name: Name of the client submitting the intake.
    """

    matter_title: str = Field(..., min_length=1, max_length=255)
    summary: str = Field(..., min_length=1, max_length=2000)
    client_name: str = Field(..., min_length=1, max_length=255)


class IntakeRecord(BaseModel):
    """Persistent intake record.

    Represents a submitted intake with tracking metadata for
    workflow progression.

    Attributes:
        id: Unique identifier for the record.
        matter_title: Title of the associated matter.
        client_name: Name of the submitting client.
        summary: Intake content summary.
        status: Current workflow status.
        created_at: Timestamp of record creation.
    """

    id: UUID = Field(default_factory=uuid4)
    matter_title: str
    client_name: str
    summary: str
    status: IntakeWorkflowStatus = Field(default=IntakeWorkflowStatus.PENDING)
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))


class IntakeStatus(BaseModel):
    """Aggregate status metrics for the intake workflow.

    Attributes:
        total_records: Total number of intake records.
        pending_records: Records not yet completed.
        completed_records: Records marked as complete.
    """

    total_records: int
    pending_records: int
    completed_records: int
