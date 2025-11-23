# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""Analysis-related domain models."""

from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import Field

from .base import BaseEntity

IssueSeverity = Literal["low", "medium", "high", "critical"]
TimelineEventType = Literal["action", "deadline", "milestone", "other"]
ActionPriority = Literal["low", "medium", "high", "urgent"]
ActionStatus = Literal["pending", "in_progress", "completed", "cancelled"]


class Issue(BaseEntity):
    """A legal issue or concern identified in a matter.

    Represents problems, risks, or areas of concern extracted from
    matter analysis with severity classification.

    Attributes:
        matter_id: UUID of the associated matter.
        title: Brief title describing the issue.
        description: Detailed explanation of the issue.
        severity: Risk severity level (low/medium/high/critical).
        category: Classification category for the issue.
    """

    matter_id: UUID = Field(..., description="Associated matter ID")
    title: str = Field(..., min_length=1, max_length=255, description="Issue title")
    description: str = Field(..., description="Detailed description of the issue")
    severity: IssueSeverity = Field(default="medium", description="Severity level")
    category: str = Field(..., min_length=1, max_length=100, description="Issue category")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440010",
                "matter_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Asset Division Dispute",
                "description": "Disagreement over property valuation",
                "severity": "high",
                "category": "property_division",
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
            }
        }
    }


class TimelineEvent(BaseEntity):
    """A chronological event in a matter timeline.

    Represents significant dates and milestones extracted from
    matter analysis for timeline visualization.

    Attributes:
        matter_id: UUID of the associated matter.
        event_date: Date when the event occurred or is scheduled.
        event_type: Classification of the event type.
        title: Brief title describing the event.
        description: Optional detailed description.
    """

    matter_id: UUID = Field(..., description="Associated matter ID")
    event_date: date = Field(..., description="Date of the event")
    event_type: TimelineEventType = Field(..., description="Type of event")
    title: str = Field(..., min_length=1, max_length=255, description="Event title")
    description: str | None = Field(None, description="Event description")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440011",
                "matter_id": "550e8400-e29b-41d4-a716-446655440000",
                "event_date": "2025-01-10",
                "event_type": "deadline",
                "title": "Discovery Due Date",
                "description": "All discovery materials must be submitted",
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
            }
        }
    }


class Action(BaseEntity):
    """A follow-up action or task derived from matter analysis.

    Represents work items generated from analysis that require
    attention or completion with priority and assignment tracking.

    Attributes:
        matter_id: UUID of the associated matter.
        title: Brief title describing the action.
        description: Detailed explanation of what needs to be done.
        priority: Urgency level for the action.
        status: Current completion status.
        assigned_to: Name or email of the responsible person.
        due_date: Target completion date.
    """

    matter_id: UUID = Field(..., description="Associated matter ID")
    title: str = Field(..., min_length=1, max_length=255, description="Action title")
    description: str = Field(..., description="Detailed description of the action")
    priority: ActionPriority = Field(default="medium", description="Priority level")
    status: ActionStatus = Field(default="pending", description="Current status")
    assigned_to: str | None = Field(None, max_length=255, description="Assignee name or email")
    due_date: date | None = Field(None, description="Due date for completion")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440012",
                "matter_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Request property appraisal",
                "description": "Contact certified appraiser for marital home valuation",
                "priority": "high",
                "status": "pending",
                "assigned_to": "paralegal@lawfirm.com",
                "due_date": "2025-02-01",
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
            }
        }
    }


class Gap(BaseEntity):
    """An information gap or missing detail identified in matter analysis.

    Represents missing information that needs to be collected or
    clarified to complete the matter analysis.

    Attributes:
        matter_id: UUID of the associated matter.
        title: Brief description of the missing information.
        description: Detailed explanation of what is needed.
        category: Classification of the gap type.
        resolved: Whether the gap has been filled.
    """

    matter_id: UUID = Field(..., description="Associated matter ID")
    title: str = Field(..., min_length=1, max_length=255, description="Gap title")
    description: str = Field(..., description="Description of missing information")
    category: str = Field(..., min_length=1, max_length=100, description="Gap category")
    resolved: bool = Field(default=False, description="Whether gap has been resolved")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440013",
                "matter_id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "Missing financial disclosures",
                "description": "Spouse's income documentation not yet provided",
                "category": "financial",
                "resolved": False,
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
            }
        }
    }


class MatterAnalysis(BaseEntity):
    """Canonical analysis of a legal matter with all extracted information.

    Represents the complete analysis output including summary and
    vector embedding for semantic search capabilities.

    Attributes:
        matter_id: UUID of the analyzed matter.
        summary: Executive summary of the matter.
        embedding: Vector embedding for similarity search.
    """

    matter_id: UUID = Field(..., description="Associated matter ID")
    summary: str = Field(..., description="Executive summary of the matter")
    embedding: list[float] | None = Field(None, description="Vector embedding for semantic search")

    # Related entities are stored separately and joined via relationships
    # This model represents the analysis record itself

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440020",
                "matter_id": "550e8400-e29b-41d4-a716-446655440000",
                "summary": "Divorce case involving property division and custody considerations",
                "embedding": None,  # Populated by analysis service
                "created_at": "2025-01-15T10:00:00Z",
                "updated_at": "2025-01-15T10:00:00Z",
            }
        }
    }
