# Copyright (c) 2025 uDocket. All Rights Reserved.
#
# PROPRIETARY AND CONFIDENTIAL
#
# This software is the confidential and proprietary information of uDocket.
# You shall not disclose such confidential information and shall use it only
# in accordance with the terms of the license agreement you entered into with uDocket.
"""uDocket domain models package."""

from .analysis import (
    Action,
    ActionPriority,
    ActionStatus,
    Gap,
    Issue,
    IssueSeverity,
    MatterAnalysis,
    TimelineEvent,
    TimelineEventType,
)
from .base import BaseEntity, BaseRequest, BaseResponse, HealthCheck
from .matter import Matter, MatterStatus, Party, PartyRole, Relationship
from .transcript import SpeakerTurn, Transcript

__version__ = "0.1.0"

__all__ = [
    "Action",
    "ActionPriority",
    "ActionStatus",
    # Base
    "BaseEntity",
    "BaseRequest",
    "BaseResponse",
    "Gap",
    "HealthCheck",
    "Issue",
    "IssueSeverity",
    # Matter
    "Matter",
    # Analysis
    "MatterAnalysis",
    "MatterStatus",
    "Party",
    "PartyRole",
    "Relationship",
    "SpeakerTurn",
    "TimelineEvent",
    "TimelineEventType",
    # Transcript
    "Transcript",
]
